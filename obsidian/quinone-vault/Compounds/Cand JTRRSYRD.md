---
type: "compound"
smiles: "O=C1C=C(F)C(=O)C(F)=C1"
inchikey: "JTRRSYRDRYQMQO-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.1981596193731763
dE_bind_kcal: -28.340990732160236
f_v2: 1.3962470270795755
o2_margin_V: -0.031959894496089714
co2_detached: false
aliases: ["Cand JTRRSYRD", "JTRRSYRDRYQMQO-UHFFFAOYSA-N", "O=C1C=C(F)C(=O)C(F)=C1"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 2
---

# Cand JTRRSYRD

Family: [[Benzoquinone (family)]]

## Structure
![[Cand JTRRSYRD.png]]
![[Cand JTRRSYRD.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand JTRRSYRD + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 2: f=1.646329197750314, margin=-0.031959894496089714, PubChem CID=None
  - Hypothesis: Adding F to the D07 Cl2 scaffold raised f from 1.24 to 1.32-1.38, while heavier halogens (Br, D11 f=0.28; Cl4, D14 f=0.72) lowered it. Swapping both Cl for F should keep the strong CO2 binding of the 2,6-disubstituted BQ (D07 bind -25.8 kcal/mol) with a smaller steric footprint. The F4 core D08 has margin 0.178, so margin should rise above D07's 0.097. Aiming for f>=2 is a stretch, and this tests whether less halogen mass helps f.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]]
