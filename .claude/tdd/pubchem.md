# PubChem TDD evidence

Source: `.omc/plans/codex-pubchem.md`. Journeys: look up and cache PubChem identifiers, annotate or optionally reject known loop candidates, add identifiers to the KG and high-level summary.

| Guarantee | RED evidence | GREEN evidence |
|---|---|---|
| Lookup handles found, 404, fetch errors, cache hits; loop annotates and optionally rejects | `test_pubchem.py`: missing module; later RuntimeError escaped | `.venv/bin/python onto/phase_8_design/tests/test_pubchem.py` passed |
| Schema has bilingual metadata and integer CID; KG consumes cache deterministically | `test_pubchem_build.py`: missing schema property | `.venv/bin/python onto/phase_5_build/tests/test_pubchem_build.py` passed |
| High-level summary includes cached CID | `test_highlevel.py`: missing cache setting | `.venv/bin/python dft/tests/test_highlevel.py` passed |

`make test` passed after integration; its existing DFT test ran a small CPU geometry optimization. No coverage measurement was configured or run. No git checkpoints were made, per project and task instructions. Independent reviewer separation was unavailable because the user expressly required direct execution without subagents.
