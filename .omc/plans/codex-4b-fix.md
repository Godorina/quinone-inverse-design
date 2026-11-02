# Codex 수정: Phase 4b 독립 검증 결과 (REQUEST_CHANGES)

이전 지시서 `codex-4b-task.md`의 규칙을 그대로 지킨다(git·설치·LLM 호출 금지, 원본 수정 금지). 하위 에이전트 쓰지 말고 직접. 각 항목은 실패하는 시험을 먼저 쓰고(RED) 고친다(GREEN).

1. `phase_4b_extend/tests/test_4b.py` (평범한 `def test_*` + assert, 스크립트로도 실행 가능하게):
   - 상태표: 38행, DOI 중복 0, 엑셀 DOI 집합과 같음, status가 허용 집합 중 정확히 하나.
   - 짝짓기: 합성 레코드 2개(같은 화합물 쌍 1, 다른 화합물 0)로 규칙 확인. 이를 위해 짝짓기 로직을 import 가능한 함수 하나로 둔다(새 클래스 금지).
2. `phase_2_schema/tests/test_onto.py`: Computation 양성 예시 1개(위반 0), 두 번째 음성 예시(Experiment + code 등), NotReported 통과 사례. 기존 시험 유지.
3. `phase_4_extract/src/qextract/checker.py`: 서명 5필드가 `NotReported`가 아니면 그 값이 인용(quote) 안에 있어야 한다. 없으면 거절. 기존 인용 검사 함수를 재사용한다. 시험 `test_signature_not_in_quote_is_refused` 추가. 기존 73개 유지.
4. `pair_review.csv`:
   - `co2_standard_state` 열 추가(레코드에 없으면 빈칸, 가이드에 "검수자가 원문에서 채움" 명시).
   - `flags` 열 추가: `ref_not_fc`(기준전극이 FcFcPlus가 아님), `basis_suspect`(BindingEnergy/ΔG인데 basis=Experiment 이고 method가 CV 등 실험법; 예: m043 F4Q/DBQ/DNQ), `diff_condition_key`. 세미콜론으로 구분.
   - 가이드에 flags 의미 3줄 추가.
5. 초록 폴더를 `data/abstracts_4b/`로 옮기고 경로를 고친다(지시서와 일치).
6. 코드 정리: `xlsx_status.py`의 bare `except Exception: pass`는 실패한 DOI를 상태표 source에 `abstract_fetch_failed: <에러>`로 남기도록 바꾼다. 엑셀 경로는 명령행 인자(기본값 유지)로. REPORT.md에 적은 `ponytail:` 표시를 실제 코드 주석으로 넣거나 REPORT에서 지운다(사실과 일치시킨다).
7. REPORT.md를 갱신: 시험 명령과 숫자, 88행의 분포(논문별, 같은 조건 key 14행), flags 개수.

끝나면 마지막 줄에 `4B-FIX-DONE`.
