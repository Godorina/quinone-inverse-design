"""Failed jobs and missing convergence/geometry fields must be visible as flags, not silently skipped (Codex review 2)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import highlevel  # noqa: E402


def _write(root, state, tz_extra, status="ok"):
    folder = root / ("CO2" if state == "CO2" else "X")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{state}_tz.json").write_text(json.dumps({"status": status, "energy_Eh": -1.0, **tz_extra}))
    (folder / f"{state}_svp.json").write_text(json.dumps({"status": "ok", "thermo": {"G_corr_Eh": 0.0}}))


def test_failed_job_is_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for s in ("Q", "Q_radical_anion", "Q_dianion", "CO2"):
            _write(root, s, {})
        _write(root, "adduct", {}, status="opt_not_converged")
        row = highlevel.composite(root, "X", 4.417)
        assert any(f.startswith("failed:adduct") for f in row["flags"]) and "dG_bind_1M_kcal" not in row


def test_missing_fields_are_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for s in ("Q", "Q_radical_anion", "Q_dianion", "adduct", "CO2"):
            _write(root, s, {})
        flags = highlevel.composite(root, "X", 4.417)["flags"]
        assert "convergence_unknown:adduct" in flags and "co2_unchecked" in flags


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
