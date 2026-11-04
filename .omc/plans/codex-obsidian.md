# Codex task: export the quinone KG + DFT results as an Obsidian vault (LLM-wiki style)

Read first: .claude/skills/ponytail/SKILL.md, .claude/skills/tdd-workflow/SKILL.md, AGENTS.md rules.
Rules: TDD (write tests first in a NEW file onto/phase_9_obsidian/tests/test_export.py, add to Makefile `test`); smallest code; stdlib + rdflib (already in .venv) only; no git commits; no GPU/LLM/network; don't modify existing data or tests.

Build `onto/phase_9_obsidian/export.py` (one file) + Makefile target `obsidian` → writes vault to `obsidian/quinone-vault/` (delete-and-regenerate only that folder; deterministic output, sorted, stable file names).

Sources (read-only):
- onto/phase_5_build/kg.ttl (Paper 55, Compound 186, Measurement 307, Evidence 285, Condition 223, Observation 96; predicates: Measurement method/ofCompound/unit/underCondition/value/reviewStatus/redoxCouple/fromPaper/property/basis/hasEvidence; Evidence quote/evidenceSource/page; Condition electrolyteText/atmosphere/additiveText/solvent/referenceElectrode/pH; Compound skeleton/substituentClass/smilesSource/form/name/inchikey/smiles/pubchemCID; Observation outcome/fromPaper/underCondition/observationKind/ofCompound/hasEvidence/reviewStatus; Paper name/identifier(DOI)/datePublished/simReviewTier). Inspect the schema onto/phase_2_schema/schema/quinone.ttl for labels.
- dft/runs/ref_set/summary.csv + per-molecule JSON (smiles, inchikey) — our reference DFT (E2_eV, dE_bind_kcal, co2_detached, family); lines.json.
- loop ledgers onto/phase_8_design/runs/loop-*/ledger.jsonl (arm, round, smiles, f, margin, pubchem_cid, hypothesis, cited_ids).
- dft/runs/highlevel*/summary.json (E2_V, dG_bind_1M_kcal, O2_margin_V, flags).

Vault layout:
- `Papers/<short title or DOI-slug>.md`: frontmatter (type: paper, doi, year, review_tier); body: compounds measured (links), measurements table (property, value, unit, method, condition summary, page) and observations.
- `Compounds/<name>.md` (KG compounds; merge with DFT/loop data by InChIKey when available): frontmatter (type: compound, smiles, inchikey, pubchem_cid, skeleton, E2_eV, dE_bind_kcal, f_v2, o2_margin_V when known, source: kg|reference|loop); body: measurements per paper with ≤200-char quote + page + [[paper]] link, our DFT values, high-level values, loop history.
- Loop candidates not in KG also get `Compounds/` notes (source: loop, arm, run, round, hypothesis, cited ids as links to the cited compounds/papers when resolvable).
- `Runs/<loop-id>.md`: per-round table with links.
- `Index.md`: overview + Dataview query examples (e.g. table of compounds sorted by f_v2; O2-feasible candidates; compounds from a paper). `README.md` in vault: how to open in Obsidian, regenerate (`make obsidian`), copyright note (only ≤200-char quotes, no full text/abstracts).
- Wikilinks [[...]] must resolve to existing note names; sanitize file names (no / : * ? " < > | #  ^ [ ]); disambiguate collisions deterministically.
Copyright: never include text beyond KG quotes; truncate quotes to 200 chars.

Tests must cover: every [[link]] resolves; quote length ≤200; frontmatter parses as YAML-ish key: value; deterministic (two runs identical); counts (one note per Paper in KG; compounds ≥ KG compounds); a loop candidate (e.g. O=C1C=CC(=O)c2nc3cnc(F)cc3nc21) has a note with f and margin; no file name collisions.
Run `make obsidian` and `make test` (CPU); report counts honestly. Write a short Korean log to .omc/research/codex-obsidian.md and print 2 sample notes' paths. Print OBSIDIAN-DONE.
