from __future__ import annotations

import re

from llm_runner import OllamaRunner
from subtasks.subtask3 import build_prompt as build_subtask3_prompt


def _limit_words(text: str, max_words: int = 75) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("[ERROR]"):
        return cleaned
    words = re.findall(r"\S+", cleaned)
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])


class SubtaskRunner:
    def __init__(self, llm: OllamaRunner):
        self.llm = llm

    def run_subtask(
        self,
        subtask: int,
        case: dict,
        system_prompt: str,
        model: str,
        answer_text: str | None = None,
    ) -> str:
        if subtask != 3:
            raise ValueError("This run configuration supports Subtask 3 only")

        user_prompt = build_subtask3_prompt(case)

        raw = self.llm.generate(model, system_prompt, user_prompt)
        return _limit_words(raw, 75)
