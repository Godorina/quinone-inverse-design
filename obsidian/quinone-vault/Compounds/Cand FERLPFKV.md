---
type: "compound"
smiles: "O=C1C(=O)c2cc(F)ccc2-c2ccc(F)cc21"
inchikey: "FERLPFKVKSIZKW-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.1429347121292843
dE_bind_kcal: -26.690916993273248
f_v2: 0.7024370837200117
o2_margin_V: -0.08718480173998167
co2_detached: false
aliases: ["Cand FERLPFKV", "FERLPFKVKSIZKW-UHFFFAOYSA-N", "O=C1C(=O)c2cc(F)ccc2-c2ccc(F)cc21"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 1
---

# Cand FERLPFKV

Family: [[Phenanthrenequinone]]

## Structure
![[Cand FERLPFKV.png]]
![[Cand FERLPFKV.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand FERLPFKV + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 1: f=1.0217097469227843, margin=-0.08718480173998167, PubChem CID=None
  - Hypothesis: Phenanthrenequinone D15 has the strongest binding (-27.9) and f=1.09, but its margin is -0.196. Halogenation raised the margin in D13 over D12 (+0.28) and in D08. Two F on the biphenyl rings should raise the margin toward 0.15 or more while retaining the o-quinone binding mode. Substitution is kept off the dione ring to avoid weakening binding. Risk: ring-remote F may not shift the margin enough. Amino and hydroxy are avoided because they lowered f in D01, D02, D04 and D05.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D13: [[2,3-dichloro-p-naphthoquinone]], D12: [[anthraquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K117: [[9,10-Phenanthrenequinone]], K038: [[9,10-Phenanthrenequinone]]
