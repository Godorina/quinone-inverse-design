# Codex 작업: 작은 닫힌 루프 `onto/phase_8_design/closed_loop.py` (PLAN 개정 4)

먼저 읽기: `PLAN.md` 맨 위 개정 4 항목, `onto/phase_8_design/generate.py`(context, check, call_llm, prompt), `dft/run_set.py`(`--input`, `--out`, `summarize`), `onto/phase_8_design/runs/20261031-0903/responses.jsonl`(지난번 LLM이 왜 거절했는지), `.claude/skills/ponytail`(full), `tdd-workflow`.
환경: `.venv/bin/python`. 실제 LLM 호출과 DFT는 하지 않는다(내가 실행한다).

## 흐름 (회차 R = 3, 회차당 M = 5)
```
for r in 1..R:
  text = loop_prompt(ctx, history)        # history = 지금까지 평가한 후보와 결과, 거절된 제안과 이유
  resp = call_llm(text)                   # generate.call_llm 재사용. 스키마는 같다
  passed = [p for p in proposals if check(p, ctx, seen) is None][:M]   # generate.check 재사용
  write round_r/input.csv (id, smiles)
  evaluate(round_r)  # 기본: subprocess로 `dft/run_set.py --input ... --out runs/loop/round_r --gpus 0,1`
  results = read per-molecule E2_eV, dE_bind_kcal, co2_detached, E_O2_eV from round_r/summary.json
  f = (a*E2_eV + b - dE_bind)/sigma        # 기준 세트 선(ref_set summary)의 a, b, sigma를 쓴다. 회차 자체 선이 아니다
  margin = E_O2_eV - E2_eV                  # 부호 주의(test_o2_sign.py와 같음)
  success = f >= 2 and margin >= 0.15 and not detached
  append to history, ledger.jsonl; save after every round   # 중간에 멈춰도 이어서 할 수 있게
```

## loop_prompt (지난번 실패를 고친다)
- 역할: "맞교환선을 넘을 **시험 가능한 가설**을 제안한다. DFT가 판정하므로, 목표에 도달한다는 증거는 필요 없다. 방향을 뒷받침하는 근거(D/K ID)를 인용하라."
- `insufficient_evidence`는 **인용할 근거가 하나도 없을 때만** 허용한다.
- D 표(기준 세트)와 K 표(KG)는 generate.prompt와 같다.
- **루프 기록 표**: 지금까지 평가한 후보마다 SMILES, 부모, f, O2 여유, CO2 이탈 여부, success. 그리고 직전 회차에서 거절된 제안과 이유(t0, 영역, 인용, 중복). 회차 2부터 들어간다.
- 회차 2부터 지시: "기록 표에서 f가 오른 방향은 더 밀고, 떨어진 방향은 피하라. 이유를 hypothesis에 써라."
- 정확히 5개. 중복 금지 목록에는 SMILES를 쓴다.

## 만들 것 (시험 먼저)
`closed_loop.py`(함수 몇 개 + main, 클래스 없음), `tests/test_closed_loop.py`(LLM과 DFT는 가짜로 주입).
- main 인자:
  - `--rounds 3 --per-round 5`
  - `--out onto/phase_8_design/runs/loop-<시각>`
  - `--resume <dir>`: 끝난 회차는 건너뛴다
  - `--dry-run`: 1회차 프롬프트만 저장
- `evaluate`와 `call_llm`은 인자로 주입할 수 있게 한다(시험용).
- 최종 `report.md`:
  - 회차별 최고 f, 회차별 평균 f, 성공 수
  - 기준 세트 최고 f(1.24)와 비교
  - 실패 유형별 개수
  - 총 LLM 비용
  - "실행 1회, 통계 비교 없음"이라는 한계 문구

## 시험
- 가짜 LLM과 가짜 평가자(f를 정해 둔 값으로 돌려줌)로 3회차를 돈다. 원장에 회차가 3개 남고, 최고 f 곡선이 단조 비감소다.
- 회차 2의 프롬프트에 회차 1의 결과(SMILES와 f)와 거절 이유가 들어 있다.
- f와 O2 여유는 기준 세트 선과 올바른 부호로 계산된다(손계산 1개).
- `--resume`: 회차 1을 저장한 뒤 다시 실행하면 회차 1의 LLM과 평가자를 부르지 않는다.
- 통과한 후보가 0개인 회차는 평가자를 부르지 않고, 기록에는 남는다.

## Makefile
- `test`에 추가: `cd onto/phase_8_design && $(PY) tests/test_closed_loop.py`
- 타깃 `loop`: `$(PY) onto/phase_8_design/closed_loop.py --rounds 3 --per-round 5`

## 규칙
git·설치·하위 에이전트 금지. 실제 LLM 호출과 DFT 금지(`--dry-run` 하나만 실행해서 프롬프트 길이를 보고). 수정은 `onto/phase_8_design/`와 Makefile만. 끝나면 `make test` 결과를 붙이고, 마지막 줄에 `P8-LOOP-DONE`.
