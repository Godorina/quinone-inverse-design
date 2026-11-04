# Codex task: resolve structures for the 119 compound notes still without SMILES

List of note names without a Structure section: /home/hgpark/.claude/jobs/95675482/tmp/nostruct.txt (copy it into .omc/research/ for reference).
Example: "benzodithiophene quinone (BDT-Q)" (KG, paper Abdinejad Angew 2024) has no structure, but our reference X02 "benzodithiophene-4,8-dione" (InChIKey SIUXRPJY…, DFT done) is the same molecule — they must merge.
Rules: ponytail + TDD (NEW test file only; add to Makefile test), no commits, no GPU/LLM. Network only PubChem PUG REST, cached (onto/data/pubchem_name_cache.json), ≤4 req/s.

Resolution order in export.py (stop at first hit), record :
1. "reference-name": exact/normalized match against our own reference names and aliases: dft/runs/ref_set JSON sources, onto/phase_4b_extend/reference_expansion.csv (name + note e.g. "BDT-Q monomer"), smiles_proposals.csv (compound column), alherz2022_table1.csv. Include abbreviations in parentheses (BDT-Q, AQ, NQ, DDQ, PAQ…) and the part before the parenthesis.
2. "pubchem-name (unverified)": PubChem lookup on normalized variants: fix common misspellings (naptho→naphtho, anthra-quinone→anthraquinone), strip "(cpd-m0xx)"/"(…)" suffixes, try the parenthesized abbreviation only if it is an unambiguous chemical name, p-/o- ↔ 1,4-/1,2- locant forms (p-benzoquinone, o-naphthoquinone), "9,10-" defaults for anthraquinone.
3. Keep the same guards as before (skip polymers/composites/ions/metal complexes/"derivative" without position; must be a quinone by loop.t0; single CID or title match).
Then merge by InChIKey as already implemented, so e.g. BDT-Q gets the DFT structure + CO2 adduct 3D.
Write .omc/research/unresolved_names.md listing remaining unresolved names with reason (so a human can fix them).
Tests: BDT-Q KG note merges with X02 and has '## Structure' with DFT geometry; misspelling normalization unit test; materials still skipped; links resolve; deterministic (cache-only rerun).
Run make obsidian + phase 9 tests. Do NOT sync to Mac. Append short Korean log with counts (resolved by step, remaining) to .omc/research/codex-obsidian.md. Print NAMES-DONE.
