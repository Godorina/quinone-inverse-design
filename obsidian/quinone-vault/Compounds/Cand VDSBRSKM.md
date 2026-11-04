---
type: "compound"
smiles: "O=C1C(=O)c2cc(Cl)ccc2-c2ccccc21"
inchikey: "VDSBRSKMXYUDTA-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.124435788125222
dE_bind_kcal: -26.93681221527399
f_v2: 0.7166879678642599
o2_margin_V: -0.10568372574404394
co2_detached: false
aliases: ["Cand VDSBRSKM", "O=C1C(=O)c2cc(Cl)ccc2-c2ccccc21", "VDSBRSKMXYUDTA-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 2
---

# Cand VDSBRSKM

Family: [[Phenanthrenequinone]]

## Structure
![[Cand VDSBRSKM.png]]
![[Cand VDSBRSKM.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand VDSBRSKM + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 2: f=1.044980376967729, margin=-0.10568372574404394, PubChem CID=None
  - Hypothesis: D15 (phenanthrenequinone) has f=1.09 and bind -27.9 kcal/mol, the strongest CO2 binding, but its margin is -0.196. Dichlorination (2,7) raised the margin to -0.017 but lowered f to 0.82. Chlorinating only one outer ring should cost less f, since the first Cl gives most of the benefit per halogen. Margin should rise by about half of the dichloro gain, which probably still falls short of 0.15. It tests the f/margin trade-off on the ortho-quinone core, and the margin is the risk here.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D13: [[2,3-dichloro-p-naphthoquinone]], D12: [[anthraquinone]], K117: [[9,10-Phenanthrenequinone]], K038: [[9,10-Phenanthrenequinone]]
