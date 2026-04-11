"""AI provider router — the ONLY place where concrete providers are imported.

Everywhere else in the codebase calls get_ai_provider() and uses the abstract
AIVideoProvider interface from services/ai/base.py. This is enforced by
CLAUDE.md AI PROVIDER RULES — search for 'services.ai.gemini' in the repo;
it should only appear in this file.
"""

import os

from services.ai.base import AIVideoProvider
from services.ai.gemini import GeminiProvider


def get_ai_provider() -> AIVideoProvider:
    """Return a configured video provider based on AI_VIDEO_PROVIDER env var.

    Default: gemini. Only 'gemini' is supported at launch. Anthropic Claude
    is a sections 5-6 fallback, not a video provider — it lives in a
    different code path (task 3.5).
    """
    provider = os.environ.get("AI_VIDEO_PROVIDER", "gemini")
    if provider == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown AI_VIDEO_PROVIDER: {provider}")
