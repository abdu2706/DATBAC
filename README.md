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

