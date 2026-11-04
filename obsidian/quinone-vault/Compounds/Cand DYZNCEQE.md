---
type: "compound"
smiles: "O=C1C(F)=C(F)C(=O)C(Cl)=C1"
inchikey: "DYZNCEQEDUXFOO-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.3730881812931712
dE_bind_kcal: -25.39666746416046
f_v2: 1.0702764691185158
o2_margin_V: 0.14296866742390524
co2_detached: false
aliases: ["Cand DYZNCEQE", "DYZNCEQEDUXFOO-UHFFFAOYSA-N", "O=C1C(F)=C(F)C(=O)C(Cl)=C1"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 3
---

# Cand DYZNCEQE

Family: [[Benzoquinone (family)]]

## Structure
![[Cand DYZNCEQE.png]]
![[Cand DYZNCEQE.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand DYZNCEQE + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 3: f=1.2460414194721385, margin=0.14296866742390524, PubChem CID=None
  - Hypothesis: D08 (F4) has margin 0.178 and f 1.03. D07 has a stronger bind (-25.8), but only 0.097 margin. A BQ with a 2,3-difluoro pair and one Cl on the opposite side, with two open C-H, mixes F-driven margin with Cl-driven binding. The open C-H sites reduce crowding at the carbonyls. Expected margin is about 0.15, bind about -25. This is a less halogenated step than the failed tetrahalo variants. The risk is that the margin falls just under 0.15.
  - Cited IDs: D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D07: [[2,6-dichloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]], K020: [[2,7-dichloro-p-benzoquinone]]
