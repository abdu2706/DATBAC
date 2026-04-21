from __future__ import annotations

from llm_runner import OllamaRunner
from config.rag_pipeline import RAGPipeline
from subtasks.subtask3 import build_prompt as build_subtask3_prompt


class SubtaskRunner:
    def __init__(self, rag: RAGPipeline, llm: OllamaRunner):
        self.rag = rag
        self.llm = llm

    def run_subtask(
        self,
        subtask: int,
        case: dict,
        system_prompt: str,
        model: str,
        answer_text: str | None = None,
    ) -> str:
        if subtask != 3:
            raise ValueError("This run configuration supports Subtask 3 only")

        self.rag.index_case(case["case_id"], case["sentences"])
        query = f"{case.get('patient_question', '')} {case.get('clinician_question', '')}"
        retrieved = self.rag.retrieve_all_ranked(query, case["case_id"])
        user_prompt = build_subtask3_prompt(case, retrieved)

        return self.llm.generate(model, system_prompt, user_prompt)
