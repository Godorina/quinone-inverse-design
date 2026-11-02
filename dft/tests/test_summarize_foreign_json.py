"""summarize() must ignore non-molecule JSON in the output folder (the closed loop writes response.json there)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_set  # noqa: E402


def test_response_json_in_folder_is_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        common = {"states": {name: {"energy": -1.0, "geom_converged": True, "error": None} for name in ("CO2", "O2", "O2_radical_anion")}}
        (out / "_common.json").write_text(json.dumps(common))
        (out / "response.json").write_text(json.dumps({"structured_output": {"proposals": []}}))
        summary = run_set.summarize(out)  # used to raise KeyError: 'states'
        assert summary["molecules"] == []


if __name__ == "__main__":
    test_response_json_in_folder_is_ignored(); print("PASS test_response_json_in_folder_is_ignored")
