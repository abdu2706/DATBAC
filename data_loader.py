from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from config import KEY_PATH, MAPPING_PATH, XML_PATH


def load_cases_from_xml(xml_path: str | Path = XML_PATH) -> dict[str, dict]:
    """Parse XML and return dict of cases keyed by case_id."""
    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    cases: dict[str, dict] = {}

    for case_elem in root.findall("case"):
        case_id = case_elem.get("id", "")

        specialty = case_elem.findtext("clinical_specialty", "").strip()
        narrative = case_elem.findtext("patient_narrative", "").strip()

        pq_elem = case_elem.find("patient_question")
        patient_question_phrases: list[str] = []
        if pq_elem is not None:
            for phrase in pq_elem.findall("phrase"):
                if phrase.text:
                    patient_question_phrases.append(phrase.text.strip())
        patient_question = " ".join(patient_question_phrases)

        clinician_question = case_elem.findtext("clinician_question", "").strip()
        note_excerpt = case_elem.findtext("note_excerpt", "").strip()

        sentences: dict[str, dict] = {}
        sent_elem = case_elem.find("note_excerpt_sentences")
        if sent_elem is not None:
            for sent in sent_elem.findall("sentence"):
                sid = sent.get("id", "")
                sentences[sid] = {
                    "id": sid,
                    "paragraph_id": sent.get("paragraph_id"),
                    "text": sent.text.strip() if sent.text else "",
                }

        cases[case_id] = {
            "case_id": case_id,
            "clinical_specialty": specialty,
            "patient_narrative": narrative,
            "patient_question": patient_question,
            "clinician_question": clinician_question,
            "note_excerpt": note_excerpt,
            "sentences": sentences,
        }

    return cases


def load_gold_answers(key_path: str | Path = KEY_PATH) -> dict[str, dict]:
    with Path(key_path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["case_id"]: item for item in data}


def load_mapping(mapping_path: str | Path = MAPPING_PATH) -> dict[str, dict]:
    with Path(mapping_path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["case_id"]: item for item in data}


def get_essential_sentence_ids(gold_case: dict) -> list[str]:
    answers = gold_case.get("answers", [])
    return [a.get("sentence_id", "") for a in answers if a.get("relevance") == "essential"]


def get_relevant_sentence_ids(gold_case: dict) -> list[str]:
    answers = gold_case.get("answers", [])
    return [
        a.get("sentence_id", "")
        for a in answers
        if a.get("relevance") in ("essential", "supplementary")
    ]
