---
type: "compound"
smiles: "O=C1C(F)=C(F)C(=O)c2nccnc21"
inchikey: "XIIXRHAKYWSWNT-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.3836501737807825
dE_bind_kcal: -24.314601928993937
f_v2: 0.7713008817608387
o2_margin_V: 0.1535306599115165
co2_detached: false
aliases: ["Cand XIIXRHAK", "O=C1C(F)=C(F)C(=O)c2nccnc21", "XIIXRHAKYWSWNT-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 1
---

# Cand XIIXRHAK

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand XIIXRHAK.png]]
![[Cand XIIXRHAK.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand XIIXRHAK + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 1: f=0.7713008817608387, margin=0.1535306599115165, PubChem CID=None
  - Hypothesis: D05 has the highest f (1.09) but O2 margin is -0.054. D09 shows ring fluorination gives margin +0.178 with f=0.86 and no detachment (K084 F4-BQ binds CO2 strongly, K123 quinoxalinedione binds). Adding F2 to the pyrazine-fused quinone should lift margin above 0.15 while the N-heteroaryl scaffold keeps strong binding, so f may rise toward 2. Avoids CN (D03/D07/D12 detached) and amino/OH (D01/D04/D06 f<-1).
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D09: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]]
