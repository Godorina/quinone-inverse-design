# Codex 작업: PubChem 연동 (신규성 검사와 온톨로지 연결)

배경: 최종 후보 3개를 PubChem에서 찾아보니 모두 이미 등록된 분자였다(CID 142730423, 3431482, 140127337). 지금 중복 검사는 우리 지식 그래프와 Alherz 표만 보고 있어서, 신규성을 과장할 위험이 있다.

먼저 읽기: `AGENTS.md`, `onto/phase_8_design/generate.py`(context, check), `closed_loop.py`, `onto/phase_5_build/build.py`, `onto/phase_2_schema/schema/quinone.ttl`, `.claude/skills/ponytail`(full), `tdd-workflow`.
환경: `.venv/bin/python`. 공개 PubChem REST 조회는 허용한다. LLM과 DFT 계산은 하지 않는다. git 명령은 쓰지 않는다.

## 만들 것 (시험 먼저)
1. `onto/phase_8_design/pubchem.py` (함수만)
   - `lookup(inchikey) -> {"cid": int|None, "iupac": str|None, "status": "found"|"not_found"|"error"}`
   - PUG REST `compound/inchikey/<key>/property/IUPACName,MolecularFormula/JSON`를 표준 라이브러리 urllib로 호출한다. timeout 15초.
   - 404는 not_found로 처리한다. 네트워크 오류는 error로 처리하고 예외를 던지지 않는다.
   - 캐시는 `onto/data/pubchem_cache.json`이다(InChIKey → 결과). found와 not_found만 저장하고 error는 저장하지 않는다.
   - 호출 간격은 0.25초 이상이다(PubChem 제한은 초당 5회).
   - fetch 함수는 인자로 주입할 수 있게 한다(시험용).
2. `generate.check()`의 동작은 바꾸지 않는다(거절하지 않는다). 대신 다음을 한다.
   - `closed_loop.py`가 통과한 제안마다 `pubchem_cid`와 `pubchem_status`를 원장(ledger)과 결과에 붙인다.
   - `report.md`에 "평가 후보 중 PubChem 등록 n/N"을 한 줄 추가한다.
   - `--reject-pubchem` 옵션(기본값 끔)을 켜면, PubChem에 있는 분자는 `known_pubchem`으로 거절한다.
3. 스키마와 온톨로지
   - `quinone.ttl`에 `qn:pubchemCID`(Compound, xsd:integer)를 추가한다. 기존 관례대로 ko/en label과 comment를 단다.
   - `phase_5_build/build.py`: InChIKey가 있는 Compound에 캐시의 CID를 붙인다. 결정성(두 번 빌드한 결과가 바이트 단위로 같아야 함)을 유지한다.
4. 캐시 채우기 (실제 조회)
   - 대상 InChIKey는 다음과 같다.
     - 기준 세트 15개(`dft/runs/ref_set`)
     - Alherz 표 7개
     - 루프 평가 분자 전부(`onto/phase_8_design/runs/loop-*/round_*/summary.json`. 편향된 무작위 실행 폴더도 포함)
     - 고수준 4개
   - 결과를 `onto/phase_8_design/pubchem_report.md`에 쓴다.
     - 실행별, arm별로 found/not_found 수를 적는다.
     - not_found 분자의 SMILES를 적는다. 이 분자들이 "PubChem 기준 신규 후보"다.
5. 결과 반영
   - `dft/highlevel.py` summary에 pubchem_cid 열을 추가하고 `summary.md`를 다시 만든다(`--summary`, DFT 없음).
   - `README.md`의 결과 요약에 한 줄을 추가한다: "최종 후보 3개는 모두 PubChem에 이미 등록된 분자다(기지 분자의 CO2 포집 관점 재발견). 신규성은 주장하지 않는다."

## 시험 (네트워크 없음, 가짜 fetch)
- lookup: found, 404→not_found, 예외→error(캐시하지 않음), 캐시 적중 시 fetch를 부르지 않음.
- closed_loop: 가짜 lookup으로 원장에 cid가 붙고, `--reject-pubchem`일 때 known_pubchem으로 거절된다.
- 스키마 시험(ko/en label)과 phase 5 빌드 시험(멱등성)이 통과한다.

## Makefile과 마무리
- `make test`에 새 시험을 추가한다.
- 끝나면 `make test` 결과와 pubchem_report.md의 요약표를 붙이고, 마지막 줄에 `PUBCHEM-DONE`.
