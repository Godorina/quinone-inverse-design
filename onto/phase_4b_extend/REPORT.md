# Phase 4b 자동화 보고서

## 완료한 일

- `xlsx_status.py`가 표준 라이브러리 ZIP/XML로 XLSX를 읽고 38 DOI 상태표를 만들었다. 결과는 matched 24, needs_judgment 10, borderline 2, out_of_scope 2이다. 기존 `master.json`과 `data/labeled_all.json`만 재사용했고, 새 10건의 공개 API 응답은 `abstracts_4b/`에 원문 바이트로 보관했다. 자동 판정은 하지 않았다.
- 스키마에 계산 방법 서명 5개, 유래 측정값, 근거 위치, InChIKey/SMILES 출처, CO2 표준상태, 표 검토 등급을 추가했다. 실험 측정값의 계산 서명은 SHACL 규칙으로 거부한다.
- 추출 레코드에 선택적 계산 서명 필드를 추가하고, 프롬프트에 계산 방법 절의 원문만 복사하도록 한 문장을 추가했다. 재추출/LLM 호출은 하지 않았다.
- `pair_candidates.py`가 MeCN 안에서 같은 논문·같은 compound key의 전위/결합값 88개를 후보로 작성했다: m005 1, m007 25, m025 45, m043 6, m044 5, m061 6. 조건 key 일치 여부와 기준전극은 표에 남겼고 판정 열은 비웠다.

## 검증

| 명령 | 결과 |
|---|---|
| `python3 xlsx_status.py` | 38행, DOI 중복 0 |
| `python3 pair_candidates.py` | 88 후보행, 6개 논문 |
| `.../.venv/bin/python tests/test_onto.py` | 11 PASS |
| `python3 phase_4b_extend/tests/test_4b.py` | 2 PASS |
| `cd phase_4_extract && uv run --frozen pytest -q` | 74 passed |

88행 분포: m005 1, m007 25, m025 45, m043 6, m044 5, m061 6; 같은 condition key는 14행이다. flags는 `diff_condition_key` 74, `ref_not_fc` 31, `basis_suspect` 8이다.

## ponytail

- CSV 생성은 표준 라이브러리만 사용하며, 코드의 `# ponytail:` 주석이 이 선택을 표시한다.

## 사람이 할 일

1. `xlsx_status.csv`의 needs_judgment 10건과 Crossref/OpenAlex 원문을 독립 검토한다.
2. `pair_review.csv`의 화합물·조건 귀속, 단위, 표준상태를 `pair_review_GUIDE.md`에 따라 판정한다.
3. 승인된 쌍만 다음 Phase의 `reviewed` 학습/보정 데이터로 승격한다.
