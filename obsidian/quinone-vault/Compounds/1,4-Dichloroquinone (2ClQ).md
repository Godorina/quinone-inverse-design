---
type: "compound"
smiles: "O=C1C=C(Cl)C(=O)C=C1Cl"
inchikey: "LNXVNZRYYHFMEY-UHFFFAOYSA-N"
skeleton: "Benzoquinone"
E2_eV: -2.3291133879426105
dE_bind_kcal: -25.275488722353856
f_v2: 0.8861917204653827
o2_margin_V: 0.09899387407334448
co2_detached: false
aliases: ["1,4-Dichloroquinone (2ClQ)", "2ClQ", "Cand LNXVNZRY", "LNXVNZRYYHFMEY-UHFFFAOYSA-N", "O=C1C=C(Cl)C(=O)C=C1Cl"]
source: "kg"
reference_name_matches: ["1,4-Dichloroquinone (2ClQ)"]
smiles_source: "reference-name"
runs: ["loop-20261031-222906", "loop-20261101-111405-random-biased-fonly", "loop-20261102-003356"]
---

# 1,4-Dichloroquinone (2ClQ)

Family: [[Benzoquinone (family)]]

Name resolution: reference-name (1,4-Dichloroquinone (2ClQ))

## Structure
![[1,4-Dichloroquinone (2ClQ).png]]
![[1,4-Dichloroquinone (2ClQ).xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[1,4-Dichloroquinone (2ClQ) + CO2.xyz]]

## Literature measurements and observations
- [[Predictive energetic tuning of quinoid O-nucleophiles for the electrochemical capture of carbon diox]]: BindingMode | CO2Adduct | solvent=Acetonitrile; electrolyte=NBu4PF6; reference=FcFcPlus; atmosphere=CO2Atmosphere | 4
> A peculiar observation about 2ClQ is that although it falls in the electron-poor category, it binds two equivalents of CO2.

## Alherz 2022 Table 1 measurements
- [[Trade-Off between Redox Potential and the Strength of Electrochemical CO 2 Capture in Quinones]]: E2 exp | -1.43 | V vs Fc/Fc+ | Acetonitrile | Table 1, PDF image entry, independently checked
- [[Trade-Off between Redox Potential and the Strength of Electrochemical CO 2 Capture in Quinones]]: dG bind exp | -9.42 ± 0.15 | kcal/mol | Acetonitrile | Table 1, PDF image entry, independently checked

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261031-222906]], llm, round 2: f=1.0959081272559288, margin=0.09899387405478288, PubChem CID=None
  - Hypothesis: D07 (2,6-Cl2) has the best f (1.24) but a margin of only 0.097. Moving a Cl to the 2,5 pattern changes the dipole and the carbonyl electron density without adding halogen bulk, which cost binding in D14 and D11. K020 reports strong CO2 binding for a dichloro-BQ (K = 8.2e5). The hope is a margin gain of 0.05 or more while holding f near D07. Risk: f gain beyond 2 is unlikely from one isomer move.
  - Cited IDs: D07: [[2,6-dichloro-p-benzoquinone]], D14: [[tetrachloro-p-benzoquinone]], D08: [[2,3,5,6-Tetrafluoro-1,4-benzoquinone]], K020: [[2,7-dichloro-p-benzoquinone]], K055: [[2,6-dichloro-p-benzoquinone]]
- [[loop-20261101-111405-random-biased-fonly]], random, round 2: f=1.0959081275213114, margin=0.09899387406096993, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
- [[loop-20261102-003356]], random, round 2: f=1.0959081287166705, margin=0.09899387407334448, PubChem CID=None
  - Hypothesis: B0 random edit
  - Cited IDs: none
