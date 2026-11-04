# Codex task: check this workflow outline against the CURRENT code (read-only)

Do not edit any file except the output. No runs except CPU dry-runs (`closed_loop.py --dry-run` into a temp dir is ok).
Draft outline to verify (fix anything wrong, add missing gates/files, keep it short):

0. Inputs: xlsx 38 papers → onto/phase_3_corpus (PDF/text)
1. Extraction: qextract/pipeline.py extract() — LLM extracts records, checker.py verifies quote/value/unit vs page text, retries ≤3 → records_final
2. KG: phase_2 schema (quinone.ttl + SHACL shapes) → phase_5_build/build.py → kg.ttl (+PubChem CID)
3. Reference DFT: run_set.py (smiles_proposals.csv 15 + reference_expansion.csv 6 = 21) → states Q, Q•−, Q2−, Q2−·CO2 per carbonyl site (B3LYP-D3BJ/def2-SVP/SMD MeCN) → summarize: attached adducts only → line fit → lines.json v1(n=12)/v2(n=18)
4. Context: generate.context() D rows (DFT, f, O2 margin) + K rows (KG) + extra refs
5. Loop round r (3 rounds × 5), config.json saved / checked on resume:
   5a LLM arm: loop_prompt (goal + rules + D/K + history) → Claude CLI → proposals (SMILES, parent, cited ids, hypothesis); refill up to 3 attempts
   5b random arm: parents = top-5 O2-feasible by f; edit() add/replace/remove/move/aza
   5c filter: t0 (6-ring sp2 quinone, neutral total charge, no radical/isotope, elements, ≤30 heavy) → in_domain → check (citations, parent, duplicates vs refs/KG/Alherz/seen) → PubChem lookup (+ optional reject known)
   5d DFT evaluate (run_set --input) → score: f=(a·E2+b−ΔE)/σ, margin=E_O2−E2, success f≥2 & margin≥0.15 & attached
   5e record: completed.json + ledger.jsonl (with line used) + report.md → history to next prompt
6. Compare: closed_loop --compare (refuses different lines)
7. High level: highlevel.py SETS v1/v2 (explicit sources) → ωB97M-V/def2-TZVPD opt + SVP freq (mRRHO) → G, E2 vs Fc (4.417 eV), O2 margin vs exp −1.23 V, ΔG 1 M (−1.894), flags (failed/not_converged/imag/co2_detached) → chloranil vs experiment

Write `.omc/research/codex-workflow-review.md` (Korean, ≤50 lines): corrected outline with file:line refs per step, list of what you changed in the outline and why. Print WORKFLOW-DONE.
