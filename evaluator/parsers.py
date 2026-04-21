from __future__ import annotations

import json
import re


def parse_sentence_ids(response: str) -> list[str]:
    """Extract sentence IDs from LLM response (expects JSON array)."""
    try:
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            ids = json.loads(match.group())
            return [str(i) for i in ids]
    except (json.JSONDecodeError, ValueError):
        pass
    return re.findall(r"\b(\d+)\b", response)


def parse_alignment(response: str) -> list[dict]:
    """Parse alignment JSON from LLM response."""
    try:
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        pass
    return []
