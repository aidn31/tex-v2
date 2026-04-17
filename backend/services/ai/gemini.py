"""Gemini provider — concrete implementation of AIVideoProvider.

Supports two backends, selected by the GEMINI_BACKEND env var:
  - "developer_api" — google-genai SDK, Gemini Developer API (original path)
  - "vertex"        — google-cloud-aiplatform / vertexai SDK, Vertex AI on GCP

Context caching on the Developer API is what makes sections 1-4 economically
viable per COSTS.md. Vertex AI context caching is available via
vertexai.preview.caching.CachedContent on newer SDK versions; when it is not
available, create_context_cache returns a sentinel and analyze_video_cached
falls back to passing GCS URI video parts directly on each call.

Do NOT import this class directly from outside services/ai/. Use
get_ai_provider() from services/ai/router.py.
"""

import json
import logging
import os

from services.ai.base import AIVideoProvider

logger = logging.getLogger(__name__)

GEMINI_PRO_MODEL = "gemini-2.5-pro"
GEMINI_FLASH_MODEL = "gemini-2.5-flash"

# Prefix returned by create_context_cache when Vertex AI caching is unavailable.
# The full sentinel is `vertex:no-cache:<json>` where <json> encodes chunk_uris
# and text_context. analyze_video_cached detects the prefix, parses the JSON,
# and rebuilds video parts per call. This is self-contained on purpose — Celery
# prefork gives each task a fresh provider instance in a separate process, so
# instance-level stashed state does not survive across the chord.
VERTEX_NO_CACHE_PREFIX = "vertex:no-cache:"


def _backend() -> str:
    return os.environ.get("GEMINI_BACKEND", "developer_api")


class GeminiProvider(AIVideoProvider):
    def __init__(self):
        super().__init__()
        self._dev_client = None
        self._vertex_initialized = False

    # -----------------------------------------------------------------
    # Developer API client
    # -----------------------------------------------------------------
    def _get_dev_client(self):
        from google import genai

        if self._dev_client is None:
            self._dev_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        return self._dev_client

    # -----------------------------------------------------------------
    # Vertex AI initialization
    # -----------------------------------------------------------------
    def _init_vertex(self):
        if self._vertex_initialized:
            return

        import vertexai
        from google.oauth2 import service_account

        key_path = os.environ["GCP_SERVICE_ACCOUNT_KEY_PATH"]
        project = os.environ["GCP_PROJECT_ID"]
        region = os.environ["GCP_REGION"]

        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        vertexai.init(project=project, location=region, credentials=credentials)
        self._vertex_credentials = credentials
        self._vertex_initialized = True

    def _vertex_model(self, model_name: str, system_instruction: str | None = None):
        self._init_vertex()
        from vertexai.generative_models import GenerativeModel

        if system_instruction:
            return GenerativeModel(model_name, system_instruction=system_instruction)
        return GenerativeModel(model_name)

    # -----------------------------------------------------------------
    # create_context_cache
    # -----------------------------------------------------------------
    def create_context_cache(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int = 3600,
        display_name: str | None = None,
    ) -> str:
        if _backend() == "vertex":
            return self._create_context_cache_vertex(
                chunk_uris, synthesis_document, roster_text, ttl_seconds, display_name
            )
        return self._create_context_cache_dev(
            chunk_uris, synthesis_document, roster_text, ttl_seconds, display_name
        )

    def _create_context_cache_dev(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int,
        display_name: str | None,
    ) -> str:
        from google.genai import types

        client = self._get_dev_client()

        parts: list[types.Part] = [
            types.Part.from_uri(file_uri=uri, mime_type="video/mp4")
            for uri in chunk_uris
        ]

        text_blocks: list[str] = []
        if synthesis_document:
            text_blocks.append("FULL-GAME SYNTHESIS DOCUMENT:\n" + synthesis_document)
        else:
            text_blocks.append(
                "FULL-GAME SYNTHESIS DOCUMENT: "
                "(not available — synthesis failed for this film)"
            )
        text_blocks.append("ROSTER:\n" + roster_text)

        parts.append(types.Part.from_text(text="\n\n".join(text_blocks)))
        contents = [types.Content(role="user", parts=parts)]

        config = types.CreateCachedContentConfig(
            contents=contents,
            ttl=f"{ttl_seconds}s",
            display_name=display_name or "tex-report-cache",
        )

        cached = client.caches.create(model=GEMINI_PRO_MODEL, config=config)
        logger.info(
            "Gemini context cache created (developer_api)",
            extra={
                "cache_name": cached.name,
                "chunk_count": len(chunk_uris),
                "has_synthesis": bool(synthesis_document),
                "ttl_seconds": ttl_seconds,
            },
        )
        return cached.name

    def _create_context_cache_vertex(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int,
        display_name: str | None,
    ) -> str:
        self._init_vertex()

        text_blocks: list[str] = []
        if synthesis_document:
            text_blocks.append("FULL-GAME SYNTHESIS DOCUMENT:\n" + synthesis_document)
        else:
            text_blocks.append(
                "FULL-GAME SYNTHESIS DOCUMENT: "
                "(not available — synthesis failed for this film)"
            )
        text_blocks.append("ROSTER:\n" + roster_text)
        text_context = "\n\n".join(text_blocks)

        try:
            from vertexai.preview import caching
            from vertexai.generative_models import Content, Part
            import datetime

            video_parts = [
                Part.from_uri(uri=uri, mime_type="video/mp4") for uri in chunk_uris
            ]
            text_part = Part.from_text(text_context)
            contents = [Content(role="user", parts=video_parts + [text_part])]

            cached = caching.CachedContent.create(
                model_name=GEMINI_PRO_MODEL,
                contents=contents,
                ttl=datetime.timedelta(seconds=ttl_seconds),
                display_name=display_name or "tex-report-cache",
            )
            logger.info(
                "Gemini context cache created (vertex)",
                extra={
                    "cache_name": cached.name,
                    "chunk_count": len(chunk_uris),
                    "has_synthesis": bool(synthesis_document),
                    "ttl_seconds": ttl_seconds,
                },
            )
            return cached.name
        except Exception as cache_exc:
            # Vertex caching unavailable in this SDK version or for this model.
            # Encode chunk URIs + text context into the sentinel string so
            # analyze_video_cached can reconstruct parts in any worker process.
            logger.warning(
                "Vertex context caching FAILED — exc_type=%s exc_str=%r",
                type(cache_exc).__name__,
                str(cache_exc),
                exc_info=True,
                extra={"chunk_count": len(chunk_uris)},
            )
            payload = json.dumps(
                {"chunk_uris": list(chunk_uris), "text_context": text_context}
            )
            return VERTEX_NO_CACHE_PREFIX + payload

    # -----------------------------------------------------------------
    # delete_context_cache
    # -----------------------------------------------------------------
    def delete_context_cache(self, cache_uri: str) -> None:
        if not cache_uri or cache_uri.startswith(VERTEX_NO_CACHE_PREFIX):
            return
        try:
            if _backend() == "vertex":
                from vertexai.preview import caching

                caching.CachedContent(cached_content_name=cache_uri).delete()
            else:
                client = self._get_dev_client()
                client.caches.delete(name=cache_uri)
            logger.info("Gemini context cache deleted", extra={"cache_name": cache_uri})
        except Exception:
            logger.warning(
                "Gemini context cache deletion failed — weekly maintenance will catch it",
                extra={"cache_name": cache_uri},
                exc_info=True,
            )

    # -----------------------------------------------------------------
    # analyze_video_cached
    # -----------------------------------------------------------------
    def analyze_video_cached(
        self,
        cache_uri: str,
        prompt: str,
        section_type: str,
    ) -> str:
        if _backend() == "vertex":
            return self._analyze_video_cached_vertex(cache_uri, prompt, section_type)
        return self._analyze_video_cached_dev(cache_uri, prompt, section_type)

    def _analyze_video_cached_dev(self, cache_uri: str, prompt: str, section_type: str) -> str:
        from google.genai import types

        client = self._get_dev_client()
        config = types.GenerateContentConfig(cached_content=cache_uri)
        response = client.models.generate_content(
            model=GEMINI_PRO_MODEL,
            contents=[prompt],
            config=config,
        )

        usage = getattr(response, "usage_metadata", None)
        if usage:
            self.last_tokens_input = getattr(usage, "prompt_token_count", 0) or 0
            self.last_tokens_output = getattr(usage, "candidates_token_count", 0) or 0
        else:
            self.last_tokens_input = 0
            self.last_tokens_output = 0

        text = response.text or ""
        if not text.strip():
            raise RuntimeError(f"Gemini returned empty content for section {section_type}")
        return text

    def _analyze_video_cached_vertex(
        self, cache_uri: str, prompt: str, section_type: str
    ) -> str:
        from vertexai.generative_models import GenerativeModel, Part

        self._init_vertex()

        if cache_uri.startswith(VERTEX_NO_CACHE_PREFIX):
            payload = json.loads(cache_uri[len(VERTEX_NO_CACHE_PREFIX):])
            chunk_uris: list[str] = payload.get("chunk_uris", [])
            text_context: str = payload.get("text_context", "")
            if not chunk_uris:
                raise RuntimeError(
                    "Vertex no-cache sentinel carried no chunk URIs"
                )
            model = GenerativeModel(GEMINI_PRO_MODEL)
            parts = [
                Part.from_uri(uri=uri, mime_type="video/mp4") for uri in chunk_uris
            ]
            if text_context:
                parts.append(Part.from_text(text_context))
            parts.append(Part.from_text(prompt))
            response = model.generate_content(parts)
        else:
            from vertexai.preview import caching
            from vertexai.preview.generative_models import GenerativeModel as PreviewModel

            cached = caching.CachedContent(cached_content_name=cache_uri)
            model = PreviewModel.from_cached_content(cached_content=cached)
            response = model.generate_content(prompt)

        usage = getattr(response, "usage_metadata", None)
        if usage:
            self.last_tokens_input = getattr(usage, "prompt_token_count", 0) or 0
            self.last_tokens_output = getattr(usage, "candidates_token_count", 0) or 0
        else:
            self.last_tokens_input = 0
            self.last_tokens_output = 0

        text = response.text or ""
        if not text.strip():
            raise RuntimeError(f"Gemini returned empty content for section {section_type}")
        return text

    # -----------------------------------------------------------------
    # analyze_text
    # -----------------------------------------------------------------
    def analyze_text(self, context: str, prompt: str, section_type: str) -> str:
        full_input = f"{context}\n\n---\n\nINSTRUCTIONS:\n{prompt}"

        if _backend() == "vertex":
            model = self._vertex_model(GEMINI_FLASH_MODEL)
            response = model.generate_content(full_input)
        else:
            client = self._get_dev_client()
            response = client.models.generate_content(
                model=GEMINI_FLASH_MODEL,
                contents=[full_input],
            )

        usage = getattr(response, "usage_metadata", None)
        if usage:
            self.last_tokens_input = getattr(usage, "prompt_token_count", 0) or 0
            self.last_tokens_output = getattr(usage, "candidates_token_count", 0) or 0
        else:
            self.last_tokens_input = 0
            self.last_tokens_output = 0

        text = response.text or ""
        if not text.strip():
            raise RuntimeError(
                f"Gemini Flash returned empty content for section {section_type}"
            )
        return text
