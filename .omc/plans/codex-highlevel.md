# Codex 작업: 최종 후보 고수준 확인 `dft/highlevel.py` (PLAN 개정 4.2의 결정 2)

먼저 읽기:
- `PLAN.md` 10절의 "절대값은 최종 후보 2~3개만 고수준으로" 항목
- `~/atomistic-agent-runs/reports/quinone-bench-pilot.md`, `~/atomistic-agent-runs/reports/analysis.json`
- `~/atomistic-agent-runs/quinone-bench/Fc_p1/mol_job.py`(180줄. build, thermo_analysis, qrrho_vib_entropy, sg1_prune_light_atoms)
- `dft/dft.py`, `dft/run_set.py`
- `.claude/skills/ponytail`(full), `tdd-workflow`

**`~/atomistic-agent-runs/` 아래는 아무것도 수정하지 마라.** 읽기와 복사만 허용한다.
환경: `.venv/bin/python`. 실제 DFT는 하지 않는다(실행은 내가 한다).

## 재사용
- `mol_job.py`를 `dft/mol_job.py`로 복사한다. 맨 위에 출처 한 줄을 단다. 고치지 말고 import해서 쓴다. 실행에 필요한 아주 작은 수정만 허용하고, 수정했다면 주석으로 남긴다.
- Fc/Fc⁺는 다시 계산하지 않는다. `analysis.json`의 `Fc_oxidation_eV`(4.417)와 `fc_composite` 값을 `dft/highlevel_fc.json`에 출처 경로와 함께 복사해서 쓴다. Fc⁺ 초기 추정 문제는 보고서에 해결 기록이 있다.

## 대상 (총 4개 분자)
1. 루프 최종 후보 3개
   - `O=C1C(F)=C(Cl)C(=O)C(Cl)=C1`
   - `O=C1C(F)=C(Cl)C(=O)C(Cl)=C1F`
   - `O=C1C(F)=C(Cl)C(=O)C=C1Cl`
2. 검증 기준 chloranil `O=C1C(Cl)=C(Cl)C(=O)C(Cl)=C1Cl`
   - 실험값(Alherz 2022): E2 −1.18 V, ΔG(1 CO2) −3.88 kcal/mol
   - `onto/phase_4b_extend/alherz2022_table1.csv`에서 읽는다.
3. 공통: CO2

## 계산 (복합 방식)
- 상태: Q(0,0), Q•⁻(−1,1), Q²⁻(−2,0), Q²⁻·CO2(−2,0), CO2(0,0)
- 부가물의 결합 위치는 저수준 계산에서 에너지가 가장 낮았던 카보닐 O 하나만 쓴다.
  - 저수준 결과 JSON(`onto/phase_8_design/runs/loop-*/round_*/<InChIKey>.json`, chloranil은 `dft/runs/ref_set/`)의 adduct `o_index`와 최적화 좌표에서 시작한다.
  - Q, Q•⁻, Q²⁻도 저수준 최적화 좌표에서 시작한다.
- TZ: ωB97M-V/def2-TZVPD/SMD(MeCN), 용매 중 최적화. 격자 (99,590), VV10 (50,194). 에너지 `E_tz`.
- SVP: ωB97M-V/def2-SVP/SMD(MeCN) 최적화와 해석적 헤시안, mRRHO(298.15 K). `G_corr_svp`와 허수 진동 수.
- 최종 `G = E_tz + G_corr_svp`. 라디칼은 UKS로 계산하고 ⟨S²⟩를 기록한다.
- 결과는 `dft/runs/highlevel/<id>/<state>_{tz,svp}.json`에 저장한다. 상태와 수준 하나가 끝날 때마다 저장하고, 다시 실행하면 이어서 한다.
- 실패하면 기록하고 계속 진행한다. 헤시안이 메모리 부족이면 그 사실을 기록한다.
- GPU: `--gpus 0,1`. spawn 풀을 쓰고, 작업 단위는 (분자, 상태, 수준)이다. 큰 작업부터 배분한다.

## 요약 `summarize()` (DFT 없이 JSON만 읽음)
- `E1 = −(G[Q•⁻] − G[Q]) − Fc_ox`, `E2 = −(G[Q²⁻] − G[Q•⁻]) − Fc_ox` (eV를 V로 바꾸고 Fc/Fc⁺ 기준). 부호 규약은 analysis.json의 BQ 값을 재현해야 한다.
- `ΔG_bind(1 atm) = (G[adduct] − G[Q²⁻] − G[CO2])·627.5`, `ΔG_bind(1 M) = ΔG(1 atm) − 1.894`(analysis.json의 −13.87 → −15.76과 같은 관계)
- O2 판정: `E2 − (−1.23 V)`. 실험 O2/O2•⁻ 값(Alherz 2022 p.904)이다. 여유 0.15 V 이상이면 통과다.
- chloranil: 계산값과 실험값의 차이를 보고한다(E2, ΔG).
- 저수준 결과와 나란히 비교하는 표: 저수준 f, O2 여유, ΔE_bind와 고수준 E2, ΔG_bind, O2 여유
- 결과는 `dft/runs/highlevel/summary.json`, `summary.md`

## 시험 (DFT 없음)
- `summarize`에 analysis.json의 BQ 값(E_tz와 G_corr에 해당하는 가짜 json)을 넣으면 E1 −0.619, E2 −1.779, ΔG(1 M) −15.76이 ±0.01 이내로 재현된다.
- 이어서 하기: 완료된 (상태, 수준)은 계산 함수를 부르지 않는다.
- 결합 위치와 시작 좌표를 저수준 JSON에서 제대로 읽는다(가짜 json).

## Makefile
- `test`에 시험을 추가한다.
- 타깃 `highlevel`: `$(PY) dft/highlevel.py --gpus 0,1`

## 규칙
git·설치·하위 에이전트 금지. 실제 DFT 금지. `~/atomistic-agent-runs/`는 수정 금지. 수정은 `dft/`와 Makefile만 한다. 끝나면 `make test` 결과와 분자별 기저함수 수(TZVPD)를 붙이고, 마지막 줄에 `HL-DONE`.
