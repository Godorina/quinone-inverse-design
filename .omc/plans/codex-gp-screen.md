# Codex task (after GRAPH-DONE): GP-only screening path (user decision 2026-11-04: MLIP dropped for scoring)

Finding: MLIP vs DFT(SMD) binding R² = 0.15 (LOO RMSE 2.28 vs sd 2.41), Tanimoto GP R² = 0.51 (LOO RMSE 1.68) on the same 73 molecules. See tail of .omc/research/codex-mlp-screen.md.
Rules: ponytail + TDD (NEW test file), no commits, no GPU/LLM/network.
1. In onto/phase_10_funnel/mlp_screen.py (or a tiny gp_screen.py reusing its functions — choose the smaller diff): add `--binding gp` (make it the default) that predicts ΔE_bind with surrogate.GP trained on attached DFT ΔE_bind (same training_records), std scaled to its LOO RMSE; E2 GP unchanged; f_pred and its std from both; O2 gate (calibrated margin + std ≥ 0.15) and UCB+diversity selection unchanged; random control 10 from the same pool. Library = the 13,836 rows minus nothing (Br is fine for GP; keep an element check only for DFT feasibility: C/H/N/O/F/Cl/Br/S).
2. Fix the calibration gate in --calibrate: report R² and compare LOO RMSE with the mean-only baseline; WARN when R² < 0.5 or LOO RMSE > 0.8 × baseline (not only the 3.2 kcal/mol absolute).
3. Exclude from candidates any molecule already DFT-computed (by InChIKey).
4. Write onto/phase_10_funnel/dft_candidates.csv (id, smiles, inchikey, core, E2_pred±std, dEbind_pred±std, f_pred±std, margin_pred, arm=gp|random) and a short summary (pool sizes at each gate, per-core counts in the top 50).
5. If o2_calib.json is missing: still write the file with raw margins and `uncalibrated`, and print that the final selection must be re-run after calibration.
Run it (CPU) on the library and report the summary. Append Korean log to .omc/research/codex-mlp-screen.md. Print GP-SCREEN-DONE.
