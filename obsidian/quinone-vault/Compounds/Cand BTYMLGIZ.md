---
type: "compound"
smiles: "O=C1C(=O)c2cc(F)c(F)cc2-c2cc(F)c(F)cc21"
inchikey: "BTYMLGIZBYPMAV-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.177410533343552
dE_bind_kcal: -25.922994056713122
f_v2: 0.5802395742630122
o2_margin_V: -0.05270898052571393
co2_detached: false
aliases: ["BTYMLGIZBYPMAV-UHFFFAOYSA-N", "Cand BTYMLGIZ", "O=C1C(=O)c2cc(F)c(F)cc2-c2cc(F)c(F)cc21"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 2
---

# Cand BTYMLGIZ

Family: [[Phenanthrenequinone]]

## Structure
![[Cand BTYMLGIZ.png]]
![[Cand BTYMLGIZ.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand BTYMLGIZ + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 2: f=0.8881917261405039, margin=-0.05270898052571393, PubChem CID=None
  - Hypothesis: D15 has the strongest binding (-27.9) with no detachment, but its margin is -0.196. Two distal F (previous round) lifted the margin by about 0.11 and cost only about 1.2 kcal of binding (f 1.02). Following that promoted direction, four distal F should lift the margin by roughly 0.2 more, reaching 0.15 or higher, while the o-quinone binding mode stays intact. K117 and K084 report CO2 adducts for o-quinone and F-quinone. Avoided: CN (detached), NH2/OH (lowered f). Risk: F on the dione ring is not used; margin gain may saturate.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D12: [[anthraquinone]], D13: [[2,3-dichloro-p-naphthoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K117: [[9,10-Phenanthrenequinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
