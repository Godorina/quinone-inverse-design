---
type: "compound"
smiles: "O=C1C=C(Cl)C(=O)C(Cl)=C1Br"
inchikey: "DKGNGCSVUFAJFC-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.483931372878407
dE_bind_kcal: -22.983638702970524
f_v2: 0.6946703910068678
o2_margin_V: 0.25381185900914094
co2_detached: false
aliases: ["Cand DKGNGCSV", "DKGNGCSVUFAJFC-UHFFFAOYSA-N", "O=C1C=C(Cl)C(=O)C(Cl)=C1Br"]
source: "loop"
runs: ["loop-20261031-222906", "loop-20261101-111405-random-biased-fonly"]
arm: "random"
run: "loop-20261101-111405-random-biased-fonly"
round: 2
---

# Cand DKGNGCSV

Family: [[Benzoquinone (family)]]

## Structure
![[Cand DKGNGCSV.png]]
![[Cand DKGNGCSV.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand DKGNGCSV + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 1: f=0.8330474930005305, margin=0.25381185897201775, PubChem CID=None
  - Hypothesis: D07 (2,6-dichloro-BQ) has the highest f (1.24) but its O2 margin is only 0.097. Adding halogens raised the margin in D08 (F4, 0.178, f 1.03) and D14 (Cl4, 0.346, f 0.72). D11 (Br4) raised it further (0.462) but f fell to 0.28, so heavy halogenation costs binding. A single Br is a partial step. It should lift the margin above 0.15 while keeping more of the CO2 binding (D07 bind -25.8) than D14 or D11 did. Promoted: halogenated BQ with no CN, since D07 and D08 raised f and none of the halogenated BQs detached CO2. Avoided: CN (D03, D06, D10 detached CO2) and OH or NH2, which lowered f in D01, D04 and D05. Risk: f may drop toward D14 as halogens are added.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D11: [[Bromanil]], D14: [[tetrachloro-p-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]], K058: [[Bromanil]], K057: [[tetrachloro-p-benzoquinone]]
- [[loop-20261101-111405-random-biased-fonly]], random, round 2: f=0.8330474806363505, margin=0.25381185900914094, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
