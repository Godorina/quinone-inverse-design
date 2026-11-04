---
type: "compound"
smiles: "O=C1C(=O)c2cc(Cl)ccc2-c2ccc(Cl)cc21"
inchikey: "FQIUZIVUKRTTMT-UHFFFAOYSA-N"
skeleton: "Phenanthrenequinone"
E2_eV: -2.2127937479256716
dE_bind_kcal: -25.36217159603197
f_v2: 0.5250320991642008
o2_margin_V: -0.017325765943594362
co2_detached: false
aliases: ["Cand FQIUZIVU", "FQIUZIVUKRTTMT-UHFFFAOYSA-N", "O=C1C(=O)c2cc(Cl)ccc2-c2ccc(Cl)cc21"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 1
---

# Cand FQIUZIVU

Family: [[Phenanthrenequinone]]

## Structure
![[Cand FQIUZIVU.png]]
![[Cand FQIUZIVU.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand FQIUZIVU + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 1: f=0.8173362219496334, margin=-0.017325765943594362, PubChem CID=None
  - Hypothesis: D15 (phenanthrenequinone) has f=1.09, the best non-halogenated f, but its margin is -0.196. Chlorination raised the margin of AQ-type and NQ-type cores by about 0.28 (D12 -0.191 to D13 0.089). Chlorinating both outer rings should bring D15's margin up substantially while retaining the ortho-quinone geometry that favors f. NH2 and OH are avoided because they lowered f in D01, D04 and D05.
  - Cited IDs: D15: [[9,10-Phenanthrenequinone]], D13: [[2,3-dichloro-p-naphthoquinone]], D12: [[anthraquinone]], K117: [[9,10-Phenanthrenequinone]], K038: [[9,10-Phenanthrenequinone]]
