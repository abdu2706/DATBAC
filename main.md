Når du vil bytte til test:

I PowerShell før kjøring: $env:ARCHEHR_SPLIT="test"
Deretter: python main.py --max-cases 5

$env:ARCHEHR_SPLIT="test"; & "c:/Users/Eng. Abdul/OneDrive - Universitetet i Stavanger/DATBACARCH/.venv/Scripts/python.exe" -u main.py --max-cases 1 --out results_test_1.json --csv-dir exports_test_1 --skip-plot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass                                                                                                                          
>> .\.venv\Scripts\Activate.ps1           

python main.py --interactive --model "llama3.1:8b" --profile "P0_neutral"
Steg 1: Prosjektstruktur
archehr-chatbot/
├── config.py              # Modeller, profiler, innstillinger
├── data_loader.py         # Parse XML + JSON
├── rag_pipeline.py        # Embedding + retrieval (ChromaDB)
├── config/prompts.py      # Kulturprofil → system prompt
├── llm_runner.py          # Ollama API-kall
├── subtasks.py            # Subtask 1-4 logikk
├── evaluator.py           # Scoring mot gold standard
├── compare.py             # Sammenligning profil × modell
├── main.py                # Kjør alt
└── data/
    ├── archehr-qa.xml
    ├── archehr-qa_key.json
    └── archehr-qa_mapping.json

Steg 2: config.py
OLLAMA_BASE_URL = "http://localhost:11434"

MODELS = [
    "billylo/medgemma-1.5-4b-vision",
    "llama3.1:8b",
    "gemma3:latest",
    "qwen3:8b",
]

HOFSTEDE_PROFILES = [
    {
        "profile_id": "P0_neutral",
        "name": "Neutral baseline",
        "hofstede": {"PDI": 0.5, "IDV": 0.5, "UAI": 0.5, "MAS": 0.5, "LTO": 0.5, "IVR": 0.5},
    },
    {
        "profile_id": "P1_highPDI_highUAI",
        "name": "Authority-trusting & uncertainty-averse",
        "hofstede": {"PDI": 1.0, "IDV": 0.5, "UAI": 1.0, "MAS": 0.5, "LTO": 0.5, "IVR": 0.0},
    },
    {
        "profile_id": "P2_lowPDI_highIDV",
        "name": "Autonomy-seeking & participatory",
        "hofstede": {"PDI": 0.0, "IDV": 1.0, "UAI": 0.5, "MAS": 0.5, "LTO": 0.5, "IVR": 0.5},
    },
    {
        "profile_id": "P3_highPDI_lowIDV",
        "name": "Family-oriented & hierarchy-aligned",
        "hofstede": {"PDI": 1.0, "IDV": 0.0, "UAI": 0.5, "MAS": 0.5, "LTO": 1.0, "IVR": 0.0},
    },
    {
        "profile_id": "P4_highUAI_lowIVR",
        "name": "Risk-averse & restraint-oriented",
        "hofstede": {"PDI": 0.5, "IDV": 0.5, "UAI": 1.0, "MAS": 0.5, "LTO": 0.5, "IVR": 0.0},
    },
    {
        "profile_id": "P5_highMAS_lowUAI",
        "name": "Action-driven & ambiguity-tolerant",
        "hofstede": {"PDI": 0.25, "IDV": 1.0, "UAI": 0.0, "MAS": 1.0, "LTO": 0.5, "IVR": 1.0},
    },
    {
        "profile_id": "P6_highLTO_medHighUAI",
        "name": "Long-term planner",
        "hofstede": {"PDI": 0.5, "IDV": 0.5, "UAI": 0.75, "MAS": 0.5, "LTO": 1.0, "IVR": 0.25},
    },
]

HOFSTEDE_DIMENSIONS = {
    "PDI": {"name": "Power Distance Index", "short": "Acceptance of unequal power distribution and hierarchy."},
    "IDV": {"name": "Individualism vs Collectivism", "short": "Degree of integration into individual versus group identity."},
    "UAI": {"name": "Uncertainty Avoidance Index", "short": "Tolerance for ambiguity and uncertainty."},
    "MAS": {"name": "Achievement Orientation", "short": "Preference for achievement/assertiveness versus care/quality of life."},
    "LTO": {"name": "Long-Term Orientation", "short": "Emphasis on long-term adaptation versus tradition-focused short-term orientation."},
    "IVR": {"name": "Indulgence vs Restraint", "short": "Freedom to gratify desires versus stricter social restraint."},
}

# RAG settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_COLLECTION = "archehr_notes"
TOP_K = 5

Steg 3: data_loader.py

La meg først se nøyaktig på XML-strukturen for å parse riktig: Nå har jeg full oversikt. Her er koden steg for steg:

Steg 3: data_loader.py
import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Any


def load_cases_from_xml(xml_path: str = "data/archehr-qa.xml") -> Dict[str, Dict]:
    """Parse XML and return dict of cases keyed by case_id."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    cases = {}

    for case_elem in root.findall("case"):
        case_id = case_elem.get("id")
        
        # Clinical specialty
        specialty = case_elem.findtext("clinical_specialty", "").strip()
        
        # Patient narrative (full text)
        narrative = case_elem.findtext("patient_narrative", "").strip()
        
        # Patient question phrases
        pq_elem = case_elem.find("patient_question")
        patient_question_phrases = []
        if pq_elem is not None:
            for phrase in pq_elem.findall("phrase"):
                patient_question_phrases.append(phrase.text.strip())
        patient_question = " ".join(patient_question_phrases)
        
        # Clinician question
        clinician_question = case_elem.findtext("clinician_question", "").strip()
        
        # Note excerpt (raw)
        note_excerpt = case_elem.findtext("note_excerpt", "").strip()
        
        # Note excerpt sentences
        sentences = {}
        sent_elem = case_elem.find("note_excerpt_sentences")
        if sent_elem is not None:
            for sent in sent_elem.findall("sentence"):
                sid = sent.get("id")
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


def load_gold_answers(key_path: str = "data/archehr-qa_key.json") -> Dict[str, Dict]:
    """Load gold standard answers keyed by case_id."""
    with open(key_path) as f:
        data = json.load(f)
    return {item["case_id"]: item for item in data}


def load_mapping(mapping_path: str = "data/archehr-qa_mapping.json") -> Dict[str, Dict]:
    """Load case-to-document mapping."""
    with open(mapping_path) as f:
        data = json.load(f)
    return {item["case_id"]: item for item in data}


def get_essential_sentence_ids(gold_case: Dict) -> List[str]:
    """Extract sentence IDs labeled 'essential' from gold answers."""
    return [a["sentence_id"] for a in gold_case["answers"] if a["relevance"] == "essential"]


def get_relevant_sentence_ids(gold_case: Dict) -> List[str]:
    """Extract sentence IDs labeled 'essential' or 'supplementary'."""
    return [a["sentence_id"] for a in gold_case["answers"] 
            if a["relevance"] in ("essential", "supplementary")]

Steg 4: rag_pipeline.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple
from config import EMBEDDING_MODEL, CHROMA_COLLECTION, TOP_K


class RAGPipeline:
    def __init__(self):
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.Client()  # in-memory; use PersistentClient for disk
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        self._indexed_cases = set()

    def index_case(self, case_id: str, sentences: Dict[str, Dict]):
        """Index all sentences for a single case into ChromaDB."""
        if case_id in self._indexed_cases:
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for sid, sent in sentences.items():
            doc_id = f"{case_id}_s{sid}"
            ids.append(doc_id)
            documents.append(sent["text"])
            metadatas.append({
                "case_id": case_id,
                "sentence_id": sid,
                "paragraph_id": sent.get("paragraph_id", ""),
            })
        
        if documents:
            embeddings = self.embedder.encode(documents).tolist()
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        self._indexed_cases.add(case_id)

    def retrieve(self, query: str, case_id: str, top_k: int = TOP_K) -> List[Tuple[str, str, float]]:
        """Retrieve top-k relevant sentences for a query within a specific case."""
        query_embedding = self.embedder.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where={"case_id": case_id},
        )
        
        retrieved = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                sid = results["metadatas"][0][i]["sentence_id"]
                distance = results["distances"][0][i] if results["distances"] else 0.0
                retrieved.append((sid, doc, distance))
        
        return retrieved

    def retrieve_all_ranked(self, query: str, case_id: str) -> List[Tuple[str, str, float]]:
        """Retrieve ALL sentences for a case, ranked by relevance."""
        # Get total count for this case
        case_docs = self.collection.get(where={"case_id": case_id})
        n = len(case_docs["ids"]) if case_docs["ids"] else 0
        if n == 0:
            return []
        return self.retrieve(query, case_id, top_k=n)

Steg 5: config/prompts.py
from typing import Dict
from config import HOFSTEDE_DIMENSIONS


def build_hofstede_system_prompt(profile: Dict) -> str:
    """Generate a system prompt that adapts clinical communication style
    based on Hofstede cultural dimensions."""
    
    h = profile["hofstede"]
    name = profile["name"]
    pid = profile["profile_id"]
    
    # Build dimension-specific instructions
    instructions = []
    
    # PDI - Power Distance
    if h["PDI"] >= 0.75:
        instructions.append(
            "Use a formal, authoritative tone. Reference the clinician's expertise "
            "and institutional authority. Present information as definitive guidance "
            "from medical professionals. Avoid inviting the patient to question decisions."
        )
    elif h["PDI"] <= 0.25:
        instructions.append(
            "Use a collaborative, egalitarian tone. Encourage the patient to ask questions "
            "and participate in decision-making. Present options rather than directives. "
            "Acknowledge the patient's perspective as valuable."
        )
    else:
        instructions.append(
            "Use a balanced tone that respects clinical expertise while remaining approachable."
        )
    
    # IDV - Individualism
    if h["IDV"] >= 0.75:
        instructions.append(
            "Focus on the individual patient's specific situation and personal health outcomes. "
            "Emphasize personal autonomy and individual rights in healthcare decisions."
        )
    elif h["IDV"] <= 0.25:
        instructions.append(
            "Acknowledge the role of family and community in healthcare decisions. "
            "Frame information in terms of how it affects the patient's family and support network. "
            "Use inclusive language (e.g., 'your family and care team')."
        )
    else:
        instructions.append(
            "Balance individual and family-oriented perspectives in the response."
        )
    
    # UAI - Uncertainty Avoidance
    if h["UAI"] >= 0.75:
        instructions.append(
            "Provide detailed, structured explanations with clear step-by-step reasoning. "
            "Minimize ambiguity. If uncertainty exists, explicitly acknowledge it and explain "
            "what is being done to reduce it. Cite specific evidence sentences."
        )
    elif h["UAI"] <= 0.25:
        instructions.append(
            "Be comfortable with ambiguity. Provide concise answers without over-explaining. "
            "Accept that not everything is fully known and present this naturally."
        )
    else:
        instructions.append(
            "Provide clear explanations while acknowledging reasonable uncertainty."
        )
    
    # MAS - Masculinity/Achievement
    if h["MAS"] >= 0.75:
        instructions.append(
            "Focus on outcomes, results, and concrete actions taken. Emphasize what was achieved "
            "and what the next actionable steps are. Be direct and solution-oriented."
        )
    elif h["MAS"] <= 0.25:
        instructions.append(
            "Emphasize care, comfort, and quality of life. Show empathy and concern for the "
            "patient's emotional well-being alongside clinical facts."
        )
    else:
        instructions.append(
            "Balance outcome-focused information with empathetic care considerations."
        )
    
    # LTO - Long-Term Orientation
    if h["LTO"] >= 0.75:
        instructions.append(
            "Emphasize long-term prognosis, follow-up plans, and preventive measures. "
            "Connect current treatment to future health outcomes. Discuss lifestyle changes "
            "and ongoing management."
        )
    elif h["LTO"] <= 0.25:
        instructions.append(
            "Focus on the immediate situation and short-term recovery. Address the current "
            "concern directly without extensive discussion of long-term implications."
        )
    else:
        instructions.append(
            "Address both immediate concerns and relevant long-term considerations."
        )
    
    # IVR - Indulgence vs Restraint
    if h["IVR"] >= 0.75:
        instructions.append(
            "Use a warm, reassuring tone. Validate the patient's feelings and concerns. "
            "Be encouraging about recovery and positive outcomes where supported by evidence."
        )
    elif h["IVR"] <= 0.25:
        instructions.append(
            "Maintain a restrained, professional tone. Focus strictly on clinical facts "
            "without emotional embellishment. Be measured and conservative in outlook."
        )
    else:
        instructions.append(
            "Maintain professional warmth while staying grounded in clinical evidence."
        )
    
    system_prompt = f"""You are a clinical QA assistant responding to patient questions using electronic health records.

Cultural Communication Profile: {name} ({pid})

Communication Style Guidelines:
{chr(10).join(f"- {inst}" for inst in instructions)}

Core Rules:
- Ground ALL answers in the provided clinical note excerpt. Cite sentence IDs in brackets [X].
- Do NOT speculate or add information not present in the notes.
- Keep answers concise (max 75 words for answer generation).
- Use professional clinical register.
- If the note does not fully answer the question, state what IS supported and note the limitation.
"""
    return system_prompt


def get_all_system_prompts(profiles: list) -> Dict[str, str]:
    """Generate system prompts for all profiles."""
    return {p["profile_id"]: build_hofstede_system_prompt(p) for p in profiles}

Steg 6: llm_runner.py
import requests
import json
from typing import Dict, List, Optional
from config import OLLAMA_BASE_URL, MODELS


class OllamaRunner:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    def generate(self, model: str, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 512) -> str:
        """Call Ollama /api/chat endpoint."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"[ERROR] {model}: {e}"

    def generate_all_models(self, system_prompt: str, user_prompt: str,
                            models: Optional[List[str]] = None) -> Dict[str, str]:
        """Run the same prompt across all configured models."""
        models = models or MODELS
        results = {}
        for model in models:
            print(f"  → Running {model}...")
            results[model] = self.generate(model, system_prompt, user_prompt)
        return results

Steg 7: subtasks.py
import json
import re
from typing import Dict, List, Tuple
from rag_pipeline import RAGPipeline
from llm_runner import OllamaRunner


class SubtaskRunner:
    def __init__(self, rag: RAGPipeline, llm: OllamaRunner):
        self.rag = rag
        self.llm = llm

    # ── Subtask 1: Question Interpretation ──
    def subtask1_prompt(self, case: Dict) -> str:
        return (
            f"Patient question:\n{case['patient_narrative']}\n\n"
            "Generate a single concise clinician-interpreted question (max 15 words) "
            "that captures the core clinical information need. "
            "Output ONLY the question, nothing else."
        )

    # ── Subtask 2: Evidence Identification ──
    def subtask2_prompt(self, case: Dict, retrieved: List[Tuple]) -> str:
        sentences_text = "\n".join(
            f"[{sid}]: {text}" for sid, text, _ in retrieved
        )
        return (
            f"Patient question: {case['patient_question']}\n"
            f"Clinician question: {case['clinician_question']}\n\n"
            f"Clinical note sentences:\n{sentences_text}\n\n"
            "Which sentence IDs are clinically relevant to answering the patient's question? "
            "Return ONLY a JSON array of sentence ID strings, e.g. [\"1\", \"5\", \"7\"]. "
            "Select only the minimal set of essential sentences."
        )

    # ── Subtask 3: Answer Generation ──
    def subtask3_prompt(self, case: Dict, retrieved: List[Tuple]) -> str:
        sentences_text = "\n".join(
            f"[{sid}]: {text}" for sid, text, _ in retrieved
        )
        return (
            f"Patient question: {case['patient_question']}\n"
            f"Clinician question: {case['clinician_question']}\n\n"
            f"Clinical note sentences:\n{sentences_text}\n\n"
            "Generate a grounded answer (max 75 words) using ONLY information from the "
            "clinical note sentences above. Cite sentence IDs in brackets [X] after each claim. "
            "Use professional clinical register. Do not speculate."
        )

    # ── Subtask 4: Evidence Alignment ──
    def subtask4_prompt(self, case: Dict, answer_text: str, sentences: Dict) -> str:
        # Number the answer sentences
        answer_sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer_text) if s.strip()]
        answer_numbered = "\n".join(f"{i+1}: {s}" for i, s in enumerate(answer_sents))
        
        note_text = "\n".join(f"[{sid}]: {s['text']}" for sid, s in sentences.items())
        
        return (
            f"Patient question: {case['patient_question']}\n"
            f"Clinician question: {case['clinician_question']}\n\n"
            f"Clinical note sentences:\n{note_text}\n\n"
            f"Answer sentences:\n{answer_numbered}\n\n"
            "For each answer sentence, identify which clinical note sentence(s) support it. "
            "Return ONLY a JSON array like:\n"
            '[{"answer_id": "1", "evidence_id": ["2", "5"]}, ...]\n'
            "Use empty list for unsupported sentences."
        )

    def run_subtask(self, subtask: int, case: Dict, system_prompt: str,
                    model: str, answer_text: str = None) -> str:
        """Run a single subtask for a case with a specific model and profile."""
        
        if subtask == 1:
            user_prompt = self.subtask1_prompt(case)
        
        elif subtask in (2, 3):
            # Index case sentences
            self.rag.index_case(case["case_id"], case["sentences"])
            # Retrieve relevant sentences
            query = f"{case['patient_question']} {case['clinician_question']}"
            retrieved = self.rag.retrieve_all_ranked(query, case["case_id"])
            
            if subtask == 2:
                user_prompt = self.subtask2_prompt(case, retrieved)
            else:
                user_prompt = self.subtask3_prompt(case, retrieved)
        
        elif subtask == 4:
            if not answer_text:
                raise ValueError("Subtask 4 requires answer_text")
            user_prompt = self.subtask4_prompt(case, answer_text, case["sentences"])
        
        else:
            raise ValueError(f"Unknown subtask: {subtask}")
        
        return self.llm.generate(model, system_prompt, user_prompt)

Steg 8: evaluator.py
import re
import json
from typing import Dict, List, Set
from collections import defaultdict


def parse_sentence_ids(response: str) -> List[str]:
    """Extract sentence IDs from LLM response (expects JSON array)."""
    try:
        # Try to find JSON array in response
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            ids = json.loads(match.group())
            return [str(i) for i in ids]
    except (json.JSONDecodeError, ValueError):
        pass
    # Fallback: extract numbers
    return re.findall(r'\b(\d+)\b', response)


def parse_alignment(response: str) -> List[Dict]:
    """Parse alignment JSON from LLM response."""
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        pass
    return []


# ── Subtask 2: Evidence Identification Metrics ──
def evidence_f1(predicted: List[str], gold: List[str]) -> Dict[str, float]:
    """Compute P, R, F1 for evidence identification."""
    pred_set = set(predicted)
    gold_set = set(gold)
    
    if not pred_set and not gold_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not pred_set:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    if not gold_set:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    tp = len(pred_set & gold_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(gold_set) if gold_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {"precision": precision, "recall": recall, "f1": f1}


# ── Subtask 4: Alignment Metrics ──
def alignment_f1(predicted: List[Dict], gold_answer: str, gold_case: Dict) -> Dict[str, float]:
    """Compute P, R, F1 for answer-evidence alignment links."""
    # Build gold alignment from clinician_answer citations
    gold_links = set()
    # Parse citations like [2], [5,6], [2, 5] from gold answer
    answer_sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', gold_answer) if s.strip()]
    for i, sent in enumerate(answer_sents, 1):
        citations = re.findall(r'\[([^\]]+)\]', sent)
        for cite_group in citations:
            for cid in re.findall(r'\d+', cite_group):
                gold_links.add((str(i), cid))
    
    # Build predicted links
    pred_links = set()
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


def compute_word_overlap(generated: str, reference: str) -> float:
    """Simple ROUGE-1-like word overlap (as a lightweight metric)."""
    gen_words = set(generated.lower().split())
    ref_words = set(reference.lower().split())
    if not ref_words:
        return 0.0
    overlap = len(gen_words & ref_words)
    precision = overlap / len(gen_words) if gen_words else 0.0
    recall = overlap / len(ref_words) if ref_words else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

Steg 9: compare.py
import json
from typing import Dict, List
from collections import defaultdict


def build_comparison_table(results: Dict) -> List[Dict]:
    """
    Build a comparison table from results.
    
    results structure:
    {
        case_id: {
            profile_id: {
                model: {
                    "subtask1": str,
                    "subtask2": str,
                    "subtask3": str,
                    "subtask4": str,
                    "metrics": {...}
                }
            }
        }
    }
    """
    rows = []
    for case_id, profiles in results.items():
        for profile_id, models in profiles.items():
            for model, data in models.items():
                row = {
                    "case_id": case_id,
                    "profile_id": profile_id,
                    "model": model,
                }
                # Add subtask outputs
                for st in ["subtask1", "subtask2", "subtask3", "subtask4"]:
                    row[st] = data.get(st, "")
                # Add metrics
                if "metrics" in data:
                    for metric_name, value in data["metrics"].items():
                        row[f"metric_{metric_name}"] = value
                rows.append(row)
    return rows


def summarize_by_profile(results: Dict) -> Dict[str, Dict]:
    """Average metrics per profile across all cases and models."""
    profile_metrics = defaultdict(lambda: defaultdict(list))
    
    for case_id, profiles in results.items():
        for profile_id, models in profiles.items():
            for model, data in models.items():
                if "metrics" in data:
                    for metric, value in data["metrics"].items():
                        if isinstance(value, (int, float)):
                            profile_metrics[profile_id][metric].append(value)
    
    summary = {}
    for pid, metrics in profile_metrics.items():
        summary[pid] = {
            metric: sum(vals) / len(vals) if vals else 0.0
            for metric, vals in metrics.items()
        }
    return summary


def summarize_by_model(results: Dict) -> Dict[str, Dict]:
    """Average metrics per model across all cases and profiles."""
    model_metrics = defaultdict(lambda: defaultdict(list))
    
    for case_id, profiles in results.items():
        for profile_id, models in profiles.items():
            for model, data in models.items():
                if "metrics" in data:
                    for metric, value in data["metrics"].items():
                        if isinstance(value, (int, float)):
                            model_metrics[model][metric].append(value)
    
    summary = {}
    for model, metrics in model_metrics.items():
        summary[model] = {
            metric: sum(vals) / len(vals) if vals else 0.0
            for metric, vals in metrics.items()
        }
    return summary


def print_comparison(results: Dict):
    """Pretty-print comparison results."""
    print("\n" + "=" * 80)
    print("PROFILE COMPARISON SUMMARY")
    print("=" * 80)
    
    profile_summary = summarize_by_profile(results)
    for pid, metrics in sorted(profile_summary.items()):
        print(f"\n  {pid}:")
        for metric, value in sorted(metrics.items()):
            print(f"    {metric}: {value:.4f}")
    
    print("\n" + "=" * 80)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 80)
    
    model_summary = summarize_by_model(results)
    for model, metrics in sorted(model_summary.items()):
        print(f"\n  {model}:")
        for metric, value in sorted(metrics.items()):
            print(f"    {metric}: {value:.4f}")

Steg 10: main.py
import json
from config import MODELS, HOFSTEDE_PROFILES
from data_loader import load_cases_from_xml, load_gold_answers, get_essential_sentence_ids
from rag_pipeline import RAGPipeline
from config import get_all_system_prompts
from llm_runner import OllamaRunner
from subtasks import SubtaskRunner
from evaluator import (
    parse_sentence_ids, parse_alignment, evidence_f1,
    alignment_f1, compute_word_overlap
)
from compare import print_comparison


def main():
    # Load data
    print("Loading data...")
    cases = load_cases_from_xml()
    gold = load_gold_answers()
    
    # Initialize components
    rag = RAGPipeline()
    llm = OllamaRunner()
    runner = SubtaskRunner(rag, llm)
    system_prompts = get_all_system_prompts(HOFSTEDE_PROFILES)
    
    # Results storage
    all_results = {}
    
    # Run for each case (dev set: cases 1-20)
    for case_id in sorted(cases.keys(), key=int):
        print(f"\n{'='*60}")
        print(f"CASE {case_id}: {cases[case_id]['clinical_specialty']}")
        print(f"{'='*60}")
        
        case = cases[case_id]
        gold_case = gold.get(case_id)
        all_results[case_id] = {}
        
        for profile in HOFSTEDE_PROFILES:
            pid = profile["profile_id"]
            sys_prompt = system_prompts[pid]
            all_results[case_id][pid] = {}
            
            print(f"\n  Profile: {profile['name']}")
            
            for model in MODELS:
                print(f"\n    Model: {model}")
                result = {}
                
                # Subtask 1: Question Interpretation
                print("      Subtask 1: Question Interpretation...")
                result["subtask1"] = runner.run_subtask(1, case, sys_prompt, model)
                print(f"      → {result['subtask1'][:80]}...")
                
                # Subtask 2: Evidence Identification
                print("      Subtask 2: Evidence Identification...")
                result["subtask2"] = runner.run_subtask(2, case, sys_prompt, model)
                
                # Subtask 3: Answer Generation
                print("      Subtask 3: Answer Generation...")
                result["subtask3"] = runner.run_subtask(3, case, sys_prompt, model)
                print(f"      → {result['subtask3'][:80]}...")
                
                # Subtask 4: Evidence Alignment
                print("      Subtask 4: Evidence Alignment...")
                result["subtask4"] = runner.run_subtask(
                    4, case, sys_prompt, model,
                    answer_text=result["subtask3"]
                )
                
                # Evaluate against gold standard
                if gold_case:
                    metrics = {}
                    
                    # Subtask 2 metrics
                    pred_ids = parse_sentence_ids(result["subtask2"])
                    gold_essential = get_essential_sentence_ids(gold_case)
                    st2_metrics = evidence_f1(pred_ids, gold_essential)
                    metrics["st2_precision"] = st2_metrics["precision"]
                    metrics["st2_recall"] = st2_metrics["recall"]
                    metrics["st2_f1"] = st2_metrics["f1"]
                    
                    # Subtask 3 metrics (simple word overlap)
                    gold_answer_text = gold_case.get("clinician_answer", "")
                    metrics["st3_word_overlap"] = compute_word_overlap(
                        result["subtask3"], gold_answer_text
                    )
                    
                    # Subtask 4 metrics
                    pred_alignment = parse_alignment(result["subtask4"])
                    st4_metrics = alignment_f1(
                        pred_alignment, gold_answer_text, gold_case
                    )
                    metrics["st4_precision"] = st4_metrics["precision"]
                    metrics["st4_recall"] = st4_metrics["recall"]
                    metrics["st4_f1"] = st4_metrics["f1"]
                    
                    result["metrics"] = metrics
                    print(f"      Metrics: ST2-F1={metrics['st2_f1']:.3f} "
                          f"ST3-overlap={metrics['st3_word_overlap']:.3f} "
                          f"ST4-F1={metrics['st4_f1']:.3f}")
                
                all_results[case_id][pid][model] = result
    
    # Save results
    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print("\nResults saved to results.json")
    
    # Print comparison
    print_comparison(all_results)


if __name__ == "__main__":
    main()

Installasjon og kjøring
# 1. Installer avhengigheter
pip install chromadb sentence-transformers requests

# 2. Sørg for at Ollama kjører med modellene
ollama pull billylo/medgemma-1.5-4b-vision
ollama pull llama3.1:8b
ollama pull gemma3:latest
ollama pull qwen3:8b

# 3. Legg filene i data/
mkdir -p data
cp archehr-qa.xml archehr-qa_key.json archehr-qa_mapping.json data/

# 4. Kjør
python main.py

Hva du får ut
results.json — Alle svar per case × profil × modell med metrics
Konsolltabell — Gjennomsnittlige metrics per profil og per modell
Sammenligning — Ser du f.eks. at P1 (authority-trusting) gir mer presise siteringer enn P5 (action-driven)?

Vil du at jeg lager neste steg — f.eks. en visualiseringsmodul som plotter profil vs. modell-ytelse, eller en Streamlit-frontend for interaktiv utforskning?