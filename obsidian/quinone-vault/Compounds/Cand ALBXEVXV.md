---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc3cc(F)c(F)cc3nc21"
inchikey: "ALBXEVXVOXRGPC-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.2116650895704253
dE_bind_kcal: -27.515869778926998
f_v2: 1.1864464765299234
o2_margin_V: -0.0184544242988407
co2_detached: false
aliases: ["ALBXEVXVOXRGPC-UHFFFAOYSA-N", "Cand ALBXEVXV", "O=C1C=CC(=O)c2nc3cc(F)c(F)cc3nc21"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 2
---

# Cand ALBXEVXV

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand ALBXEVXV.png]]
![[Cand ALBXEVXV.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand ALBXEVXV + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 2: f=1.1864464765299234, margin=-0.0184544242988407, PubChem CID=None
  - Hypothesis: Larger aromatic substituents on the pyrazine (D19 phenyl f 0.86, D14 anisyl f 0.97) kept f high and left binding at -25 to -27 kcal/mol, so extending conjugation on that side does not hurt binding. Fusing a benzo ring keeps the N atoms next to the carbonyl and adds electron delocalisation, which should raise f through stronger binding. The distal F2 sits far from the quinone carbonyls, so it should add margin without removing the f gain, unlike the quinone-ring F that cut f in D05 to D09-type edits. Test of whether remote fluorination can lift margin from about 0 to 0.15 V.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D14: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], D21: [[9,10-Phenanthrenequinone]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], K124: [[2,3-diphenylquinoxaline-5,8-dione]]
