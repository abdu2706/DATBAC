"""Official metrics plus legacy exploratory proxy metrics for Subtask 3."""
from __future__ import annotations

import importlib
import math
import os
import re
from collections import Counter
from functools import lru_cache


OFFICIAL_METRIC_KEYS = (
    "st3_bleu",
    "st3_rouge_l",
    "st3_sari",
    "st3_bertscore",
    "st3_alignscore",
    "st3_medcon",
)

_LAST_OFFICIAL_STATUS: dict[str, str] = {}


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


def bleu_local(generated: str, reference: str, max_n: int = 4) -> float:
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


def rouge_l_local(generated: str, reference: str) -> float:
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


def sari_unigram_proxy(source: str, generated: str, reference: str) -> float:
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


def token_overlap_f1_proxy(generated: str, reference: str) -> float:
    # Lexical set overlap only; not embedding-based BERTScore.
    return _set_f1(set(_tokens(generated)), set(_tokens(reference)))


def weighted_overlap_proxy(generated: str, reference: str, note_excerpt: str) -> float:
    # Reward answers that both align with the reference and stay supported by note content.
    ref_align = token_overlap_f1_proxy(generated, reference)
    note_support = _set_f1(set(_tokens(generated)), set(_tokens(note_excerpt)))
    return max(0.0, min(1.0, 0.6 * ref_align + 0.4 * note_support))


def medical_lexical_f1_proxy(generated: str, reference: str) -> float:
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


def _unavailable(metric: str, reason: str) -> None:
    _LAST_OFFICIAL_STATUS[metric] = f"unavailable: {reason}"


@lru_cache(maxsize=1)
def _load_rouge():
    return importlib.import_module("rouge_score.rouge_scorer").RougeScorer(
        ["rougeL"], use_stemmer=True
    )


@lru_cache(maxsize=1)
def _load_bert_scorer():
    bert_score = importlib.import_module("bert_score")
    return bert_score.BERTScorer(lang="en", rescale_with_baseline=False)


@lru_cache(maxsize=1)
def _load_alignscore_scorer(ckpt_path: str):
    alignscore = importlib.import_module("alignscore")
    return alignscore.AlignScore(
        model="roberta-large",
        ckpt_path=ckpt_path,
        evaluation_mode="nli",
    )


@lru_cache(maxsize=1)
def _load_medcon_scorer(module_name: str):
    module = importlib.import_module(module_name)
    return module.UMLSScorer()


def _official_scores(
    generated: str,
    reference: str,
    source: str,
    note_excerpt: str,
) -> dict[str, float | None]:
    _LAST_OFFICIAL_STATUS.clear()
    scores: dict[str, float | None] = {key: None for key in OFFICIAL_METRIC_KEYS}

    try:
        sacrebleu = importlib.import_module("sacrebleu")
        scores["st3_bleu"] = float(
            sacrebleu.sentence_bleu(generated, [reference]).score / 100.0
        )
        _LAST_OFFICIAL_STATUS["st3_bleu"] = "ok"
    except Exception as exc:
        _unavailable("st3_bleu", f"{type(exc).__name__}: {exc}")

    try:
        rouge = _load_rouge().score(reference, generated)["rougeL"].fmeasure
        scores["st3_rouge_l"] = float(rouge)
        _LAST_OFFICIAL_STATUS["st3_rouge_l"] = "ok"
    except Exception as exc:
        _unavailable("st3_rouge_l", f"{type(exc).__name__}: {exc}")

    try:
        sari = importlib.import_module("easse.sari")
        scores["st3_sari"] = float(
            sari.corpus_sari([source], [generated], [[reference]]) / 100.0
        )
        _LAST_OFFICIAL_STATUS["st3_sari"] = "ok"
    except Exception as exc:
        _unavailable("st3_sari", f"{type(exc).__name__}: {exc}")

    try:
        _, _, f1 = _load_bert_scorer().score([generated], [reference])
        scores["st3_bertscore"] = float(f1[0].item())
        _LAST_OFFICIAL_STATUS["st3_bertscore"] = "ok"
    except Exception as exc:
        _unavailable("st3_bertscore", f"{type(exc).__name__}: {exc}")

    try:
        ckpt_path = os.environ.get("ALIGNSCORE_CKPT_PATH")
        if not ckpt_path:
            raise RuntimeError("set ALIGNSCORE_CKPT_PATH to an AlignScore checkpoint")
        scorer = _load_alignscore_scorer(ckpt_path)
        scores["st3_alignscore"] = float(
            scorer.score(contexts=[note_excerpt], claims=[generated])[0]
        )
        _LAST_OFFICIAL_STATUS["st3_alignscore"] = "ok"
    except Exception as exc:
        _unavailable("st3_alignscore", f"{type(exc).__name__}: {exc}")

    try:
        module_name = os.environ.get("MEDCON_SCORER_MODULE", "src.UMLSScorer")
        scores["st3_medcon"] = float(
            _load_medcon_scorer(module_name)(generated, reference)
        )
        _LAST_OFFICIAL_STATUS["st3_medcon"] = "ok"
    except Exception as exc:
        _unavailable("st3_medcon", f"{type(exc).__name__}: {exc}")

    return scores


def get_official_metric_status() -> dict[str, str]:
    """Return statuses from the most recent official metric evaluation."""
    return dict(_LAST_OFFICIAL_STATUS)


def compute_subtask3_metrics(
    generated: str,
    reference: str,
    patient_question: str,
    clinician_question: str,
    note_excerpt: str,
) -> dict[str, float]:
    source = " ".join([patient_question or "", clinician_question or "", note_excerpt or ""])
    bleu = bleu_local(generated, reference)
    rouge = rouge_l_local(generated, reference)
    sari = sari_unigram_proxy(source, generated, reference)
    bert = token_overlap_f1_proxy(generated, reference)
    align = weighted_overlap_proxy(generated, reference, note_excerpt)
    medcon = medical_lexical_f1_proxy(generated, reference)

    metrics = {
        "st3_bleu_local": bleu,
        "st3_rouge_l_local": rouge,
        "st3_sari_unigram_proxy": sari,
        "st3_token_overlap_f1_proxy": bert,
        "st3_weighted_overlap_proxy": align,
        "st3_medical_lexical_f1_proxy": medcon,
        "st3_bleu_local_pct": bleu * 100.0,
        "st3_rouge_l_local_pct": rouge * 100.0,
        "st3_sari_unigram_proxy_pct": sari * 100.0,
        "st3_token_overlap_f1_proxy_pct": bert * 100.0,
        "st3_weighted_overlap_proxy_pct": align * 100.0,
        "st3_medical_lexical_f1_proxy_pct": medcon * 100.0,
    }
    metrics.update(_official_scores(generated, reference, source, note_excerpt))
    for key in OFFICIAL_METRIC_KEYS:
        metrics[f"{key}_pct"] = (
            metrics[key] * 100.0 if metrics[key] is not None else None
        )
    return metrics


def compute_word_overlap(generated: str, reference: str) -> float:
    """Backward-compatible alias for simple overlap."""
    return _set_f1(set(_tokens(generated)), set(_tokens(reference)))
