import json
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pubchem
import closed_loop
from test_loop2 import evaluate


def test_lookup():
    with tempfile.TemporaryDirectory() as tmp, patch.object(pubchem, 'CACHE', Path(tmp) / 'cache.json'), patch.object(pubchem.time, 'sleep'):
        calls = []
        def found(url, timeout):
            calls.append((url, timeout))
            return {'PropertyTable': {'Properties': [{'CID': 123, 'IUPACName': 'name', 'MolecularFormula': 'C6H4O2'}]}}
        assert pubchem.lookup('A', fetch=found) == {'cid': 123, 'iupac': 'name', 'status': 'found'}
        assert pubchem.lookup('A', fetch=lambda *a, **k: 1/0)['cid'] == 123
        def missing(*a, **k):
            raise HTTPError('url', 404, 'missing', {}, None)
        assert pubchem.lookup('B', fetch=missing)['status'] == 'not_found'
        def failed(*a, **k):
            raise URLError('offline')
        assert pubchem.lookup('C', fetch=failed)['status'] == 'error'
        def unexpected(*a, **k):
            raise RuntimeError('fetch failed')
        assert pubchem.lookup('D', fetch=unexpected)['status'] == 'error'
        assert set(json.loads(pubchem.CACHE.read_text())) == {'A', 'B'}
        assert calls[0][1] == 15


def test_loop():
    proposal = {'parent_id': 'D01', 'smiles': 'O=C1C=C(Cl)C(=O)C=C1', 'cited_ids': []}
    fake = lambda key: {'cid': 123, 'iupac': 'name', 'status': 'found'}
    for reject in (False, True):
        with tempfile.TemporaryDirectory() as tmp:
            args = ['--rounds', '1', '--per-round', '1', '--out', tmp] + (['--reject-pubchem'] if reject else [])
            closed_loop.main(args, llm=lambda _: {'proposals': [proposal]}, evaluator=evaluate, lookup=fake)
            record = json.loads((Path(tmp) / 'ledger.jsonl').read_text())
            if reject:
                assert record['rejected'][0]['reason'] == 'known_pubchem'
                assert record['rejected'][0]['pubchem_cid'] == 123
            else:
                assert record['accepted'][0]['pubchem_cid'] == record['results'][0]['pubchem_cid'] == 123
                assert record['results'][0]['pubchem_status'] == 'found'
                assert 'PubChem 등록 1/1' in (Path(tmp) / 'report.md').read_text()


if __name__ == '__main__':
    test_lookup(); test_loop()
    print('pubchem tests passed')
