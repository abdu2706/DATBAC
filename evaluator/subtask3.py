"""ArchEHR-QA Subtask 3 metrics.

The implementations and model settings mirror the official 2026 scorer:
https://github.com/soni-sarvesh/archehr-qa-2026/tree/main/evaluation

Neural and UMLS dependencies are loaded lazily because importing the evaluator
must remain cheap for commands that do not score generated answers.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


METRIC_KEYS = (
    "st3_bleu_pct",
    "st3_rouge_pct",
    "st3_sari_pct",
    "st3_bertscore_pct",
    "st3_alignscore_pct",
    "st3_medcon_pct",
)


class OfficialMetricError(RuntimeError):
    """A metric failed after zero or more official metrics were computed."""

    def __init__(self, metric: str, partial_scores: dict[str, float], cause: Exception) -> None:
        super().__init__(f"{metric} failed: {cause}")
        self.metric = metric
        self.partial_scores = partial_scores
        self.__cause__ = cause


def _load_evaluate_metric(name: str) -> Any:
    try:
        from evaluate import load
    except ImportError as exc:
        raise RuntimeError(
            "Official metrics require the evaluation dependencies. "
            "Install requirements.txt before running scoring."
        ) from exc
    return load(name)


@lru_cache(maxsize=1)
def _text_metrics() -> tuple[Any, Any, Any]:
    return (
        _load_evaluate_metric("bleu"),
        _load_evaluate_metric("rouge"),
        _load_evaluate_metric("sari"),
    )


@lru_cache(maxsize=1)
def _bert_scorer(device: str) -> Any:
    try:
        from bert_score import score
    except ImportError as exc:
        raise RuntimeError(
            "Official BERTScore requires bert-score, torch and transformers. "
            "Install requirements.txt before running scoring."
        ) from exc
    return score


@lru_cache(maxsize=4)
def _align_scorer(device: str) -> Any:
    try:
        from alignscore import AlignScore
    except ImportError as exc:
        raise RuntimeError(
            "Official AlignScore requires the alignscore dependency. "
            "Install requirements.txt before running scoring."
        ) from exc
    return AlignScore(
        model="roberta-base",
        device=device,
        batch_size=8,
        ckpt_path="https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-base.ckpt",
        evaluation_mode="nli_sp",
    )


@lru_cache(maxsize=4)
def _medcon_scorer(quickumls_path: str) -> Any:
    try:
        import spacy
        from quickumls import QuickUMLS
    except ImportError as exc:
        raise RuntimeError(
            "Official MEDCON requires spaCy, scispaCy and QuickUMLS. "
            "Install requirements.txt and prepare the QuickUMLS database."
        ) from exc

    if not spacy.util.is_package("en_core_web_sm"):
        raise RuntimeError(
            "MEDCON requires the spaCy model en_core_web_sm. "
            "Install it with: python -m spacy download en_core_web_sm"
        )
    try:
        nlp = spacy.load("en_ner_bc5cdr_md")
    except OSError as exc:
        raise RuntimeError(
            "MEDCON requires the scispaCy model en_ner_bc5cdr_md. "
            "Install the model URL from requirements.txt."
        ) from exc

    return _MedconScorer(
        nlp=nlp,
        matcher=QuickUMLS(
            quickumls_path,
            window=5,
            threshold=1,
            accepted_semtypes=_MEDCON_SEMANTIC_TYPES,
        ),
    )


_MEDCON_SEMANTIC_TYPES = (
    "T017", "T029", "T023", "T030", "T031", "T022", "T025", "T026",
    "T018", "T021", "T024", "T116", "T195", "T123", "T122", "T103",
    "T120", "T104", "T200", "T196", "T126", "T131", "T125", "T129",
    "T130", "T197", "T114", "T109", "T121", "T192", "T127", "T203",
    "T074", "T075", "T020", "T190", "T049", "T019", "T047", "T050",
    "T033", "T037", "T048", "T191", "T046", "T184", "T087", "T088",
    "T028", "T085", "T086", "T038", "T069", "T068", "T034", "T070",
    "T067", "T043", "T201", "T045", "T041", "T044", "T032", "T040",
    "T042", "T039",
)


class _MedconScorer:
    def __init__(self, nlp: Any, matcher: Any) -> None:
        self.nlp = nlp
        self.matcher = matcher

    def _matches(self, text: str) -> tuple[dict[str, list[str]], list[str]]:
        concepts: dict[str, list[str]] = {}
        cuis: list[str] = []
        for match in self.matcher.match(text or "", ignore_syntax=True):
            for item in match:
                term = item["term"]
                cui = item["cui"]
                if cui not in concepts.get(term, []):
                    concepts.setdefault(term, []).append(cui)
                    cuis.append(cui)
        return concepts, cuis

    def score(self, reference: str, prediction: str) -> float:
        reference_concepts, reference_cuis = self._matches(reference)
        prediction_concepts, prediction_cuis = self._matches(prediction)
        if not reference_concepts or not prediction_concepts:
            return 0.0
        matched = sum(
            any(cui in prediction_cuis for cui in cuis)
            for cuis in reference_concepts.values()
        )
        precision = matched / len(prediction_concepts)
        recall = matched / len(reference_concepts)
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _device_name() -> str:
    try:
        import torch
    except ImportError:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def _official_scores(
    generated: str,
    reference: str,
    source: str,
    quickumls_path: str,
) -> dict[str, float]:
    scores: dict[str, float] = {}

    def run(metric: str, calculate: Any) -> None:
        try:
            scores[metric] = float(calculate())
        except Exception as exc:
            raise OfficialMetricError(metric, scores.copy(), exc) from exc

    bleu, rouge, sari = _text_metrics()
    run(
        "st3_bleu_pct",
        lambda: bleu.compute(
            references=[[reference]], predictions=[generated]
        )["bleu"] * 100,
    )
    run(
        "st3_rouge_pct",
        lambda: rouge.compute(
            references=[reference], predictions=[generated]
        )["rougeLsum"] * 100,
    )
    run(
        "st3_sari_pct",
        lambda: sari.compute(
            sources=[source], predictions=[generated], references=[[reference]]
        )["sari"],
    )

    device = _device_name()
    run(
        "st3_bertscore_pct",
        lambda: float(
            _bert_scorer(device)(
                [generated],
                [reference],
                model_type="distilbert-base-uncased",
                device=device,
                num_layers=4,
                batch_size=8,
                nthreads=4,
                all_layers=False,
                idf=False,
                lang="en",
                rescale_with_baseline=True,
                baseline_path=None,
                verbose=False,
            )[2].item()
        ) * 100,
    )
    run(
        "st3_alignscore_pct",
        lambda: _align_scorer(device).score(
            contexts=[reference], claims=[generated]
        )[0] * 100,
    )
    run(
        "st3_medcon_pct",
        lambda: _medcon_scorer(str(Path(quickumls_path).resolve())).score(
            reference, generated
        ) * 100,
    )
    return scores


def compute_subtask3_metrics(
    generated: str,
    reference: str,
    patient_narrative: str,
    clinician_question: str,
    note_excerpt: str,
    *,
    quickumls_path: str = "quickumls",
) -> dict[str, float]:
    """Return official ArchEHR-QA metrics as percentages.

    ``patient_narrative`` is the SARI source. The remaining case arguments are
    retained for call-site compatibility; AlignScore uses the official scorer's
    reference-answer context rather than a lexical note proxy.
    """
    del clinician_question, note_excerpt
    return _official_scores(generated, reference, patient_narrative, quickumls_path)


def compute_word_overlap(generated: str, reference: str) -> float:
    """Deprecated compatibility helper; it is not used for evaluation."""
    generated_words = set((generated or "").lower().split())
    reference_words = set((reference or "").lower().split())
    if not generated_words or not reference_words:
        return 0.0
    overlap = len(generated_words & reference_words)
    precision = overlap / len(generated_words)
    recall = overlap / len(reference_words)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0
