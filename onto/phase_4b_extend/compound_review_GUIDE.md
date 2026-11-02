# compound_review.csv 검수 가이드

분자 1개 = 1행(22행). 원문 PDF의 해당 쪽을 열고 아래 칸을 채운다. 다른 칸은 고치지 않는다.

1. **E2_ok**: `E2_V`가 이음이온을 만드는 두 번째 환원 전위이고, 기준 전극(`ref_electrode`)과 값이 원문과 같으면 `y`, 아니면 `n`.
   - `E2_V`가 비어 있으면 `E2_note`의 "choose E2" 후보 중 맞는 값을 `E2_V`에 적고 `y`. CO2가 없을 때(N2/Ar) 측정한 값을 고른다.
2. **binding_ok**: `binding_value`와 단위가 원문과 같고, `basis`(실험/계산)가 맞으면 `y`.
   - 비어 있으면 "choose binding" 후보 중 목표 조건(MeCN)에 맞는 값을 골라 적는다.
   - `basis_suspect` 표시가 있으면 원문이 실험값인지 계산값인지 확인해서 `reviewer_note`에 적는다.
3. **co2_standard_state**: 원문에 있으면 `1atm` 또는 `1M`, 없으면 비워 둔다.
4. **verdict**: 두 값이 모두 맞고 쓸 수 있으면 `ok`, 아니면 `reject`(이유는 `reviewer_note`).
   - `ref_not_fc`(SHE, Ag/AgCl 기준)는 논문이 Fc 환산 상수를 줄 때만 `ok`이고, 그 상수를 note에 적는다. 없으면 `reject`.
   - m044(이미다졸륨 염, SMILES 없음)는 루프 대상이 아니므로 `reject`(note: 범위 밖)로 둔다.

진행도와 게이트 확인: 프로젝트 루트에서 `make review`. ok 10개 이상, 논문 2편 이상이면 통과.
