"""Gemini provider — concrete implementation of AIVideoProvider.

Supports two backends, selected by the GEMINI_BACKEND env var:
  - "developer_api" — google-genai SDK, Gemini Developer API (original path)
  - "vertex"        — google-cloud-aiplatform / vertexai SDK, Vertex AI on GCP

SYNTHESIS-ONLY MODE (Option 3):
Sections 1-4 no longer re-read the video. They run against the full-game
synthesis document (produced during film processing and persisted in
film_analysis_cache.synthesis_document) plus the roster text. No video
Parts are sent to Gemini at section time. This removes the dependency on
Google's context caching quota (broken on both backends) and eliminates
the per-call video token cost that made long films unviable.

create_context_cache() no longer calls Google's cache API. It returns a
sentinel string carrying the text context (synthesis + roster). The
sentinel is detected by analyze_video_cached(), which sends [text_context,
prompt] as text Parts to Gemini 2.5 Pro.

The sentinel prefix is retained for wire compatibility with any in-flight
messages and so the downstream orchestrator code path does not change.
The real-cache code paths in analyze_video_cached are unreachable in this
mode — retained for future re-enablement if Google caching is fixed.

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

# Prefix returned by create_context_cache in synthesis-only mode (Option 3).
# Shared by BOTH backends. The full sentinel is `vertex:no-cache:<json>` where
# <json> carries only `text_context` — the synthesis document + roster block.
# No chunk URIs, no video. analyze_video_cached detects the prefix, parses
# the JSON, and sends [text_context, prompt] as text Parts to Gemini.
# (The "vertex:" prefix is kept for wire compatibility with any in-flight
# sentinels; the value is backend-agnostic.) This is self-contained on
# purpose — Celery prefork gives each task a fresh provider instance in a
# separate process, so instance-level stashed state does not survive across
# the chord.
NO_CACHE_PREFIX = "vertex:no-cache:"


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
        # Synthesis-only mode: do not call Google's cache API. Sections 1-4
        # run against the synthesis document + roster text only. No video.
        # ttl_seconds and display_name are retained in the signature but
        # unused here — kept to avoid touching callers.
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

        logger.info(
            "synthesis-only mode: bypassing video cache "
            "(chunk_count=%d, text_chars=%d)",
            len(chunk_uris),
            len(text_context),
        )

        payload = json.dumps({"text_context": text_context})
        return NO_CACHE_PREFIX + payload

    def _create_context_cache_vertex(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int,
        display_name: str | None,
    ) -> str:
        # Synthesis-only mode: do not call Vertex caching. Sections 1-4 run
        # against the synthesis document + roster text only. No video.
        # ttl_seconds and display_name are retained in the signature but
        # unused here — kept to avoid touching callers. _init_vertex() is
        # also not needed at this point because we never touch the Vertex
        # SDK until analyze_video_cached runs.
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

        logger.info(
            "synthesis-only mode: bypassing video cache "
            "(chunk_count=%d, text_chars=%d)",
            len(chunk_uris),
            len(text_context),
        )

        payload = json.dumps({"text_context": text_context})
        return NO_CACHE_PREFIX + payload

    # -----------------------------------------------------------------
    # delete_context_cache
    # -----------------------------------------------------------------
    def delete_context_cache(self, cache_uri: str) -> None:
        if not cache_uri or cache_uri.startswith(NO_CACHE_PREFIX):
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

        if cache_uri.startswith(NO_CACHE_PREFIX):
            payload = json.loads(cache_uri[len(NO_CACHE_PREFIX):])
            text_context: str = payload.get("text_context", "")
            if not text_context:
                raise RuntimeError(
                    "synthesis-only sentinel carried no text_context — "
                    "synthesis document missing upstream"
                )
            parts = [
                types.Part.from_text(text=text_context),
                types.Part.from_text(text=prompt),
            ]
            contents = [types.Content(role="user", parts=parts)]
            response = client.models.generate_content(
                model=GEMINI_PRO_MODEL,
                contents=contents,
            )
        else:
            # unreachable in synthesis-only mode — retained for future
            # re-enablement if Google caching is fixed.
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

        if cache_uri.startswith(NO_CACHE_PREFIX):
            payload = json.loads(cache_uri[len(NO_CACHE_PREFIX):])
            text_context: str = payload.get("text_context", "")
            if not text_context:
                raise RuntimeError(
                    "synthesis-only sentinel carried no text_context — "
                    "synthesis document missing upstream"
                )
            model = GenerativeModel(GEMINI_PRO_MODEL)
            parts = [Part.from_text(text_context), Part.from_text(prompt)]
            response = model.generate_content(parts)
        else:
            # unreachable in synthesis-only mode — retained for future
            # re-enablement if Google caching is fixed.
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
