# Codex 작업: Phase 4b 중 자동화 가능한 부분

기준 문서: `/home/hgpark/whlee/hgpark/quinone/PLAN.md` 3절(Phase 4b). 먼저 읽어라.
작업 위치: `Q=/home/hgpark/whlee/hgpark/ontology/quinone`. 새 파일은 `$Q/phase_4b_extend/` 아래에 둔다.
스킬: `/home/hgpark/whlee/hgpark/quinone/.claude/skills/`의 ponytail(full), tdd-workflow, verification-loop를 읽고 따른다.

## 확정된 기본값 (사용자가 "진행해"라고 해서 계획의 기본값을 쓴다)
- 목표 조건: 용매 Acetonitrile, 기준 전극 FcFcPlus, CO2 표준상태 1 atm(논문이 다르게 쓰면 그대로 기록하고 변환하지 않는다).
  근거: records_final에서 MeCN/Fc 전위 36, 결합 24로 가장 많다. 단 같은 논문 안에서도 조건 key가 달라 지금은 쌍이 1개뿐이다.
- 파이썬: 스키마 시험은 `/home/hgpark/whlee/hgpark/mlp-icl-llmsr/.venv/bin/python tests/test_onto.py`(phase_2_schema에서, 현재 10 PASS), 추출기는 `cd $Q/phase_4_extract && uv run --frozen pytest -q`(현재 72 passed). RDKit은 `/home/hgpark/Downloads/prog/miniforge3/envs/gpu4pyscf/bin/python`에 있다.
- 엑셀: `/home/hgpark/whlee/hgpark/quinone/quinone_CO2_simulation_papers_2020-2026.xlsx` (openpyxl 없음, zipfile+xml).

## 할 일 (이 순서, 각 항목마다 실패하는 시험을 먼저 쓴다)

1. **38편 상태표** `phase_4b_extend/xlsx_status.py` → `xlsx_status.csv`
   - 열: doi, xlsx_tier(A/B), title, status, source, quote, page_or_locator
   - status ∈ {matched, added_on_topic, borderline, out_of_scope, unavailable, needs_judgment}
   - master.json에 있으면 matched. `data/labeled_all.json`에 라벨이 있으면 그 라벨을 매핑해서 재사용하고 source에 그 파일명과 이유를 적는다.
   - 나머지는 Crossref/OpenAlex 초록(공개 API 읽기만)을 가져와 `data/abstracts_4b/<doi>.json`에 원문 그대로 저장한다. 판정은 하지 말고 needs_judgment로 둔다(판정은 별도 독립 검토자 몫).
   - 시험: 38행, DOI 중복 0, 엑셀 DOI 집합과 일치, 각 행의 status가 정확히 하나.

2. **스키마 보강** `phase_2_schema/schema/quinone.ttl`과 shapes
   - 추가: `qn:functional, qn:basisSet, qn:solvationModel, qn:dispersion, qn:code`(Measurement, 문자열), `qn:derivedFrom`(Measurement→Measurement), `qn:locator`(Evidence, 문자열), `qn:inchikey, qn:smilesSource`(Compound), `qn:co2StandardState`(Condition), `qn:simReviewTier`(Paper).
   - 기존 관례대로 ko/en label과 comment를 단다(시험 `test_every_term_has_ko_en_label_and_comment`).
   - SHACL 규칙 1개: 방법 서명 5개 속성은 `qn:basis`가 Computation인 Measurement에만 허용.
   - 시험: 양성 예시 1개와 음성 예시 2개(Experiment에 functional, Computation에 서명 누락은 `NotReported`이면 통과). 기존 10개 유지.

3. **추출기 필드** `phase_4_extract/src/qextract`
   - 출력 스키마에 방법 서명 5개 필드를 선택 항목으로 추가하고, 기존 인용 검사를 그대로 적용한다. 프롬프트에는 "계산 방법 절에서만, 원문에 있는 그대로, 없으면 NotReported"라는 문장 하나만 더한다.
   - 재추출은 하지 마라(LLM 서버 호출 금지). 단위 시험만: 서명 필드가 인용에 없으면 거절, Experiment 값에 서명이 있으면 거절.
   - 기존 72개 유지.

4. **쌍 검수표** `phase_4b_extend/pair_candidates.py` → `pair_review.csv`
   - records_final에서 목표 조건(Acetonitrile; 기준 전극은 열로 남긴다) 안의 전위(ReductionPotential/HalfWavePotential)와 결합(Log10BindingConstant/BindingConstant/BindingEnergy) 값을 **같은 논문, 같은 compound key**로 짝짓는다(조건 key가 달라도 용매가 같으면 후보).
   - 열: paper_id, compound, potential_property, potential_value, unit, ref_electrode, redox_couple, potential_quote, potential_page, binding_property, binding_value, binding_unit, binding_quote, binding_page, basis, method, same_condition_key(bool), reviewer_verdict(빈칸), reviewer_note(빈칸)
   - 사람이 채울 표이므로 판정 열은 비운다. `pair_review_GUIDE.md`에 판정 기준(원문 대조, 화합물·조건 귀속, 단위, 표준상태)을 10줄 이내로 쓴다.
   - 시험: 합성 레코드 2개로 짝짓기 규칙 확인.

5. **보고** `phase_4b_extend/REPORT.md`: 한 일, 시험 결과(명령과 출력 숫자), 목표 조건 쌍 후보 수(논문별), needs_judgment 목록, `ponytail:` 표시 목록, 사람이 할 일.

## 규칙
- git 명령(commit, checkout, reset, stash, clean 등) 금지. 현재 상태 스냅샷은 `refs/quinone/before-4b`에 있다.
- `records_final/`, `records*/`, `phase_3_corpus/` 원본, PDF는 수정 금지(읽기만).
- 새 의존성 설치 금지. LLM 서버 호출 금지.
- 기존 시험이 깨지면 고칠 이유가 이 문서에 있을 때만 시험을 고친다.
- 끝나면 마지막에 한 줄로 `4B-DONE` 을 출력한다.
