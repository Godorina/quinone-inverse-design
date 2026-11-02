"""Fast contracts for the DFT helpers; no benchmark calculation is run here."""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dft import co2_adduct, embed, optimize


BQ = "O=C1C=CC(=O)C=C1"


def test_embed_has_expected_atom_counts():
    assert len(embed(BQ)[0]) == 12
    assert len(embed("O=C=O")[0]) == 3


def test_co2_adduct_has_expected_distance_and_bend():
    symbols, coords = embed(BQ)
    oxygen = next(i for i, symbol in enumerate(symbols) if symbol == "O")
    adduct_symbols, adduct_coords = co2_adduct(symbols, coords, oxygen)
    co2_c, co2_o1, co2_o2 = len(symbols), len(symbols) + 1, len(symbols) + 2
    assert len(adduct_symbols) == 15
    assert abs(np.linalg.norm(adduct_coords[oxygen] - adduct_coords[co2_c]) - 1.45) < 0.01
    assert np.linalg.norm(adduct_coords[oxygen] - adduct_coords[co2_o1]) > 2.0
    assert np.linalg.norm(adduct_coords[oxygen] - adduct_coords[co2_o2]) > 2.0
    first, second = adduct_coords[co2_o1] - adduct_coords[co2_c], adduct_coords[co2_o2] - adduct_coords[co2_c]
    angle = math.degrees(math.acos(np.dot(first, second) / np.linalg.norm(first) / np.linalg.norm(second)))
    assert 120 < angle < 140


def test_cpu_h2_optimization_returns_a_converged_result():
    result = optimize(["H", "H"], [[0, 0, 0], [0, 0, 0.74]], 0, 0,
                      basis="sto-3g", solvent=None, gpu=False)
    assert set(result) == {"energy", "xyz", "seconds", "steps", "converged", "geom_converged", "max_gpu_memory", "error"}
    assert result["converged"] is True
    assert result["geom_converged"] is True
    assert result["error"] is None
    assert "H" in result["xyz"]


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} passed")
