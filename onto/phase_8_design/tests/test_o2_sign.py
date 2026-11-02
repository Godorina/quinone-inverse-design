"""O2 margin sign guard: E = -dE/F, so margin = E(Q-/Q2-) - E(O2/O2-) = dE_O2 - dE_Q.

Anthraquinone dianions reduce O2 (literature and our DFT: margin < 0); tetrafluoro-BQ does not (margin > 0).
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generate", HERE / "generate.py")
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)


def test_o2_margin_sign_on_real_reference_set():
    rows = {r["inchikey"]: r for r in gen.context()["dft"]}
    assert rows["RZVHIXYEVGDQDX-UHFFFAOYSA-N"]["o2_margin_V"] < -0.1   # anthraquinone: fails O2
    assert rows["JKLYZOGJWVAIQS-UHFFFAOYSA-N"]["o2_margin_V"] > 0.1    # tetrafluoro-BQ: passes O2


if __name__ == "__main__":
    test_o2_margin_sign_on_real_reference_set(); print("PASS test_o2_margin_sign_on_real_reference_set")
