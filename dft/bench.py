"""Run the small benzoquinone DFT benchmark; use --cpu to disable gpu4pyscf."""

import argparse
from pathlib import Path

import numpy as np

from dft import co2_adduct, embed, optimize, save_json


BQ = "O=C1C=CC(=O)C=C1"
OUT = Path(__file__).parent / "runs" / "bench_bq" / "result.json"


def distance_from_xyz(xyz, first, second):
    lines = xyz.splitlines()[2:]
    coords = [line.split() for line in lines]
    return float(np.linalg.norm(np.array(coords[first][1:], float) - np.array(coords[second][1:], float)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()
    bq_symbols, bq_coords = embed(BQ)
    co2_symbols, co2_coords = embed("O=C=O")
    oxygen = next(index for index, symbol in enumerate(bq_symbols) if symbol == "O")
    adduct_symbols, adduct_coords = co2_adduct(bq_symbols, bq_coords, oxygen)
    # def2-SVP lacks diffuse functions for dianions; this is a benchmark, with phase 7 T2 owning accuracy.
    states = [("BQ", bq_symbols, bq_coords, 0, 0), ("BQ_radical_anion", bq_symbols, bq_coords, -1, 1),
              ("BQ_dianion", bq_symbols, bq_coords, -2, 0), ("BQ_dianion_CO2", adduct_symbols, adduct_coords, -2, 0),
              ("CO2", co2_symbols, co2_coords, 0, 0)]
    result = {"states": {}, "references": {}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for name, symbols, coords, charge, spin in states:
        result["states"][name] = optimize(symbols, coords, charge, spin, gpu=not args.cpu)
        save_json(OUT, result)
    energies = {name: state["energy"] for name, state in result["states"].items()}
    if all(energies[name] is not None for name, *_ in states):
        result["references"] = {
            "dE_red2_eV": (energies["BQ_dianion"] - energies["BQ_radical_anion"]) * 27.2114,
            "dE_bind_kcal": (energies["BQ_dianion_CO2"] - energies["BQ_dianion"] - energies["CO2"]) * 627.5,
            "adduct_o_c_distance": distance_from_xyz(result["states"]["BQ_dianion_CO2"]["xyz"], oxygen, len(bq_symbols)),
            "geom_converged": {name: state["geom_converged"] for name, state in result["states"].items()},
        }
        result["references"]["co2_detached"] = result["references"]["adduct_o_c_distance"] > 2.0
        result["references"]["molecule_seconds"] = sum(result["states"][name]["seconds"] for name in (
            "BQ", "BQ_radical_anion", "BQ_dianion", "BQ_dianion_CO2"))
        save_json(OUT, result)
    print(result["references"])


if __name__ == "__main__":
    main()
