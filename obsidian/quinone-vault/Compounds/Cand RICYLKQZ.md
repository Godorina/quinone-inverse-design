---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc3nc(F)cnc3nc21"
inchikey: "RICYLKQZEXDOCT-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.555180647325057
dE_bind_kcal: -22.817243121225346
f_v2: 0.8808984284286052
o2_margin_V: 0.32506113345579113
co2_detached: false
aliases: ["Cand RICYLKQZ", "O=C1C=CC(=O)c2nc3nc(F)cnc3nc21", "RICYLKQZEXDOCT-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 3
---

# Cand RICYLKQZ

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand RICYLKQZ.png]]
![[Cand RICYLKQZ.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand RICYLKQZ + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 3: f=0.8808984284286052, margin=0.32506113345579113, PubChem CID=None
  - Hypothesis: Tetra-aza D05 core gave margin 0.18 with f 1.07 and no detachment, so extra ring N is a margin lever. A single pyrazine F raised f in the D05 series (1.09 to 1.24) while moving margin up. Combining them tests whether f rises while margin stays above 0.15. Pyrazine-side halogens kept f, unlike quinone-ring halogens, which cut f (F2 0.77, Cl2 0.65). Avoids CN, which detached (D03/D07/D12). K123/K124 support strong binding in the quinoxalinedione class.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], D09: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], K124: [[2,3-diphenylquinoxaline-5,8-dione]]
