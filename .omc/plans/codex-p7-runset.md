# Codex 작업: Phase 7 기준 세트 DFT 실행 스크립트 `dft/run_set.py`

먼저 읽기: `PLAN.md` 5절(개정 3, B안), `dft/dft.py`, `dft/bench.py`, `.claude/skills/ponytail`(full), `tdd-workflow`.
환경: `.venv/bin/python`. GPU0과 GPU1이 모두 비어 있다.

## 입력
- `onto/phase_4b_extend/smiles_proposals.csv`에서 `canonical_smiles`가 있는 행. InChIKey 기준으로 중복을 빼면 15개다.
- 같은 분자가 여러 행에 있으면 `paper_id:compound`를 `;`로 이어 함께 기록한다.

## 만들 것 (시험 먼저)
`dft/run_set.py` (함수 몇 개 + main, 클래스 없음), `dft/tests/test_run_set.py`(DFT 호출 없음).

1. `reference_set(csv) -> list[dict]`: InChIKey 중복 제거, 15개.
2. `carbonyl_sites(smiles) -> list[int]`: 서로 대칭이 아닌 카보닐 O 원자 인덱스만 고른다(RDKit `CanonicalRankAtoms(breakTies=False)`로 대칭 판단).
3. 분자 하나 처리 `run_molecule(item, out_dir, gpu)`:
   - Q(0,0), Q•⁻(−1,1), Q²⁻(−2,0)을 `dft.optimize`로 계산한다.
   - 부가물은 **최적화된 Q²⁻ 좌표**에 `co2_adduct`로 CO2를 붙여서 시작한다. 결합 위치는 `carbonyl_sites`에서 고른 위치마다 하나씩 계산한다.
   - 결과는 `out_dir/<inchikey>.json`에 상태별로 저장한다. 상태 하나가 끝날 때마다 저장한다.
   - 파일에 이미 성공한 상태가 있으면 그 상태는 건너뛴다(다시 실행하면 이어서 계산).
4. 공통 계산(한 번만, `out_dir/_common.json`): CO2(0,0), O2(0, spin=2, 삼중항), O2•⁻(−1,1).
5. 요약 `summarize(out_dir) -> dict`(DFT 없이 json만 읽음):
   - 분자마다 `E2_eV = (E[Q2-] − E[Q•-])·27.2114`. 전위는 −E2_eV로 보고, 부호 규약은 주석에 적는다.
   - `dE_bind_kcal = min over sites (E[adduct] − E[Q2-] − E[CO2])·627.5`
   - `co2_detached`: 최소값을 준 부가물의 O–C가 2.0 Å보다 크면 참.
   - `E_O2_eV = (E[O2•-] − E[O2])·27.2114`
   - 맞교환선: CO2가 떨어지지 않은 분자만으로 `dE_bind = a·E2 + b`를 최소제곱 적합하고 σ(잔차 표준편차)를 구한다. 남은 점이 10개 미만이면 `line_measurable=false`.
   - 결과는 `out_dir/summary.json`과 `summary.csv`.
6. main:
   - `--gpus 0,1`: 분자 목록을 GPU 수만큼 나눠 `multiprocessing`으로 동시에 돈다(프로세스마다 `CUDA_VISIBLE_DEVICES`를 하나씩).
   - `--only N`: 앞의 N개만(시간 실측용).
   - `--summary`: 계산 없이 요약만.
   - 출력 폴더는 `dft/runs/ref_set/`.

## 시험 (DFT 없음)
- `reference_set`: 15개, InChIKey가 모두 다르다.
- `carbonyl_sites`: 벤조퀴논 1개, 2,6-다이클로로-BQ 2개, 9,10-페난트렌퀴논 1개.
- `summarize`: 가짜 json 12개(그중 하나는 CO2 이탈)로 선 적합, 이탈 제외, `line_measurable` 확인. 가짜 json 9개면 측정 불가.
- 이어서 계산: 이미 성공한 상태가 있는 json이면 `optimize`가 호출되지 않는다(가짜 optimize 주입).

## Makefile
- `test`에 추가: `cd dft && $(PY) tests/test_run_set.py`
- 새 타깃 `refset`: `$(PY) dft/run_set.py --gpus 0,1`. `.PHONY`에도 추가.

## 규칙
git·설치·하위 에이전트 금지. **실제 DFT 실행 금지**(실행은 내가 한다). `dft/`와 Makefile만 수정. 끝나면 `make test` 결과를 붙이고, 마지막 줄에 `P7-RUNSET-DONE`.
