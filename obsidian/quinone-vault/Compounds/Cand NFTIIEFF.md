---
type: "compound"
smiles: "O=C1C(F)=C(Cl)C(=O)C(F)=C1"
inchikey: "NFTIIEFFLZTNLW-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.330126227816594
dE_bind_kcal: -25.8101643471052
f_v2: 1.0547063516883126
o2_margin_V: 0.10000671394732796
co2_detached: false
aliases: ["Cand NFTIIEFF", "NFTIIEFFLZTNLW-UHFFFAOYSA-N", "O=C1C(F)=C(Cl)C(=O)C(F)=C1"]
source: "loop"
runs: ["loop-20261031-222906"]
arm: "llm"
run: "loop-20261031-222906"
round: 3
---

# Cand NFTIIEFF

Family: [[Benzoquinone (family)]]

## Structure
![[Cand NFTIIEFF.png]]
![[Cand NFTIIEFF.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand NFTIIEFF + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 3: f=1.2542120484195618, margin=0.10000671394732796, PubChem CID=None
  - Hypothesis: The closest result so far is the trihalo-BQ with one open C-H (2,3-dichloro-5-fluoro: f 1.17, margin 0.157). It kept the margin above 0.15 and lost less binding than the tetrahalo BQs (D14 f 0.72, D11 f 0.28). D07 (bind -25.8, f 1.24) and D08 (bind -24.3, no detachment) both support small halogens with an open C-H. I promote that direction and flip the halogen ratio to two F and one Cl on D08's frame. F is smaller than Cl, so it should cost less carbonyl-region crowding and keep the CO2 binding. The one Cl and two F should still lift the margin toward 0.15 or more, since D08 (F4) reached 0.178. This tests whether the F-rich trihalo pattern gets more binding than the Cl-rich one. I avoid CN (D03, D06, D10 detached CO2) and NH2/OH (D01, D02, D04, D05 lowered f), and I avoid Br and a full set of heavy halogens (D11). K084 and K020 report CO2 adducts for F4-BQ and a dichloro-BQ. Risk: f is unlikely to reach 2, since no reference has, so the best realistic outcome is f above 1.2 with a margin of at least 0.15.
  - Cited IDs: D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D07: [[2,6-dichloro-p-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]], K020: [[2,7-dichloro-p-benzoquinone]]
