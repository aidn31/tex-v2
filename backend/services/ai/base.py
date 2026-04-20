"""Abstract interface for AI video providers.

Every concrete provider (gemini.py, anthropic.py) subclasses this and
implements every method. The router (router.py) is the only place in the
codebase that imports concrete providers — everywhere else uses
get_ai_provider() and the abstract interface below.

Per CLAUDE.md AI PROVIDER RULES:
    from services.ai.gemini import GeminiProvider  # ← NEVER do this
    from services.ai.router import get_ai_provider  # ← always this
"""

from abc import ABC, abstractmethod


class AIVideoProvider(ABC):
    """Abstract interface for video analysis providers.

    Implementations track the most recent call's token usage on instance
    attributes so callers can log cost and capacity metrics without
    threading usage through the return value.
    """

    def __init__(self):
        self.last_tokens_input: int = 0
        self.last_tokens_output: int = 0

    @abstractmethod
    def create_context_cache(
        self,
        chunk_uris: list[str],
        synthesis_document: str | None,
        roster_text: str,
        ttl_seconds: int = 3600,
        display_name: str | None = None,
    ) -> str:
        """Create a provider-side context cache from film chunks + text context.

        Returns a cache identifier (opaque string) suitable for passing to
        analyze_video_cached and delete_context_cache.

        synthesis_document may be None if Prompt 0B failed for this film —
        per SCHEMA.md films.synthesis_failed. Sections 1-4 degrade gracefully.
        """
        ...

    @abstractmethod
    def delete_context_cache(self, cache_uri: str) -> None:
        """Delete a previously created context cache.

        Should not raise on failure — callers rely on this running in a
        finally block and a failure here must not block report delivery.
        """
        ...

    @abstractmethod
    def analyze_video_cached(
        self,
        cache_uri: str,
        prompt: str,
        section_type: str,
    ) -> str:
        """Run a prompt against an existing context cache. Returns generated text.

        Updates last_tokens_input and last_tokens_output after the call.
        section_type is passed through for logging / metrics only.
        """
        ...

    @abstractmethod
    def analyze_video(
        self,
        uris: list[str],
        prompt: str,
        section_type: str,
    ) -> str:
        """Run a prompt against raw video URIs with no context cache.

        Used by Prompt 0A (chunk extraction) during film pre-processing —
        each chunk is analyzed individually, so a shared cache would be
        wasted setup. uris may contain one or more video URIs (Developer
        API file names or gs:// paths); the implementation builds video
        Parts + a text prompt Part.

        Updates last_tokens_input and last_tokens_output after the call.
        """
        ...

    @abstractmethod
    def analyze_text(
        self,
        context: str,
        prompt: str,
        section_type: str,
    ) -> str:
        """Run a text-only prompt (no video, no cache). Returns generated text.

        Used by sections 5-6 which take completed section 1-4 output as
        context. The concrete Gemini implementation uses Flash; the Claude
        fallback (task 3.6) uses Sonnet.

        Updates last_tokens_input and last_tokens_output after the call.
        """
        ...
