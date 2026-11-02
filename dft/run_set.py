"""Run and summarize the phase-7 quinone DFT reference set."""

import argparse
import csv
import json
import multiprocessing as mp
import os
import shutil
from pathlib import Path

import numpy as np
from rdkit import Chem

from dft import co2_adduct, embed, optimize, save_json


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "onto" / "phase_4b_extend" / "smiles_proposals.csv"
OUT = Path(__file__).parent / "runs" / "ref_set"


def reference_set(csv_path):
    grouped = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["canonical_smiles"] and row["inchikey"]:
                grouped.setdefault(row["inchikey"], []).append(row)
    return [{"inchikey": inchikey, "smiles": rows[0]["canonical_smiles"],
             "sources": ";".join(f"{row['paper_id']}:{row['compound']}" for row in rows)}
            for inchikey, rows in grouped.items()]


def input_set(csv_path):
    """Read phase-8 selections; compute an InChIKey only when CSV omitted it."""
    with open(csv_path, newline="", encoding="utf-8") as handle:
        return [{"inchikey": row.get("inchikey") or Chem.MolToInchiKey(Chem.MolFromSmiles(row["smiles"])),
                 "smiles": row["smiles"], "sources": row["id"]} for row in csv.DictReader(handle)]


def carbonyl_sites(smiles):
    mol = Chem.MolFromSmiles(smiles)
    ranks, sites = Chem.CanonicalRankAtoms(mol, breakTies=False), []
    for carbon in mol.GetAtoms():
        for oxygen in carbon.GetNeighbors():
            bond = mol.GetBondBetweenAtoms(carbon.GetIdx(), oxygen.GetIdx())
            if carbon.GetSymbol() == "C" and oxygen.GetSymbol() == "O" and bond.GetBondType() == Chem.BondType.DOUBLE:
                if ranks[oxygen.GetIdx()] not in {ranks[site] for site in sites}:
                    sites.append(oxygen.GetIdx())
    return sites


def _done(value):
    return bool(value and value.get("converged") and value.get("geom_converged") and not value.get("error"))


def _xyz(xyz):
    lines = xyz.splitlines()[2:]
    return [line.split()[0] for line in lines], np.array([[float(value) for value in line.split()[1:]] for line in lines])


def run_molecule(item, out_dir, gpu, optimize_fn=optimize):
    """Run one molecule, saving every completed state so a later run can resume."""
    out_dir, path = Path(out_dir), Path(out_dir) / f"{item['inchikey']}.json"
    data = json.loads(path.read_text()) if path.exists() else {**item, "states": {}, "adducts": {}}
    symbols, coords = embed(item["smiles"])
    for name, charge, spin in (("Q", 0, 0), ("Q_radical_anion", -1, 1), ("Q_dianion", -2, 0)):
        if not _done(data["states"].get(name)):
            data["states"][name] = optimize_fn(symbols, coords, charge, spin, gpu=gpu)
            save_json(path, data)
    q2 = data["states"].get("Q_dianion")
    if not _done(q2):
        return data
    missing_sites = [site for site in carbonyl_sites(item["smiles"]) if not _done(data["adducts"].get(str(site)))]
    if not missing_sites:
        return data
    q2_symbols, q2_coords = _xyz(q2["xyz"])
    for site in missing_sites:
        key = str(site)
        adduct_symbols, adduct_coords = co2_adduct(q2_symbols, q2_coords, site)
        data["adducts"][key] = {**optimize_fn(adduct_symbols, adduct_coords, -2, 0, gpu=gpu), "o_index": site}
        save_json(path, data)
    return data


def run_common(out_dir, gpu, optimize_fn=optimize):
    out_dir, path = Path(out_dir), Path(out_dir) / "_common.json"
    data = json.loads(path.read_text()) if path.exists() else {"states": {}}
    for name, smiles, charge, spin in (("CO2", "O=C=O", 0, 0), ("O2", "O=O", 0, 2), ("O2_radical_anion", "O=O", -1, 1)):
        if not _done(data["states"].get(name)):
            symbols, coords = embed(smiles)
            data["states"][name] = optimize_fn(symbols, coords, charge, spin, gpu=gpu)
            save_json(path, data)
    return data


def run_selected(items, out_dir, gpu, common_path=OUT / "_common.json", optimize_fn=optimize):
    """Run selected candidates after copying already-computed common states."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(common_path, out_dir / "_common.json")
    for item in items:
        run_molecule(item, out_dir, gpu, optimize_fn=optimize_fn)


def _distance(adduct):
    symbols, coords = _xyz(adduct["xyz"])
    return float(np.linalg.norm(coords[adduct["o_index"]] - coords[len(symbols) - 3]))


def summarize(out_dir):
    """Read completed JSON files and fit the attached-adduct exchange line only."""
    out_dir = Path(out_dir)
    common = json.loads((out_dir / "_common.json").read_text())["states"]
    co2, o2, o2_minus = (common[name]["energy"] for name in ("CO2", "O2", "O2_radical_anion"))
    rows, fit_rows = [], []
    for path in sorted(out_dir.glob("*.json")):
        if path.name.startswith("_") or path.name == "summary.json":
            continue
        data = json.loads(path.read_text())
        if "states" not in data:  # other JSON in the folder (e.g. the loop's response.json) is not a molecule
            continue
        states = data["states"]
        if not all(_done(states.get(name)) for name in ("Q_radical_anion", "Q_dianion")):
            continue
        e2 = (states["Q_dianion"]["energy"] - states["Q_radical_anion"]["energy"]) * 27.2114
        candidates = [(adduct["energy"], _distance(adduct)) for adduct in data["adducts"].values() if _done(adduct)]
        if not candidates:
            continue
        adduct_energy, distance = min(candidates)
        # ponytail: electronic energies only; add vibrational/free-energy corrections for absolute comparisons.
        bind = (adduct_energy - states["Q_dianion"]["energy"] - co2) * 627.5
        row = {"inchikey": data["inchikey"], "E2_eV": e2, "E2_reported_V": -e2, "dE_bind_kcal": bind,
               "co2_distance": distance, "co2_detached": distance > 2.0,
               "E_O2_eV": (o2_minus - o2) * 27.2114}
        rows.append(row)
        if not row["co2_detached"]:
            fit_rows.append(row)
    summary = {"molecules": rows, "excluded_detached": len(rows) - len(fit_rows), "line_measurable": len(fit_rows) >= 10}
    if summary["line_measurable"]:
        x, y = np.array([row["E2_eV"] for row in fit_rows]), np.array([row["dE_bind_kcal"] for row in fit_rows])
        a, b = np.linalg.lstsq(np.column_stack([x, np.ones(len(x))]), y, rcond=None)[0]
        summary["line"] = {"a": float(a), "b": float(b), "sigma": float(np.std(y - (a * x + b))), "n": len(x)}
    save_json(out_dir / "summary.json", summary)
    with open(out_dir / "summary.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["inchikey", "E2_eV", "E2_reported_V", "dE_bind_kcal", "co2_distance", "co2_detached", "E_O2_eV"])
        writer.writeheader()
        writer.writerows(rows)
    return summary


def _worker(gpu, items, out_dir):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    for item in items:
        run_molecule(item, out_dir, True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpus", default="0,1")
    parser.add_argument("--only", type=int)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.summary:
        print(summarize(args.out or OUT))
        return
    out = args.out or OUT
    items, gpus = (input_set(args.input) if args.input else reference_set(INPUT)), args.gpus.split(",")
    if args.only is not None:
        items = items[:args.only]
    out.mkdir(parents=True, exist_ok=True)
    os.environ["CUDA_VISIBLE_DEVICES"] = gpus[0]
    if args.input:
        run_selected([], out, True)  # only copies the reference-set common states; molecules go to the GPU pool below
    else:
        run_common(out, True)
    # spawn, not fork: the parent already initialised CUDA in run_common, and a forked child cannot re-init it
    with mp.get_context("spawn").Pool(len(gpus)) as pool:
        pool.starmap(_worker, [(gpu, items[index::len(gpus)], out) for index, gpu in enumerate(gpus)])
    print(summarize(out))


if __name__ == "__main__":
    main()
