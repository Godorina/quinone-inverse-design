# Codex task: fix high+medium findings from .omc/research/review-v2-merged.md

Read first: .claude/skills/ponytail/SKILL.md, .claude/skills/tdd-workflow/SKILL.md, AGENTS.md rules, .omc/research/review-v2-merged.md, .omc/research/codex-review-v2.md.
Rules:
- RED→GREEN: for every fix write the failing test FIRST in a NEW test file (a hook blocks editing existing test files): onto/phase_8_design/tests/test_review_fixes.py and dft/tests/test_review_fixes.py. Add both to the Makefile `test` target.
- Smallest diff. No git commits. No GPU or LLM runs. Do not touch onto/phase_4_extract/records*, onto/phase_3_corpus, existing run results under runs/ (except you may ADD a new line file, see 5).
- Existing tests must keep passing, except the known stale test_generate.py:69 (15 vs 21) — leave it.

Fixes (numbers from review-v2-merged.md):
1. loop.py t0 v2: accept only a 6-membered ring whose ring atoms are all sp2 and that holds a C=O pair at 1,2 or 1,4 positions. Negative tests: indan-1,3-dione O=C1CC(=O)c2ccccc21, cyclohexane-1,4-dione O=C1CCC(=O)CC1, diketopiperazine O=C1CNC(=O)CN1, succinimide, maleimide, isatin. Positive: BQ, NQ, AQ, PQ (1,2), quinoxaline-5,8-dione, both v2 top candidates, all 21 reference SMILES that are quinones (check dft/runs/ref_set/summary.csv rows/ smiles in JSONs).
2. t0: reject radicals (Descriptors.NumRadicalElectrons != 0).
3. t0: reject isotope-labelled atoms.
4. closed_loop.py: save args (arm, domain, seed, per_round, reject_pubchem, extra_ref) to out/config.json on first run; on --resume, refuse with a clear error when given args differ from saved (or restore them if not given — pick the simpler, document it). Old runs without config.json: allow resume as before.
5. Line versions: store the fitted line(s) in a committed file dft/runs/ref_set/lines.json {"v1": {...n=12 line...}, "v2": {...n=18 line...}} taken from current summary.json line_v1/line. run_set.summarize stops inheriting line_v1 from the previous summary.json (keep writing "line" = current fit). highlevel SETS name the line key ('v1'/'v2') read from lines.json; no silent fallback (KeyError if missing). closed_loop: record the line used (a,b,sigma,n) in each round record; compare_runs refuses (or warns clearly) when the two runs used different lines.
6. loop.py objective/_score O2 sign: margin = E_O2 - E2 >= margin threshold, consistent with closed_loop.score. Check which tests encode the old sign; if an existing test asserts the wrong sign, leave it and report it (cannot edit), but add correct-sign tests.
7. t0: judge charge by total formal charge == 0 (allow nitro [N+](=O)[O-]); still reject disconnected fragments.
8. generate._substituents/select family key: for scaffolds outside the 4 cores include substituent identity so F vs Cl differ.
9. run_set family: use explicit class when present; for original refs map by core (BQ/NQ/AQ/PQ) instead of ring count.
10. highlevel.start_geometry / summarize and run_set.summarize: pick the lowest-energy adduct among attached ones (O–C <= 2.0 Å); if none attached, keep current behaviour (detached flag).
11. highlevel.inputs: candidate source path explicit in SETS (no matches[-1] glob guess). v1 must reproduce the current dft/runs/highlevel/summary.json low_f values exactly; v2 the highlevel_v2 ones.

After: run `make test` (CPU) and report pass/fail counts honestly. Write a short Korean change log to .omc/research/codex-fix-v2.md (finding → files:lines → test name). Print FIX-DONE.
