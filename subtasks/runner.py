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


def _strip_profile_mentions(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("[ERROR]"):
        return cleaned

    banned = [
        r"\bprofile\b",
        r"\bcultural profile\b",
        r"\bcommunication profile\b",
        r"\bhofstede\b",
        r"\bpower distance\b",
        r"\bindividualism\b",
        r"\bcollectivism\b",
        r"\buncertainty avoidance\b",
        r"\blong-term orientation\b",
        r"\bshort-term orientation\b",
        r"\bindulgence\b",
        r"\brestraint\b",
        r"\bPDI\b",
        r"\bIDV\b",
        r"\bUAI\b",
        r"\bMAS\b",
        r"\bLTO\b",
        r"\bIVR\b",
        r"based on the cultural communication profile",
        r"\bin this culture\b",
        r"\bfor this profile\b",
    ]

    def has_banned(sentence: str) -> bool:
        return any(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in banned)

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    kept = [sentence for sentence in sentences if sentence and not has_banned(sentence)]
    if kept:
        return " ".join(kept)

    # Fallback: strip banned terms inline if all sentences were removed.
    for pattern in banned:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


class SubtaskRunner:
    def __init__(self, llm: OllamaRunner, processing: str = "legacy", attempt_sink=None):
        self.llm = llm
        self.processing = processing
        self.attempt_sink = attempt_sink
        self.last_attempt = None

    def run_subtask(
        self,
        subtask: int,
        case: dict,
        system_prompt: str,
        model: str,
        answer_text: str | None = None,
        extra_instructions: str | None = None,
    ) -> str:
        if subtask != 3:
            raise ValueError("This run configuration supports Subtask 3 only")

        user_prompt = build_subtask3_prompt(case)
        if extra_instructions:
            user_prompt = f"{extra_instructions}\n\n{user_prompt}"

        self.last_attempt = None
        raw = self.llm.generate(model, system_prompt, user_prompt)
        cleaned = (_limit_words(_strip_profile_mentions(raw), 75)
                   if self.processing == "legacy" else raw)
        self.last_attempt = {
            **getattr(self, "context", {}),
            "model": model, "case_id": case.get("case_id"),
            "system_prompt": system_prompt, "user_prompt": user_prompt,
            "extra_instructions": extra_instructions,
            "raw_response": raw, "processed_response": cleaned,
            "raw_word_count": len(raw.split()),
            "processed_word_count": len(cleaned.split()),
            "processing": self.processing,
        }
        # Persist before validation/scoring so a later failure cannot discard output.
        if self.attempt_sink:
            self.attempt_sink(self.last_attempt)
        return cleaned
