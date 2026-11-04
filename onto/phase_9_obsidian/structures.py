"""Deterministic structure assets and conservative, cached PubChem name lookup."""
import csv
import json
import math
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from rdkit import Chem
from rdkit.Chem import AllChem, Draw

ROOT = Path(__file__).resolve().parents[2]
NAME_CACHE = ROOT / 'onto/data/pubchem_name_cache.json'
sys.path.insert(0, str(ROOT / 'onto/phase_8_design'))

_last_call = 0.0


def _fetch(url, timeout):
    with urlopen(url, timeout=timeout) as response:
        return json.load(response)


def name_guard(name):
    if re.search(r'poly|composite|nanotube|resin|salt|complex|\b(?:sodium|disodium|chitosan|pbdt-q|aqcof|cnts?)\b|\b\w*sulfonate\b|\bion\b|\b(?:di|tri|tetra)?(?:an|cat)ion\b|[-\s]based\b|[\[\]{}]|\b(?:ru|re|fe|co|mn|zn|cu|ni|pt|pd)\s*\(', name, re.I):
        return 'material'
    if re.search(r'\bderivative\b', name, re.I) and not re.search(r'\b\d+(?:,\d+)*[-\s]+[a-z]+\s+derivative\b', name, re.I):
        return 'unspecified_derivative'
    return None


def name_variants(name):
    name = unicodedata.normalize('NFKC', name).strip().strip('"').replace('−', '-').replace('–', '-').replace('—', '-')
    values = []
    def add(value):
        value = re.sub(r'\s+', ' ', value).strip(' ;')
        if value and value not in values:
            values.append(value)
    add(name)
    base = re.sub(r'\s*\([^()]*\)\s*$', '', name).strip()
    add(base)
    for value in list(values):
        corrected = re.sub('naptho', 'naphtho', value, flags=re.I)
        corrected = re.sub('anthra-quinone', 'anthraquinone', corrected, flags=re.I)
        add(corrected)
    for value in list(values):
        for prefix, locant in (('p-', '1,4-'), ('o-', '1,2-')):
            add(re.sub(r'(?i)(^|[-\s])' + prefix + r'(?=(?:benzo|naphtho)quinone\b)', lambda m: m.group(1) + locant, value))
            add(re.sub(r'(?i)(^|[-\s])' + locant + r'(?=(?:benzo|naphtho)quinone\b)', lambda m: m.group(1) + prefix, value))
        if value.casefold() == 'anthraquinone':
            add('9,10-anthraquinone')
        elif value.casefold() == '9,10-anthraquinone':
            add('anthraquinone')
    return values


def _name_key(name):
    return re.sub(r'[\s_\-]+', '', unicodedata.normalize('NFKC', name).casefold())


def display_rejection(smiles):
    """Validate one small neutral organic molecule for display, not design."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return 'invalid_smiles'
    if len(Chem.GetMolFrags(mol)) != 1 or sum(a.GetFormalCharge() for a in mol.GetAtoms()) != 0:
        return 'charged_or_disconnected'
    if any(a.GetAtomicNum() not in {1, 5, 6, 7, 8, 9, 14, 15, 16, 17, 34, 35, 53} for a in mol.GetAtoms()):
        return 'metal'
    if not any(a.GetAtomicNum() == 6 for a in mol.GetAtoms()):
        return 'not_organic'
    if mol.GetNumHeavyAtoms() > 40:
        return 'too_many_heavy_atoms'
    return None


def is_quinone(smiles):
    """The ring portion of loop.t0's v2 rule, independent of domain size."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return False
    carbonyls = {a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 6 and
                 any(n.GetAtomicNum() == 8 and mol.GetBondBetweenAtoms(a.GetIdx(), n.GetIdx()).GetBondType() == Chem.BondType.DOUBLE for n in a.GetNeighbors())}
    return any(len(r) == 6 and all(mol.GetAtomWithIdx(i).GetAtomicNum() in {6, 7, 16} and
               mol.GetAtomWithIdx(i).GetHybridization() == Chem.HybridizationType.SP2 for i in r) and
               any(r[i] in carbonyls and r[(i + d) % 6] in carbonyls for i in range(6) for d in (1, 3))
               for r in mol.GetRingInfo().AtomRings())


def reference_names(root):
    """Index explicit aliases; aliases pointing to multiple structures remain ambiguous."""
    root = Path(root)
    index = defaultdict(dict)
    def add(smiles, name):
        if not smiles or not name or name_guard(name) or display_rejection(smiles):
            return
        molecule = Chem.MolFromSmiles(smiles)
        key = Chem.MolToInchiKey(molecule)
        aliases = name_variants(name)
        for value in re.findall(r'\(([^()]*)\)', name):
            if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{1,20}', value) and not re.fullmatch(r'cpd-m\d+', value, re.I):
                aliases.append(value)
        for alias in aliases:
            index[_name_key(alias)][key] = smiles

    refs = root / 'dft/runs/ref_set'
    expansion = root / 'onto/phase_4b_extend/reference_expansion.csv'
    with expansion.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            smiles = row['smiles']
            for name in (row['name'], row['id']):
                add(smiles, name)
            # ponytail: only an explicit "<name> monomer" note is treated as an alias.
            match = re.match(r'^([A-Za-z0-9][A-Za-z0-9-]+)\s+monomer\b', row['note'], re.I)
            if match:
                add(smiles, match.group(1))
    with (root / 'onto/phase_4b_extend/smiles_proposals.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for name in (row.get('compound'), row.get('name')):
                add(row.get('canonical_smiles'), name)
    with (root / 'onto/phase_4b_extend/alherz2022_table1.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for name in (row['entry'], row['name_in_paper'].strip('"')):
                add(row['smiles'], name)
    for path in sorted(refs.glob('*.json')):
        data = json.loads(path.read_text())
        for name in str(data.get('sources', '')).split(';'):
            if re.fullmatch(r'X\d{2}', name):
                add(data.get('smiles'), name)
    return index


def reference_match(name, index):
    if name_guard(name):
        return None
    variants = name_variants(name)
    parent = re.search(r'\(([^()]*)\)\s*$', name)
    if parent and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{1,20}', parent.group(1)) and not re.fullmatch(r'cpd-m\d+', parent.group(1), re.I):
        variants.append(parent.group(1))
    for variant in variants:
        matches = index.get(_name_key(variant), {})
        if len(matches) == 1:
            key, smiles = next(iter(matches.items()))
            return {'status': 'reference-name', 'inchikey': key, 'smiles': smiles, 'matched_name': variant}
        if len(matches) > 1:
            return None
    return None


def resolve_variants(name, online=False):
    reason = name_guard(name)
    if reason:
        return {'status': reason}
    statuses = []
    for variant in name_variants(name):
        result = resolve_name(variant, online=online)
        if result['status'] == 'found':
            return {**result, 'matched_name': variant}
        statuses.append(result['status'])
    for status in ('error', 'ambiguous', 'not_cached', 'metal', 'charged_or_disconnected', 'too_many_heavy_atoms', 'not_organic', 'not_quinone', 'invalid_smiles', 'not_found'):
        if status in statuses:
            return {'status': status}
    return {'status': 'not_found'}


def resolve_name(name, fetch=None, online=True):
    global _last_call
    guard = name_guard(name)
    if guard:
        return {'status': guard}
    cache = json.loads(NAME_CACHE.read_text()) if NAME_CACHE.exists() else {}
    if name in cache:
        cached = cache[name]
        stale = cached.get('status') == 'not_quinone' or (cached.get('status') == 'too_many_heavy_atoms' and cached.get('max_heavy_atoms') != 40)
        if not online or not stale:
            if cached.get('status') == 'found':
                reason = display_rejection(cached.get('smiles'))
                return {'status': reason} if reason else cached
            return cached
    if not online:
        return {'status': 'not_cached'}
    # ponytail: process-local limiter; concurrent exporters need a shared limiter.
    time.sleep(max(0, .26 - (time.monotonic() - _last_call)))
    _last_call = time.monotonic()
    url = ('https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/' + quote(name, safe='')
           + '/property/IsomericSMILES,Title/JSON')
    try:
        properties = (fetch or _fetch)(url, timeout=10)['PropertyTable']['Properties']
        if not properties:
            result = {'status': 'not_found'}
        else:
            first = properties[0]
            if len(properties) != 1:
                result = {'status': 'ambiguous'}
            else:
                smiles = first.get('SMILES') or first.get('IsomericSMILES')
                reason = display_rejection(smiles)
                result = {'status': reason} if reason else {'status': 'found', 'cid': int(first['CID']), 'smiles': smiles}
                if reason == 'too_many_heavy_atoms':
                    result['max_heavy_atoms'] = 40
    except HTTPError as exc:
        if exc.code != 404:
            return {'status': 'error'}
        result = {'status': 'not_found'}
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return {'status': 'error'}
    cache[name] = result
    NAME_CACHE.parent.mkdir(parents=True, exist_ok=True)
    NAME_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    return result


def xyz_text(atoms, source):
    return f'{len(atoms)}\n{source}\n' + '\n'.join(atoms) + '\n'


def geometry(smiles, low=None, high=None):
    if high and high.get('status') == 'ok' and high.get('opt_converged') is True and high.get('xyz_final'):
        source = 'ωB97M-V/def2-TZVPD'
        return xyz_text(high['xyz_final'].strip().splitlines(), source), source
    q = (low or {}).get('states', {}).get('Q', {})
    if q.get('converged') is True and q.get('geom_converged') is True and not q.get('error') and q.get('xyz'):
        source = 'DFT B3LYP/def2-SVP'
        return xyz_text(q['xyz'].splitlines()[2:], source), source
    source = 'RDKit/MMFF (not DFT)'
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = 0
    if AllChem.EmbedMolecule(mol, params) != 0:
        params.useRandomCoords = True
        if AllChem.EmbedMolecule(mol, params) != 0:
            raise ValueError(f'Cannot embed SMILES: {smiles}')
    if AllChem.MMFFHasAllMoleculeParams(mol):
        AllChem.MMFFOptimizeMolecule(mol, maxIters=1000)
    elif AllChem.UFFHasAllMoleculeParams(mol):
        AllChem.UFFOptimizeMolecule(mol, maxIters=1000)
        source = 'RDKit/UFF (not DFT)'
    else:
        source = 'RDKit/ETKDG (not DFT; no force field)'
    return xyz_text(Chem.MolToXYZBlock(mol).splitlines()[2:], source), source


def attached_adduct(low):
    attached = []
    for adduct in (low or {}).get('adducts', {}).values():
        if not (adduct.get('converged') is True and adduct.get('geom_converged') is True and not adduct.get('error') and adduct.get('xyz') and adduct.get('energy') is not None):
            continue
        try:
            atoms = [line.split() for line in adduct['xyz'].splitlines()[2:]]
            carbon, oxygen = atoms[-3], atoms[int(adduct['o_index'])]
            if carbon[0] != 'C' or oxygen[0] != 'O':
                continue
            distance = math.dist([float(x) for x in carbon[1:4]], [float(x) for x in oxygen[1:4]])
            if distance <= 2.0:
                attached.append(adduct)
        except (ValueError, TypeError, IndexError, KeyError):
            continue
    return min(attached, key=lambda item: item['energy']) if attached else None


def write_assets(directory, name, smiles, low=None, high=None):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f'Invalid SMILES: {smiles}')
    Draw.MolToFile(mol, str(directory / (name + '.png')), size=(300, 300))
    xyz, source = geometry(smiles, low, high)
    (directory / (name + '.xyz')).write_text(xyz, encoding='utf-8')
    adduct = attached_adduct(low)
    if adduct:
        (directory / (name + ' + CO2.xyz')).write_text(xyz_text(adduct['xyz'].splitlines()[2:], 'DFT B3LYP/def2-SVP; lowest-energy attached CO2 adduct'), encoding='utf-8')
    return source, bool(adduct)
