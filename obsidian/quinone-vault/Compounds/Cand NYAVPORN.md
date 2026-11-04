---
type: "compound"
smiles: "O=C1C(=O)c2cc(F)ccc2-c2ccccc21"
inchikey: "NYAVPORNTNZVOE-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.0868843158330983
dE_bind_kcal: -27.770468309773122
f_v2: 0.8489299780331144
o2_margin_V: -0.1432351980361677
co2_detached: false
aliases: ["Cand NYAVPORN", "NYAVPORNTNZVOE-UHFFFAOYSA-N", "O=C1C(=O)c2cc(F)ccc2-c2ccccc21"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 3
---

# Cand NYAVPORN

Family: [[Phenanthrenequinone]]

## Structure
![[Cand NYAVPORN.png]]
![[Cand NYAVPORN.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand NYAVPORN + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 3: f=1.189602008313186, margin=-0.1432351980361677, PubChem CID=None
  - Hypothesis: D15 has the strongest CO2 binding (-27.9 kcal/mol) and f=1.09, but a margin of -0.196. Monochlorination lowered the margin penalty only to -0.106 and cost little f (1.04), while dichlorination lowered f to 0.82. F is the halogen that raised f in the BQ series (F2 compound 1.65 vs Cl2 1.24), so one F on the ortho-quinone core should give a similar margin gain with a smaller f cost. The margin will probably stay below 0.15. This tests whether F is better than Cl on this core.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D13: [[2,3-dichloro-p-naphthoquinone]], K117: [[9,10-Phenanthrenequinone]], K038: [[9,10-Phenanthrenequinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
