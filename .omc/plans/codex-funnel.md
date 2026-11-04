# Codex task: systematic funnel search (code only; I launch GPU runs)

Goal: scan a wide quinone chemical space systematically (user decision 2026-11-04, air capture: O2 stability required).
Funnel: enumerate library → rule filter → cheap DFT tier (E2 only) with O2-calibrated gate → surrogate-ranked full DFT (adduct, f) → high-level for top.
Read first: .claude/skills/ponytail/SKILL.md, tdd-workflow, mle-workflow (data contract, baseline before complexity), AGENTS.md rules.
Rules: TDD with NEW test files in onto/phase_10_funnel/tests/ (add to Makefile test); smallest code; no commits; no GPU/LLM/network runs (CPU unit tests with fake evaluators). Reuse existing code: loop.t0 (quinone/domain filter), loop.edit (mutations), generate._inchikey, sa_score, run_set.run_molecule pieces / dft.optimize, closed_loop.score + o2 calibration (dft/runs/ref_set/o2_calib.json, lines.json v2). numpy only for the surrogate (sklearn is NOT installed; do not add dependencies) — a small numpy Gaussian process (RBF on Morgan fingerprints → Tanimoto kernel) is enough; ponytail-mark the ceiling.

Files (one folder onto/phase_10_funnel/):
1. enumerate.py → library.csv (smiles, inchikey, core, substituents, sa_score). Deterministic.
   Cores (6-ring quinone variants): 1,4-BQ, 1,2-BQ, 1,4-NQ, 1,2-NQ, 9,10-AQ, 9,10-PQ, quinoxaline-5,8-dione, quinoline-5,8-dione, phenanthroline-5,6-dione, BDT-Q (thiophene-fused), plus aza variants (one/two ring C→N on fused rings).
   Substituents on free C-H positions: H, F, Cl, Br, CN, CF3, OMe, NH2, OH, Me, SO2Me — up to 2 substituents for BQ/NQ-size cores and 1 for larger; symmetry-deduplicate by InChIKey. Report library size; aim 10^3–10^5, cap via config.
2. filter: loop.t0 (v2 rules), SA ≤ 4.5, drop duplicates of refs/KG/Alherz/previous loops (reuse ctx dedupe sources), note PubChem status later (not in funnel).
3. tier1.py: cheap E2 tier = optimize Q_radical_anion and Q_dianion only (same B3LYP-D3BJ/def2-SVP/SMD as run_set) per molecule, resumable JSON per InChIKey in dft/runs/funnel_tier1/; multi-GPU spawn like run_set (`--gpus`). Output tier1.csv with E2_eV, raw margin, calibrated margin (class shift from o2_calib.json; if file missing, refuse unless --no-calib for tests).
   Gate: calibrated margin ≥ 0.15 V − tol (tol 0.1 V, configurable) → candidates for tier 2.
4. surrogate.py: numpy GP (Tanimoto kernel, Morgan r=2 2048) trained on all molecules with full DFT f (ref_set + loop runs, attached only, v2 line) → predicts f mean/std for tier-1 survivors; pick next batch by UCB (mean + κ·std), batch diversity by max Tanimoto < 0.7 within batch. Baseline to report: random pick from the same survivors (mle-workflow: baseline before complexity).
5. tier2.py: full DFT for the picked batch = reuse run_set.run_selected (adds adduct) into dft/runs/funnel_tier2/round_N/; score with closed_loop.score + calibration; append to a ledger; retrain GP; repeat N rounds (CLI --rounds, --batch).
6. Makefile targets: funnel-enumerate (CPU), funnel-tier1 (GPU; `--limit` and `--gpus`), funnel-tier2 (GPU). Do not run GPU targets.
7. Timing estimate from dft/runs/bench_bq and ref_set JSON wall times (if recorded) → print expected hours for tier 1 per 100 molecules.
Tests: enumeration determinism & dedupe; every library row passes t0; calibrated gate math; GP recovers a simple synthetic trend better than random on toy data; UCB batch diversity; tier1/tier2 resume with fake optimize; ledger append.
After code: run `make funnel-enumerate` (CPU) and report library size per core and filter attrition. Short Korean log .omc/research/codex-funnel.md. Print FUNNEL-CODE-DONE.
