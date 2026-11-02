# Codex 수정: Phase 8 뼈대 독립 검증 결과 (REQUEST_CHANGES)

이전 지시서 `codex-p8-skeleton.md`의 규칙을 그대로 지킨다. 각 항목마다 실패하는 시험을 먼저 쓴다(RED → GREEN).

## 차단 결함 (반드시 수정)
1. `run()`이 `in_domain`을 호출하지 않는다. T0 다음, 평가 전에 호출한다. 영역 밖이면 `out_of_domain`으로 기록하고 1단계로 센다. 평가자는 호출하지 않는다.
   시험: 영역 밖 후보만 내는 제안자를 넣으면 평가자 호출이 0번이고, 원장 80줄이 모두 `out_of_domain`이다.
2. `feedback=False`(B2)인데 제안자에게 점수가 붙은 `parents`(start_records)가 넘어간다. B2 문맥에는 이전 SMILES 목록과 시작 SMILES(점수 없음)만 준다.
   시험: B2 모드에서 제안자가 받은 문맥에 f, E2, ΔG 같은 점수 키가 하나도 없다.
3. 평가자가 예외를 내면 실행 전체가 중단된다. 예외를 잡아 `calculation_fail: <예외 이름>`으로 기록하고 1단계로 센다.
   시험: 평가자가 RuntimeError를 던져도 원장이 80줄이고 최고 f는 그대로다.

## 그 밖의 수정
4. `_proposal`: 제안자 시그니처를 하나로 고정한다(`propose(context) -> list[dict]`). 시그니처 검사와 TypeError fallback을 지운다. 지금은 제안자를 두 번 부를 수 있다.
5. ponytail-review 지적 반영:
   - `edit`는 명시적 키워드 인자만 받는다. dict와 rng를 겸하는 인자, 이름 별칭 두 개는 없앤다.
   - `_pattern`은 코어당 한 번만 계산한다.
6. 시험 보강:
   - 시작 집합의 f가 서로 다를 때 최고 f의 시작값이 그 최대값인지 명시적으로 확인한다.
   - `insufficient_evidence` 이후에는 제안자가 다시 호출되지 않는지 확인한다.

끝나면 `make test` 전체 결과를 붙이고, 마지막 줄에 `P8-FIX-DONE`.
