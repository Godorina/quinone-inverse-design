"""B0 fairness guard: the random arm picks parents among O2-feasible molecules only (the LLM arm's goal)."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("closed_loop", HERE / "closed_loop.py")
cl = importlib.util.module_from_spec(spec); spec.loader.exec_module(cl)


def test_infeasible_high_f_rows_are_not_parents():
    rows = [{"f": 1.75, "margin": -0.14, "co2_detached": False},        # loop row, fails O2
            {"f": 1.24, "o2_margin_V": 0.097, "co2_detached": False},  # reference row, fails O2
            {"f": 0.50, "o2_margin_V": 0.90, "co2_detached": True},    # detached
            {"f": 1.03, "o2_margin_V": 0.178, "co2_detached": False},  # feasible reference
            {"f": 1.38, "margin": 0.176, "co2_detached": False}]       # feasible loop row
    assert [r["f"] for r in cl.o2_feasible(rows)] == [1.03, 1.38]


def test_reference_set_has_at_least_five_feasible_parents():
    import generate
    assert len(cl.o2_feasible(generate.context()["dft"])) >= 5


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
