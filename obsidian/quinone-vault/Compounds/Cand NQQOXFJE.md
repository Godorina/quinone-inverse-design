---
type: "compound"
smiles: "O=C1C(Br)=C(Cl)C(=O)C(Cl)=C1Br"
inchikey: "NQQOXFJEPQDWHC-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.6343449111456323
dE_bind_kcal: -21.25982958794438
f_v2: 0.6639017668835152
o2_margin_V: 0.4042253972763663
co2_detached: false
aliases: ["Cand NQQOXFJE", "NQQOXFJEPQDWHC-UHFFFAOYSA-N", "O=C1C(Br)=C(Cl)C(=O)C(Cl)=C1Br"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 1
---

# Cand NQQOXFJE

Family: [[Benzoquinone (family)]]

## Structure
![[Cand NQQOXFJE.png]]
![[Cand NQQOXFJE.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand NQQOXFJE + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 1: f=0.724055233065234, margin=0.4042253972763663, PubChem CID=None
  - Hypothesis: Br gave the largest O2 margin in the set (D11, 0.462, no detachment). D07's margin is only 0.097. Placing Br at 3,5 on the Cl2 scaffold should raise the margin well above 0.15. The risk is that heavier halogens lowered f (D11 f=0.28 versus D08 f=1.03), so f>=2 is unlikely. This probes the margin-versus-f edge of the tradeoff, and DFT will show whether the Cl2 core keeps f from collapsing.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D11: [[Bromanil]], D14: [[tetrachloro-p-benzoquinone]], K058: [[Bromanil]]
