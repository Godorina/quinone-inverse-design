# quinone competency questions (phase 2 view)

The 11 must-have questions of `../phase_1_scope/cq.md`; query file `cq/cqNN.rq` has the same number as the question.

| CQ | Question | Query returns | Needs |
|---|---|---|---|
| CQ01 | Which quinones were used (skeleton, form, papers)? | compound, skeleton, form, paper count | Compound |
| CQ02 | How do substituents change potential and binding constant? | skeleton, substituent class, potential or log K, solvent | Compound, Measurement |
| CQ04 | In which form does the reduced quinone hold CO2? | compound, binding mode, solvent, DOI | Observation (BindingMode) |
| CQ05 | What are the binding constants and energies, by which basis and method? | value, unit, basis, method | Measurement |
| CQ07 | What are the reduction potentials, for which step, against which reference, in which medium? | value, couple, reference, solvent, electrolyte | Measurement, Condition |
| CQ08 | Which compounds have potential and binding constant in one condition (trade-off table)? | potential, log K per compound | Measurement x2, Condition |
| CQ13 | How does the medium change one value of one compound? | two values with their solvents and additives | Measurement x2, Condition x2 |
| CQ14 | Which compounds survive oxygen, with which additive? | outcome, atmosphere, additive | Observation (OxygenStability) |
| CQ19 | Which paper, quote, source and page stand behind each value? | DOI, quote, source, page, review status | Evidence |
| CQ20 | Same skeleton, other substituent, same condition: how do potential and log K differ? | paired potentials and log K | Compound x2, Measurement x4 |
| CQ22 | Which compounds bind at least as strongly as a threshold and are oxygen stable? | compound, log K, outcome (param minLogK) | Measurement, Observation |

Design rules that follow from the questions:
- A value is comparable only with values of the same condition (CQ07, CQ08, CQ13, CQ20): every result points to exactly one `qn:Condition`.
- A missing detail is stated, not guessed: `qn:NotReported` is a value of solvent, reference electrode, atmosphere, redox couple and method.
- Every result has a paper, at least one quote and a review status (CQ19). Abstract quotes have no page; full-text quotes need one.
- Computed and measured values live side by side and are told apart by `qn:basis` (decision of phase 1).
