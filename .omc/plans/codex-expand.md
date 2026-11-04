# Codex 작업: 탐색 범위 확장 1단계 (PLAN 개정 5)

먼저 읽기: `PLAN.md` 맨 위 개정 5, `AGENTS.md`, `onto/phase_8_design/{generate.py,loop.py,closed_loop.py}`, `dft/run_set.py`, `.claude/skills/ponytail`(full), `tdd-workflow`.
환경: `.venv/bin/python`. 실제 DFT와 LLM 호출은 하지 않는다(실행은 내가 한다). PubChem 조회는 허용한다. git 명령은 쓰지 않는다.

## 1. 확장 기준 세트 `onto/phase_4b_extend/reference_expansion.csv`
- 열: id, name, smiles, class, source(DOI와 원문 위치), note
- 목표는 6~9개 분자다. 우리 코퍼스 논문에서 고르고, 구조는 원문으로 확인한다.
  - 원문 텍스트: `onto/phase_3_corpus/text/*.txt` (로컬에만 있다. 공개 저장소에는 없음)
  - 후보 계열:
    - 1,10-페난트롤린-5,6-다이온 (Hazra 2026)
    - 벤조[1,2-b:4,5-b']다이티오펜-4,8-다이온 BDT-Q (Abdinejad 2024)
    - 퀴녹살린-5,8-다이온 (Pizarro 2025)
    - 퀴놀린-5,8-다이온
    - 중성 나프토이미다졸-다이온: 이미다졸륨 계열(Petersen 2025)의 중성 대응물. 중성 대응물을 만들 수 없으면 뺀다.
    - 우리 코퍼스에 있는 다른 헤테로고리 퀴논이 있으면 추가한다.
- 규칙: 중성 분자, 원소 C/H/N/O/F/Cl/Br/S, 중원자 30개 이하. 기존 기준 세트 15개와 InChIKey가 겹치면 안 된다.
- RDKit으로 파싱되는지, 아래 새 T0 검사를 통과하는지 확인한다. PubChem CID도 함께 기록한다(캐시 재사용).

## 2. `dft/run_set.py` 확장
- 위 csv를 입력으로 넣으면 `dft/runs/ref_set/`에 이어서 계산되게 한다. 이미 계산한 15개는 건너뛴다.
- 결합 위치(카보닐 O) 열거가 헤테로고리 분자에서도 맞게 동작해야 한다.
- 이 부분은 기존 `--input`과 `--out`을 쓰는 것으로 충분하다면 코드를 고치지 말고 실행 명령만 정리한다.
- summarize:
  - 맞교환선을 전체(기존 + 확장)로 다시 적합한다.
  - 계열별 잔차(평균, 최대)를 보고한다.
  - 기존 선 a, b, σ는 `line_v1`로 함께 보관한다.

## 3. 루프 검사 확장 (`generate.py`, `loop.py`)
- T0 퀴논 패턴을 일반화한다: 고리 안의 1,2- 또는 1,4- 카보닐 쌍. 고리 원자로 N과 S를 허용한다.
- `in_domain`:
  - 코어 SMARTS 4종 목록 대신 일반 퀴논 패턴을 쓴다.
  - 치환기 허용 목록을 없애고, 원소 C/H/N/O/F/Cl/Br/S, 중성, 중원자 30개 이하로 바꾼다.
  - Tanimoto 조건을 없앤다.
  - 예전 동작은 `--domain v1` 옵션으로 남긴다(기본값 v2).
- 합성 가능성: RDKit Contrib의 SA score를 쓸 수 있으면 원장에 `sa_score`를 기록한다(판정에는 쓰지 않음). 쓸 수 없으면 건너뛰고 보고한다.
- 편집 연산(무작위 arm)
  - 치환기 목록을 넓힌다: F, Cl, Br, CN, CF3, CH3, OCH3, OH, NH2, CO2CH3, SO2CH3.
  - 방향족 C-H를 N으로 바꾸는 연산을 추가한다.
- LLM 프롬프트
  - 허용 범위 문구를 새 규칙에 맞게 바꾼다.
  - 확장 기준 세트(D 표)가 근거로 들어가게 한다.
  - "알려진 분자보다 PubChem에 없는 분자를 선호하라"는 문장을 넣지 않는다. 신규성은 기록만 한다.

## 4. 시험
- 페난트롤린-다이온, BDT-Q, 퀴녹살린-다이온이 v2 T0와 영역 검사를 통과한다.
- 벤젠, 하전된 이미다졸륨, Fe 포함 분자, 중원자 31개 이상은 거절된다.
- `--domain v1`이면 예전 결과와 같다.
- 무작위 편집으로 C→N과 CF3 편집이 실제로 만들어진다.
- 기존 시험이 모두 통과한다.

## 5. 마무리
- Makefile 타깃을 추가한다.
  - `refset-expand`: 확장 기준 세트 DFT, `--gpus 0,1`
  - `loop3`, `loop3-random`: v2 영역에서 3회차 × 5개
- `make test` 결과, 확장 기준 세트 표(id, SMILES, 계열, CID), 예상 DFT 시간을 붙이고, 마지막 줄에 `EXPAND-DONE`.
