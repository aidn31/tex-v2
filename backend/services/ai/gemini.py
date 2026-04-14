"""Gemini provider — concrete implementation of AIVideoProvider.

Uses google-genai (the current SDK — do NOT import google.generativeai).
Context caching is the mechanism that makes sections 1-4 economically viable
per COSTS.md: without it, every section re-reads the full film at $2.50/M
video input tokens.

Do NOT import this class directly from outside services/ai/. Use
get_ai_provider() from services/ai/router.py.
"""

import logging
import os

from google import genai
from google.genai import types

from services.ai.base import AIVideoProvider

logger = logging.getLogger(__name__)

# Model IDs — update when Gemini ships a new version.
GEMINI_PRO_MODEL = "gemini-2.5-pro"
GEMINI_FLASH_MODEL = "gemini-2.5-flash"


class GeminiProvider(AIVideoProvider):
    def __init__(self):
        super().__init__()
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Create a fresh client per worker instance.

        The SDK is not guaranteed thread-safe across Celery workers, and
        creating one is cheap. One per GeminiProvider instance is fine —
        the provider itself is short-lived per task.
        """
        if self._client is None:
            self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        return self._client

    def create_context_cache(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int = 3600,
        display_name: str | None = None,
    ) -> str:
        """Build a Gemini context cache containing video chunks + roster + synthesis.

        The cache is created under the Pro model since sections 1-4 run
        against it. TTL is 1 hour by default — enough for a full chord to
        complete. The returned cache name is the string used by
        analyze_video_cached and delete_context_cache.
        """
        client = self._get_client()

        # Video chunks — one Part per chunk URI. Gemini reads them in order.
        parts: list[types.Part] = [
            types.Part.from_uri(file_uri=uri, mime_type="video/mp4")
            for uri in chunk_uris
        ]

        # Text context — synthesis document first (if available), then roster.
        # Sections 1-4 see this as the cached user-turn content.
        text_blocks: list[str] = []
        if synthesis_document:
            text_blocks.append(
                "FULL-GAME SYNTHESIS DOCUMENT:\n" + synthesis_document
            )
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
            "Gemini context cache created",
            extra={
                "cache_name": cached.name,
                "chunk_count": len(chunk_uris),
                "has_synthesis": bool(synthesis_document),
                "ttl_seconds": ttl_seconds,
            },
        )
        return cached.name

    def delete_context_cache(self, cache_uri: str) -> None:
        """Delete a cache. Swallows errors by design — called from finally blocks."""
        if not cache_uri:
            return
        try:
            client = self._get_client()
            client.caches.delete(name=cache_uri)
            logger.info("Gemini context cache deleted", extra={"cache_name": cache_uri})
        except Exception:
            logger.warning(
                "Gemini context cache deletion failed — weekly maintenance will catch it",
                extra={"cache_name": cache_uri},
                exc_info=True,
            )

    def analyze_video_cached(
        self,
        cache_uri: str,
        prompt: str,
        section_type: str,
    ) -> str:
        """Run a section prompt against a cached context and return the text output.

        Writes token counts to self.last_tokens_input / last_tokens_output
        so the caller (run_section) can persist them to report_sections.
        """
        client = self._get_client()

        config = types.GenerateContentConfig(cached_content=cache_uri)
        response = client.models.generate_content(
            model=GEMINI_PRO_MODEL,
            contents=[prompt],
            config=config,
        )

        # Usage metadata may not exist on every response — default to 0.
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
                f"Gemini returned empty content for section {section_type}"
            )
        return text

    def analyze_text(
        self,
        context: str,
        prompt: str,
        section_type: str,
    ) -> str:
        """Run a text-only prompt via Gemini 2.5 Flash. For sections 5-6.

        context is the concatenated output of sections 1-4. prompt is the
        section-specific instructions from backend/prompts/*.txt.
        """
        client = self._get_client()

        full_input = f"{context}\n\n---\n\nINSTRUCTIONS:\n{prompt}"

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
