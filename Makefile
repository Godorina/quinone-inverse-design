# Run everything from this folder. onto/ is the working copy of the pipeline (copied from ../ontology/quinone on 2026-10-30).
PY := $(CURDIR)/.venv/bin/python
# GPU1 is mostly taken by llama-server; gpu4pyscf fails when it spreads onto it.
export CUDA_VISIBLE_DEVICES ?= 0
B4 := onto/phase_4b_extend

.PHONY: env dft-check test bench refset generate status pairs compounds review
env:       ## create .venv here from requirements.txt (python 3.11)
	uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt

dft-check: ## CPU vs GPU DFT on water must agree
	$(PY) dft_check.py

test:      ## all test suites
	cd onto/phase_2_schema && $(PY) tests/test_onto.py
	cd onto/phase_4_extract && uv run --frozen pytest -q
	cd $(B4) && $(PY) tests/test_4b.py && $(PY) tests/test_compound_review.py
	cd onto/phase_8_design && $(PY) tests/test_loop.py
	cd onto/phase_8_design && $(PY) tests/test_generate.py && $(PY) tests/test_o2_sign.py && $(PY) tests/test_loop_contract.py && $(PY) tests/test_random_parents.py
	cd onto/phase_8_design && $(PY) tests/test_closed_loop.py && $(PY) tests/test_loop2.py && $(PY) tests/test_pubchem.py
	cd onto/phase_5_build && $(PY) tests/test_build.py && $(PY) tests/test_pubchem_build.py
	cd dft && $(PY) tests/test_dft.py
	cd dft && $(PY) tests/test_run_set.py && $(PY) tests/test_summarize_foreign_json.py && $(PY) tests/test_highlevel_flags.py && $(PY) tests/test_highlevel_failed_jobs.py
	cd dft && $(PY) tests/test_highlevel.py

bench:      ## run the BQ DFT benchmark
	$(PY) dft/bench.py

refset:     ## run the phase-7 DFT reference set on GPUs 0 and 1
	$(PY) dft/run_set.py --gpus 0,1

generate:   ## generate phase-8 candidates with Claude
	$(PY) onto/phase_8_design/generate.py --calls 4

loop:       ## run the phase-8 closed loop
	$(PY) onto/phase_8_design/closed_loop.py --rounds 3 --per-round 5

status:    ## rebuild the 38-paper status table (uses cached abstracts)
	$(PY) $(B4)/xlsx_status.py

pairs:     ## rebuild the MeCN pair candidates (keeps no reviewer edits: back up pair_review.csv first)
	$(PY) $(B4)/pair_candidates.py

compounds: ## rebuild compound_review.csv (one row per compound; refuses to overwrite reviewer verdicts)
	$(PY) $(B4)/compound_review.py

review:    ## compound review progress toward the phase 7 gate (>=10 ok from >=2 papers)
	@python3 -c "import csv,collections as C;r=list(csv.DictReader(open('$(B4)/compound_review.csv')));v=C.Counter(x['verdict'] or '-' for x in r);ok={x['paper_id'] for x in r if x['verdict']=='ok'};print(f'compounds {len(r)}  verdicts {dict(v)}  ok papers {len(ok)}  gate', 'PASS' if v['ok']>=10 and len(ok)>=2 else 'not yet')"

loop2:
	$(PY) onto/phase_8_design/closed_loop.py --rounds 3 --per-round 5 --arm llm --extra-ref onto/phase_8_design/runs/loop-20261031-151304

loop2-random:
	$(PY) onto/phase_8_design/closed_loop.py --rounds 3 --per-round 5 --arm random --extra-ref onto/phase_8_design/runs/loop-20261031-151304

highlevel: ## composite final-candidate calculations on GPUs 0 and 1
	$(PY) dft/highlevel.py --gpus 0,1
