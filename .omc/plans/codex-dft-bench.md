# Codex 작업: quinone/dft/ 와 벤조퀴논 DFT 벤치마크 코드

먼저 읽기: `AGENTS.md`, `PLAN.md` 5절(Phase 7 T2 절차), `.claude/skills/`의 ponytail(full), tdd-workflow.
위치: `/home/hgpark/whlee/hgpark/quinone/dft/`. 환경은 `quinone/.venv/bin/python`이다(PySCF 2.13, gpu4pyscf 1.7.1, geomeTRIC, RDKit 설치됨). GPU0과 GPU1은 모두 비어 있다.

## 만들 것 (시험 먼저)
```
dft/dft.py           # 함수만. 클래스 금지
dft/bench.py         # BQ 벤치마크 실행: python dft/bench.py [--cpu]
dft/tests/test_dft.py  # DFT 없이 빠른 시험 (평범한 def test_* + assert, 스크립트로 실행)
dft/runs/bench_bq/   # 실행 산출물 (bench.py가 만든다)
```

### dft.py
1. `embed(smiles, seed=0) -> (symbols, coords)`: RDKit AddHs, ETKDG, MMFF 최적화.
2. `co2_adduct(symbols, coords, o_index) -> (symbols, coords)`: 카보닐 O(o_index)에 CO2의 C를 1.45 Å로 붙인다. C=O 결합 방향의 연장선 위에 두고, CO2는 O–C–O 각도 약 130°로 굽힌다.
3. `optimize(symbols, coords, charge, spin, xc='b3lyp', disp='d3bj', basis='def2-svp', solvent='acetonitrile', gpu=True) -> dict`
   - gpu4pyscf로 계산한다(`gpu=False`면 PySCF CPU). spin=0이면 RKS, 그 밖에는 UKS.
   - 용매는 `.SMD()`로 걸고, 최적화는 geomeTRIC으로 한다.
   - SCF가 수렴하지 않으면 level_shift=0.2로 한 번만 다시 한다(`# ponytail:` 주석).
   - 반환: energy(Hartree), 최종 xyz 문자열, 걸린 시간(s), 최적화 단계 수, SCF 수렴 여부, 최대 GPU 메모리(cupy memory pool 기준), 오류(실패 시 예외 문자열. 예외를 밖으로 던지지 않는다).
4. `write_xyz`, `save_json`은 표준 라이브러리로 몇 줄만.

### bench.py
- BQ SMILES `O=C1C=CC(=O)C=C1`과 CO2. 다섯 가지 상태: BQ(0,0), BQ•⁻(−1,1), BQ²⁻(−2,0), BQ²⁻·CO2(−2,0), CO2(0,0).
  - spin은 2S, 즉 PySCF의 `mol.spin`이다.
- 상태마다 `optimize`를 순서대로 부르고, 끝날 때마다 `runs/bench_bq/result.json`에 누적 저장한다. 중간에 죽어도 그때까지의 결과가 남아야 한다.
- 마지막에 참고 값을 출력하고 저장한다:
  - `dE_red2_eV = (E[BQ2-] - E[BQ-]) * 27.2114`
  - `dE_bind_kcal = (E[adduct] - E[BQ2-] - E[CO2]) * 627.5`
  - 최적화 후 부가물의 O–C(CO2) 거리. 2.0 Å를 넘으면 `co2_detached=true`.
  - 분자 1개 평가 시간 = 4개 상태 시간의 합(CO2는 한 번만 계산하므로 제외)
- `--cpu` 옵션이면 PySCF CPU로 돈다.

### tests/test_dft.py (DFT 호출 없음)
- `embed`: BQ의 원자 수 12, CO2의 원자 수 3.
- `co2_adduct`: 원자 수 15, 붙인 O–C 거리 1.45 ± 0.01 Å, CO2 각도 120~140°.
- `optimize`에 아주 작은 계 하나(H2, STO-3G, gpu=False, solvent=None)를 넣어 dict 키와 수렴을 확인한다. 이 시험만 SCF를 쓴다. 수 초 안에 끝나야 한다.
- solvent=None이면 용매 없이 계산하도록 허용한다.

## Makefile
- `test`에 한 줄 추가: `cd dft && $(PY) tests/test_dft.py`
- 새 타깃 `bench`: `$(PY) dft/bench.py`, 그리고 `.PHONY`에 추가.

## 규칙
- git 금지, 설치 금지, 하위 에이전트 금지. **bench.py 실제 실행 금지**(오래 걸린다. 실행은 내가 따로 한다). 시험만 돌린다.
- 수정은 `dft/`와 Makefile만.
- 끝나면 `make test` 결과를 붙이고, 마지막 줄에 `DFT-CODE-DONE`.
