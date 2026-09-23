from __future__ import annotations

import os
from pathlib import Path

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# LLM generation settings for reproducible comparisons.
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024
DEFAULT_SEED = 42

MODELS = [
    "llama3.1:8b",
]

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATASET_BASE = WORKSPACE_ROOT / "Data" / "archehr-qa-a-dataset-for-addressing-patients-information-needs-related-to-clinical-course-of-hospitalization-1.3"
DATASET_SPLIT = os.getenv("ARCHEHR_SPLIT", "test")
DATASET_DIR = DATASET_BASE / DATASET_SPLIT

XML_PATH = DATASET_DIR / "archehr-qa.xml"
KEY_PATH = DATASET_DIR / "archehr-qa_key.json"
MAPPING_PATH = DATASET_DIR / "archehr-qa_mapping.json"

RESULTS_DIR = WORKSPACE_ROOT / "results"
