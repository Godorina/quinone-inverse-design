---
type: "compound"
smiles: "O=C1C(=O)c2c(F)cccc2-c2cccc(F)c21"
inchikey: "DNSPKDJMYHQLGP-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.1098441738017897
dE_bind_kcal: -27.330049208705844
f_v2: 0.7894770407659466
o2_margin_V: -0.12027534006747631
co2_detached: false
aliases: ["Cand DNSPKDJM", "DNSPKDJMYHQLGP-UHFFFAOYSA-N", "O=C1C(=O)c2c(F)cccc2-c2cccc(F)c21"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 2
---

# Cand DNSPKDJM

Family: [[Phenanthrenequinone]]

## Structure
![[Cand DNSPKDJM.png]]
![[Cand DNSPKDJM.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand DNSPKDJM + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 2: f=1.1213514315336497, margin=-0.12027534006747631, PubChem CID=None
  - Hypothesis: Distal F far from the dione raised the D15 margin only partly. Placing F ortho to the dione-bearing carbons puts the inductive effect nearer the carbonyls, which should raise the reduction potential and margin more per F, as the dione-ring halogens did in D13 (+0.28). D15's binding of -27.9 gives headroom for some loss. Avoided CN, NH2 and OH. Risk: F near the carbonyls may disturb the CO2 adduct geometry and lower f.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D12: [[anthraquinone]], K117: [[9,10-Phenanthrenequinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
