# Existing Project Architecture

## Evidence and scope
This architecture was supplied by the project owner. File names below are known from that description, but source contents, signatures, configuration fields, and output schemas have not been inspected. Roles are interpretations of the supplied diagram, not verified implementation details.

## Pipeline
1. ArchEHR-QA XML/JSON files enter `data_loader.py`.
2. `data_loader.py` supplies data to `main.py`.
3. `main.py` coordinates `config`, `SubtaskRunner`, and `evaluator`.
4. `config` supplies Hofstede prompts.
5. `SubtaskRunner` invokes `llm_runner.py`.
6. `llm_runner.py` communicates with Ollama through `/api/chat`.
7. The model produces a generated answer.
8. The answer passes through `quality_checks.py`.
9. `compare.py` and `visualize.py` support comparison and visualization.
10. The described outputs are JSON, CSV, CI95 reports, and plots.
11. The evaluation branch connects `evaluator` to `metrics`.

The diagram does not establish the exact timing or integration of evaluation relative to quality checks and reporting. Inspect the implementation before changing that ordering.

## Component map
| Supplied identifier | Described or inferred responsibility | Confirm before editing |
| --- | --- | --- |
| `data_loader.py` | Reads the XML/JSON dataset | Input schema, split handling, sentence identifiers |
| `main.py` | Main orchestration | Actual entry point and supported arguments |
| `config` | Experiment configuration and prompt selection | Whether this is a file, package, object, or directory |
| `SubtaskRunner` | Task execution | Definition location and public interface |
| `llm_runner.py` | Model execution through Ollama | Request construction, response parsing, retries |
| `Ollama /api/chat` | Model-serving interface in the supplied architecture | Existing model identifier and request settings |
| `evaluator` | Evaluation coordination | Module location, inputs, and metric dispatch |
| `metrics` | Metric implementations or wrappers | Available metrics and required inputs |
| `quality_checks.py` | Answer validation | Existing checks, failure recording, retry policy |
| `compare.py` | Cross-run/profile comparisons | Pairing logic and statistical methods |
| `visualize.py` | Plots | Existing report inputs and plotting conventions |

## Integration guidance — recommendations
- Preserve existing interfaces and filenames unless a change is necessary and explicitly agreed.
- Inspect current implementation before proposing another runner, loader, evaluator, or configuration layer.
- Keep the same case identity across profiles so comparisons can be paired.
- Keep source note sentence identifiers unchanged through loading, prompting, alignment, and scoring.
- Preserve raw generated answers separately from any normalized, shortened, or retried versions.
- Keep reference answers available for evaluation, not as answer-generation inputs.
- Store alignment results separately if the task requires plain answer text without citations.

## Reproducibility information to locate or add
These are conceptual records, **not prescribed field names**:
- Dataset release, split, and case identity.
- Exact question variant and note excerpt used.
- Exact prompt and cultural profile.
- Model identity and generation settings.
- Raw response, selected response, and retry history.
- Word-limit and other quality-check outcomes.
- Metric implementation versions and results.
- Comparison method, confidence interval method, and analysis settings.

Use existing project schema names. Do not create new fields without checking the code.

## Reporting caveat
The owner lists CI95 reports as pipeline outputs. This does not verify their implementation or method. Document whether intervals are paired, what is resampled, and how repeated generations are handled before interpreting them.
