# Codex task: classify loop candidates by structure (no more "Unclassified" hub)

Problem: 73 loop-only compound notes have no KG skeleton, so onto/phase_9_obsidian/export.py (lines ~167, ~267) puts them in Families/Unclassified (one giant hub in the Obsidian graph).
Rules: ponytail + TDD; new test file onto/phase_9_obsidian/tests/test_export_family.py (add to Makefile test); don't edit existing tests; no network/GPU/LLM; no commits.

Fix: add `skeleton_from_smiles(smiles)` (RDKit, .venv has it) used when KG skeleton is missing, returning the KG's own vocabulary so loop molecules join existing hubs:
- find the quinone ring (6-ring, two exocyclic C=O at 1,2 or 1,4; reuse loop.py logic if importable cleanly, else minimal copy);
- fused ring system containing it: if any ring atom in that system is N, S or ring O → "HeterocyclicQuinone";
- else carbocyclic ring count of the fused system: 1 → "Benzoquinone", 2 → "Naphthoquinone", 3 with 1,2-dione → "Phenanthrenequinone", 3 → "Anthraquinone", otherwise "OtherQuinoid".
Check the exact skeleton strings used in kg.ttl (Families/ currently has "Anthraquinone (family)", "Benzoquinone (family)", "Naphthoquinone", "Phenanthrenequinone", "HeterocyclicQuinone", "OtherQuinoid", "NotReported") and return those exact values.
Also put `skeleton:` in frontmatter for these notes. Reference-only molecules keep their explicit class (quinoxaline-dione etc.) as family but ALSO get `skeleton` from structure; add a line "Skeleton: [[<skeleton hub>]]" so finer class hubs link into the main skeleton hubs (graph: class hub → skeleton hub).
Tests: BQ/2,6-diCl-BQ → Benzoquinone; NQ → Naphthoquinone; AQ → Anthraquinone; PQ → Phenanthrenequinone; quinoxaline-5,8-dione and O=C1C=CC(=O)c2nc3cnc(F)cc3nc21 and BDT-Q → HeterocyclicQuinone; after export no compound note links to Unclassified (Unclassified hub absent or empty); all links resolve.
Run `make obsidian`, the phase_9 tests. Then sync to the Mac: `rsync -a --exclude .omc --exclude .obsidian obsidian/quinone-vault/ macbook:Documents/quinone-vault/ --delete-after --filter='protect .obsidian/'` — NO: do not sync; I will. Append a short Korean note to .omc/research/codex-obsidian.md with counts per family. Print FAMILY-DONE.
