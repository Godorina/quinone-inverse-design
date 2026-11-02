# Phase 5 report

## Build
`kg.ttl`: 8015 data triples (9488 with schema and vocab loaded by check.py). Two builds are byte-identical (md5 2932e38c...). Re-parse keeps the triple count.

| Class | Count |
|---|---|
| Paper | 55 (24 with simReviewTier) |
| Compound | 186 (17 with qn:smiles, qn:inchikey, qn:smilesSource "llm_checked") |
| Condition | 223 |
| Measurement | 307 |
| Observation | 96 |
| Evidence | 285 |

review_status: machine_extracted on all 403 results (none reviewed by a person).

## Checks (check.py on phase_2_schema)
SHACL + rules: 0 violations. OWL-RL inconsistencies: 0.
CQ rows: cq01 186, cq02 213, cq04 79, cq05 62, cq07 153, cq08 13, cq13 183, cq14 17, cq19 403, cq20 22, cq22 4.
Negative case: `qn:functional "B3LYP"` on an Experiment measurement gives exactly 1 violation.

## Skipped (data problem, records untouched)
28 results have a quote shorter than 20 chars, which EvidenceShape rejects: m025 15, m060 8, m005 2, m074 2, m029 1. The quotes are table fragments such as "2.3 ± 0.3" or "2-AQS (56 kJ⋅mol−1)". All 28 are measurements; 335 extracted -> 307 built. Fix belongs in phase 4 (use the table row as the quote), then rebuild.

## Gaps
- Records carry no computation signature, so the CQ08/CQ20/CQ14/CQ22 signature and standard-state filters of PLAN section 4 have nothing to filter on yet; no `qn:co2StandardState` is emitted.
- Shape-only negatives (missing signature, missing standard state, reference-electrode mix-up) are covered by one test only (signature on Experiment).

## ponytail markers
`build.py`: no canonicalization beyond rdflib's sorted turtle (no blank nodes).
