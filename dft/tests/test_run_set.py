"""No-DFT contracts for the phase-7 reference-set driver."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_set import carbonyl_sites, input_set, reference_set, run_molecule, run_selected, summarize


BQ = "O=C1C=CC(=O)C=C1"
CSV = Path(__file__).resolve().parents[2] / "onto/phase_4b_extend/smiles_proposals.csv"


def result(energy, xyz=None):
    return {"energy": energy, "xyz": xyz, "seconds": 1, "steps": 1, "converged": True,
            "geom_converged": True, "max_gpu_memory": 0, "error": None}


def adduct_xyz(distance):
    return f"4\n\nO 0 0 0\nC {distance} 0 0\nO {distance + 1} 0 0\nO {distance + 2} 0 0\n"


def fake_record(index, detached=False):
    return {"inchikey": f"KEY{index:02d}", "smiles": BQ, "states": {
        "Q_radical_anion": result(-10 - index / 27.2114), "Q_dianion": result(-10),
    }, "adducts": {"0": {**result(-10 - (2 * index + 1) / 627.5, adduct_xyz(2.5 if detached else 1.45)), "o_index": 0}}}


def test_reference_set_has_15_unique_inchikeys():
    items = reference_set(CSV)
    assert len(items) == 15
    assert len({item["inchikey"] for item in items}) == 15
    assert any("m005:c10;m025:Q3" == item["sources"] for item in items)


def test_carbonyl_sites_remove_symmetric_oxygens():
    assert len(carbonyl_sites(BQ)) == 1
    assert len(carbonyl_sites("O=C1C=C(Cl)C(=O)C(Cl)=C1")) == 2
    assert len(carbonyl_sites("O=C1C(=O)c2ccccc2-c2ccccc21")) == 1


def test_summarize_fits_only_attached_adducts_and_requires_ten(tmp_path):
    for index in range(12):
        (tmp_path / f"KEY{index:02d}.json").write_text(json.dumps(fake_record(index, detached=index == 11)))
    (tmp_path / "_common.json").write_text(json.dumps({"states": {"CO2": result(-20), "O2": result(-30), "O2_radical_anion": result(-29.5)}}))
    summary = summarize(tmp_path)
    assert summary["line_measurable"] is True
    assert summary["excluded_detached"] == 1
    assert len(summary["molecules"]) == 12
    assert (tmp_path / "summary.json").exists() and (tmp_path / "summary.csv").exists()

    short = tmp_path / "short"
    short.mkdir()
    for index in range(9):
        (short / f"KEY{index:02d}.json").write_text(json.dumps(fake_record(index)))
    (short / "_common.json").write_text((tmp_path / "_common.json").read_text())
    assert summarize(short)["line_measurable"] is False


def test_run_molecule_skips_an_already_successful_state():
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory)
        item = {"inchikey": "KEY", "smiles": BQ, "sources": "m:test"}
        (out / "KEY.json").write_text(json.dumps({"inchikey": "KEY", "smiles": BQ, "states": {
            "Q": result(-1), "Q_radical_anion": result(-2), "Q_dianion": result(-3),
        }, "adducts": {"0": {**result(-4, adduct_xyz(1.45)), "o_index": 0}}}))
        calls = []
        run_molecule(item, out, False, optimize_fn=lambda *args, **kwargs: calls.append(args))
        assert calls == []


def test_input_set_and_selected_run_reuse_common_results(tmp_path):
    source = tmp_path / "chosen.csv"
    source.write_text("id,smiles\nnew,BQ\n".replace("BQ", BQ))
    assert input_set(source) == [{"inchikey": "AZQWKYJCGOJGHM-UHFFFAOYSA-N", "smiles": BQ, "sources": "new"}]
    common = Path(__file__).resolve().parents[1] / "runs/ref_set/_common.json"
    calls = []
    run_selected(input_set(source), tmp_path / "out", False, common_path=common,
                 optimize_fn=lambda *args, **kwargs: calls.append(args))
    assert calls and all(call[0] != ["O", "C", "O"] for call in calls)
    assert (tmp_path / "out/_common.json").read_text() == common.read_text()


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    with tempfile.TemporaryDirectory() as directory:
        for test in tests:
            if "tmp_path" in test.__code__.co_varnames:
                path = Path(directory) / test.__name__
                path.mkdir()
                test(path)
            else:
                test()
    print(f"{len(tests)} passed")
