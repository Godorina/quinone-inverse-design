# Codex task: fix review findings for the Obsidian exporter

Read: .claude/skills/ponytail/SKILL.md, .claude/skills/tdd-workflow/SKILL.md. Rules as before: new failing tests first in a NEW file onto/phase_9_obsidian/tests/test_export_fixes.py (add to Makefile test; do not edit existing test files), smallest diff, no network/GPU/LLM, no commits.

Fix in onto/phase_9_obsidian/export.py:
1. [HIGH] Do not rmtree the whole vault. Remove/regenerate only Papers/, Compounds/, Runs/, Families/, Index.md, README.md; keep .obsidian/ and any other user files.
2. One note per InChIKey: merge KG nodes sharing an InChIKey (DNXUGBMARDFRGG…, SVPKNMBRVBMTLB…) into one note (all measurements kept); run tables link to that note.
3. Frontmatter: add co2_detached (and highlevel flags when present); Index Dataview queries exclude detached (WHERE !co2_detached).
4. source='highlevel' for molecules that only come from highlevel summaries.
5. Parse cited IDs from every round prompt, not only prompts[0].
6. Readable note names: title = KG name; else PubChem-free fallback: `<family or skeleton> <InChIKey[:8]>` for reference/loop molecules — but prefer a short SMILES-free label like `loop <run-date> R<round>-<i>`? Choose: reference molecules use their reference id/name from reference_expansion.csv or smiles_proposals.csv (compound column) when available; loop-only candidates `Cand <InChIKey[:8]>`. Add ` (<InChIKey[:8]>)` only when names collide; drop the hash suffix everywhere else (Papers use title only, add year/DOI tail only on collision). Put full InChIKey and SMILES in `aliases:` frontmatter so search finds them.
7. Hub notes Families/<skeleton or family>.md linking members; every compound links to its family (no orphan compound notes).
8. Index: replace the in-paper query with (a) loop candidates grouped by run with f_v2 and o2_margin_V, (b) papers by year; keep top-f query (attached only).
9. Ponytail cuts from review: isinstance(value, URIRef); single node instead of 'nodes' list; drop link-re-detecting regex by escaping at build time; test cleanups only in the new test file.
Tests: no orphans, no hash suffix unless collision, .obsidian/ survives regeneration, merged InChIKey notes, detached flag present, links resolve, determinism.
Run `make obsidian` + the new tests + existing test_export.py. Append a short Korean log to .omc/research/codex-obsidian.md with 2 sample note paths. Print OBSIDIAN-FIX-DONE.
