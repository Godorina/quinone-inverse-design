---
type: "compound"
smiles: "O=C1C(F)=C(F)C(=O)C(F)=C1Cl"
inchikey: "AUONGOLCSJUEQR-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.447540299113845
dE_bind_kcal: -24.474957486616944
f_v2: 1.0339042070166746
o2_margin_V: 0.21742078524457886
co2_detached: false
aliases: ["AUONGOLCSJUEQR-UHFFFAOYSA-N", "Cand AUONGOLC", "O=C1C(F)=C(F)C(=O)C(F)=C1Cl"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 1
---

# Cand AUONGOLC

Family: [[Benzoquinone (family)]]

## Structure
![[Cand AUONGOLC.png]]
![[Cand AUONGOLC.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand AUONGOLC + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 1: f=1.1721632945351486, margin=0.21742078524457886, PubChem CID=None
  - Hypothesis: D08 (F4-BQ) is f-positive with margin 0.178 and no detachment. D14 (Cl4) has a higher margin of 0.346 but lower f. A single Cl swap on the F4 scaffold should keep most of the F4 f value while gaining some margin. It tests whether a small amount of Cl is a favorable trade-off. Because D07 shows Cl-bearing BQs can have f above 1, I expect f to stay above 1.
  - Cited IDs: D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], D07: [[2,6-dichloro-p-benzoquinone]], K057: [[tetrachloro-p-benzoquinone]], K021: [[tetrachloro-p-benzoquinone]]
