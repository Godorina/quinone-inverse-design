# 퀴논 CO2 계산문헌 온톨로지·역설계 계획

## 목표와 경계

- 목표: `quinone_CO2_simulation_papers_2020-2026.xlsx`의 38편을 기존 퀴논 RDF/KG에 근거·조건과 함께 편입하고, 그 KG를 근거 입력으로 쓰는 퀴논 분자 역설계와 다단계 스크리닝 경로를 완성한다.
- 범위: 기존 `/home/hgpark/whlee/hgpark/ontology/quinone/`을 확장한다. 새 병렬 온톨로지, 새 추출 프레임워크, 새 ML 플랫폼은 만들지 않는다.
- 비목표: 세계 최초성, 합성 가능성, O2 내성 또는 포집 성능을 LLM/MLIP 예측만으로 확정하지 않는다. DFT·실험은 후속 검증이며 이 계획의 산출물은 후보와 재현 가능한 근거 사슬이다.
- 선행 조건: Phase 4는 조건부 통과다. 독립 검토에서 값-화합물-조건 대응 오류가 남았으므로, `machine_extracted`를 설계 정답으로 쓰지 않고 사람 검수된 레코드만 학습/승격에 사용한다.

## 확인한 현재 상태

| 기존 단계 | 재사용할 자산 | 이 계획에서의 연결 |
|---|---|---|
| Phase 1 | `phase_1_scope/cq.md`, CQ 11개 | 새 계산조건·역설계 CQ를 기존 질문과 충돌 없이 추가 |
| Phase 2 | `phase_2_schema/schema/quinone.ttl`, `shapes/`, `cq/` | 기존 `Result–Condition–Evidence` 계약을 확장 |
| Phase 3 | `phase_3_corpus/master.json`, PDF/text 코퍼스 | XLSX 38 DOI의 서지 정합 및 전문 확보 상태의 기준 |
| Phase 4 | `phase_4_extract/src/qextract/`, `records_final/`, 테스트 72개 | 추출기와 인용/쪽 검사기를 계산 메타데이터에 재사용 |
| Phase 5~6 | 아직 미착수 | RDF 변환·전체 KG 검증 후 역설계/스크리닝과 문서화 |

참고 근거: 기존 스키마는 값마다 하나의 조건과 최소 하나의 근거를 요구한다(`phase_2_schema/schema/quinone.ttl:34-79`). Phase 4는 전문 55편에서 값 335개를 추출했지만 독립 2차 검토에서 10% 확정 오류와 확인 불가 항목을 보고했다(`phase_4_extract/DONE.md`).

## XLSX–master DOI 대조 결과

ZIP/XML로 XLSX를 읽어 DOI를 정규화(doi.org 접두사·대소문자·끝 문장부호 제거)해 `master.json`과 비교했다. XLSX 38편 중 24편 일치, 아래 14편은 누락이다. `B 경계`는 자동으로 대상화하지 않는다.

| 연도/분류 | DOI | 제목 | 편입 결정 |
|---|---|---|---|
| 2020 B 경계 | 10.1002/celc.201901884 | Experimental, Simulation, and Computational Study of the Interaction of Reduced Forms of N-Methyl-4,4'-Bipyridinium with CO2 | 경계 재판정 |
| 2021 B 경계 | 10.1021/acs.cgd.1c00271 | Insights into Host–Guest Binding in Hydroquinone Clathrates | 경계 재판정 |
| 2021 B 경계 | 10.1021/acs.chemmater.0c03218 | Polyimide COFs for CO2 Capture and Sodium-Ion Batteries | 경계 재판정 |
| 2023 B 경계 | 10.1016/j.ces.2023.118673 | PCET-controlled CO2 capture sorbent properties | 경계 재판정 |
| 2023 B 경계 | 10.1038/s41560-023-01347-z | Phenazine-based ECC cell | 경계 재판정 |
| 2024 A 핵심 | 10.1002/slct.202401490 | Functional groups on pillar[5]arenes | 대상 적합성 재판정 |
| 2024 B 경계 | 10.1002/anie.202401707 | Oxygenated carbon nanofiber CO2 capture | 경계 재판정 |
| 2024 B 경계 | 10.1021/acs.jpclett.4c01188 | Hydroquinone-clathrate methane replacement | 경계 재판정 |
| 2024 B 경계 | 10.1038/s41467-024-45410-z | Redox-tunable isoindigos | 경계 재판정 |
| 2025 B 경계 | 10.1002/cssc.202501724 | Benzothiadiazole electrochemical CO2 capture | 경계 재판정 |
| 2025 B 경계 | 10.1021/acs.energyfuels.5c01091 | Hydroquinone-clathrate simulation | 경계 재판정 |
| 2022 B 경계 | 10.1038/s41560-022-01137-z | Redox-tunable Lewis bases | 경계 재판정 |
| 2026 A 핵심 | 10.1021/acs.jpclett.6c01786 | High-throughput computational screening of quinones | 대상 편입 우선 |
| 2026 B 경계 | 10.26434/chemrxiv.15010519/v1 | Oxygen-tolerant electrochemical DAC | 경계 재판정 |

## 공통 데이터·검증 계약

- 식별자: 논문은 정규화 DOI, 화합물은 표준화 SMILES와 InChIKey를 함께 보관한다. 구조가 모호하면 둘 다 비워 두고 `NotReported`/검수 사유를 남긴다.
- 레코드 단위: `Paper → Result → Compound + Condition + Evidence`를 유지한다. 수치 하나는 하나의 화합물, 하나의 조건, 하나 이상의 원문 인용에 연결한다.
- 출처 계약: 모든 학습·랭킹 입력은 `review_status=reviewed`, 원문 인용문, PDF 쪽(초록 전용은 `Abstract`)과 DOI를 가져야 한다. 누락은 0/추정값으로 채우지 않는다.
- 비교 계약: E1/2, ΔG_CO2, log K는 같은 골격·전하/환원상태·용매·전해질·온도·기준전극/변환법이 명시적으로 호환될 때만 짝짓는다. 호환 불명은 비교·학습에서 제외한다.
- 분할 계약: 분자 중복/동일 InChIKey는 한 split에만 두고, scaffold-group 분할과 시간 보류(2026)를 모두 보고한다. 문헌별 무작위 split만으로 성능을 주장하지 않는다.
- 단계별 공통 게이트: 구현 전에 데이터 계약·기준선·합격 기준을 테스트로 선언하고, 최소 하나의 실행 검증을 통과해야 다음 단계로 넘어간다. 변경은 기존 추출기/검사기/테스트를 우선 재사용하며 새 추상화·의존성은 추가하지 않는다.

## 단계 0 — 누락 논문 판정과 코퍼스 동기화

1. 위 14 DOI의 Crossref 서지, 전문/초록 접근 상태, 퀴논 구조와 전기화학 CO2 포집의 직접성을 기존 Phase 1 기준으로 판정한다.
2. 대상이면 `master.json`과 코퍼스에 DOI·제목·연도·전문 상태·판정 인용문을 추가하고, 경계/비대상이면 이유와 인용문을 보존한다. 원문 미확보는 `abstract_only`로 남긴다.
3. 24개 기존 일치 DOI도 제목/연도/DOI 중복을 점검한다. 38개 모두를 `matched`, `added_on_topic`, `borderline`, `out_of_scope`, `unavailable` 중 하나로 끝낸다.

산출물: Phase 3 마스터/판정 레코드의 38 DOI 교차대조표와 갱신된 DONE 증거.  
실행 검증 1개: ZIP/XML DOI 목록과 갱신 `master.json` DOI의 집합 차가 0이고, 38행 각각에 위 다섯 상태 중 정확히 하나가 있는지 검사한다.  
합격: 38/38 상태화, DOI 중복 0, 새 대상/경계 판정마다 원문 또는 초록의 정확 인용 1개 이상.

## 단계 1 — 계산조건 스키마와 추출 보강

기존 속성을 재사용하고, 정말 필요한 항목만 다음처럼 추가한다. 각 새 값은 `NotReported` 허용, 단위/근거/조건/검수 상태를 상속한다.

| 영역 | 추가/정규화 필드 | 연결 대상·규칙 |
|---|---|---|
| 분자 | `smiles`, `inchiKey`, 구조 표준화 상태 | `Compound`; InChIKey는 SMILES에서 검증 가능할 때만 |
| 계산법 | 범함수, 기저, 분산보정, 용매모델, 계산 코드, 열역학 보정 | `Measurement`의 계산 `method` 세부값; 인용 필수 |
| 전기화학 | 기준전극, 환원상태/산화환원쌍, E1/2, 변환 기준 | `Condition`과 전위 `Measurement`; 서로 다른 기준전극은 직접 비교 금지 |
| 포집 열역학 | ΔG_CO2, log K, 온도, 표준상태, CO2 분압/농도 | `Measurement + Condition`; ΔG와 log K의 유도 관계면 원값·유도법을 구분 |
| 내성 | O2 존재/농도, 관찰 기간, O2 내성 결과 | `Condition + Observation`; 산소 언급이 없으면 내성 없음으로 해석 금지 |

새 CQ: (a) 계산법·용매모델별 E1/2/ΔG_CO2 조회, (b) 같은 조건에서 E1/2–ΔG_CO2 쌍 조회, (c) O2 조건이 명시된 후보만 조회, (d) SMILES/InChIKey와 근거를 함께 반환한다.

산출물: `quinone.ttl`/vocab/SHACL/CQ와 Phase 4 추출 규칙·회귀표본.  
실행 검증 1개: 각 새 필드의 누락·단위·기준전극·계산근거 오류를 넣은 음성 사례가 SHACL/추출 검사에서 각각 거부되고, 양성 예시는 새 CQ 네 개 모두에 행을 낸다.  
합격: 기존 11 CQ와 기존 Phase 2 테스트가 유지되고, 새 CQ 4개·음성 규칙이 모두 통과한다.

## 단계 2 — 사람 검수 뒤 Phase 5 RDF 빌드

1. Phase 4의 잔여 오류 유형(표 열 방향, 화합물/조건 귀속, 관찰 분류)을 층화한 40개 값·관찰 표본으로 독립 검수한다.
2. 오류는 추출 규칙/테스트로 먼저 재현하고 최소 수정 후 재추출한다. 원문이 불충분하면 삭제 또는 `insufficient_evidence`로 격리한다.
3. 검수 통과한 레코드만 RDF로 변환한다. `machine_extracted`, `reviewed`, `rejected`, `insufficient_evidence`를 보존해 하위 그래프가 상태를 숨길 수 없게 한다.
4. 전체 KG(기존 대상 67편, 새 DOI 판정, 새 계산 레코드, vocab, schema)를 한 번에 로드해 SHACL, OWL-RL, CQ, DOI/인용 dangling 검사를 수행하고, 직렬화 후 다시 로드해 같은 결과를 확인한다.

산출물: Phase 5의 단일 합성 KG, 검사 보고서, 사람이 검수한 학습용 스냅샷.  
실행 검증 1개: 합성 KG의 직렬화→재로드 뒤 트리플 수·CQ 결과·검수상태별 레코드 수가 동결 스냅샷과 동일하고 SHACL 위반 0이다.  
합격: 독립 표본 40개에서 확정 오류 0, 불확실 항목은 설계/학습 입력 0개, 전체 KG 검사 통과.

## 단계 3 — 역설계 계약과 기준선

### 설계 목표

- 주목적: 조건이 맞는 퀴논에서 O2 환원보다 양(덜 음)인 E1/2와 더 유리한 CO2 포집 ΔG_CO2/log K의 상충을 완화하는 후보를 제안한다.
- 제약: 근거가 있는 용매·전해질·온도·기준전극·환원상태 안에서만 비교한다. O2 내성은 명시적 O2 실험/계산 근거가 있을 때만 통과 제약으로 사용한다.
- 기준선 논문/세트: Bui 2022 (`10.1021/acs.jpcc.2c03752`, m015), Zito 2022 (`10.1021/acssuschemeng.2c03463`, m005), Taylor 2026 (`10.1002/cphc.202500472`, m055)의 검수된 동조건 E1/2–ΔG_CO2 쌍. 각 논문별, 합친 세트별, scaffold-holdout별로 별도 보고한다.

### 사전 선언 평가

| 항목 | 기준선 | 합격 수치 |
|---|---|---|
| 데이터 적격성 | 검수·동조건 쌍만 사용 | 세 기준 논문에서 적격 쌍 100%, 부적격 쌍 0% 학습 입력 |
| DFT 앵커 보정 | xTB, AIMNet2, MACE-OFF, UMA의 무보정 값 | 보정 검증세트 MAE: E1/2 ≤0.10 V, ΔG_CO2 ≤5 kJ/mol; 둘 중 하나 미달이면 후보 순위에 사용하지 않음 |
| 맞교환 재현 | 단순 선형 E1/2→ΔG_CO2 및 ΔG_CO2→E1/2 기준선 | 각 Bui/Zito/Taylor 보류세트에서 상관 부호 일치, 두 방향 MAE가 각 단순 기준선보다 10% 이상 낮음 |
| 일반화 | 무작위 분할만 보고하는 모델 | scaffold-holdout에서 위 MAE의 1.5배 이내, 시간 보류 Taylor에서도 상관 부호 유지 |
| Pareto 개선 | 검수된 기준 분자 중 동조건 Pareto 전선 | 후보의 예측 95% 구간이 전선의 한 점보다 E1/2는 ≥0.05 V 양, ΔG_CO2는 ≥5 kJ/mol 유리; 불확실성 겹침이면 `insufficient_evidence` |

모델 순서: 논문 DFT 라벨을 기준으로 먼저 xTB/MLIP(AIMNet2, MACE-OFF, UMA)의 에너지/구조 출력과의 편향을 보정한다. 이후에만 LLM이 구조 제약 안에서 후보를 제안하게 하며, 라벨 없는 물성은 생성하지 않는다.

산출물: 고정 데이터 스냅샷, 분할표, 단순 기준선 결과, 모델별 보정표, 사전 등록 평가 명세.  
실행 검증 1개: 동일 스냅샷·seed·split로 기준선/보정 평가를 두 번 실행해 행 수·지표·후보 정렬이 동일한지 확인한다.  
합격: 표의 모든 수치를 충족하며, 미달 모델은 `screening_only_not_rankable`로만 남긴다.

## 단계 4 — KG 근거형 LLM 역설계

1. 입력은 전체 합성 KG에서 SPARQL로 만든 후보별 근거 경로(분자, 동조건 측정, 계산법, 인용문, 가장 가까운 선행 구조)뿐이다. 벡터 청크나 기억 기반 수치를 근거로 쓰지 않는다.
2. LLM 출력은 SMILES 후보, 편집/치환 레시피, 목표 조건, 인용한 KG 경로 ID, 상충 완화 가설, 반증 조건, 위험을 구조화한다. 인용 ID는 실제 전달된 후보 근거에만 허용한다.
3. 구조 유효성·중복(InChIKey/scaffold)·조건 호환성·인용 연결·전체 KG 선행 조회를 검증한다. 일부 프롬프트에 준 근거만이 아니라 모든 논문/후보/이전 설계 RDF를 검사한다.
4. 근거가 모자라거나 동조건 비교가 불가하면 LLM은 후보 수를 채우지 않고 `insufficient_evidence`로 종료한다. 이 종료는 실패가 아니라 정직한 산출물이다.
5. 각 후보, 전체 선행조회 결과, 근거 해시, 검증 결과와 보류 사유를 RDF에 저장하고 직렬화·재로드·SPARQL 재질의로 환류를 검증한다.

산출물: 후보별 RDF 설계 사건, 요청/응답 스키마, KG 전후 스냅샷, `accepted`와 `hypothesis_only`를 분리한 목록.  
실행 검증 1개: 프롬프트에는 없지만 전체 KG에는 있는 가까운 선행·근거 부족·잘못된 인용을 넣은 세 음성 대조가 각각 `prior_art_review_required` 또는 `insufficient_evidence`로 귀결되는지 검사한다.  
합격: 모든 제안에 DOI-인용-조건 경로가 있고, 근거 없는 후보 0개, 자동 신규성 확정 0개, RDF 왕복 검증 통과.

## 단계 5 — 독립 차별성 심사와 스크리닝

1. 생성자와 독립된 검토자가 후보별로 전체 KG의 최근접 선행·미해결 출처·구조 차이·반증 가능 가설을 심사한다. LLM 자기평가나 KG 미기록만으로 승격하지 않는다.
2. `unresolved_source_ids`가 하나라도 있으면 `hypothesis_only`이다. 제한적 통과도 “DFT/실험으로 시험할 가설”이지 신규 분자·세계 최초·성능 보장이 아니다.
3. 통과 후보만 구조 생성/저비용 완화→xTB→보정된 MLIP→선별 DFT 순으로 간다. 각 단계는 전 단계의 원자/SMILES/전하/스핀/용매 가정을 고정하고, 실패·범위 밖·불확실 후보는 다음 단계로 보내지 않는다.
4. DFT 결과는 기존 문헌 DFT와 구별한 새 `Measurement`/계산조건/근거로 RDF에 적재하고, 보정·Pareto·선행 심사를 다시 실행한다.

산출물: 독립 심사표, 단계별 스크리닝 원장, DFT 환류 레코드와 재평가 보고서.  
실행 검증 1개: 후보의 근거 RDF 또는 구조/조건/심사 상태를 하나씩 변조한 뒤 전체 KG 재검증이 거부하는지 확인한다.  
합격: 승격 후보 100%가 독립 심사·보정 합격·Pareto 기준을 모두 만족하고, DFT 환류 후 전 후보의 상태가 재계산된다.

## 위험과 사람이 결정할 것

| 결정/위험 | 사람이 결정할 항목 | 완화/중단 규칙 |
|---|---|---|
| 대상 경계 | 비퀴논(phenazine, isoindigo, viologen), clathrate, 흡착재를 학습 그래프에 포함할지 | 기본은 경계 보존·학습 제외; 기준 변경은 Phase 1 CQ 갱신 후에만 |
| 데이터 정확도 | 40개 독립 검수의 검토자와 허용 오류 | 확정 오류가 하나라도 있으면 해당 유형의 자동 승격 중단 |
| 목표 조건 | 사용 용도(배가스/DAC), O2 기준, 용매·기준전극 변환 허용 범위 | 미결정이면 조건별 모델만 만들고 통합 순위 금지 |
| 계산 예산 | xTB/각 MLIP/DFT의 실행 환경과 최대 후보 수 | 예산/환경 미정이면 DFT 큐를 만들지 않고 KG 후보까지 멈춤 |
| 모델 범위 | AIMNet2/MACE-OFF/UMA의 원소·전하·라디칼/용매 적합성 | 지원 범위 밖 또는 보정 미달은 `insufficient_evidence` |
| 신규성 | 독립 심사자, 검토 문헌 범위, 통과 표현 | 전세계 신규성 주장은 금지; 미해결 출처가 있으면 보류 |

## 실행 순서와 완료 조건

`누락 14편 판정 → 스키마/추출 보강 → 사람 검수·Phase 5 전체 KG 빌드 → DFT 앵커 보정·기준선 평가 → 근거형 역설계 → 독립 심사 → 단계적 스크리닝·RDF 환류` 순서로만 진행한다.

완료는 다음 모두일 때다: XLSX 38 DOI가 상태화됨, 새 필드/CQ/SHACL이 통과함, 학습 입력이 검수·근거·조건 계약을 만족함, 사전 선언 수치 평가를 충족함, 모든 후보가 전체 KG·독립 심사·RDF 왕복을 통과했거나 정직하게 보류됨, DFT 결과가 있으면 재평가까지 끝남.

### 적용 원칙

- `ponytail`/`ponytail-review`: 기존 Phase 2~4 코드와 검사기를 재사용하고, 새 계층·의존성·추상화는 추가하지 않는다.
- `mle-workflow`: 데이터 계약, 누출 없는 분할, 고정 스냅샷, 기준선·보정·실패 원장을 먼저 만든다.
- `eval-harness`/`tdd-workflow`: 위의 각 단계 검증을 구현 전 합격 기준으로 선언하고, 결함은 재현 테스트(RED) 뒤 최소 수정(GREEN)으로만 고친다.
- `verification-loop`: 단계 산출물마다 스키마/타입·정적 검사·대상 테스트·전체 KG 재로드 검증 결과를 기록하며, 실행하지 못한 검증은 통과로 쓰지 않는다.
- `ontology-mlip` 원칙: 인용 강제, 근거 부족 종료, 전체 KG 검사, 독립 신규성 심사, RDF 저장 후 재질의/환류를 그대로 적용한다.
