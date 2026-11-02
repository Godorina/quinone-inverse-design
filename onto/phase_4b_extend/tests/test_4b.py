import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def test_status_table_contract():
    status = load("xlsx_status")
    with (ROOT / "xlsx_status.csv").open(encoding="utf-8") as f: rows = list(csv.DictReader(f))
    assert len(rows) == 38 == len({r["doi"] for r in rows})
    assert {r["doi"] for r in rows} == {status.norm(r["H"]) for r in status.xrows()}
    assert {r["status"] for r in rows} <= {"matched", "added_on_topic", "borderline", "out_of_scope", "unavailable", "needs_judgment"}

def test_pairing_same_compound_only():
    pairs = load("pair_candidates")
    data = {"paper_id":"p", "conditions":[{"key":"a","solvent":"Acetonitrile","reference_electrode":"FcFcPlus"}], "measurements":[
        {"compound":"q","condition":"a","property":"HalfWavePotential","value":-1,"unit":"Volt","quote":"p","page":1,"redox_couple":"SecondReduction","basis":"Experiment","method":"CyclicVoltammetry"},
        {"compound":"q","condition":"a","property":"BindingEnergy","value":-10,"unit":"KJPerMol","quote":"b","page":2,"basis":"Computation","method":"DFT"},
        {"compound":"other","condition":"a","property":"BindingEnergy","value":-9,"unit":"KJPerMol","quote":"c","page":2,"basis":"Computation","method":"DFT"}]}
    got = pairs.pair_rows(data)
    assert len(got) == 1 and got[0]["compound"] == "q"

if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
