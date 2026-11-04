---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc(Cl)cnc21"
inchikey: "JRTUYKKYUKKRIS-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.303899618070858
dE_bind_kcal: -26.16894572886153
f_v2: 1.078050359547159
o2_margin_V: 0.07378010420159198
co2_detached: false
aliases: ["Cand JRTUYKKY", "JRTUYKKYUKKRIS-UHFFFAOYSA-N", "O=C1C=CC(=O)c2nc(Cl)cnc21"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 3
---

# Cand JRTUYKKY

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand JRTUYKKY.png]]
![[Cand JRTUYKKY.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand JRTUYKKY + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 3: f=1.078050359547159, margin=0.07378010420159198, PubChem CID=None
  - Hypothesis: Mono-F on the pyrazine gave f 1.24 and margin 0.03. Pyrazine Cl2 gave margin 0.17 but f 0.89. Cl is the stronger margin lever per atom and a single halogen is the smaller f penalty (D08 to D18 to D13 shows f falls with halogen count). One Cl should land between the two and may give f above 1.2 with margin near 0.1. Cl-quinones show CO2 binding (K008, K056). No CN, no amino/OH, which lowered f in D01/D04/D06.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], D08: [[2,6-dichloro-p-benzoquinone]], D18: [[tetrachloro-p-benzoquinone]], K008: [[2,3-dichloro-p-naphthoquinone]], K056: [[2,3-dichloro-p-naphthoquinone]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]]
