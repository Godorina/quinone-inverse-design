# Codex task: O2-margin calibration set (high-level E2 only) + calibrated O2 gate in the loop

Goal (user decision 2026-11-04): air capture, O2 stability required. Low-level (B3LYP/SVP) O2 margin is too optimistic vs high level (ωB97M-V/TZVPD, Fc, exp O2 −1.23 V): shift −0.28…−0.34 V for halogenated BQs, −0.61 V for N-heterocyclic quinoxaline-diones (dft/runs/highlevel*/summary.json). Need class-aware calibration.
Rules: ponytail + TDD (NEW test files only; add to Makefile test), no commits, no LLM calls. GPU jobs: only via the Makefile target below, I launch it.

A. dft/highlevel.py: add SETS['calib'] — states Q_radical_anion and Q_dianion only (no adduct, no CO2), sources = dft/runs/ref_set/<KEY>.json, out dft/runs/highlevel_calib/. Molecules (InChIKey prefix → ref_set file):
   GHLUWAJF (X03 quinoxaline-5,8-dione), KCALAFIV (X01 phenanthroline-dione), SIUXRPJY (X02 BDT-Q), VNBZDYJW (X04), RZVHIXYE (AQ), SVPKNMBR (2,3-diCl-NQ), JKLYZOGJ (F4BQ), YYVYAPXY (PAQ), JCARTGJG (2,6-diCl-BQ).
   Reuse jobs()/run_job/composite machinery; composite must tolerate missing adduct/CO2 (E2_V and O2_margin_V only). Summary rows: low E2_eV, low margin (E_O2_eV − E2_eV), high E2_V, high O2_margin_V, shift = high − low margin, class = 'heterocyclic' if quinone fused ring system has N/S/O ring atom else 'carbocyclic' (reuse onto/phase_9_obsidian/export.skeleton_from_smiles or minimal copy).
   Makefile target `highlevel-calib` (GPUs 0,1). Also include the 6 existing high-level molecules in the calibration table by reading dft/runs/highlevel*/summary.json (no recompute).
B. Calibration file dft/runs/ref_set/o2_calib.json written by `highlevel.py --set calib --summary`: per class {mean_shift, sd, n}. ponytail: constant per-class shift (note ceiling: linear in E2 if residuals demand).
C. onto/phase_8_design/closed_loop.py: new flag `--o2-calib PATH`. When given, score() uses corrected margin = raw margin + class shift (class from SMILES) for the success test and for o2_feasible() (random-arm parents and LLM prompt O2 numbers). Record raw and corrected margins in results; save calib path+content hash in config.json. Prompt text: tell the LLM margins are calibrated to high level. Without the flag, behaviour unchanged (old runs reproducible).
D. Makefile targets loop4 / loop4-random = loop3 settings + --o2-calib dft/runs/ref_set/o2_calib.json (do not run them).
Tests: composite without adduct; class detection; corrected margin math; flag absent → identical scores; config records calib.
Run CPU tests only. Short Korean log .omc/research/codex-o2-calib.md. Print CALIB-CODE-DONE.
