---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc3cnc(F)cc3nc21"
inchikey: "METHVWQPJYOAPU-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.429064919178158
dE_bind_kcal: -25.378675528278762
f_v2: 1.2514048858742115
o2_margin_V: 0.19894540530889193
co2_detached: false
highlevel_flags: []
aliases: ["Cand METHVWQP", "METHVWQPJYOAPU-UHFFFAOYSA-N", "O=C1C=CC(=O)c2nc3cnc(F)cc3nc21"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 3
---

# Cand METHVWQP

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand METHVWQP.png]]
![[Cand METHVWQP.xyz]]
Geometry: ωB97M-V/def2-TZVPD

### CO2 adduct (Q²⁻·CO₂)
![[Cand METHVWQP + CO2.xyz]]

## Literature measurements and observations

## High-level
- highlevel_v2: E2_V=-1.6404029586271331; dG_bind_1M_kcal=-13.71442552836549; O2_margin_V=-0.41040295862713316; flags=[]

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 3: f=1.2514048858742115, margin=0.19894540530889193, PubChem CID=None
  - Hypothesis: Two directions raised f in the DFT data. Pyrazine-side substitution on the D05 core kept f at or above 1 (D19 0.86, D14 0.97; the pyrazine-F analog reached f 1.24). The tetra-aza core reached margin 0.18 with f 1.07. Ring N atoms away from the carbonyls lifted margin by about 0.19 V in D10 versus D21, with no CO2 detachment. Quinone-ring halogens cut f (D05 to F2 and Cl2 variants: f 0.65-0.77), so this proposal avoids them. The aza-phenazinedione keeps the N,N pocket beside the carbonyls (K123/K124 report strong binding with log K of 9-11), so binding stays near -27 kcal/mol. The distal aza plus F pair should add margin of 0.15 V or more. The difluoro-phenazine analog had f 1.19 and margin -0.018. The extra N should supply the missing margin, and one F rather than two limits the halogen-count f penalty (D18, D13). Whether f can approach 2 is untested; DFT will decide. Avoids CN, amino and OH, which detached or gave f below -1.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D10: [[1,10-phenanthroline-5,6-dione]], D21: [[9,10-Phenanthrenequinone]], D19: [[2,3-diphenylquinoxaline-5,8-dione]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]], K124: [[2,3-diphenylquinoxaline-5,8-dione]]
