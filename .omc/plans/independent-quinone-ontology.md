# 계획: 기존 quinone 온톨로지 확장, KG+LLM 역설계와 보정된 계산 선별

작성 2026-10-30. 계획만 담는다. 코드, 설치, git은 범위 밖이다.
대상 저장소: `/home/hgpark/whlee/hgpark/ontology/quinone/` (이하 `Q/`). 새 저장소는 만들지 않는다.

## 0. 현재 상태 (확인한 사실)

- Phase 1-4 완료(조건부), Phase 5 변환·검증과 Phase 6 문서는 빈 폴더, `final/`도 비어 있다.
- 스키마 `Q/phase_2_schema/schema/quinone.ttl`: Paper, Compound, Condition, Result, Measurement, Observation, Evidence. `qn:basis`(실험/계산), `qn:method`(CV, CPE, DFT, MD 등 개념), `qn:referenceElectrode`(Condition), `qn:smiles`(Compound). SHACL 7개, CQ 11개, 검사 루프 `ontology/al_alloy/common/check.py`.
- 추출 `Q/phase_4_extract/records_final/`: 전문 55편, 값 335, 관찰 96, 화합물 186, 전위 161개 전부 기준 전극 기재. **화합물 186개 중 SMILES 0개.** DFT 값에도 범함수, 기저, 용매화 모형 필드가 없다(`method=DFT`뿐).
- 독립 2차 검토: 확정 오류 10%, 확인 불가 12/40. `human_review_40.csv`는 미완. 모든 값이 `machine_extracted`.
- xlsx 38편 대 `phase_3_corpus/master.json`(80편): **24편 있음(A 23/25, B 1/13), 14편 없음.**
  - 없는 A 2편: Morozova 2026 고처리량 스크리닝(10.1021/acs.jpclett.6c01786, 기준선과 대량 계산값의 핵심), Ho 2024 pillar[5]arene(10.1002/slct.202401490).
  - 없는 B 12편: 비피리디늄, 하이드로퀴논 클라스레이트 3편, 폴리이미드 COF, sp2 질소 루이스 염기, 페나진, PCET 분류기, 퀴논 탄소섬유, 아이소인디고, 벤조티아디아졸, Hazra 2026 프리프린트.
  - m055(Taylor 2026, 맞교환 기준 논문)는 xlsx A인데 추출 0개(인용 재작성으로 전부 거절). 수동 입력이 필요하다.
- 참고 패턴 `/home/hgpark/ontology-mlip`: SPARQL로 읽은 근거만 LLM에 전달(벡터 검색 없음), 편집마다 KG 경로 인용, 근거 부족 시 `insufficient_evidence`, 일부가 아닌 전체 KG로 재검사, 차별성 심사와 `priority_candidates` 분리, RDF 환류 후 재파싱 검증, "KG에 없음 ≠ 신규".

## 1. 원칙, 결정 요인, 선택지

원칙 (ponytail, mle-workflow, eval-harness, verification-loop)
1. 재사용 먼저: 스키마, SHACL, CQ, `check.py`, `qextract`(추출기, 검사기, `llm.py`), 시험 실행 방식을 그대로 쓴다. 새 모듈은 새 phase당 1개, 클래스 계층 없음.
2. 사람 검수 전 값(`machine_extracted`)은 조회 문맥에는 쓰되 **보정 기준값과 성공 판정에는 `reviewed`만** 쓴다.
3. 계산 도구는 논문 DFT값과 실험값으로 보정을 통과하기 전에는 순위에 쓰지 않는다.
4. 합격 수치는 실행 전에 이 문서에 고정한다. 바꾸면 이유를 DONE.md에 남긴다.
5. 단순화는 `# ponytail: <한계>, <업그레이드 조건>`으로 표시하고 phase 종료 때 `ponytail-debt`로 대장을 만든다.

결정 요인: (1) 검수된 수치 쌍(E1/2, 결합 세기)이 적다, (2) DFT 비용, (3) 라디칼 음이온과 이음이온에서의 xTB/MLIP 신뢰도.

선택지
- A (채택): 기존 `qn:` 스키마에 속성 몇 개만 추가하고 phase 7-9를 덧붙인다. 장점: CQ, SHACL, 검사 루프 재사용. 단점: 기존 시험 72개와 SHACL을 깨지 않게 순서를 지켜야 한다.
- B: ontology-mlip처럼 별도 설계 TTL 층(`design.ttl`)만 만들고 기존 KG는 읽기 전용으로 둔다. 장점: 기존 결과 불변. 단점: 방법 서명이 없으면 보정을 못 하므로 결국 스키마 확장이 필요하다.
- 절충: 방법 서명은 기존 스키마에(A), 후보와 계산 결과는 별도 파일 `phase_8_design/design.ttl`에(B) 둔다. 문헌 KG와 설계 KG를 파일 단위로 분리하면 오염 검사가 쉽다.
- 기각: 벡터 DB, 새 KG 엔진, 새 추출기. 근거 없는 추가 구성이다.

## 2. 새 phase 배치

| Phase | 폴더 | 내용 |
|---|---|---|
| 4b | `phase_4b_extend/` | 빠진 14편 추가, 방법 서명과 SMILES 보강, m055 수동 입력, 사람 검수 완료 |
| 5 | `phase_5_build/` (기존 계획) | JSON 기록을 RDF로 변환, SHACL, CQ. 새 필드 포함 |
| 7 | `phase_7_calibrate/` | 맞교환 재현, xTB/MLIP/DFT 보정 관문 |
| 8 | `phase_8_design/` | KG 조회, LLM SMILES 편집, 전체 KG 검증, 차별성 심사, RDF 환류 |
| 9 | `phase_9_screen/` | 보정된 계층식 선별, 기준선 비교, 2회차 |

Phase 6 문서는 기존 정의대로 마지막에 갱신한다. 각 폴더에 `DONE.md`가 있어야 다음 phase를 시작한다(기존 규칙).

## 3. Phase 4b. 코퍼스와 추출 보강

1. 빠진 14편: `master.json`에 같은 형식으로 추가한다. 라벨은 기존 규칙(대상/경계선/비대상)으로 다시 판정하고, xlsx 등급은 새 속성 `qn:simReviewTier`(A/B)로 따로 둔다. Morozova 2026은 SI 데이터 표(31,000개, 후보 681개)를 원본 그대로 `data/morozova2026/`에 해시와 함께 보관한다. 이것은 문헌 Result로 하나씩 옮기지 않고 `qn:ScreeningDataset` 1개 노드로만 연결한다(ontology-mlip의 `ScreeningRecord` 구분과 같다).
2. 방법 서명: Measurement에 문자열 속성 5개 추가. `qn:functional`, `qn:basisSet`(기존 `qn:basis`와 이름 충돌 방지), `qn:solvationModel`, `qn:dispersion`, `qn:code`. 값이 글에 없으면 `NotReported`. `basis=Computation`일 때만 허용하는 SHACL 규칙 1개 추가.
   - `# ponytail: 개념 목록 대신 문자열, 서로 다른 값이 20개를 넘으면 SKOS 목록으로`
   - 추출은 `qextract` 프롬프트에 필드 5개를 추가하고, 인용 검사(값이 인용에 있어야 함)를 그대로 적용한다. 논문의 계산 방법 절(보통 한 곳)을 Evidence로 걸고 그 논문의 모든 계산값에 같은 서명을 붙인다.
3. 기준 전극 변환: 원값은 그대로 두고, Fc+/Fc 환산값은 `qn:derivedFrom`으로 원값을 가리키는 새 Measurement로 만든다. 환산 상수는 논문이 준 값만 쓰고, 없으면 환산하지 않는다.
4. SMILES: 186개 전부가 아니라 **E1/2나 결합 세기 값이 있는 분자 먼저**. LLM이 이름과 인용에서 SMILES를 제안하고, RDKit 정규화와 분자식 대조 후 사람이 확인한다. `qn:smilesSource`(paper/llm_checked/human)와 `qn:inchikey` 추가.
5. m055 수동 입력과 `human_review_40.csv` 완료. 검수 결과는 `review_status=reviewed|rejected`로 기록한다.
6. 수치 쌍 추가 추출 우선순위: Bui 2022 m015, Zito 2022 m005, Alherz, Schimanofsky, Massen-Hane m077, Taylor m055, Zhang 2026 m062, Wang 2026 PAQ, Abdinejad m029. 그림 속 값은 사람이 읽고 `locator=Figure n`으로 표시한다.

검사 (`phase_4b_extend/tests/`, 기존 시험 실행 방식)
- xlsx 38개 DOI가 모두 master에 있음, DOI 중복 0.
- 계산값 중 방법 서명 5필드가 비어 있는 것 0(`NotReported`는 허용), 실험값에 서명 필드가 붙은 것 0.
- SMILES가 있는 화합물은 RDKit 파싱 성공, 이름과 분자식 대조 일치.
- 기존 시험 72개 통과(회귀).
수용: 검수된(`reviewed`) E1/2와 결합 세기 쌍이 **같은 조건, 같은 방법 서명으로 30개 이상, 3편 이상**. 미달이면 phase 7을 멈추고 사람 결정.

## 4. Phase 5. 변환과 검증 (기존 계획에 필드만 추가)

- 기존 정의대로 JSON을 RDF로 변환하고 `check.py`로 SHACL, OWL-RL, CQ를 돈다. 새 속성 6개와 규칙 1개만 추가된다.
- 새 CQ 3개: `cqD1` 같은 조건·같은 방법 서명의 (E1/2, ΔG_bind 또는 log K) 쌍, `cqD2` 골격·치환기 위치별 쌍, `cqD3` 산소 안정성 관찰과 O2 관련 전위. 기존 CQ08, CQ20, CQ22는 그대로 재사용한다.
- 검사: 삼중항 재파싱, SHACL 위반 0, CQ 14개 모두 1행 이상, 두 번 빌드한 그래프 동형.

## 5. Phase 7. 보정 관문 (설계보다 먼저)

목표: 계산 계층이 논문값을 재현하는지 먼저 증명한다.

1. 맞교환 재현: `cqD1` 결과로 논문별 `ΔG_bind = a·E1/2 + b`를 적합하고 Bui 2022, Zito 2022, Taylor 2026의 보고 경향과 비교한다.
2. 계층별 보정. 기준 분자는 `reviewed`이면서 SMILES가 있는 것만. 논문(DOI) 단위로 보정/평가 분할.
   - T1 GFN2-xTB(ALPB 용매) + CREST 형태 탐색. Zito 2022 절차.
   - T1' MLIP: AIMNet2, UMA(OMol25). 전하와 스핀을 학습한 모델만 음이온 에너지에 쓴다. MACE-OFF는 중성 위주라 구조 전처리에만 쓴다.
   - T2 DFT: 문헌 프로토콜 하나를 고정(기본 Bui 2022 B3LYP/6-311++G(d,p)/SMD, 대안 Massen-Hane 2025 ωB97M-V/def2-TZVPD/SMD).
   - 비교 대상은 두 종류를 따로 본다: (a) **같은 방법 서명의 논문 DFT값**(계산 재현성), (b) 실험값(물리 정확도).
3. 각 계층의 E1/2와 ΔG_bind 선형 보정식, MAE, Spearman을 `design.ttl`에 `qn:Calibration` 노드로 저장한다.

합격 수치 (실행 전 고정, 기본값)

| 항목 | 기준 |
|---|---|
| 맞교환 재현 | 세 논문 각각 기울기 부호 일치, 기울기 ±30% 이내 |
| T1/T1' 대 논문 DFT | leave-one-paper-out MAE E1/2 ≤ 0.15 V, ΔG_bind ≤ 3 kcal/mol, Spearman ≥ 0.7 |
| T2 대 논문 DFT(같은 서명) | MAE E1/2 ≤ 0.05 V, ΔG_bind ≤ 1 kcal/mol (재현성) |
| T2 대 실험 | MAE E1/2 ≤ 0.10 V, log K ≤ 1.5 |

불합격 계층은 phase 9 순위에서 빠진다. 전 계층 불합격이면 phase 8은 "가설 목록"까지만 만든다.
검사: 합성 직선 자료에서 보정식이 기울기를 복원하는 시험 1개, 벤조퀴논과 안트라퀴논 기준 분자 2개의 xTB 실행 시험(`slow` 표식).

## 6. Phase 8. KG+LLM 역설계 (ontology-mlip 패턴)

1. 조회: `cqD1-3`과 기존 CQ로 부모 분자, 쌍 값, 치환기 효과, 산소 관찰을 표로 만든다. 레코드 IRI를 짧은 ID로 줄이고 `kg_context.json`에 원 IRI를 보존한다. 평가용 hold-out 분자는 문맥에서 뺀다.
2. 생성: LLM은 **부모 SMILES의 편집**(치환기 추가·교체·위치 이동, 고리 헤테로원자 치환, 고리 확장)을 JSON으로 낸다. 필드: `parent_id, edits[], smiles, cited_ids[], hypothesis(E1/2 방향, ΔG 방향, 근거), known_elements, unresolved`. 클라이언트는 `qextract/llm.py`(로컬 llama-server)를 재사용하고 모델은 바꿀 수 있게 URL만 받는다.
3. 근거 부족이면 개수를 채우지 않고 `insufficient_evidence`로 끝낸다. 인용 ID가 KG에 없거나 인용 내용과 가설 방향이 모순이면 거절한다.
4. 전체 KG 재검사: 프롬프트에 넣은 일부가 아니라 전체 KG와 Morozova 데이터셋에서 InChIKey, 같은 골격+같은 치환기 집합(위치 무관)을 찾는다. 일치는 선행으로 기록한다.
5. 차별성 심사: 최근접 선행(골격, 치환기, Tanimoto), 이미 알려진 요소, 바뀐 점, 시험할 가설, 미확정을 분리한다. `candidates.json`(전체 가설)과 `priority_candidates.json`(심사 통과, 비어도 됨)을 나눈다. "등록 범위 내 미중복"으로만 표기하고 세계 신규성은 주장하지 않는다.
6. RDF 환류: `qn:Candidate`, `qn:DesignEdit`(부모, 편집, 인용), `qn:NoveltyReview`, `qn:ScreeningRun`을 `design.ttl`에 저장하고 재파싱해 JOIN을 확인한다. 계산값은 `basis=Computation`, `qn:calibratedWith`로 표시하고 문헌 Result로 승격하지 않는다. 다음 회차 조회는 이전 후보의 실패 이유도 읽는다.

T0 화학 검사: RDKit 파싱, 원자가, 중성, 퀴논 C=O 2개(1,2- 또는 1,4-) 패턴, 중원자 ≤ 40, 금속 없음(기본).
검사: 저장한 모의 LLM 응답으로 (a) 가짜 인용, (b) 빈 SMILES, (c) 부모와 같은 SMILES, (d) 비퀴논을 거절하고 (e) `insufficient_evidence`를 정상 종료로 처리. 환류 후 문헌 KG 삼중항 수 불변.

## 7. Phase 9. 계층식 선별과 평가

목표: E1/2(V vs Fc+/Fc, 비양성자성 용매)를 덜 음으로, ΔG_bind를 더 음으로. 둘은 맞교환 관계다.

- 맞교환선: phase 7 적합선, 잔차 표준편차 σ_line.
- 후보 성공: 보정된 예측이 선보다 **max(2σ_line, 해당 계층 보정 MAE_ΔG)** 이상 아래, 그리고 E1/2가 O2/O2•− 전위보다 양이거나 Massen-Hane 2025 기준으로 O2 반응이 불리. O2 기준값은 phase 4b에서 인용과 함께 레코드로 고정한다.
- 흐름: T0 전부 → T1/T1' 50개 → 파레토 상위 10개 T2 DFT → 성공 판정.

기준선 (같은 계산 예산)
- B0 열거: KG 골격(BQ, NQ, AQ, PQ)에 KG 치환기 목록을 무작위 결합.
- B1 KG 없는 LLM: 같은 모델과 목표, 조회 표 없이.
- B2 Morozova 2026: 후보 681개를 같은 보정 계층으로 재평가해 파레토 전선 비교.
- B3 규칙: 해밋 상수 선형 규칙(Zhang 2026 치환기 효과).

합격 수치

| 항목 | 기준 |
|---|---|
| 생성 품질 | T0 통과 ≥ 95%, 고유 ≥ 90%, KG·Morozova 미중복 ≥ 80%, 인용 유효 100% |
| 역설계 성과 | 성공률이 B0의 2배 이상, 파레토 초부피가 B0, B1보다 큼 |
| B2 대비 | 보고만 한다(목표 아님). 우리 T2 성공 후보가 Morozova 전선 밖에 있는지 |

검사: 지표 함수(성공 판정, 초부피) 손계산 시험 1개. 회차별 지표 표를 `phase_9_screen/DONE.md`에 기록.

## 8. 작업 순서와 수용 기준

1. Phase 4b. 수용: 3절 검사 통과, 검수된 쌍 ≥ 30개(3편 이상), 기존 시험 72개 통과.
2. Phase 5. 수용: SHACL 위반 0, CQ 14개 통과, 멱등.
3. Phase 7. 수용: 맞교환 재현과 한 계층 이상 보정 합격. 아니면 멈추고 사람 결정.
4. Phase 8 1회차. 수용: 거절 규칙 시험 통과, 환류 JOIN, 문헌 KG 불변.
5. Phase 9와 2회차, Phase 6 문서 갱신. 수용: 지표 표, B0/B1 비교, `ponytail-debt` 대장, 독립 검토자(verifier)의 게이트 통과.

## 9. 단계별 최소 검사 요약

| Phase | 검사 1개 |
|---|---|
| 4b | xlsx DOI 38/38, 계산값 방법 서명 누락 0, 기존 72개 회귀 |
| 5 | `check.py`: SHACL 0, CQ 14개 행 존재, 그래프 동형 |
| 7 | 합성 직선 보정 복원, 기준 분자 2개 xTB(`slow`) |
| 8 | 모의 응답 거절 5종, 환류 후 문헌 삼중항 불변 |
| 9 | 성공 판정과 초부피 손계산 일치 |

## 10. 위험

| 위험 | 대응 |
|---|---|
| 검수 값 부족(38편, 쌍 희소, 오류율 10%) | `reviewed`만 보정에 사용, 쌍 < 30이면 중단 |
| B 경계 12편 추가로 비퀴논 혼입 | `simReviewTier=B`는 조회 문맥만, 보정·성공 판정 제외 |
| 원문 접근(Morozova SI, 프리프린트, Elsevier) | 없으면 레코드를 만들지 않고 `fulltext` 상태로 추적 |
| 방법·기준 전극 혼재 | 같은 방법 서명, 같은 조건 안에서만 선 적합 |
| 그림 속 값 | 사람 판독, `Figure` 위치 표시 |
| DFT 비용 | T2는 상위 10개, CO2 2분자 부가물은 필요할 때만 |
| MLIP의 라디칼 음이온·이음이온 오차, 열린 껍질 | 보정 관문 통과 전 사용 금지, 스핀 다중도 명시 |
| 연속 용매화 한계(염 농도, 이온쌍, 수소결합 첨가제: Liu 2020, Wang 2026) | 염·알코올 없는 비양성자성 조건으로 범위 한정 |
| 형태와 결합 부위 다수 | CREST 탐색, 최저 에너지 부가물만 비교 |
| LLM 인용 날조, 신규성 과장 | 기계 인용 검사, 전체 KG 재검사, 신규성 문구 제한 |
| 기존 시험·SHACL 회귀 | 스키마 변경 직후 기존 시험 전부 실행 |
| 합성 가능성·용해도 미평가 | 범위 밖으로 명시, SA 점수는 참고값 |

## 11. 열린 결정 (사람 확인 필요)

- [ ] `human_review_40.csv` 완료 담당과 기한. 보정은 이것 없이 시작하지 않는다.
- [ ] 빠진 B 경계 12편을 코퍼스에 넣을지(기본: 넣되 tier=B 문맥 전용) 아니면 A 2편만 넣을지.
- [ ] 문헌 KG와 설계 KG 분리(기본: `design.ttl` 별도 파일).
- [ ] 목표 조건 하나(용매 MeCN/DMF/DMSO, 전해질). 기본: 검수 쌍이 가장 많은 조건.
- [ ] 금속착물 퀴논 리간드(Pizarro 계열)와 고분자를 생성 대상에서 뺄지(기본: 뺌).
- [ ] T2 DFT 프로토콜(Bui B3LYP/SMD 또는 Massen-Hane ωB97M-V/SMD), DFT 코드와 계산 자원.
- [ ] RDKit, xTB/CREST, AIMNet2, UMA 설치 위치(기존 `mlp-icl-llmsr/.venv` 재사용 여부)와 GPU.
- [ ] 설계 LLM: 로컬 Qwen(llama-server, 추출과 같은 서버) 또는 Claude. 호출 예산과 승인 방식.
- [ ] 5, 7절 합격 수치와 O2 내성 기준값 최종 확인.
- [ ] Morozova 2026 SI 데이터의 사용 조건.
