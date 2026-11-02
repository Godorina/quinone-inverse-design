# Codex 작업: Phase 8 닫힌 루프 뼈대 (가짜 평가자, 실제 xTB·LLM 없음)

먼저 읽기: `PLAN.md` 6~8절, `AGENTS.md`, `.claude/skills/`의 ponytail(full), tdd-workflow, mle-workflow.
위치: 모두 `/home/hgpark/whlee/hgpark/quinone/` 안. 새 파일은 `onto/phase_8_design/`에만 둔다.

## 만들 것 (실패하는 시험 먼저)
`onto/phase_8_design/loop.py` 하나 + `onto/phase_8_design/tests/test_loop.py` (평범한 `def test_*` + assert, 스크립트로 실행).
클래스 계층 금지. 함수 몇 개와 for 루프. 평가자와 제안자는 함수 인자로 주입한다(실제 xTB/LLM은 나중에 같은 시그니처로 꽂는다).

1. `edit(smiles, op, rng_or_args) -> smiles|None`: PLAN 7절 2번의 편집 연산(치환기 추가, 교체, 제거, 위치 이동). 치환기 목록은 인자로 받는다. RDKit 사용.
2. `t0(smiles) -> reason|None`: RDKit 파싱, 원자가, 퀴논 C=O 패턴(1,2-/1,4-), 중원자 ≤ 40, 금속 없음.
3. `in_domain(smiles, cores_smarts, allowed_subst, ref_fps) -> reason|None`: PLAN 7절 1번의 (a)(b)(c).
4. `objective(E2, dG, a, b, sigma, o2_E, margin=0.15) -> f|None`: `f=(a*E2+b-dG)/sigma`, O2 제약 위반이면 None.
5. `run(propose, evaluate, start, budget=80, rounds=8, k=5, feedback=True, ledger_path) -> list[float]`:
   - 예산 단위는 제안 1개다. 실패(T0, 영역 밖, 중복, O2, 계산 실패, 인용 실패)도 1단계로 세고, 최고 f는 그대로 둔다.
   - `insufficient_evidence`가 오면 남은 단계를 개선 없이 소진한다.
   - 최고 f의 시작값은 시작 집합의 최대 f다.
   - 단계마다 `ledger.jsonl`에 한 줄을 남긴다(PLAN 7절 6번 필드).
   - `feedback=False`(B2)이면 propose에 상위 k개와 실패 집계를 주지 않고, 이전 SMILES 목록만 준다.
   - 반환값은 단계별 최고 f(길이 80).
6. `auc(best_curve, start_best)`, 그리고 `random_proposer`(B0: 상위 k에서 부모 균등, 연산 균등, seed).

## 시험 (최소)
- T0: 벤조퀴논 통과, 벤젠 거절, 금속 포함 거절.
- 영역: 코어 밖, 미등록 치환기 각각 거절.
- 예산: 가짜 제안자가 매번 무효 SMILES를 내도 정확히 80단계이고, 최고 f가 시작값 그대로다.
- `insufficient_evidence`이면 남은 단계가 소진된다.
- **피드백 경로**: 가짜 평가자(f = 분자 속 F 개수)와 random_proposer(seed 고정)를 쓰면 feedback=True에서 최고 f가 시작값보다 오르고, feedback=False에서는 같은 seed로 덜 오르거나 같다.
- AUC 손계산 1개.
- 원장 줄 수가 80이다.

## 실행
- RDKit 파이썬: `/home/hgpark/Downloads/prog/miniforge3/envs/gpu4pyscf/bin/python`
- `Makefile`의 `test` 타깃에 한 줄 추가: `cd onto/phase_8_design && $(PY_CHEM) tests/test_loop.py`
- 끝나면 `make test` 전체 결과를 붙인다.

## 규칙
- git 금지, 설치 금지, LLM·xTB 호출 금지, 하위 에이전트 금지.
- `onto/phase_8_design/`와 `Makefile` 한 줄 외에는 수정하지 않는다.
- 단순화한 곳에는 `# ponytail:` 주석을 단다.
- 마지막 줄에 `P8-SKELETON-DONE`.
