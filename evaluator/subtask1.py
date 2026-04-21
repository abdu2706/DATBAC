from __future__ import annotations

import re


def question_overlap_f1(predicted: str, reference: str) -> float:
    """Lightweight lexical overlap for Subtask 1 question interpretation."""
    pred_tokens = set(re.findall(r"\w+", predicted.lower()))
    ref_tokens = set(re.findall(r"\w+", reference.lower()))

    if not ref_tokens:
        return 0.0
    if not pred_tokens:
        return 0.0

    overlap = len(pred_tokens & ref_tokens)
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
