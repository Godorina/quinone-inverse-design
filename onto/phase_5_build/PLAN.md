# Phase 5: JSON -> RDF (build.py)

Input: `phase_4_extract/records_final/*.json` (55), `phase_3_corpus/master.json` (DOI, year via id), `phase_4b_extend/xlsx_status.csv`, `smiles_proposals.csv`.
Output: `kg.ttl` (data only; schema/vocab are loaded by check.py). Check: `al_alloy/common/check.py` against `phase_2_schema` (SHACL + rules + OWL-RL + CQ).

## IRIs (base `https://w3id.org/quinone/entity/`, local part percent-encoded)
paper-<id>, cpd-<id>-<key>, cond-<id>-<key>, m-<id>-<i>, o-<id>-<i> (i = position in the record list), ev-<id>-<sha1(quote|page)[:10]>.

## Mapping
- record -> qn:Paper (schema:name title, schema:identifier DOI, schema:datePublished year); qn:simReviewTier from xlsx_status.csv when the DOI is listed.
- compounds[] -> qn:Compound: skeleton, form, substituentClass (each), substituentText; if (paper, key) is in smiles_proposals with a canonical_smiles: qn:smiles, qn:inchikey, qn:smilesSource "llm_checked".
- conditions[] -> qn:Condition: solvent, referenceElectrode, atmosphere, electrolyteText, additiveText, pH, temperatureK. Vocabulary values map to `qn:<Name>`.
- measurements[] -> qn:Measurement: ofCompound, underCondition, fromPaper, property, value (xsd:decimal), unit, basis, method, redoxCouple (if set).
- observations[] -> qn:Observation: observationKind (kind), outcome.
- every result: qn:hasEvidence -> qn:Evidence (evidenceSource = record evidence_source, quote, page if set), qn:reviewStatus = record review_status (kept verbatim).

## Skipped
- Results whose quote is < 20 chars (EvidenceShape minimum): data problem, counted in REPORT, not padded.
- `not_reported`, `dropped`, `attempts` (extraction bookkeeping), the other columns of the 4b tables.
- Compounds without SMILES get no qn:smiles. No computation signatures (qn:functional etc.): records carry none.

## Determinism
rdflib turtle output is sorted and there are no blank nodes; test_build compares two builds byte for byte.
