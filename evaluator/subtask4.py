from __future__ import annotations

import re


def alignment_f1(predicted: list[dict], gold_answer: str) -> dict[str, float]:
    """Compute P/R/F1 for answer-evidence alignment links."""
    gold_links: set[tuple[str, str]] = set()

    answer_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", gold_answer) if s.strip()]
    for i, sent in enumerate(answer_sents, 1):
        citations = re.findall(r"\[([^\]]+)\]", sent)
        for cite_group in citations:
            for cid in re.findall(r"\d+", cite_group):
                gold_links.add((str(i), cid))

    pred_links: set[tuple[str, str]] = set()
    for item in predicted:
        aid = str(item.get("answer_id", ""))
        for eid in item.get("evidence_id", []):
            pred_links.add((aid, str(eid)))

    if not pred_links and not gold_links:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not pred_links:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    if not gold_links:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = len(pred_links & gold_links)
    precision = tp / len(pred_links)
    recall = tp / len(gold_links)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}
