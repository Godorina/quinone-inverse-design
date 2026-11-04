---
type: "compound"
smiles: "O=C1C(=O)c2c(F)cccc2-c2c(F)cccc21"
inchikey: "ZVYRXFLPQRSQDX-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.171409084205928
dE_bind_kcal: -26.85966688439194
f_v2: 0.849519674634483
o2_margin_V: -0.05871042966333784
co2_detached: false
aliases: ["Cand ZVYRXFLP", "O=C1C(=O)c2c(F)cccc2-c2c(F)cccc21", "ZVYRXFLPQRSQDX-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 3
---

# Cand ZVYRXFLP

Family: [[Phenanthrenequinone]]

## Structure
![[Cand ZVYRXFLP.png]]
![[Cand ZVYRXFLP.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand ZVYRXFLP + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 3: f=1.1452077535254936, margin=-0.05871042966333784, PubChem CID=None
  - Hypothesis: D15 has the strongest CO2 binding (-27.9, f 1.09) but a margin of -0.196. Distal F at 2,7, 3,6 and 1,8 and four F at 2,3,6,7 raised the margin only to between -0.05 and -0.12 while losing some f. A bay-region F at 4,5 is a different electronic position, conjugated through the biaryl bond, and it twists the biphenyl. That may shift the LUMO and the margin more than the earlier placements. The dione-adjacent positions 1,8 kept bind -27.3, so the o-quinone binding mode should hold. K117 reports a very large CO2 adduct constant for PQ. This is a lower-confidence exploration of the PQ core; it avoids CN, NH2 and OH.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D12: [[anthraquinone]], D13: [[2,3-dichloro-p-naphthoquinone]], K117: [[9,10-Phenanthrenequinone]], K097: [[9,10-Phenanthrenequinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
