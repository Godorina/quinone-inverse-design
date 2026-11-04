---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc3nc(F)c(F)nc3nc21"
inchikey: "VHKSHSDHWXAPIT-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.497457505160564
dE_bind_kcal: -23.7367678565532
f_v2: 0.9723877637495733
o2_margin_V: 0.26733799129129787
co2_detached: false
aliases: ["Cand VHKSHSDH", "O=C1C=CC(=O)c2nc3nc(F)c(F)nc3nc21", "VHKSHSDHWXAPIT-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 3
---

# Cand VHKSHSDH

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand VHKSHSDH.png]]
![[Cand VHKSHSDH.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand VHKSHSDH + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 3: f=0.9723877637495733, margin=0.26733799129129787, PubChem CID=None
  - Hypothesis: The tetra-aza core gave the best margin and f pair so far (0.18, 1.07). Remote F2 on the far pyrazine adds withdrawal, as in D19 where pyrazine-side F2 raised f from 0.86 to 0.97. Fluorination far from the carbonyls should keep the CO2 binding at the quinone O atoms (K084 shows F-quinones bind CO2). Tests whether margin can grow without the f loss seen for quinone-ring halogens. Avoids CN.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], D09: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], K124: [[2,3-diphenylquinoxaline-5,8-dione]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
