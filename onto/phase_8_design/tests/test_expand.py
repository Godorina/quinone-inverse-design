import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from loop import t0, in_domain, edit

BQ = 'O=C1C=CC(=O)C=C1'

def test_expanded_domain():
    for smiles in ['O=C1C(=O)c2cccnc2-c2ncccc21', 'O=C1c2ccsc2C(=O)c2ccsc21', 'O=C1C=CC(=O)c2nccnc21']:
        assert t0(smiles) is None
        assert in_domain(smiles, [], set(), []) is None
    for smiles in ['c1ccccc1', BQ + '.[Fe]', BQ + '.[NH4+]', 'O=C1C(' + 'C'*24 + ')=CC(=O)C=C1']:
        assert t0(smiles) is not None
    assert in_domain('O=C1C=C(Cl)C(=O)C=C1', [BQ], {'F'}, [BQ], domain='v1') == 'unregistered_substituent'

def test_reference_expansion():
    import csv
    from rdkit import Chem
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dft'))
    from run_set import reference_set, INPUT, carbonyl_sites
    keys = {r['inchikey'] for r in reference_set(INPUT)}
    path = Path(__file__).resolve().parents[2] / 'phase_4b_extend/reference_expansion.csv'
    rows = list(csv.DictReader(path.open()))
    assert 6 <= len(rows) <= 9
    for row in rows:
        mol = Chem.MolFromSmiles(row['smiles'])
        assert mol and t0(row['smiles']) is None and carbonyl_sites(row['smiles'])
        key = Chem.MolToInchiKey(mol)
        assert key not in keys
        keys.add(key)

def test_edits():
    assert 'F' in edit(BQ, 'add', substituent='C(F)(F)F')
    assert 'n' in edit('O=C1C=CC(=O)c2ccccc21', 'aza')

if __name__ == '__main__':
    test_expanded_domain()
    test_reference_expansion()
    test_edits()
    print('3 passed')
