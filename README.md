# quinone: 온톨로지와 LLM으로 하는 퀴논 CO₂ 포집 분자 역설계

전기화학적 CO₂ 포집에 쓰는 퀴논을 다룬 계산 논문 38편(`quinone_CO2_simulation_papers_2020-2026.xlsx`)으로 지식 그래프(온톨로지)를 만들었다. 그 위에서 LLM이 근거를 인용해 분자를 제안하고, DFT가 평가하고, 결과를 다시 LLM에 되돌리는 닫힌 루프를 돌렸다.

- 계획과 변경 이력: [`PLAN.md`](PLAN.md)
- 현재 상태와 결과 요약: [`AGENTS.md`](AGENTS.md)
- 한 장 요약 그림: [`.omc/artifacts/quinone_progress.html`](.omc/artifacts/quinone_progress.html) (브라우저로 열기)

## 결과 요약

- 기준 분자 15개를 DFT로 계산해 "환원전위와 CO₂ 결합 세기" 사이의 맞교환선을 만들었다. 데이터는 B3LYP-D3BJ/def2-SVP/SMD(MeCN)로 계산한 12개 점이며, 잔차 σ는 3.4 kcal/mol이다.
- 닫힌 루프를 4번 실행했다(LLM 2번, 무작위 2번, 각 3회차 × 5개). 목표인 f ≥ 2이면서 O₂ 여유 ≥ 0.15 V를 만족한 분자는 0개다. O₂ 조건을 통과한 분자 중 최고 f는 기준 세트의 1.03에서 1.38로 올랐다.
- LLM과 무작위를 공정하게 비교했을 때 찾은 최고값은 같았다. LLM은 평균 품질과 제안 효율에서 앞섰다. 각 조건을 1번씩만 실행했으므로 통계적 결론은 아니다.
- 최종 후보 3개를 고수준으로 다시 계산했다(ωB97M-V/def2-TZVPD/SMD, Fc 기준, mRRHO). 실험 O₂ 전위(−1.23 V vs Fc)와 비교하면 세 후보 모두 O₂ 기준을 통과하지 못했다(−0.13, −0.02, −0.12 V). chloranil로 실험값과 대조한 오차는 E2 −0.045 V, ΔG −2.9 kcal/mol이다.

## 구성

| 경로 | 내용 |
|---|---|
| `onto/` | 온톨로지 파이프라인: 스키마(phase 2), 추출(phase 4), 보강과 실험표(phase 4b), RDF(phase 5), 루프(phase 8) |
| `dft/` | DFT 코드(PySCF, gpu4pyscf)와 결과(`runs/ref_set`, `runs/highlevel`) |
| `.claude/skills/` | 작업에 쓴 스킬 문서(ponytail, ECC 계열) |
| `.omc/plans/` | 계획 초안, 개정본, 에이전트 작업 지시서 |

## 실행

```bash
make env     # .venv 생성 (Python 3.11, requirements.txt)
make test    # 모든 시험
make loop2   # LLM 닫힌 루프 (GPU, Claude CLI 필요)
```

## 포함하지 않은 것

저작권 때문에 논문 PDF, 추출한 원문 텍스트, 출판사 초록(`phase_3_corpus/pdf|text|master.json`, `data/abstracts_4b` 등)은 올리지 않았다. 추출 기록(`records_final`)과 지식 그래프에는 근거로 쓴 200자 이내의 짧은 인용과 쪽 번호만 들어 있다. 환경(`.venv`)과 계산 로그도 제외했다. `onto/phase_2_schema/tests`가 쓰는 공통 검사기는 `onto/al_alloy/common/`에 복사해 두었다.

Alherz 2022 Table 1 값(`onto/phase_4b_extend/alherz2022_table1.csv`)은 PDF 페이지 이미지에서 읽어 입력했고, 독립 검증 에이전트가 한 번 더 대조했다. 사람이 직접 검수한 값은 아니다.
