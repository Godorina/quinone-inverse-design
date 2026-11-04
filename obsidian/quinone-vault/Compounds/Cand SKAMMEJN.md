---
type: "compound"
smiles: "O=C1C(F)=C(F)C(=O)C(Cl)=C1Cl"
inchikey: "SKAMMEJNGMSJPB-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.500848498569783
dE_bind_kcal: -23.016150386859948
f_v2: 0.7611312421084122
o2_margin_V: 0.2707289847005172
co2_detached: false
aliases: ["Cand SKAMMEJN", "O=C1C(F)=C(F)C(=O)C(Cl)=C1Cl", "SKAMMEJNGMSJPB-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 1
---

# Cand SKAMMEJN

Family: [[Benzoquinone (family)]]

## Structure
![[Cand SKAMMEJN.png]]
![[Cand SKAMMEJN.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand SKAMMEJN + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 1: f=0.8866972429642604, margin=0.2707289847005172, PubChem CID=None
  - Hypothesis: D08 (F4) has a good margin of 0.178 and f=1.03, with bind -24.3. D07 shows that Cl pairs keep binding strong (-25.8). A mixed F2Cl2 BQ may combine the F-derived margin with the Cl-derived binding and reach f>=2. D14 (Cl4) lost f to a weaker bind (-21.8), so the Cl count is held at two.
  - Cited IDs: D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D07: [[2,6-dichloro-p-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], K029: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
