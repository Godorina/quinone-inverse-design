---
type: "compound"
smiles: "O=C1C=C(F)C(=O)C(Cl)=C1"
inchikey: "JUEZZBCFCJSJOC-UHFFFAOYSA-N"
pubchem_cid: 101865165
skeleton: "Benzoquinone"
E2_eV: -2.263138681046443
dE_bind_kcal: -26.71826544803409
f_v2: 1.1117701848481953
o2_margin_V: 0.0330191671771769
co2_detached: false
aliases: ["Cand JUEZZBCF", "JUEZZBCFCJSJOC-UHFFFAOYSA-N", "O=C1C=C(F)C(=O)C(Cl)=C1"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 2
---

# Cand JUEZZBCF

Family: [[Benzoquinone (family)]]

## Structure
![[Cand JUEZZBCF.png]]
![[Cand JUEZZBCF.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand JUEZZBCF + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 2: f=1.1117701848481953, margin=0.0330191671771769, PubChem CID=101865165
  - Hypothesis: D08 (Cl2, f 1.04, margin 0.097) is the only benzoquinone with f above 1, and f falls as halogens are added (D18 0.63, D13 0.22, D09 0.86). The previous Cl2F2 try (f 0.76, margin 0.25) shows that mixed halogens give margin to spare, so one fewer halogen may be affordable. Swapping one Cl for F keeps two halogens, so the f penalty from halogen count is avoided. F is the stronger margin lever in D09 (0.178), and K084 shows F-quinones bind CO2. Expected margin is 0.15 V or higher with f near 1.
  - Cited IDs: D08: [[2,6-dichloro-p-benzoquinone]], D09: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D18: [[tetrachloro-p-benzoquinone]], D13: [[Bromanil]], K055: [[2,6-dichloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
