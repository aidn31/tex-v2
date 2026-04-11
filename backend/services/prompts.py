"""Prompt file loader. Reads backend/prompts/*.txt files in the exact format
documented in PROMPTS.md → HOW PROMPTS ARE LOADED:

    VERSION: v1.0
    CHANGELOG:
      v1.0 — Initial version.
    ---
    [prompt text]

The `---` delimiter is on its own line. Everything after it is the prompt body.
"""

import os
from pathlib import Path

# backend/prompts/ is a sibling of services/
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(section_type: str) -> tuple[str, str]:
    """Load a prompt file and return (prompt_text, version).

    section_type matches the filename without extension, e.g. 'offensive_sets'
    for backend/prompts/offensive_sets.txt.
    """
    path = PROMPTS_DIR / f"{section_type}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    raw = path.read_text()
    first_line, _, rest = raw.partition("\n")
    if not first_line.startswith("VERSION:"):
        raise ValueError(f"Prompt file {path} missing VERSION header")
    version = first_line.replace("VERSION:", "").strip()

    # Split on --- delimiter — must be on its own line
    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"Prompt file {path} missing --- delimiter")
    prompt_text = parts[1].strip()

    return prompt_text, version
