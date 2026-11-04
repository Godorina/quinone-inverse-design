---
type: "compound"
smiles: "O=C1C(=O)c2cc(F)cnc2-c2ncc(F)cc21"
inchikey: "XQDJIZIIZRWTNV-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.3296837213684656
dE_bind_kcal: -24.25758334239319
f_v2: 0.5737095631412332
o2_margin_V: 0.09956420749919959
co2_detached: false
aliases: ["Cand XQDJIZII", "O=C1C(=O)c2cc(F)cnc2-c2ncc(F)cc21", "XQDJIZIIZRWTNV-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 1
---

# Cand XQDJIZII

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand XQDJIZII.png]]
![[Cand XQDJIZII.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand XQDJIZII + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 1: f=0.5737095631412332, margin=0.09956420749919959, PubChem CID=None
  - Hypothesis: D10 (f=0.56, margin -0.010) beats the carbocyclic analog D21 (f=0.71 vs margin -0.196) on margin, so ring N raises margin without detachment. N placement near the 1,2-dione gives strong binding (-25 kcal-like bind) and K110/K117 show high binding constants for this class. Adding F to the pyridines should withdraw electron density, add roughly 0.15-0.2 V margin, and keep binding; f could reach above 1.
  - Cited IDs: D10: [[1,10-phenanthroline-5,6-dione]], D21: [[9,10-Phenanthrenequinone]], D05: [[quinoxaline-5,8-dione]], K110: [[1,10-phenanthroline-5,6-dione]], K117: [[9,10-Phenanthrenequinone]]
