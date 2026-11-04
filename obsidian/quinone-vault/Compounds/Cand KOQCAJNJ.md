---
type: "compound"
smiles: "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1F"
inchikey: "KOQCAJNJSQGENA-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.489645501769092
dE_bind_kcal: -24.597630892362616
f_v2: 1.2122154076260463
o2_margin_V: 0.25952598789982595
co2_detached: false
highlevel_flags: []
aliases: ["Cand KOQCAJNJ", "KOQCAJNJSQGENA-UHFFFAOYSA-N", "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1F"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 1
---

# Cand KOQCAJNJ

Family: [[Benzoquinone (family)]]

## Structure
![[Cand KOQCAJNJ.png]]
![[Cand KOQCAJNJ.xyz]]
Geometry: ωB97M-V/def2-TZVPD

### CO2 adduct (Q²⁻·CO₂)
![[Cand KOQCAJNJ + CO2.xyz]]

## Literature measurements and observations

## High-level
- highlevel: E2_V=-1.2491977919468158; dG_bind_1M_kcal=-7.5336680922540555; O2_margin_V=-0.019197791946815812; flags=[]

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 1: f=1.3178486611224265, margin=0.25952598789982595, PubChem CID=None
  - Hypothesis: This mixes the two f-positive motifs, Cl at 2,6 (D07 f=1.24) and F at 3,5 (D08 f=1.03). The aim is to keep f>0 while pushing the margin toward or above 0.15, since D08 and D14 show halogen count raises the margin. Fluorine is smaller than Br, so it should not repeat the f penalty of D11. CN is avoided because every CN reference detached CO2.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], K029: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
