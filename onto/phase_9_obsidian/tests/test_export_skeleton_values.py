"""Structure-derived skeletons use the KG's plain values, so Dataview groups loop and KG molecules together."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export import skeleton_from_smiles


def test_plain_skeleton_values():
    assert skeleton_from_smiles('O=C1C=CC(=O)C=C1') == 'Benzoquinone'
    assert skeleton_from_smiles('O=C1c2ccccc2C(=O)c2ccccc21') == 'Anthraquinone'


if __name__ == '__main__':
    test_plain_skeleton_values()
    print('skeleton values ok')
