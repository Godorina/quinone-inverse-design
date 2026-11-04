---
type: "compound"
smiles: "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1Br"
inchikey: "DUASVMAXEPQZIW-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.563467773453735
dE_bind_kcal: -22.419331603423274
f_v2: 0.7856398171280167
o2_margin_V: 0.333348259584469
co2_detached: false
aliases: ["Cand DUASVMAX", "DUASVMAXEPQZIW-UHFFFAOYSA-N", "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1Br"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 1
---

# Cand DUASVMAX

Family: [[Benzoquinone (family)]]

## Structure
![[Cand DUASVMAX.png]]
![[Cand DUASVMAX.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand DUASVMAX + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 1: f=0.876498314109975, margin=0.333348259584469, PubChem CID=None
  - Hypothesis: D07 (2,6-dichloro-BQ) is the best-f parent (f=1.24, bind -25.8, no detachment) but its O2 margin is only 0.097. Ring halogenation raised the margin: D08 (F4) 0.178, D14 (Cl4) 0.346, D11 (Br4) 0.462. Heavier halogens cost binding, though (f fell from 1.24 to 0.72 with Cl4 and to 0.28 with Br4), so I add one Br and one F instead of filling the ring with a single heavy halogen. Br should lift the margin above 0.15. F is small and kept strong CO2 binding in D08 (bind -24.3, f=1.03), so it should limit the binding loss. K084 and K029 report CO2 adducts for tetrafluoro-BQ and chloranil, and K058 and K055 show that halogenated BQs stay reducible. I avoided CN (D03, D06, D10 all detached CO2) and NH2/OH (D01, D02, D04, D05 lowered f). This is a promoted-direction test: a mixed F/Cl/Br benzoquinone should combine D07's binding with a margin of at least 0.15. Risk: f may still stay below 2, since no reference reached it, and the margin gain may not offset the binding loss seen from D07 to D14 and D11. DFT will decide.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D11: [[Bromanil]], D14: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]], K058: [[Bromanil]], K029: [[tetrachloro-p-benzoquinone]]
