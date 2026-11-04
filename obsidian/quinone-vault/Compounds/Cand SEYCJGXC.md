---
type: "compound"
smiles: "O=C1C(Cl)=C(Cl)C(=O)c2nccnc21"
inchikey: "SEYCJGXCYDOTGT-UHFFFAOYSA-N"
pubchem_cid: 149159
skeleton: "HeterocyclicQuinone"
E2_eV: -2.44942422892068
dE_bind_kcal: -23.224650393519113
f_v2: 0.6540247395507779
o2_margin_V: 0.2193047150514138
co2_detached: false
aliases: ["Cand SEYCJGXC", "O=C1C(Cl)=C(Cl)C(=O)c2nccnc21", "SEYCJGXCYDOTGT-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 1
---

# Cand SEYCJGXC

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand SEYCJGXC.png]]
![[Cand SEYCJGXC.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand SEYCJGXC + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 1: f=0.6540247395507779, margin=0.2193047150514138, PubChem CID=149159
  - Hypothesis: Cl substitution raised margin in D08 (0.097) and D18 (0.346) with f staying positive and no detachment. Two Cl on the high-f pyrazine-quinone (D05) should add about 0.15-0.2 V margin, with binding preserved by the N-heterocycle. Cl count is limited to 2 because D08 to D18 to D13 shows f falling as halogen count increases. Cl-quinones also have CO2-adduct and moderate binding evidence (K008, K056).
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D08: [[2,6-dichloro-p-benzoquinone]], D17: [[2,3-dichloro-p-naphthoquinone]], D18: [[tetrachloro-p-benzoquinone]], K008: [[2,3-dichloro-p-naphthoquinone]], K056: [[2,3-dichloro-p-naphthoquinone]]
