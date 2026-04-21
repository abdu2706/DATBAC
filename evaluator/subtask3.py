from __future__ import annotations

import math
import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").lower())


def _set_f1(pred: set[str], gold: set[str]) -> float:
    if not pred and not gold:
        return 1.0
    if not pred or not gold:
        return 0.0
    overlap = len(pred & gold)
    p = overlap / len(pred)
    r = overlap / len(gold)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def _ngrams(tokens: list[str], n: int) -> Counter[tuple[str, ...]]:
    if n <= 0 or len(tokens) < n:
        return Counter()
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def _lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def bleu_score(generated: str, reference: str, max_n: int = 4) -> float:
    gen = _tokens(generated)
    ref = _tokens(reference)
    if not gen or not ref:
        return 0.0

    precisions: list[float] = []
    for n in range(1, max_n + 1):
        gen_ngrams = _ngrams(gen, n)
        ref_ngrams = _ngrams(ref, n)
        if not gen_ngrams:
            precisions.append(0.0)
            continue
        overlap = sum(min(count, ref_ngrams[gram]) for gram, count in gen_ngrams.items())
        precisions.append(overlap / sum(gen_ngrams.values()))

    smooth = 1e-9
    log_precision = sum(math.log(max(p, smooth)) for p in precisions) / max_n
    bp = 1.0 if len(gen) > len(ref) else math.exp(1.0 - (len(ref) / max(len(gen), 1)))
    return max(0.0, min(1.0, bp * math.exp(log_precision)))


def rouge_l_f1(generated: str, reference: str) -> float:
    gen = _tokens(generated)
    ref = _tokens(reference)
    if not gen or not ref:
        return 0.0
    lcs = _lcs_length(gen, ref)
    p = lcs / len(gen)
    r = lcs / len(ref)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def sari_score(source: str, generated: str, reference: str) -> float:
    src = set(_tokens(source))
    pred = set(_tokens(generated))
    ref = set(_tokens(reference))

    keep_pred = pred & src
    keep_gold = ref & src
    keep_f1 = _set_f1(keep_pred, keep_gold)

    add_pred = pred - src
    add_gold = ref - src
    add_f1 = _set_f1(add_pred, add_gold)

    del_pred = src - pred
    del_gold = src - ref
    del_precision = len(del_pred & del_gold) / len(del_pred) if del_pred else 0.0

    return max(0.0, min(1.0, (keep_f1 + add_f1 + del_precision) / 3.0))


def bertscore_proxy(generated: str, reference: str) -> float:
    # Proxy based on token overlap F1; replace with embedding-based BERTScore if needed.
    return _set_f1(set(_tokens(generated)), set(_tokens(reference)))


def alignscore_proxy(generated: str, reference: str, note_excerpt: str) -> float:
    # Reward answers that both align with the reference and stay supported by note content.
    ref_align = bertscore_proxy(generated, reference)
    note_support = _set_f1(set(_tokens(generated)), set(_tokens(note_excerpt)))
    return max(0.0, min(1.0, 0.6 * ref_align + 0.4 * note_support))


def medcon_score(generated: str, reference: str) -> float:
    medical_terms = {
        "pain",
        "fever",
        "blood",
        "pressure",
        "heart",
        "lung",
        "kidney",
        "liver",
        "diabetes",
        "hypertension",
        "infection",
        "antibiotic",
        "medication",
        "dose",
        "surgery",
        "treatment",
        "diagnosis",
        "symptom",
        "follow",
        "discharge",
    }

    gen = set(_tokens(generated))
    ref = set(_tokens(reference))
    gen_med = {t for t in gen if t in medical_terms or len(t) > 6}
    ref_med = {t for t in ref if t in medical_terms or len(t) > 6}
    return _set_f1(gen_med, ref_med)


def compute_subtask3_metrics(
    generated: str,
    reference: str,
    patient_question: str,
    clinician_question: str,
    note_excerpt: str,
) -> dict[str, float]:
    source = " ".join([patient_question or "", clinician_question or "", note_excerpt or ""])
    bleu = bleu_score(generated, reference)
    rouge = rouge_l_f1(generated, reference)
    sari = sari_score(source, generated, reference)
    bert = bertscore_proxy(generated, reference)
    align = alignscore_proxy(generated, reference, note_excerpt)
    medcon = medcon_score(generated, reference)

    return {
        "st3_bleu": bleu,
        "st3_rouge": rouge,
        "st3_sari": sari,
        "st3_bertscore": bert,
        "st3_alignscore": align,
        "st3_medcon": medcon,
        "st3_bleu_pct": bleu * 100.0,
        "st3_rouge_pct": rouge * 100.0,
        "st3_sari_pct": sari * 100.0,
        "st3_bertscore_pct": bert * 100.0,
        "st3_alignscore_pct": align * 100.0,
        "st3_medcon_pct": medcon * 100.0,
    }


def compute_word_overlap(generated: str, reference: str) -> float:
    """Backward-compatible alias for simple overlap."""
    return _set_f1(set(_tokens(generated)), set(_tokens(reference)))
