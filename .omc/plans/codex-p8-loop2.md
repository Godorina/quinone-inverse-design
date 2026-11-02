# Codex 작업: 닫힌 루프 보완 (PLAN 개정 4.1)

먼저 읽기:
- `PLAN.md` 맨 위 개정 4.1
- `onto/phase_8_design/closed_loop.py`, `generate.py`, `loop.py`(`random_proposer`, `edit`, `in_domain`)
- 첫 실행 결과 `onto/phase_8_design/runs/loop-20261031-151304/`(ledger.jsonl, round_*/summary.json, report.md)
- `.claude/skills/ponytail`(full), `tdd-workflow`

환경: `.venv/bin/python`. **실제 LLM 호출과 DFT는 하지 마라**(실행은 내가 한다).

## 보완 1: 적용 영역 확장
- `--extra-ref <dir> [<dir> ...]` 인자를 추가한다. 지정한 폴더의 `round_*/*.json` 중 계산이 끝난 분자(Q, Q•⁻, Q²⁻, 부가물이 모두 수렴)의 SMILES를 `ctx["ref_fps"]`(적용 영역 지문)에 추가한다.
- 맞교환선 a, b, σ와 D 표는 바꾸지 않는다.
- 이 분자들은 중복 검사 대상에도 넣는다. 이미 계산한 분자를 다시 제안하면 `duplicate`로 거절한다.
- 허용 치환기 집합은 그대로 둔다.

## 보완 2: 빈자리 보충
- 한 회차에서 통과한 후보가 M개보다 적으면, 같은 회차 안에서 LLM에 최대 2번 다시 묻는다.
  - 재질문 프롬프트에는 탈락한 제안과 이유, 그리고 이미 통과한 SMILES를 넣는다.
- `response.json`은 `response_1.json`, `response_2.json`처럼 순서대로 저장한다. `--resume`은 저장된 응답을 다시 사용한다.
- 탈락한 이유는 모두 원장에 남긴다.

## 보완 3: 무작위 기준선 B0
- `--arm llm|random` 인자를 추가한다(기본값 llm).
- random arm은 LLM을 호출하지 않는다.
  - 부모는 지금까지 평가한 분자와 기준 세트 중 f 상위 k=5개에서 균등하게 고른다. 회차 1에서는 기준 세트 상위 5개에서 고른다.
  - `loop.edit`로 무작위 편집하고, 같은 `check`를 통과한 후보로 회차당 M개를 채운다. seed를 고정하고, 최대 2000번 시도한다.
- 평가, 원장, 보고서는 llm arm과 똑같이 처리한다.

## 보고서
- `report.md`에 다음을 추가한다:
  - arm 이름
  - 회차별 최고 f와 O2 조건 통과 후보 중 최고 f
  - 시도한 제안 수와 탈락 이유 분포
- 두 실행 폴더를 받아 회차별 비교표를 만드는 `compare_runs(dir_a, dir_b) -> markdown` 함수를 추가한다. main에서 `--compare A B`로 실행한다.

## 시험 (LLM과 DFT는 가짜)
- extra-ref: 가짜 분자 json이 있는 폴더를 주면 그 SMILES가 `ref_fps`와 중복 검사에 들어간다. 맞교환선은 바뀌지 않는다.
- 빈자리 보충: 첫 응답에서 2개만 통과하면 재질문이 일어나고, 최대 3번 호출해서 M개를 채운다. 3번 호출해도 모자라면 있는 만큼만 평가한다.
- random arm: LLM이 호출되지 않는다. 회차당 M개가 모두 `check`를 통과한다. 같은 seed로 실행하면 같은 후보가 나온다.
- `--resume`이 `response_2.json`까지 다시 사용한다.
- `compare_runs`: 가짜 두 실행 결과로 표가 만들어진다.

## Makefile
- `test`에 새 시험을 추가한다.
- 타깃 추가:
  - `loop2`: `$(PY) onto/phase_8_design/closed_loop.py --rounds 3 --per-round 5 --arm llm --extra-ref onto/phase_8_design/runs/loop-20261031-151304`
  - `loop2-random`: 위와 같은 인자에 `--arm random`을 쓴다.

## 규칙
git·설치·하위 에이전트 금지. 실제 LLM 호출과 DFT 금지. 수정은 `onto/phase_8_design/`와 Makefile만 한다. 끝나면 `make test` 결과를 붙이고, 마지막 줄에 `P8-LOOP2-DONE`.
