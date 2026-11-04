---
type: "compound"
smiles: "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1"
inchikey: "QCOVIANIHBBUDY-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.4057293264657087
dE_bind_kcal: -25.560091102218934
f_v2: 1.2296104275291677
o2_margin_V: 0.1756098125964427
co2_detached: false
highlevel_flags: []
aliases: ["Cand QCOVIANI", "O=C1C(F)=C(Cl)C(=O)C(Cl)=C1", "QCOVIANIHBBUDY-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261031-151304"]
arm: "llm"
run: "loop-20261031-151304"
round: 1
---

# Cand QCOVIANI

Family: [[Benzoquinone (family)]]

## Structure
![[Cand QCOVIANI.png]]
![[Cand QCOVIANI.xyz]]
Geometry: ωB97M-V/def2-TZVPD

### CO2 adduct (Q²⁻·CO₂)
![[Cand QCOVIANI + CO2.xyz]]

## Literature measurements and observations

## High-level
- highlevel: E2_V=-1.3578648106552071; dG_bind_1M_kcal=-9.29008598685038; O2_margin_V=-0.12786481065520716; flags=[]

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-151304]], llm, round 1: f=1.3788717309511884, margin=0.1756098125964427, PubChem CID=None
  - Hypothesis: D07 (2,6-dichloro-BQ) has f=1.24 but O2 margin only 0.097. D08 (F4) has a higher margin of 0.178 while keeping f=1.03. Adding one F should lift the margin above 0.15 without the f loss seen with heavier halogenation (D14 f=0.72, D11 f=0.28). Aiming for f>=2 is a stretch. This is the minimal-risk test of whether an F raises the margin on the Cl2 scaffold.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]], K084: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]]
