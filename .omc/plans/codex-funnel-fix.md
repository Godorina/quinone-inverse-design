# Codex task: funnel fixes from verification (same rules: ponytail, TDD with NEW test files, no commits, no GPU/LLM/network)

1. enumerate.py core labels: label `core` by the ACTUAL ring system after enumeration (classify the final molecule: 1,4-BQ, 1,2-BQ, 1,4-NQ, 1,2-NQ, AQ, PQ, quinoline-5,8-dione, quinoxaline-5,8-dione, phenanthroline-5,6-dione, BDT-Q, and "aza-<parent>" for other aza variants), not the first-enumerated parent.
2. Drop molecules with any N–N bond (triazines/tetrazines etc. are exotic for this study); report how many removed.
3. New `subset.py` → onto/phase_10_funnel/tier1_subset.csv: stratified MaxMin (Morgan r2 Tanimoto) diverse subset, default 300 molecules, quota per true core proportional to sqrt(core size) with min 10 per core, deterministic seed; prefer smaller molecules by excluding > 20 heavy atoms; record heavy-atom count and estimated GPU time (time ∝ HA^2.5 fitted on ref_set wall times if available, else the log's numbers) and print the total estimated GPU-hours.
4. tier1 gate: default tol = 0 (cut exactly at calibrated margin ≥ 0.15 V); `--tol` stays as an option.
5. tier1 takes `--library PATH` (use tier1_subset.csv); remove reliance on `--limit` ordering (keep --limit only as a cap after the explicit CSV).
6. Makefile: funnel-subset target; funnel-tier1 uses the subset CSV.
7. Add Stage "E₂ surrogate" option (document only, do not implement now): after tier1, a GP on tier-1 E₂ can predict E₂ for the remaining library to choose the next tier-1 batch.
Run make funnel-enumerate and funnel-subset (CPU). Append short Korean log (new library size, per-core counts, N–N removed, subset size, est. GPU-hours) to .omc/research/codex-funnel.md. Print FUNNEL-FIX-DONE.
