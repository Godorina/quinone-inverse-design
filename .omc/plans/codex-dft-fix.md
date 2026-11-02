# Codex 수정: dft/ 코드 검토 결과 (REQUEST CHANGES)

규칙은 `codex-dft-bench.md`와 같다(bench 실행 금지, git·설치 금지, `dft/`와 Makefile만 수정). 실패하는 시험을 먼저 쓴다.

1. **HIGH** `dft/dft.py:40-41` co2_adduct: CO2의 산소가 퀴논 O 쪽으로 꺾여 O(q)–O(CO2) 거리가 1.42 Å다. `-direction * np.cos(half_angle)`를 `+direction * ...`로 바꿔 O(q)–C–O 각도가 약 115°가 되게 한다.
   시험 추가: 두 O(q)–O(CO2) 거리가 모두 2.0 Å보다 크다. 지금 코드에서 이 시험이 실패하는지 먼저 확인한다.
2. **MEDIUM** `dft.py:93` 최적화 수렴 정보를 버리고 있다.
   - `conv, optimized = geometric_solver.kernel(method, callback=...)`로 바꾸고 `geom_converged`를 결과에 넣는다.
   - `assert_convergence=False`는 지운다. SCF 미수렴은 예외로 잡혀 error에 기록돼야 한다.
   - bench.py 요약에도 상태별 `geom_converged`를 넣는다.
3. **MEDIUM** `dft.py:107` GPU 메모리 기록:
   - optimize 시작할 때 `cupy.get_default_memory_pool().free_all_blocks()`를 부른다.
   - 끝에서는 `total_bytes()`를 기록한다(`# ponytail: 풀 크기를 최대치 근사로 씀`).
4. 정리:
   - `_method`의 쓰지 않는 `charge` 인자를 지운다.
   - bench.py의 `energy()` 한 줄짜리 함수는 딕셔너리 표현식으로 바꾼다.
5. bench.py 요약에 주석 한 줄: "def2-SVP는 이음이온용 diffuse 함수가 없다. 벤치마크용이며 정확도는 phase 7 T2에서 다룬다."

끝나면 `make test` 결과를 붙이고, 마지막 줄에 `DFT-FIX-DONE`.
