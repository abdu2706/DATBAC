# DATBACARCH

Kort oversikt over oppsettet for Subtask 3 (svar-generering) og evaluering.

## Mekanisme (kort)
1. Leser cases og gull-svar fra valgt split (test/dev).
2. Bygger systemprompt fra Hofstede-profiler (definisjoner + verdier).
3. Bygger brukerprompt kun fra case-innhold (sporsmal + note-utdrag).
4. Kaller Llama via Ollama og begrenser svaret til maks 75 ord.
5. Sammenligner svaret mot gull-svar og beregner metrikker.
6. Eksporterer JSON og CSV-rapporter.

Merk: Ingen RAG eller ekstern henting brukes i denne flyten.

## Hva sammenlignes
Evaluator sammenligner modellens svar mot gull-svar ("clinician_answer") i
`archehr-qa_key.json` for valgt split (test/dev) og beregner flere metrikker.

## Hvordan sammenlignes Llama-svar
Llama genererer ett svar per case og profil. Evaluatoren sammenligner dette
svaret ord for ord og sekvensvis mot gull-svaret, og bruker notat-teksten som
ekstra signal i AlignScore. Ingen ekstern kunnskap brukes i selve evalueringen.

## Metrikker (kort forklart)
- BLEU: N-gram-overlapp mellom generert svar og gull-svar (presisjon).
- ROUGE-L: Lengste felles delsekvens mellom svar og gull-svar (dekning).
- SARI: Måler kvalitet i omskriving ved å se hva som beholdes, legges til og fjernes.
- BERTScore: Semantisk likhet mellom svar og gull-svar (her som token-overlapp-proxy).
- AlignScore: Kombinerer likhet med gull-svar og støtte i notat-teksten.
- MedCon: Overlapp av medisinske/tekniske termer mellom svar og gull-svar.

## Kjoring (eksempel)
```powershell
$env:ARCHEHR_SPLIT="test"
python main.py --max-cases 5 --out results_test_5.json --csv-dir exports_test_5 --skip-plot
```


## Reproducible experiments

Each invocation now creates `results/runs/<UTC timestamp>_<experiment name>_<id>/`.
Existing result files are not overwritten. Each folder contains:

- `manifest.json`: arguments, dataset/reference hashes, selected cases and profiles,
  exact system prompts, model tags, generation settings, Git revision/status and outcome.
- `attempts.jsonl`: append-only, flushed raw/processed responses and exact prompts,
  written before validation or scoring. Interactive generations are also logged here.
- `results.json`: batch results, all attempts, validation warnings, selected attempt and metrics.
- `answers.json`: selected batch answers, updated after each attempt.
- `exports/`: the existing CSV reports.
- `source_snapshot/`: Python source, profiles and requirements as used for this run.

New defaults are `--quality-mode observe --processing none`. These deliberately
retain the original answer and only observe validation warnings. Prior behavior
modified responses and retried them. Do not compare old/new runs as if their settings
were identical.

| Quality mode | Validation | Validation retries |
| --- | --- | --- |
| `off` | Disabled | None |
| `observe` | Recorded | None |
| `enforce` | Recorded | Up to `--max-retries` per answer (default 1) |

`--processing none` preserves the model text, including overlong or invalid answers.
`--processing legacy` separately enables the old sentence filtering and 75-word cut.
Quality mode does not change this setting. All original responses remain saved.
Enforce retries on any single-answer warning; exhausted warnings remain reported.
Cross-profile checks are observational in observe/enforce; similarity never triggers
regeneration. Generation errors are retained and not scored. Interactive mode supports
off/observe only; its output is in the journal, without batch scoring/CSV exports.

Example controlled pilot in PowerShell (run from the repository root):

```powershell
$env:ARCHEHR_SPLIT="dev"
python main.py --max-cases 5 --experiment-name dev-no-checks --quality-mode off --processing none --skip-plot
python main.py --max-cases 5 --experiment-name dev-observe --quality-mode observe --processing none --skip-plot
python main.py --max-cases 5 --experiment-name dev-enforce --quality-mode enforce --processing none --max-retries 1 --skip-plot
```

Off and observe have the same generation policy; observe additionally measures
warnings. Neither should systematically produce different styles. The configured
profiles/models are used (currently seven profiles, not the planned thirteen).

Optional `--out`, `--answers-out` and `--csv-dir` paths now resolve **inside the new
run folder**. They must be distinct relative paths; absolute paths and `..` are rejected.
For example `--out pilot.json` changes the name without reusing an older file.

A normally interrupted/failed process records `interrupted_or_failed`; an abrupt kill
can leave `running`, which must not be interpreted as completed. Partial journals and
checkpoints remain available. `completed_with_errors` means the batch finished but
some individual results failed. No resume behavior is implemented.

Model tags are recorded, but immutable Ollama model digests are not yet captured.
Current custom scoring approximations are unchanged; run tracking does not make
these official BERTScore, AlignScore or MEDCON measurements. New run folders contain
clinical inputs/outputs and are excluded from Git by `.gitignore`.

Run synthetic regression checks without a model server:

```powershell
python -m unittest discover -s tests -v
```

Earlier JSON/CSV files remain in their original locations. Missing prompts, retry
histories and experiment settings cannot be reconstructed reliably from final answers.
