---
type: "compound"
smiles: "O=C1C=CC(=O)c2ncc(F)cc21"
inchikey: "TXVFLDVSASONQS-UHFFFAOYSA-N"
pubchem_cid: 129919848
skeleton: "HeterocyclicQuinone"
E2_eV: -2.1445809071600936
dE_bind_kcal: -27.546997258397568
f_v2: 0.9723311274688894
o2_margin_V: -0.08553860670917235
co2_detached: false
aliases: ["Cand TXVFLDVS", "O=C1C=CC(=O)c2ncc(F)cc21", "TXVFLDVSASONQS-UHFFFAOYSA-N"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 3
---

# Cand TXVFLDVS

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand TXVFLDVS.png]]
![[Cand TXVFLDVS.xyz]]
Geometry: DFT B3LYP/def2-SVP

### CO2 adduct (Q²⁻·CO₂)
![[Cand TXVFLDVS + CO2.xyz]]

## Literature measurements and observations

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 3: f=0.9723311274688894, margin=-0.08553860670917235, PubChem CID=129919848
  - Hypothesis: D05 f comes from the ring N next to the carbonyl (bind -27.6). Keeping one N but adding F tests whether a lighter heteroaryl with a single remote F gives f near the 1.24 of the mono-F pyrazine. D10 vs D21 shows ring N adds margin without detachment, and K110 shows a high binding constant for the N-heterocyclic dione. A single pyridine F is far from the carbonyls and adds withdrawal without the quinone-ring halogen f penalty.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D10: [[1,10-phenanthroline-5,6-dione]], D21: [[9,10-Phenanthrenequinone]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], K110: [[1,10-phenanthroline-5,6-dione]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]]
