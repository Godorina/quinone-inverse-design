"""v2 high-level set: new candidates, own output folder, scored with the refit line; v1 keeps line_v1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import highlevel as hl

V2 = ['O=C1C=CC(=O)c2nc3cnc(F)cc3nc21', 'O=C1C=CC(=O)c2nc3nccnc3nc21']


def test_v2_set():
    smiles, out, line_key = hl.SETS['v2']
    assert smiles[:2] == V2 and smiles[-1] == hl.SETS['v1'][0][-1]  # chloranil stays last for the experiment check
    assert out != hl.SETS['v1'][1] and line_key == 'line'
    assert hl.SETS['v1'][2] == 'line_v1'
    items = hl.inputs(smiles)
    assert [i['smiles'] for i in items] == smiles and all('states' in i['low'] for i in items)


if __name__ == '__main__':
    test_v2_set()
    print('highlevel v2 tests passed')
