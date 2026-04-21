from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROFILES_PATH = Path(__file__).resolve().parent / "profiles.json"


def load_hofstede_profiles(path: Path = PROFILES_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        profiles = json.load(f)
    if not isinstance(profiles, list):
        raise ValueError("profiles.json must contain a list of profiles")
    return profiles


HOFSTEDE_PROFILES = load_hofstede_profiles()
