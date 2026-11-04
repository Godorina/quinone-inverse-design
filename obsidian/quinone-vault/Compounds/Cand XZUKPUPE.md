---
type: "compound"
smiles: "O=C1C=C(F)C(=O)C(F)=C1F"
inchikey: "XZUKPUPEYNAPPU-UHFFFAOYSA-N"
pubchem_cid: 21282859
skeleton: "Benzoquinone"
E2_eV: -2.2985894742092317
dE_bind_kcal: -26.2686938762171
f_v2: 1.0911483807952402
o2_margin_V: 0.06846996033996566
co2_detached: false
aliases: ["Cand XZUKPUPE", "O=C1C=C(F)C(=O)C(F)=C1F", "XZUKPUPEYNAPPU-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-151304", "loop-20261103-031133"]
arm: "random"
run: "loop-20261103-031133"
round: 3
---

# Cand XZUKPUPE

Family: [[Benzoquinone (family)]]

## Structure
![[Cand XZUKPUPE.png]]
![[Cand XZUKPUPE.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand XZUKPUPE + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 2: f=1.305333630830766, margin=0.06846996031212349, PubChem CID=None
  - Hypothesis: D08 (F4) has f=1.03, margin 0.178 and no detachment. D07, with two ring H atoms, has the higher f of 1.24. Removing one F leaves a trifluoro-BQ with one H, to test whether an open ring site raises f toward D07's level while F keeps the margin above 0.15. Heavier halogenation lowered f (D14, D11), so I expect f to rise as halogen count falls.
  - Cited IDs: D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D07: [[2,6-dichloro-p-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
- [[loop-20261103-031133]], random, round 3: f=1.0911483807952402, margin=0.06846996033996566, PubChem CID=21282859
  - Hypothesis: B0 random edit
  - Cited IDs: none
