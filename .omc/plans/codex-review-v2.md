# Codex task: correctness review of the uncommitted v2 work (read-only)

Do NOT modify any file except the output file. No git state changes, no GPU jobs. `make test` (CPU) is allowed.

Scope: `git diff 2a8d603` plus untracked code/tests (dft/tests/test_expand.py, dft/tests/test_highlevel_v2.py, onto/phase_8_design/tests/test_expand.py if present).
Files: Makefile, dft/run_set.py, dft/highlevel.py, onto/phase_8_design/{closed_loop,generate,loop}.py and their tests.
Context: README.md, AGENTS.md (state 2026-11-03). Success = f>=2 AND O2 margin (E_O2_eV - E2_eV) >= 0.15 V AND CO2 attached (O-C <= 2.0 A).

Look for real bugs only (wrong results, silent data loss, wrong sign/unit, unfair LLM-vs-random comparison, resume bugs, tests that cannot fail).
Known/accepted, do not re-report: test_generate.py:69 expects 15 rows (now 21, hook blocks edit); generate.check accepts empty cited_ids.

Write `.omc/research/codex-review-v2.md` (Korean, short): per finding -> severity (high/med/low), file:line, failure scenario, minimal fix. Max 10 findings, most severe first. Then print REVIEW-DONE.
