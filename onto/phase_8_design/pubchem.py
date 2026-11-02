"""Cached PubChem PUG REST lookup by InChIKey."""
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

CACHE = Path(__file__).resolve().parents[1] / 'data/pubchem_cache.json'
_last_call = 0.0


def _fetch(url, timeout):
    with urlopen(url, timeout=timeout) as response:
        return json.load(response)


def lookup(inchikey, fetch=None):
    global _last_call
    try:
        cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
        if inchikey in cache:
            return cache[inchikey]
        # ponytail: process-local spacing; a shared limiter is needed for concurrent processes.
        time.sleep(max(0, .25 - (time.monotonic() - _last_call)))
        _last_call = time.monotonic()
        url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/' + quote(inchikey, safe='') + '/property/IUPACName,MolecularFormula/JSON'
        try:
            prop = (fetch or _fetch)(url, timeout=15)['PropertyTable']['Properties'][0]
            result = {'cid': int(prop['CID']), 'iupac': prop.get('IUPACName'), 'status': 'found'}
        except HTTPError as exc:
            if exc.code != 404:
                raise
            result = {'cid': None, 'iupac': None, 'status': 'not_found'}
        except Exception:  # A failing fetch must not reject or cache a candidate.
            return {'cid': None, 'iupac': None, 'status': 'error'}
        cache[inchikey] = result
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True) + '\n')
        return result
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return {'cid': None, 'iupac': None, 'status': 'error'}
