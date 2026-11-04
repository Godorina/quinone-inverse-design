---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc(F)cnc21"
inchikey: "IAOSJZVZBBNNOU-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.2587776827808748
dE_bind_kcal: -27.188696481627375
f_v2: 1.2425205841884432
o2_margin_V: 0.028658168911608772
co2_detached: false
aliases: ["Cand IAOSJZVZ", "IAOSJZVZBBNNOU-UHFFFAOYSA-N", "O=C1C=CC(=O)c2nc(F)cnc21"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 2
---

# Cand IAOSJZVZ

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand IAOSJZVZ.png]]
![[Cand IAOSJZVZ.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand IAOSJZVZ + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 2: f=1.2425205841884432, margin=0.028658168911608772, PubChem CID=None
  - Hypothesis: Two things from the data point the same way. Halogens placed on the quinone ring of D05 raised margin but lowered f (F2: 1.09 to 0.77; Cl2: 0.65). Pyrazine-ring substitution in D19 kept f high (0.86 to 0.97 with F2) and still moved margin up. A single F on the pyrazine ring should lift margin from -0.054 toward +0.05 to +0.10 while keeping the strong CO2 binding of the N-heteroaryl quinone (D05 bind -27.6; K123/K124 high binding constants). It is untested whether one F is enough to reach 0.15 V, but it tests the direction with the smallest f penalty. Avoids CN (D03/D07/D12 detached) and quinone-ring halogens that lowered f.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], D09: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], K124: [[2,3-diphenylquinoxaline-5,8-dione]]
