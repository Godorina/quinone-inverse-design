# quinone ontology

목적: 전기화학적 CO2 포집용 quinone 설계. `al_alloy`와 같은 틀(schema, cq, shapes, convert, tests, build)과 `common/check.py`를 쓴다.

| Phase | 폴더 | 상태 |
|---|---|---|
| 1 범위와 질문 | phase_1_scope/ | 완료(조건부): 질문 11개 확정, CQ19·CQ20은 Phase 3에서 재확인 |
| 2 스키마와 어휘 | phase_2_schema/ | 완료(조건부): 클래스 7, 개념 92, 질문 11개 질의 통과. 이월 항목은 DONE.md |
| 3 논문 전문 확보 | phase_3_corpus/ | 완료: 대상 67편(전문 55), PDF 70편 백업, 텍스트 변환, 마스터 목록 |
| 4 추출 | phase_4_extract/ | 다음 |
| 5 변환과 검증 | phase_5_build/ | 대기 |
| 6 개념도와 문서 | phase_6_docs/ | 대기 |
| 최종 | final/ | 통과한 결과만 승격 |

규칙: 각 phase 폴더에 `DONE.md`가 있어야 다음 phase를 시작한다.

## data/
- `on_topic_final.json`: 대상 논문 64편 (초록 판정)
- `borderline.json`: 경계선 29편
- `labeled_all.json`: 후보 452편 전체와 라벨, 확신도, 이유
- `collect/`: 수집 스크립트 (OpenAlex, Crossref, Europe PMC)
