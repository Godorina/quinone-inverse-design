# Codex 작업: Phase 8 `onto/phase_8_design/generate.py` (B안: KG 근거 LLM 후보 생성) + Phase 9 준비

먼저 읽기: `PLAN.md` 7~8절(개정 3.1), `AGENTS.md`, `onto/phase_8_design/loop.py`(`t0`, `in_domain`, `edit`, `random_proposer`), `dft/run_set.py`, `.claude/skills/ponytail`(full), `tdd-workflow`.
환경: `.venv/bin/python`. **GPU는 쓰지 않는다**(지금은 다른 에이전트 차례다).

## 입력
- KG: `onto/phase_5_build/kg.ttl`. rdflib SPARQL로 화합물(이름, SMILES, InChIKey), 전위·결합 측정값(값, 단위, 조건 용매, 기준 전극, review_status), 산소 관찰을 읽는다. 각 행에 짧은 ID(`K001`…)를 붙이고, 원래 IRI와의 대응을 저장한다.
- 우리 DFT 기준 세트: `dft/runs/ref_set/summary.json` + `onto/phase_4b_extend/smiles_proposals.csv`.
  - 분자별 E2, ΔE_bind, `co2_detached`, O2 여유(E2 − E_O2)를 읽는다.
  - 맞교환선 a, b, σ로 `f = (a·E2_eV + b − ΔE_bind)/σ`를 계산한다.
  - 짧은 ID는 `D01`…로 붙인다. **이 표가 LLM에 주는 핵심 근거다.**
- 적용 영역(`in_domain` 인자):
  - 코어 SMARTS: BQ, NQ, AQ, PQ
  - 허용 치환기: 기준 세트에 나오는 것만(F, Cl, Br, CN, NH2, OH)
  - 기준 세트 Morgan 지문

## 만들 것 (시험 먼저)
`onto/phase_8_design/generate.py` (함수 몇 개 + main, 클래스 없음), `onto/phase_8_design/tests/test_generate.py`.

1. `context()`: 위 두 표와 ID 대응을 반환한다.
2. `prompt(ctx, previous_smiles)`: 한국어나 영어 모두 괜찮다. 다음을 넣는다.
   - 목표: 맞교환선보다 유리하게 f ≥ 2, O2 여유 ≥ 0.15 V, CO2가 떨어지지 않을 것
   - 기준 세트 표(D…)와 KG 표(K…)
   - 편집 규칙: 기준 세트 분자를 부모로, 치환기 추가·교체·제거·위치 이동만, 허용 치환기만
   - 출력: 10개, 각 `parent_id, smiles, edits, cited_ids, hypothesis`
   - 근거가 부족하면 `insufficient_evidence`
   - 이미 낸 SMILES 목록(중복 금지)
3. `call_llm(prompt) -> dict`: ontology-mlip과 같은 방식의 Claude CLI 호출이다.
   - `~/.local/bin/claude -p --model sonnet --tools "" --output-format json --json-schema <schema> --no-session-persistence --setting-sources "" --strict-mcp-config`, 입력은 stdin, timeout 900초.
   - `structured_output`, `total_cost_usd`, `usage`를 기록한다.
4. `check(proposal, ctx, seen) -> reason|None`: 아래 중 하나라도 걸리면 거절한다.
   - `t0`, `in_domain`
   - `cited_ids`가 모두 ctx에 있는지(없으면 `bad_citation`)
   - `parent_id`가 D 표에 있는지
   - InChIKey가 기준 세트, KG 화합물, `seen`(앞서 나온 것)과 겹치면 `duplicate`
5. `select(checked, n=10)`: 출력 순서대로 통과한 후보 중 처음 10개를 고른다. 같은 코어와 같은 치환기 집합(위치 무관)은 하나만 남긴다.
6. `baseline(ctx, parents_used, n=10, seed=0)`: B0.
   - LLM 선정 후보의 부모 비율과 같은 비율로 부모를 고른다.
   - `loop.edit`로 무작위 편집하고, 같은 `check`를 통과한 처음 10개를 쓴다. 최대 시도는 2000회다.
7. main
   - `--calls 4`(호출 4번 × 10개)
   - `--replay <dir>`: 저장된 `responses.jsonl`로 LLM 없이 재실행
   - `--dry-run`: 프롬프트만 저장하고 LLM을 호출하지 않음
   - 출력 폴더 `onto/phase_8_design/runs/<YYYYmmdd-HHMM>/`
     - `prompt_*.txt`, `responses.jsonl`, `ledger.jsonl`(제안마다 통과 여부와 이유)
     - `selected_llm.csv`, `selected_b0.csv`(열: id, smiles, inchikey, parent_id, cited_ids, hypothesis, arm)
     - `manifest.json`(KG 해시, summary 해시, 호출 수, 비용 합)

## 시험 (LLM과 GPU 없음)
- 가짜 응답으로 거절 규칙을 확인한다: 가짜 인용, 없는 부모, 퀴논 아님, 허용되지 않은 치환기, 기준 세트와 같은 분자(InChIKey), 앞 호출과 중복.
- `select`: 같은 코어와 치환기 집합은 하나만, 출력 순서 유지, 최대 10개.
- `baseline`: 10개를 반환하고 모두 `check`를 통과하며, 부모 비율이 LLM 선정과 같다.
- `context()`가 실제 파일에서 D 표 15행, f 값, K 표 1행 이상을 만든다.
- `--replay`로 같은 결과가 다시 나온다.

## Phase 9 준비: `dft/run_set.py`
- `--input <csv>`(열: id, smiles; inchikey는 있으면 쓰고 없으면 계산), `--out <dir>` 옵션을 추가한다.
- 기본값은 지금 동작 그대로 둔다(기준 세트, `dft/runs/ref_set/`).
- `--input`일 때는 공통 계산(CO2, O2, O2•⁻)을 기준 세트의 `_common.json`에서 복사해 재사용한다. 같은 방법이므로 다시 계산하지 않는다.
- 시험: `--input` csv 읽기, 공통 결과 재사용(가짜 optimize가 공통 계산에 호출되지 않는다).

## Makefile
- `test`에 추가: `cd onto/phase_8_design && $(PY) tests/test_generate.py`
- 타깃 `generate`: `$(PY) onto/phase_8_design/generate.py --calls 4`

## 규칙
- git·설치·하위 에이전트 금지.
- **실제 LLM 호출 금지**(`--dry-run`으로 프롬프트 하나만 만들어 붙여라). 실제 호출은 내가 한다. **GPU 계산 금지.**
- 수정은 `onto/phase_8_design/`, `dft/run_set.py`, `dft/tests/`, Makefile만.
- 끝나면 `make test` 결과와 dry-run 프롬프트 길이(문자 수)를 붙이고, 마지막 줄에 `P8-GEN-DONE`.
