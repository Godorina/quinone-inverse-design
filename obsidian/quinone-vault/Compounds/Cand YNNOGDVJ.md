---
type: "compound"
smiles: "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1Cl"
inchikey: "YNNOGDVJNHDUFX-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.5334763675408962
dE_bind_kcal: -23.27884814961905
f_v2: 0.9510821440076296
o2_margin_V: 0.30335685367163023
co2_detached: false
aliases: ["Cand YNNOGDVJ", "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1Cl", "YNNOGDVJNHDUFX-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-222906", "loop-20261102-003356"]
arm: "random"
run: "loop-20261102-003356"
round: 1
---

# Cand YNNOGDVJ

Family: [[Benzoquinone (family)]]

## Structure
![[Cand YNNOGDVJ.png]]
![[Cand YNNOGDVJ.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand YNNOGDVJ + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 1: f=1.0483942639768593, margin=0.30335685367163023, PubChem CID=None
  - Hypothesis: D14 (chloranil) has a large margin (0.346) but f is only 0.72 because binding is weak (-21.8). Replacing one Cl with the smaller F should relieve crowding and strengthen binding, as seen for D08 (-24.3) and D07 (-25.8). This should keep the margin above 0.15 and raise f. D11 (Br4) shows that bulkier halogens lower f (0.28), so the change goes to smaller halogens.
  - Cited IDs: D14: [[tetrachloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D07: [[2,6-dichloro-p-benzoquinone]], D11: [[Bromanil]], K057: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
- [[loop-20261102-003356]], random, round 1: f=1.0483942645583793, margin=0.30335685367163023, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
