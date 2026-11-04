---
type: "compound"
smiles: "O=C1C(F)=CC(=O)C(Cl)=C1Cl"
inchikey: "UUKXSRGFRMNCGI-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.38642952530352
dE_bind_kcal: -25.03661867279149
f_v2: 1.003567992651372
o2_margin_V: 0.15631001143425394
co2_detached: false
aliases: ["Cand UUKXSRGF", "O=C1C(F)=CC(=O)C(Cl)=C1Cl", "UUKXSRGFRMNCGI-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-222906", "loop-20261102-003356"]
arm: "random"
run: "loop-20261102-003356"
round: 3
---

# Cand UUKXSRGF

Family: [[Benzoquinone (family)]]

## Structure
![[Cand UUKXSRGF.png]]
![[Cand UUKXSRGF.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand UUKXSRGF + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 2: f=1.1689033214067537, margin=0.15671608062229003, PubChem CID=None
  - Hypothesis: D07 gains margin with each halogen (D08, D14) but loses binding with heavy halogens (D14 f 0.72). A trihalo BQ with one small F and two Cl, keeping one open C-H, limits steric crowding around the carbonyls that weakened binding. D08 (F4) kept bind -24.3, and K084 shows F-BQ adducts. Expected margin around 0.2 with binding near -24. Risk: f may stay around 1.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]]
- [[loop-20261102-003356]], random, round 3: f=1.176066850010531, margin=0.15631001143425394, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
