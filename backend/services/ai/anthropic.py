"""Claude provider — fallback for sections 5-6 when Gemini Flash fails.

Uses the Anthropic SDK (anthropic==0.36.*). Claude 3.5 Sonnet is the only
model used — it handles text-only section generation (game plan, adjustments
+ practice plan). It does NOT handle video analysis or context caching.

Do NOT import this class directly from outside services/ai/. Use
get_fallback_provider() from services/ai/router.py.
"""

import logging
import os

import anthropic

from services.ai.base import AIVideoProvider

logger = logging.getLogger(__name__)

# Model ID — update when Anthropic ships a newer Sonnet.
CLAUDE_SONNET_MODEL = "claude-3-5-sonnet-20241022"

# Max output tokens for section generation. Sections 5-6 produce detailed
# game plans and practice plans — 8192 tokens is generous but bounded.
MAX_OUTPUT_TOKENS = 8192


class ClaudeProvider(AIVideoProvider):
    """Claude 3.5 Sonnet fallback for text-only sections.

    Only analyze_text is functional. Video methods raise NotImplementedError
    because Claude is never used for sections 1-4 (video analysis).
    """

    def __init__(self):
        super().__init__()
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(
                api_key=os.environ["ANTHROPIC_API_KEY"],
            )
        return self._client

    def create_context_cache(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int = 3600,
        display_name: str | None = None,
    ) -> str:
        raise NotImplementedError("Claude does not support video context caching")

    def delete_context_cache(self, cache_uri: str) -> None:
        # No-op — Claude has no cache to delete. Safe to call from finally blocks.
        pass

    def analyze_video_cached(
        self,
        cache_uri: str,
        prompt: str,
        section_type: str,
    ) -> str:
        raise NotImplementedError("Claude does not support cached video analysis")

    def analyze_text(
        self,
        context: str,
        prompt: str,
        section_type: str,
    ) -> str:
        """Run a text-only prompt via Claude 3.5 Sonnet. Fallback for sections 5-6.

        context is the concatenated output of sections 1-4. prompt is the
        section-specific instructions from backend/prompts/*.txt.
        """
        client = self._get_client()

        full_input = f"{context}\n\n---\n\nINSTRUCTIONS:\n{prompt}"

        message = client.messages.create(
            model=CLAUDE_SONNET_MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[{"role": "user", "content": full_input}],
        )

        self.last_tokens_input = message.usage.input_tokens
        self.last_tokens_output = message.usage.output_tokens

        text = message.content[0].text if message.content else ""
        if not text.strip():
            raise RuntimeError(
                f"Claude returned empty content for section {section_type}"
            )

        logger.info(
            "Claude fallback generated section",
            extra={
                "section_type": section_type,
                "model": CLAUDE_SONNET_MODEL,
                "tokens_input": self.last_tokens_input,
                "tokens_output": self.last_tokens_output,
            },
        )
        return text
