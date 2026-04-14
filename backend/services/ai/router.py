"""AI provider router — the ONLY place where concrete providers are imported.

Everywhere else in the codebase calls get_ai_provider() / get_fallback_provider()
and uses the abstract AIVideoProvider interface from services/ai/base.py. This is
enforced by CLAUDE.md AI PROVIDER RULES — search for 'services.ai.gemini' or
'services.ai.anthropic' in the repo; they should only appear in this file.
"""

import os

from services.ai.base import AIVideoProvider
from services.ai.anthropic import ClaudeProvider
from services.ai.gemini import GeminiProvider


def get_ai_provider() -> AIVideoProvider:
    """Return a configured video provider based on AI_VIDEO_PROVIDER env var.

    Default: gemini. Only 'gemini' is supported at launch. Used for sections
    1-4 (video via context cache) and sections 5-6 primary path (Flash text).
    """
    provider = os.environ.get("AI_VIDEO_PROVIDER", "gemini")
    if provider == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown AI_VIDEO_PROVIDER: {provider}")


def get_fallback_provider() -> AIVideoProvider:
    """Return the fallback provider for sections 5-6 when Gemini Flash fails.

    Per CLAUDE.md AI PROVIDER RULES: sections 5-6 use Gemini 2.5 Flash
    primary, Claude 3.5 Sonnet fallback. The fallback fires automatically
    with no manual intervention.
    """
    return ClaudeProvider()
