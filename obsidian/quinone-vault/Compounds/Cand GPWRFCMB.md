---
type: "compound"
smiles: "O=C1C(Br)=CC(=O)C(Cl)=C1Cl"
inchikey: "GPWRFCMBQARQFA-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.4896577891825493
dE_bind_kcal: -23.42948459307749
f_v2: 0.8514696144310947
o2_margin_V: 0.25953827531328333
co2_detached: false
aliases: ["Cand GPWRFCMB", "GPWRFCMBQARQFA-UHFFFAOYSA-N", "O=C1C(Br)=CC(=O)C(Cl)=C1Cl"]
source: "loop"
runs: ["loop-20261031-222906", "loop-20261102-003356"]
arm: "random"
run: "loop-20261102-003356"
round: 2
---

# Cand GPWRFCMB

Family: [[Benzoquinone (family)]]

## Structure
![[Cand GPWRFCMB.png]]
![[Cand GPWRFCMB.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand GPWRFCMB + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 3: f=0.9718174958534919, margin=0.2604260587375786, PubChem CID=None
  - Hypothesis: The trihalo BQ with one open C-H (2,3-Cl2-5-F) was the best margin/f balance so far (0.157, 1.17). Replacing F with Br should raise the margin further (D11 Br4 had 0.462) and give some room above 0.15. Only one Br is used, since D11 shows that Br4 collapses binding (-19.2, f 0.28). This tests whether the margin can be gained with a heavier halogen while the open C-H keeps binding. It is a direction that raised the margin; Br is limited to one to avoid the f drop.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D11: [[Bromanil]], D14: [[tetrachloro-p-benzoquinone]], K058: [[Bromanil]], K055: [[2,6-dichloro-p-benzoquinone]]
- [[loop-20261102-003356]], random, round 2: f=0.9778017407941888, margin=0.25953827531328333, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
