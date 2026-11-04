---
type: "compound"
smiles: "O=C1C(=O)c2ccc(Cl)cc2-c2cc(Cl)ccc21"
inchikey: "QMANTEXNUQSCLC-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.1839387339975747
dE_bind_kcal: -25.552392058978484
f_v2: 0.4875495132425652
o2_margin_V: -0.046180779871691335
co2_detached: false
aliases: ["Cand QMANTEXN", "O=C1C(=O)c2ccc(Cl)cc2-c2cc(Cl)ccc21", "QMANTEXNUQSCLC-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 2
---

# Cand QMANTEXN

Family: [[Phenanthrenequinone]]

## Structure
![[Cand QMANTEXN.png]]
![[Cand QMANTEXN.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand QMANTEXN + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 2: f=0.7973500303569029, margin=-0.046180779871691335, PubChem CID=None
  - Hypothesis: Ring Cl raised margin in D13 over D12 (+0.28). Cl at the 3,6 positions, para to the biaryl bond and meta to the carbonyl-bearing carbon, is a different electronic placement from the tested 2,7 pattern, and should lift the margin from -0.196 while keeping most of D15's strong binding (-27.9, f 1.09). K019 shows chlorinated quinones still bind CO2. Avoided CN and NH2/OH. Risk: margin may stay under 0.15.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D13: [[2,3-dichloro-p-naphthoquinone]], D12: [[anthraquinone]], K117: [[9,10-Phenanthrenequinone]], K019: [[2-Chloroanthraquinone]]
