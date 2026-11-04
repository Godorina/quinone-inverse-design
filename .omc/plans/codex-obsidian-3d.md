# Codex task: structure images + interactive 3D in Obsidian compound notes

User wants: open a compound note → see its structure in 3D. Viewer = Obsidian community plugin ChemRender3D (Mol*): embedding a `.xyz` file with `![[file.xyz]]` renders an interactive 3D viewer; it also renders ```3dmol code blocks containing SMILES. The user installs the plugin; you only write files.
Rules: ponytail + TDD (NEW test file onto/phase_9_obsidian/tests/test_export_structures.py; add to Makefile test), no commits, no GPU/LLM. Network allowed ONLY for PubChem PUG REST name lookup in step 2, cached, rate-limited (≤4 req/s), reuse onto/phase_8_design/pubchem.py style/cache conventions.

1. For every compound note WITH a SMILES (currently 94):
   - `Structures/<note name>.xyz`: prefer our DFT-optimized neutral geometry (low-level `states.Q.xyz` in dft/runs/ref_set/<KEY>.json or the loop round JSON; if a high-level `Q_tz` result has `xyz_final`, prefer that and say which in a comment line of the xyz). Else RDKit ETKDGv3(seed 0)+MMFF from SMILES, marked "RDKit/MMFF (not DFT)".
   - `Structures/<note name>.png`: RDKit 2D depiction (300x300).
   - In the note add `## Structure` near the top: `![[<name>.png]]`, then `![[<name>.xyz]]`, then one line: geometry source (DFT B3LYP/def2-SVP, ωB97M-V/def2-TZVPD, or RDKit/MMFF).
   - For DFT-computed molecules also add the CO2 adduct geometry `Structures/<name> + CO2.xyz` (lowest-energy attached adduct) and embed it under "CO2 adduct (Q²⁻·CO₂)".
2. KG compounds WITHOUT SMILES (169): try PubChem name → CID → IsomericSMILES, conservatively: skip names with poly/polymer/composite/nanotube/resin/salt/complex/ion/“-based”/brackets of materials; accept only if exactly one CID or the top CID's title matches the name case-insensitively after removing hyphens/spaces; must parse in RDKit and be a quinone per loop.t0 (else skip). Cache to onto/data/pubchem_name_cache.json. Frontmatter: smiles, smiles_source: "pubchem-name (unverified)". Then step 1 applies (RDKit/MMFF geometry).
   Report counts: resolved / skipped(reason).
3. Keep determinism (except first network fill; afterwards cache-only), keep links resolving (xyz/png embeds count), keep .obsidian preserved, Structures/ regenerated like other generated folders.
4. Vault README: add "Install community plugin ChemRender3D to see 3D; PNG shows without plugins".
Run `make obsidian`, phase 9 tests. Do NOT sync to the Mac. Short Korean log appended to .omc/research/codex-obsidian.md. Print STRUCT-DONE.
