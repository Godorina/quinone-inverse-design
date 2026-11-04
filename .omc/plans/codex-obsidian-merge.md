# Codex task: one note per structure + small calibration guard

Rules: ponytail + TDD (NEW test files only, add to Makefile test), no commits, no GPU/LLM; network not needed (use caches).

A. onto/phase_9_obsidian/export.py — merge compounds by structure:
   - Compute InChIKey from SMILES for every compound that has a SMILES (incl. smiles_source "pubchem-name (unverified)"); fill `inchikey` frontmatter.
   - All KG/reference/loop items with the same InChIKey → ONE note. Name: prefer the reference/DFT name if any, else the most frequent KG name, ties → shortest; deterministic. Other names go into `aliases:` (so Obsidian search and [[alias]] links work) and a line "Also reported as: …".
   - All measurements/observations/DFT/high-level/loop sections merged; paper notes and run tables link to the merged note; family hubs list it once.
   - Verifier found ~10 anthraquinone notes (9,10-anthraquinone, Anthraquinone (cpd-m0xx), anthraquinone, …), BQ / p-benzoquinone / 1,4-benzoquinone, tetrachloro-BQ ×3, phendione vs 1,10-phenanthroline-5,6-dione, 9,10-phenanthrenequinone vs phenanthraquinone, Vitamin K3 vs 2-methyl-NQ, 1-NH2-AQ vs 1-aminoanthraquinone, Bromanil vs tetrabromo-BQ.
   - Names without SMILES stay separate (cannot prove identity).
   Tests: no two compound notes share an InChIKey; aliases contain the merged names; all links/embeds resolve; measurement count conserved (sum over notes == before merge); deterministic.
B. onto/phase_8_design/closed_loop.py: class lookup for the O2 calibration must not crash on an unclassifiable SMILES — reject such a proposal in the filter with reason 'unclassifiable' (test it).
Run `make obsidian` and phase 9 + calibration tests. Do NOT sync to the Mac. Append a short Korean log (note count before/after) to .omc/research/codex-obsidian.md. Print MERGE-DONE.
