"""Scientific metrics for Subtask 3."""
from __future__ import annotations

import importlib
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path


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


def _f1_from_counts(overlap: int, predicted: int, reference: int) -> float:
    if predicted == 0 and reference == 0:
        return 1.0
    if predicted == 0 or reference == 0:
        return 0.0
    precision = overlap / predicted
    recall = overlap / reference
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def sari_score(source: str, generated: str, reference: str, max_n: int = 4) -> float:
    """Compute the standard single-reference SARI score in the [0, 1] range."""
    source_tokens = _tokens(source)
    generated_tokens = _tokens(generated)
    reference_tokens = _tokens(reference)
    operation_scores: list[float] = []

    for n in range(1, max_n + 1):
        source_ngrams = set(_ngrams(source_tokens, n))
        generated_ngrams = set(_ngrams(generated_tokens, n))
        reference_ngrams = set(_ngrams(reference_tokens, n))

        keep_generated = generated_ngrams & source_ngrams
        keep_reference = reference_ngrams & source_ngrams
        keep_overlap = len(keep_generated & keep_reference)
        operation_scores.append(
            _f1_from_counts(
                keep_overlap, len(keep_generated), len(keep_reference)
            )
        )

        add_generated = generated_ngrams - source_ngrams
        add_reference = reference_ngrams - source_ngrams
        add_overlap = len(add_generated & add_reference)
        operation_scores.append(
            _f1_from_counts(add_overlap, len(add_generated), len(add_reference))
        )

        delete_generated = source_ngrams - generated_ngrams
        delete_reference = source_ngrams - reference_ngrams
        delete_overlap = len(delete_generated & delete_reference)
        operation_scores.append(
            _f1_from_counts(
                delete_overlap, len(delete_generated), len(delete_reference)
            )
        )

    return sum(operation_scores) / len(operation_scores) if operation_scores else 0.0


def medical_lexical_f1_proxy(generated: str, reference: str) -> float:
    """Legacy lexical medical-term overlap; not the scientific MEDCON metric."""
    medical_terms = {
        "pain", "fever", "blood", "pressure", "heart", "lung", "kidney",
        "liver", "diabetes", "hypertension", "infection", "antibiotic",
        "medication", "dose", "surgery", "treatment", "diagnosis",
        "symptom", "follow", "discharge",
    }
    generated_terms = set(_tokens(generated))
    reference_terms = set(_tokens(reference))
    generated_terms = {
        term for term in generated_terms
        if term in medical_terms or len(term) > 6
    }
    reference_terms = {
        term for term in reference_terms
        if term in medical_terms or len(term) > 6
    }
    return _set_f1(generated_terms, reference_terms)


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
        batch_size=8,
        device="cpu",
        ckpt_path=ckpt_path,
        evaluation_mode="nli",
        verbose=False,
    )


@lru_cache(maxsize=1)
def _load_medcon_scorer(module_name: str):
    module = importlib.import_module(module_name)
    return module.UMLSScorer()


def _alignscore_checkpoint() -> str | None:
    configured = os.environ.get("ALIGNSCORE_CKPT_PATH")
    if configured:
        return configured

    project_checkpoint = (
        Path(__file__).resolve().parents[1] / "models" / "AlignScore-large.ckpt"
    )
    return str(project_checkpoint) if project_checkpoint.is_file() else None


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
        scores["st3_sari"] = sari_score(source, generated, reference)
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
        ckpt_path = _alignscore_checkpoint()
        if not ckpt_path:
            raise RuntimeError(
                "AlignScore checkpoint not found; set ALIGNSCORE_CKPT_PATH "
                "or place AlignScore-large.ckpt in models"
            )
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
) -> dict[str, float | None]:
    source = " ".join([patient_question or "", clinician_question or "", note_excerpt or ""])
    metrics = _official_scores(generated, reference, source, note_excerpt)
    medical_lexical = medical_lexical_f1_proxy(generated, reference)
    metrics["st3_medical_lexical_f1_proxy"] = medical_lexical
    metrics["st3_medical_lexical_f1_proxy_pct"] = medical_lexical * 100.0
    for key in OFFICIAL_METRIC_KEYS:
        metrics[f"{key}_pct"] = (
            metrics[key] * 100.0 if metrics[key] is not None else None
        )
    return metrics


def compute_word_overlap(generated: str, reference: str) -> float:
    """Backward-compatible alias for simple overlap."""
    return _set_f1(set(_tokens(generated)), set(_tokens(reference)))
