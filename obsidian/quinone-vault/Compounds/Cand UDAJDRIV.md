---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc(F)c(F)nc21"
inchikey: "UDAJDRIVAYGYRP-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.3187515290740746
dE_bind_kcal: -25.66483942851889
f_v2: 0.9718869496070901
o2_margin_V: 0.08863201520480857
co2_detached: false
aliases: ["Cand UDAJDRIV", "O=C1C=CC(=O)c2nc(F)c(F)nc21", "UDAJDRIVAYGYRP-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 1
---

# Cand UDAJDRIV

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand UDAJDRIV.png]]
![[Cand UDAJDRIV.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand UDAJDRIV + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 1: f=0.9718869496070901, margin=0.08863201520480857, PubChem CID=None
  - Hypothesis: D19, D14 and D05 form a high-f series (0.86-1.09) that all have margin near zero. Aryl groups (D19 margin 0.076, D14 -0.002) do not help much. Swapping them for F on the pyrazine should add electron withdrawal and lift margin above 0.15, and removes the steric bulk that may weaken binding. The quinoxalinedione core has strong measured binding (K124, K123). CN-type detachment is avoided because F is much less withdrawing than CN.
  - Cited IDs: D19: [[2,3-diphenylquinoxaline-5,8-dione]], D05: [[quinoxaline-5,8-dione]], D14: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], K124: [[2,3-diphenylquinoxaline-5,8-dione]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]]
