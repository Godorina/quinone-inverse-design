"""High-level composite must not silently use unconverged, imaginary-mode or CO2-detached results (Codex review, 2026-11-02)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import highlevel  # noqa: E402

STATES = ("Q", "Q_radical_anion", "Q_dianion", "adduct", "CO2")


def _write(folder, state, energy, *, conv=True, n_imag=0, xyz=None, o_index=0):
    folder.mkdir(parents=True, exist_ok=True)
    tz = {"status": "ok", "opt_converged": conv, "energy_Eh": energy, "o_index": o_index,
          "xyz_final": xyz or "O 0 0 0\nC 1.46 0 0\nO 2.1 1 0\nO 2.1 -1 0"}
    svp = {"status": "ok", "opt_converged": True, "thermo": {"G_corr_Eh": 0.0, "n_imag": n_imag}}
    (folder / f"{state}_tz.json").write_text(json.dumps(tz))
    (folder / f"{state}_svp.json").write_text(json.dumps(svp))


def _setup(tmp, **adduct):
    out = Path(tmp)
    for state in STATES:
        folder = out / ("CO2" if state == "CO2" else "X")
        _write(folder, state, -1.0, **(adduct if state == "adduct" else {}))
    return out


def test_clean_result_has_no_flags_and_keeps_binding():
    with tempfile.TemporaryDirectory() as tmp:
        row = highlevel.composite(_setup(tmp), "X", 4.417)
        assert row["flags"] == [] and "dG_bind_1M_kcal" in row


def test_detached_co2_drops_binding_and_flags():
    with tempfile.TemporaryDirectory() as tmp:
        row = highlevel.composite(_setup(tmp, xyz="O 0 0 0\nC 2.6 0 0\nO 3.2 1 0\nO 3.2 -1 0"), "X", 4.417)
        assert any(f.startswith("co2_detached") for f in row["flags"]) and "dG_bind_1M_kcal" not in row


def test_unconverged_state_is_excluded():
    with tempfile.TemporaryDirectory() as tmp:
        row = highlevel.composite(_setup(tmp, conv=False), "X", 4.417)
        assert "not_converged:adduct" in row["flags"] and "dG_bind_1M_kcal" not in row


def test_imaginary_mode_is_flagged_but_kept():
    with tempfile.TemporaryDirectory() as tmp:
        row = highlevel.composite(_setup(tmp, n_imag=1), "X", 4.417)
        assert "imag:adduct:1" in row["flags"] and "dG_bind_1M_kcal" in row


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
