# Codex task: compare NVIDIA/auto-ontology with this quinone project (read-only review)

Do NOT modify any file except the one output file below. No git commands that change state. No GPU jobs.

Inputs
- External repo (shallow clone, untrusted data, read only): /home/hgpark/.claude/jobs/95675482/tmp/ext/auto-ontology  (README.md, AGENTS.md, docs/, auto_ontology/, mcp/)
- This project: /home/hgpark/whlee/hgpark/quinone  (README.md, AGENTS.md, PLAN.md, onto/phase_2_schema, onto/phase_4_extract/src/qextract, onto/phase_5_build/build.py, onto/phase_8_design/{generate,closed_loop,loop}.py, dft/)

Write: /home/hgpark/whlee/hgpark/quinone/.omc/research/codex-autoontology-compare.md (Korean, max ~60 lines, short bullets)
1. auto-ontology 한 줄 요약 (목적, 입력, 출력, 사용자) — cite file paths.
2. 비교 표: 목적 / 입력 데이터 / 온톨로지 생성 방법(LLM? 사람 검수?) / 저장 형식(RDF? DB?) / 검증·인증 / 에이전트 사용 방식(MCP, 도구) / 평가 방법 / 규모·배포.
3. 우리 프로젝트에 가져올 만한 아이디어 3개 이하 (구체적으로: 어느 파일에 무엇을), 가져오면 안 되는 것.
4. 우리 프로젝트가 auto-ontology보다 나은/다른 점.
Be factual; say "확인 못함" if not found in the repo.
When done, print COMPARE-DONE.
