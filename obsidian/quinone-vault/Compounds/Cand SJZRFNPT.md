---
type: "compound"
smiles: "O=C1C(F)=C(Cl)C(=O)C=C1Cl"
inchikey: "SJZRFNPTPXVJLK-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.4110272306818157
dE_bind_kcal: -24.83210491417637
f_v2: 1.0224376926430854
o2_margin_V: 0.1809077168125497
co2_detached: false
highlevel_flags: []
aliases: ["Cand SJZRFNPT", "O=C1C(F)=C(Cl)C(=O)C=C1Cl", "SJZRFNPTPXVJLK-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-222906", "loop-20261102-003356"]
arm: "random"
run: "loop-20261102-003356"
round: 2
---

# Cand SJZRFNPT

Family: [[Benzoquinone (family)]]

## Structure
![[Cand SJZRFNPT.png]]
![[Cand SJZRFNPT.xyz]]
Geometry: ωB97M-V/def2-TZVPD

### CO2 adduct (Q²⁻·CO₂)
![[Cand SJZRFNPT + CO2.xyz]]

## Literature measurements and observations

## High-level
- highlevel: E2_V=-1.3532587662049274; dG_bind_1M_kcal=-8.416005078553548; O2_margin_V=-0.12325876620492737; flags=[]

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 3: f=1.1769613437647524, margin=0.18093251797181953, PubChem CID=None
  - Hypothesis: The closest result so far was a trihalo BQ with two Cl and one F (f 1.17, margin 0.157, bind -25.0). Moving Cl from 2,6 to 2,5 kept f near 1.10 and bind -25.3 with no detachment. That points to F added on a 2,5-Cl2 core as a promoted direction. One F should lift the margin above 0.15 and keep the one open C-H, which limits the binding loss seen with fully substituted rings (D14, D11). K020 reports strong dichloro-BQ binding and K084 shows F-BQ adducts. I avoided CN (all detached) and NH2/OH (lowered f). Reaching f>=2 is unlikely, but this tests whether the 2,5 geometry adds binding.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K020: [[2,7-dichloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]]
- [[loop-20261102-003356]], random, round 2: f=1.180772491317112, margin=0.1809077168125497, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
