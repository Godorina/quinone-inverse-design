# quinone: 퀴논 CO2 포집 논문 → 온톨로지 → 닫힌 루프 역설계

작업은 모두 이 폴더에서 시작한다. 계획은 `PLAN.md` 하나만 따른다(현재 개정 2).

## 위치
- `quinone_CO2_simulation_papers_2020-2026.xlsx`: 출발점인 논문 38편 목록
- `onto/`: 파이프라인(phase 1~9) **작업본**. 2026-10-30에 `../ontology/quinone/`을 복사해 만들었고, 이후 작업은 여기서만 한다. 원본은 그대로 남아 있지만 더는 갱신하지 않는다.
- `onto/al_alloy/common/`: 공통 검사기(`check.py`, `vocab.ttl` 등) 복사본. `phase_2_schema/tests/test_onto.py`가 상위 폴더에서 `al_alloy/common/check.py`를 찾기 때문에 이 위치에 둔다.
- `.claude/skills/`: ponytail, mle-workflow, eval-harness, verification-loop, tdd-workflow 등. 코드를 쓰기 전에 읽는다.
- `.omc/plans/`: 계획 초안, 개정 이력, Codex 지시서

## 명령
- `make test`: 모든 시험(스키마, 추출기, 4b, phase 5, phase 8 루프와 계약, DFT, 고수준 검사). 개수는 실행 출력을 본다.
- `make review`: 분자 검수 진행도와 phase 7 게이트(ok 10개 이상, 논문 2편 이상). `make compounds`: 검수표 재생성(검수 내용이 있으면 거부)
- `make status`, `make pairs`: 4b 표 재생성. `pairs`는 검수 내용을 덮어쓰므로 먼저 백업한다.

## 환경 (모두 이 폴더 안)
- `.venv/`: Python 3.11. `requirements.txt`의 버전 고정으로 `make env`가 만든다.
  - 들어 있는 것: PySCF 2.13, gpu4pyscf 1.7.1(CUDA 12 휠 포함), RDKit, ASE, rdflib, pyshacl.
  - 온톨로지 시험, 4b, phase 8, DFT가 모두 이것을 쓴다.
- 추출기만 자체 uv 프로젝트를 쓴다: `onto/phase_4_extract/.venv` (`uv run --frozen`).
- 계산 방법: **DFT만 쓴다(xTB 안 씀, 사용자 결정).** CPU는 PySCF, GPU는 gpu4pyscf.
- GPU: 2026-10-30 23:09에 llama-server(로컬 Qwen)를 꺼서 GPU0, GPU1이 모두 비어 있다(각 16 GB). Makefile 기본값은 `CUDA_VISIBLE_DEVICES=0`이다. 다시 켜는 명령은 `.omc/llama-server.restart.sh`에 있다. 켜면 GPU 메모리를 약 23 GB 차지하므로 DFT와 함께 쓸 수 없다.
- `make dft-check`: 물 분자 B3LYP/def2-SVP/SMD(MeCN)를 CPU와 GPU로 계산해 결과가 같은지 확인한다(현재 차이 0.0000 kcal/mol, CPU 15.7초, GPU 2.6초).
- ORCA는 없다. `/usr/bin/orca`는 화면 낭독기다.

## 규칙
- 외부 참고 자료(읽기만): `~/atomistic-agent-runs/reports/quinone-protocol-literature.md`(DFT 프로토콜 문헌 비교). **`~/atomistic-agent-runs/quinone-bench/`는 다른 에이전트의 계산 폴더이므로 건드리지 않는다.**
- GPU 순서: 우리 `dft/run_set.py`(기준 세트 15개)가 먼저 돌고, 끝나면 atomistic-agent가 GPU를 쓴다. 그 동안에는 GPU 계산을 새로 시작하지 않는다.
- 원본 수정 금지: `onto/phase_4_extract/records*/`, `onto/phase_3_corpus/`, PDF.
- git 기록 변경 금지(commit, reset, checkout 등). 사용자가 요청할 때만 한다. 4b 이전 상태는 `refs/quinone/before-4b`에 있다(원본 경로 `ontology/quinone` 기준).
- 결함은 실패하는 시험부터 쓴다(RED→GREEN). 단순화한 곳에는 `# ponytail:` 주석을 단다.
- 작성과 검토는 분리한다. 각 phase의 통과 여부는 작성자가 아닌 검토자가 정한다.

## 지금 상태 (2026-11-02, 최신)
- **고수준 확인 완료** (`dft/runs/highlevel/summary.md`). Codex 2차 검토를 반영했고, 경고(실패, 미수렴, 허수 진동, CO2 이탈)는 하나도 없다.
  - chloranil과 실험의 차이: E2 −0.045 V, ΔG −2.9 kcal/mol.
  - 최종 후보 3개의 O2 여유(실험 O2 −1.23 V 기준): −0.13 / −0.02 / −0.12 V. 세 후보 모두 사전 기준 +0.15 V에 미달한다. −0.02 V 후보는 O2와 경쟁하는지 자체가 불확실하다.
  - 저수준 대비 O2 여유가 약 0.3 V 낮아졌다. 다만 계산 방법과 O2 기준이 함께 바뀌었으므로 원인을 하나로 분리할 수 없다.
- **공정한 비교** (`loop-20261102-003356` 대 `loop-20261031-222906`): LLM과 무작위가 찾은 최고 f는 같다. LLM은 평균 f와 제안 효율이 더 높다. 실행은 각 1회다.
- 신규성은 "KG와 Alherz 표에 등록된 범위 안에서"로만 적는다. 2,5-다이클로로-BQ(Alherz 2ClQ)는 기지 분자인데 루프에서 후보로 평가됐다.

## 이전 상태 (2026-10-31)
- **작은 닫힌 루프 완료(22:22, 독립 검증 PASS)**: `onto/phase_8_design/runs/loop-20261031-151304/`
  - 3회차 × 최대 5개, 평가 10개, LLM 비용 $0.55. 성공(f ≥ 2이고 O2 여유 ≥ 0.15 V)은 0개.
  - O2 조건을 통과한 분자 중 최고 f는 기준 세트 1.03(F4Q)에서 1.38로 올랐다(1회차, `O=C1C(F)=C(Cl)C(=O)C(Cl)=C1`). 다만 이 값은 피드백 전인 1회차에 나왔고, 이후 회차에서는 넘지 못했다.
  - 2회차 최고 f는 1.65(2,6-다이플루오로-BQ)였지만 O2 여유가 −0.03 V로 탈락했다.
  - 3회차는 적용 영역(Tanimoto < 0.4)에서 4개가 탈락했고, 빈 자리를 채우지 않아 1개만 평가했다.
  - 주장할 수 없는 것: 무작위보다 낫다는 것, 피드백 효과, f ≥ 2, 절대 전위.
- **Phase 7 완료(07:11)**: 기준 세트 15개 DFT, 오류 0, 모두 수렴, 417분. CO2 이탈 3개(다이사이아노 계열 Q1/DDQ, DBQ, DNQ) 제외 후 12점으로 맞교환선 적합: ΔE_bind = −8.97·E2_eV − 42.41, σ = 3.43 kcal/mol (`dft/runs/ref_set/summary.json`). GPU는 이제 atomistic-agent 차례다.
- Phase 4b 자동화 부분 완료(독립 검증 PASS).
- 사람 확인 대기 제안 2건(검증 PASS):
  - `onto/phase_4b_extend/judgment_10_proposed.csv`: 편입 2, 경계 1, 범위 밖 1, 초록 없음 6
  - `smiles_proposals.csv`: 17개 제안, m044 5개는 비움. m025 Q6 = m043 DBQ, m005 c10 = m025 Q3
- Phase 8 루프 뼈대 `onto/phase_8_design/loop.py`(가짜 평가자, 시험 10개) 완료. 독립 검증 PASS. 피드백 시험은 피드백을 끄면 실패하는 것을 확인했다.
- 시험은 `make test` 기준 모두 통과(위 명령 줄의 숫자).
- 분자 검수 `onto/phase_4b_extend/compound_review.csv`는 선택 사항이다(진행을 막지 않는다). 실험 대조에는 `alherz2022_table1.csv`(독립 검증 완료)를 쓴다.
- 방식: **작은 닫힌 루프**(PLAN.md 개정 4~4.2). B안(단발 생성)은 개정 4에서 대체됐다.
- 벤치마크(`dft/runs/bench_bq/`): 벤조퀴논 1분자 13분, GPU 메모리 최대 3.2 GB, 부가물이 시간의 78%. 5개 상태 모두 수렴했다.
- 다음: 고수준 확인 결과 점검(수렴, 허수 진동, CO2 이탈) → chloranil로 실험과 대조 → 최종 보고서. 보고서에는 신규성을 "등록 범위(KG와 Alherz 표) 안에서"로만 적는다.
