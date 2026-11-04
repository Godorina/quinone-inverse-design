---
type: "compound"
smiles: "O=C1C=CC(=O)c2nc3nccnc3nc21"
inchikey: "CAVKVIOROYYCTO-UHFFFAOYSA-N"
skeleton: "HeterocyclicQuinone"
E2_eV: -2.4127377759126163
dE_bind_kcal: -24.96769848511704
f_v2: 1.0700210791010891
o2_margin_V: 0.1826182620433503
co2_detached: false
highlevel_flags: []
aliases: ["CAVKVIOROYYCTO-UHFFFAOYSA-N", "Cand CAVKVIOR", "O=C1C=CC(=O)c2nc3nccnc3nc21"]
source: "loop"
runs: ["loop-20261102-212436"]
arm: "llm"
run: "loop-20261102-212436"
round: 2
---

# Cand CAVKVIOR

Family: [[HeterocyclicQuinone]]

## Structure
![[Cand CAVKVIOR.png]]
![[Cand CAVKVIOR.xyz]]
Geometry: ωB97M-V/def2-TZVPD

### CO2 adduct (Q²⁻·CO₂)
![[Cand CAVKVIOR + CO2.xyz]]

## Literature measurements and observations

## High-level
- highlevel_v2: E2_V=-1.6578481217177337; dG_bind_1M_kcal=-12.974447100557933; O2_margin_V=-0.4278481217177337; flags=[]

## Loop history
- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.
- [[loop-20261102-212436]], llm, round 2: f=1.0700210791010891, margin=0.1826182620433503, PubChem CID=None
  - Hypothesis: D10 (N-containing phenanthrenequinone) shifted margin by +0.19 V versus its carbocyclic analog D21 (-0.010 vs -0.196) with no detachment and binding of about -25 kcal/mol, and K110 reports a high binding constant for the N-containing dione. Adding ring N atoms is therefore a margin lever that is not CN-like, and the N-heteroaryl scaffold is what gives D05 its f of 1.09. Putting more ring N atoms into the D05 core should raise the margin by at least 0.15 V while the N next to the carbonyl keeps binding strong. This avoids the halogen-count f penalty seen in D13 and D18.
  - Cited IDs: D05: [[quinoxaline-5,8-dione]], D10: [[1,10-phenanthroline-5,6-dione]], D21: [[9,10-Phenanthrenequinone]], D02: [[1-OH-AQ]], K110: [[1,10-phenanthroline-5,6-dione]], K123: [[2,3-bis(4-methoxyphenyl)quinoxaline-5,8-dione]]
