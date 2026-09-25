# DATBAC — Culture-Aware Grounded Health Question Answering

## Project purpose
Investigate whether Hofstede-inspired communication instructions change a health chatbot's answers while preserving fidelity to the supplied clinical notes.

The project uses ArchEHR-QA (called ARCHER in the student guide), focusing on answer generation and answer–evidence alignment.

## Current status
- **Subtask 3: nearly finished**, according to the project owner.
- An existing Python pipeline connects data loading, task execution, Ollama, evaluation, quality checks, comparison, and reporting.
- This documentation describes the architecture supplied by the owner; the source code has not been inspected.
- Completion of Subtask 4, cultural profiles, individual metrics, and reporting features has not been confirmed.
- Extend the existing project. Do not restart it from the student guide's Phase 0.

## Documentation map
| File | Purpose |
| --- | --- |
| `ARCHITECTURE.md` | Owner-provided architecture and component boundaries |
| `TASK_SPECIFICATION.md` | Structured conversion of `Arch.docx`: Subtasks 3 and 4, examples, evaluation |
| `RESEARCH_GUIDE.md` | Structured research plan derived from the student guide |
| `PROJECT_STATUS_AND_NEXT_STEPS.md` | Remaining-work checklist appropriate to the current progress |
| `.github/copilot-instructions.md` | Repository-wide instructions for GitHub Copilot |

## Suggested placement
Keep `README.md` at the repository root. Place the four other documentation files next to it for simple relative navigation. Move the downloaded `copilot-instructions.md` into `.github/copilot-instructions.md`.

If your repository already has a README or Copilot instructions, merge the relevant documentation rather than overwriting existing instructions.

## Sources and interpretation
1. `Hofstede_Chatbot_Student_Guide.docx.pdf`: research rationale, profiles, measurement groups, phased plan, research questions.
2. `Arch.docx`: supplied task descriptions and evaluation definitions.
3. Project owner's architecture and statement that Subtask 3 is nearly finished.

These Markdown documents are organized adaptations, not verbatim transcriptions. Source-derived requirements and additional methodological recommendations are distinguished. No implementation, experiments, or metric results were verified while preparing them.

## Core rules
- Ground medical claims in the clinical note excerpt.
- Do not invent explanations when the note cannot fully answer the question.
- Use a professional register and a maximum of 75 words for Subtask 3.
- Cultural style must not override grounding, uncertainty, or task constraints.
- Keep generated answers distinct from reference answers.
- Keep official reference-answer alignment evaluation distinct from grounding checks on generated answers.
- Report observed findings, including negative or inconclusive results; expected outcomes are not established facts.
