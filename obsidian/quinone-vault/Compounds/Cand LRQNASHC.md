---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc(Cl)c(Cl)nc21"
inchikey: "LRQNASHCYSQENE-UHFFFAOYSA-N"
pubchem_cid: 14067871
skeleton: "HeterocyclicQuinone"
E2_eV: -2.4038832029355137
dE_bind_kcal: -24.47713880735577
f_v2: 0.8889792556992493
o2_margin_V: 0.17376368906624773
co2_detached: false
aliases: ["Cand LRQNASHC", "LRQNASHCYSQENE-UHFFFAOYSA-N", "O=C1C=CC(=O)c2nc(Cl)c(Cl)nc21"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 2
---

# Cand LRQNASHC

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand LRQNASHC.png]]
![[Cand LRQNASHC.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand LRQNASHC + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 2: f=0.8889792556992493, margin=0.17376368906624773, PubChem CID=14067871
  - Hypothesis: Quinone-ring Cl2 on D05 gave margin 0.22 but f fell to 0.65. D19 shows that pyrazine-side substituents retain f (0.86 to 0.97 with F2). Moving the Cl2 off the quinone ring onto the pyrazine ring should keep the bound CO2 geometry at the quinone O atoms and still withdraw electrons. Cl gave a larger margin gain than F in the D05 pair, so this may clear 0.15 V while f stays near D05 (about 1.0). Two Cl are used because D08 to D18 to D13 shows f drops as halogen count grows.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], D08: [[2,6-dichloro-p-benzoquinone]], D18: [[tetrachloro-p-benzoquinone]], K008: [[2,3-dichloro-p-naphthoquinone]], K056: [[2,3-dichloro-p-naphthoquinone]]
