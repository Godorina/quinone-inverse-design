"""Export existing quinone evidence and calculations to a deterministic Obsidian vault."""
import argparse
import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import RDFS
from rdkit import Chem

import structures

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / 'obsidian/quinone-vault'
QN = Namespace('https://w3id.org/quinone#')
SCHEMA = Namespace('https://schema.org/')


def skeleton_from_smiles(smiles):
    """Classify the fused ring system containing a six-membered quinone ring."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return 'NotReported'
    rings = mol.GetRingInfo().AtomRings()
    bonds = [{mol.GetBondBetweenAtoms(ring[i], ring[(i + 1) % len(ring)]).GetIdx()
              for i in range(len(ring))} for ring in rings]
    for index, ring in enumerate(rings):
        if len(ring) != 6 or any(mol.GetAtomWithIdx(i).GetHybridization() != Chem.HybridizationType.SP2 for i in ring):
            continue
        carbonyls = {i for i in ring if mol.GetAtomWithIdx(i).GetAtomicNum() == 6 and
                     any(n.GetAtomicNum() == 8 and n.GetIdx() not in ring and
                         mol.GetBondBetweenAtoms(i, n.GetIdx()).GetBondType() == Chem.BondType.DOUBLE
                         for n in mol.GetAtomWithIdx(i).GetNeighbors())}
        ortho = any(ring[i] in carbonyls and ring[(i + 1) % 6] in carbonyls for i in range(6))
        para = any(ring[i] in carbonyls and ring[(i + 3) % 6] in carbonyls for i in range(6))
        if not (ortho or para):
            continue
        system = {index}
        while True:
            expanded = system | {j for j in range(len(rings)) if any(bonds[j] & bonds[k] for k in system)}
            if expanded == system:
                break
            system = expanded
        if any(mol.GetAtomWithIdx(i).GetAtomicNum() in {7, 8, 16} for j in system for i in rings[j]):
            return 'HeterocyclicQuinone'
        if len(system) == 1:
            return 'Benzoquinone'
        if len(system) == 2:
            return 'Naphthoquinone'
        if len(system) == 3:
            return 'Phenanthrenequinone' if ortho else 'Anthraquinone'
        return 'OtherQuinoid'
    return 'NotReported'


def clean(value):
    return ' '.join(str('' if value is None else value).split()).replace('[[', '［［').replace(']]', '］］')


def preferred_kg_name(names):
    """Count case-insensitively; break frequency ties by locants and length."""
    forms = Counter(names)
    totals = Counter()
    for name, count in forms.items():
        totals[name.casefold()] += count
    normalized = min(totals, key=lambda name: (-totals[name], -bool(re.search(r'\d', name)), len(name), name))
    return min((name for name in forms if name.casefold() == normalized),
               key=lambda name: (-forms[name], name != name.casefold(), name))


def filename(title):
    stem = re.sub(r'[/\\:*?"<>|#^\[\]\x00-\x1f]', ' ', clean(title))
    stem = re.sub(r'\s+', ' ', stem).strip(' .')[:100].strip(' .') or 'unnamed'  # strip again: a cut can leave a trailing space
    return stem


def cell(value):
    return clean(value).replace('|', '&#124;')


def yaml_note(meta, body):
    # JSON scalars are YAML scalars and avoid hand-escaping names and SMILES.
    return '---\n' + ''.join(f'{k}: {json.dumps(v, ensure_ascii=False)}\n' for k, v in meta.items() if v is not None) + '---\n\n' + body.rstrip() + '\n'


def export(out=VAULT, lookup_names=False, report_path=None):
    out = Path(out)
    if out.is_symlink():
        raise ValueError('Vault directory must not be a symlink')
    out.mkdir(parents=True, exist_ok=True)
    for name in ('Papers', 'Compounds', 'Runs', 'Families', 'Structures', 'Images', 'Index.md', 'README.md'):
        path = out / name
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
    for directory in ('Papers', 'Compounds', 'Runs', 'Families', 'Structures'):
        (out / directory).mkdir()

    graph = Graph().parse(ROOT / 'onto/phase_5_build/kg.ttl', format='turtle')
    schema = Graph().parse(ROOT / 'onto/phase_2_schema/schema/quinone.ttl', format='turtle')
    vocab = Graph().parse(ROOT / 'onto/phase_2_schema/schema/quinone-vocab.ttl', format='turtle')

    def val(node, predicate):
        return graph.value(node, predicate) if node else None

    def label(value):
        if value is None:
            return ''
        if isinstance(value, URIRef):
            labels = list(schema.objects(value, RDFS.label)) + list(vocab.objects(value, RDFS.label))
            english = sorted(str(x) for x in labels if x.language == 'en')
            return english[0] if english else str(value).rsplit('#', 1)[-1].rsplit('/', 1)[-1]
        return clean(value)

    def value(node, predicate):
        return label(val(node, predicate))

    papers = sorted(set(graph.subjects(RDF.type, QN.Paper)), key=str)
    compounds = sorted(set(graph.subjects(RDF.type, QN.Compound)), key=str)
    identities = {}
    nodes_by_identity = defaultdict(list)
    node_identity = {}
    by_key = defaultdict(list)
    by_smiles = defaultdict(list)
    name_counts = Counter()
    unresolved = []
    reference_index = structures.reference_names(ROOT)

    def structure_key(smiles, fallback=None):
        molecule = Chem.MolFromSmiles(smiles) if smiles else None
        return Chem.MolToInchiKey(molecule) if molecule else fallback

    for node in compounds:
        given_key, smiles = value(node, QN.inchikey), value(node, QN.smiles)
        title = value(node, SCHEMA.name)
        name_result = None
        if not smiles:
            name_result = structures.reference_match(title, reference_index) or structures.resolve_variants(title, online=lookup_names)
            if name_result['status'] in ('found', 'reference-name') and given_key and structure_key(name_result['smiles']) != given_key:
                name_result = {'status': 'inchikey_mismatch'}
            name_counts[name_result['status']] += 1
            if name_result['status'] in ('found', 'reference-name'):
                smiles = name_result['smiles']
            else:
                unresolved.append((title, name_result['status']))
        key = structure_key(smiles, given_key)
        identity = 'key:' + key if key else str(node)
        is_new = identity not in identities
        if is_new:
            identities[identity] = {'node': node, 'key': key, 'smiles': smiles,
                                    'title': title, 'source': 'kg',
                                    'history': [], 'high': []}
            if key:
                by_key[key].append(identity)
        item = identities[identity]
        if name_result and name_result['status'] == 'found':
            item.setdefault('name_cid', name_result['cid'])
            item.setdefault('unverified_names', set()).add(title)
            if is_new:
                item['smiles_source'] = 'pubchem-name (unverified)'
        elif name_result and name_result['status'] == 'reference-name':
            item.setdefault('reference_names', set()).add(title)
            if is_new or item.get('smiles_source') == 'pubchem-name (unverified)':
                item['smiles'] = smiles
                item['smiles_source'] = 'reference-name'
        elif smiles and item.get('smiles_source'):
            item['smiles'] = smiles
            item.pop('smiles_source')
        nodes_by_identity[identity].append(node)
        node_identity[node] = identity
        if smiles and identity not in by_smiles[smiles]:
            by_smiles[smiles].append(identity)

    def ensure(key, smiles, source):
        key = structure_key(smiles, key)
        matches = by_key.get(key, []) if key else by_smiles.get(smiles, [])
        if matches:
            if smiles and matches[0] not in by_smiles[smiles]:
                by_smiles[smiles].append(matches[0])
            return matches
        identity = f'{source}:{key or smiles}'
        if identity not in identities:
            title = ('Cand ' if source == 'loop' else 'Reference ') + (key or 'unknown')[:8]
            identities[identity] = {'node': None, 'key': key,
                                    'smiles': smiles, 'title': title, 'source': source,
                                    'history': [], 'high': []}
            if key:
                by_key[key].append(identity)
            if smiles:
                by_smiles[smiles].append(identity)
        return [identity]

    refs = ROOT / 'dft/runs/ref_set'
    line = json.loads((refs / 'lines.json').read_text())['v2']
    names = {}
    with (ROOT / 'onto/phase_4b_extend/smiles_proposals.csv').open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            if row.get('inchikey'):
                names.setdefault(row['inchikey'], row.get('name') or row['compound'])
    expansion = {}
    with (ROOT / 'onto/phase_4b_extend/reference_expansion.csv').open(newline='', encoding='utf-8') as handle:
        expansion = {row['id']: row['name'] for row in csv.DictReader(handle)}
    with (refs / 'summary.csv').open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            data = json.loads((refs / (row['inchikey'] + '.json')).read_text())
            for identity in ensure(row['inchikey'], data['smiles'], 'reference'):
                identities[identity]['reference'] = row
                ref_name = names.get(row['inchikey']) or expansion.get(data.get('sources'))
                if ref_name:
                    identities[identity]['reference_title'] = ref_name
                if not identities[identity]['smiles'] or identities[identity].get('smiles_source') == 'pubchem-name (unverified)':
                    identities[identity]['smiles'] = data['smiles']
                    identities[identity].pop('smiles_source', None)
                if identity not in by_smiles[data['smiles']]:
                    by_smiles[data['smiles']].append(identity)

    run_dir = ROOT / 'onto/phase_8_design/runs'
    runs = {}
    for ledger in sorted(run_dir.glob('loop-*/ledger.jsonl')):
        records = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
        runs[ledger.parent.name] = records
        for record in records:
            for result in record.get('results', []):
                key, smiles = result.get('inchikey'), result.get('smiles')
                if not smiles:
                    continue
                for identity in ensure(key, smiles, 'loop'):
                    identities[identity]['history'].append((ledger.parent.name, record.get('arm') or 'llm', record.get('round'), result))

    for summary in sorted((ROOT / 'dft/runs').glob('highlevel*/summary.json')):
        for row in json.loads(summary.read_text()).get('molecules', []):
            for identity in ensure(row.get('id'), row.get('smiles'), 'highlevel'):
                identities[identity]['high'].append((summary.parent.name, row))

    # ponytail: Table 1 is an independently checked experimental source, not a DFT result.
    alherz_doi = '10.1021/acs.jpcc.2c03752'
    alherz_papers = [paper for paper in papers if value(paper, SCHEMA.identifier) == alherz_doi]
    if len(alherz_papers) != 1:
        raise ValueError('Expected exactly one Alherz 2022 paper')
    alherz_paper = alherz_papers[0]
    alherz_rows = []
    with (ROOT / 'onto/phase_4b_extend/alherz2022_table1.csv').open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            if not row['inchikey']:  # O2 reference electrode, not a quinone entry.
                continue
            if structure_key(row['smiles']) != row['inchikey']:
                raise ValueError(f"Table 1 structure mismatch: {row['entry']}")
            identity = ensure(row['inchikey'], row['smiles'], 'reference')[0]
            item = identities[identity]
            item.setdefault('table_names', set()).update((row['entry'], row['name_in_paper'].strip('"')))
            if not item.get('smiles'):
                item['smiles'] = row['smiles']
            alherz_rows.append((identity, row))

    for identity, item in identities.items():
        kg_names = Counter(value(node, SCHEMA.name) for node in nodes_by_identity[identity] if value(node, SCHEMA.name))
        if kg_names:
            item['title'] = preferred_kg_name(kg_names.elements())
        elif item.get('reference_title'):
            item['title'] = item['reference_title']
        elif item.get('table_names'):
            item['title'] = min(item['table_names'], key=lambda name: (len(name), name))

    # Index saved calculations once, without running any quantum chemistry.
    geometries = defaultdict(list)
    low_paths = sorted(refs.glob('*.json')) + sorted(run_dir.glob('loop-*/round_*/*.json'))
    for path in low_paths:
        data = json.loads(path.read_text())
        key = data.get('inchikey')
        if key and isinstance(data.get('states'), dict):
            geometries[key].append(data)
    high_geometry = {}
    for path in sorted((ROOT / 'dft/runs').glob('highlevel*/*/Q_tz.json')):
        data = json.loads(path.read_text())
        if data.get('status') == 'ok' and data.get('opt_converged') is True and data.get('xyz_final'):
            high_geometry.setdefault(path.parent.name, data)

    used = {'index', 'readme'}
    def unique(title, suffix):
        base = filename(title)
        name = base
        if name.casefold() in used:
            name = f'{base} ({filename(suffix)})'
        number = 2
        while name.casefold() in used:
            name = f'{base} ({filename(suffix)} {number})'
            number += 1
        used.add(name.casefold())
        return name

    paper_names = {p: unique(value(p, SCHEMA.name), value(p, SCHEMA.datePublished) or value(p, SCHEMA.identifier)[-12:]) for p in papers}
    for identity, item in sorted(identities.items()):
        item['name'] = unique(item['title'], (item['key'] or identity.rsplit('/', 1)[-1])[:8])
    compound_names = {node: identities[identity]['name'] for node, identity in node_identity.items()}
    run_names = {run: unique(run, 'run') for run in runs}
    family_members = defaultdict(list)
    family_skeletons = defaultdict(set)
    for identity, item in sorted(identities.items()):
        kg_skeleton = value(item['node'], QN.skeleton)
        item['skeleton'] = kg_skeleton or skeleton_from_smiles(item['smiles'])
        # ponytail: the parenthesized names are hub filenames; KG uses the bare concepts.
        skeleton = {'Benzoquinone (family)': 'Benzoquinone',
                    'Anthraquinone (family)': 'Anthraquinone'}.get(item['skeleton'], item['skeleton'])
        family = kg_skeleton or (item.get('reference') or {}).get('family') or skeleton
        item['family'] = family
        families = {family, (item.get('reference') or {}).get('family')}
        families.update(value(node, QN.skeleton) for node in nodes_by_identity[identity])
        for member_family in sorted(f for f in families if f):
            family_members[member_family].append(identity)
            if member_family != skeleton:
                family_skeletons[member_family].add(skeleton)
                family_members.setdefault(skeleton, [])
    family_names = {family: unique(family + ' (family)' if family in ('Benzoquinone', 'Anthraquinone') else family, 'family') for family in sorted(family_members)}
    def link(name):
        return f'[[{name}]]'

    def condition(node):
        return '; '.join(f'{key}={value(node, prop)}' for key, prop in (
            ('solvent', QN.solvent), ('electrolyte', QN.electrolyteText), ('reference', QN.referenceElectrode),
            ('atmosphere', QN.atmosphere), ('additive', QN.additiveText), ('pH', QN.pH)) if val(node, prop) is not None)

    measurements = sorted(set(graph.subjects(RDF.type, QN.Measurement)), key=str)
    observations = sorted(set(graph.subjects(RDF.type, QN.Observation)), key=str)
    by_paper = defaultdict(list)
    by_compound = defaultdict(list)
    for node in measurements + observations:
        by_paper[val(node, QN.fromPaper)].append(node)
        by_compound[val(node, QN.ofCompound)].append(node)

    def page(node):
        return value(val(node, QN.hasEvidence), QN.page) or 'abstract/unknown'

    def measure(node):
        return [value(node, QN.property), value(node, QN.value), value(node, QN.unit),
                value(node, QN.method), condition(val(node, QN.underCondition)), page(node)]

    def table_row(values):
        return '| ' + ' | '.join(values) + ' |'

    no_compound_papers = []
    provenance = 'Table 1, PDF image entry, independently checked'

    def experimental_values(row):
        values = [('E2 exp', row['exp_E2_V'], 'V vs Fc/Fc+')]
        if row['exp_dG_bind_kcal']:
            binding = row['exp_dG_bind_kcal']
            if row['exp_dG_bind_unc_kcal']:
                binding += ' ± ' + row['exp_dG_bind_unc_kcal']
            values.append(('dG bind exp', binding, 'kcal/mol'))
        return values

    for paper in papers:
        nodes = by_paper[paper]
        related = {compound_names[val(n, QN.ofCompound)] for n in nodes if val(n, QN.ofCompound) in compound_names}
        if paper == alherz_paper:
            related.update(identities[identity]['name'] for identity, _ in alherz_rows)
        related = sorted(related)
        if not related:
            no_compound_papers.append(paper)
        body = ['# ' + clean(value(paper, SCHEMA.name)), '', '## Compounds',
                ', '.join(link(name) for name in related) or 'No compound extracted from this paper (needs review)', '', '## Measurements',
                '| Compound | Property | Value | Unit | Method | Condition | Page |', '|---|---|---:|---|---|---|---|']
        for node in nodes:
            if (node, RDF.type, QN.Measurement) in graph:
                compound = val(node, QN.ofCompound)
                body.append(table_row([link(compound_names[compound]) if compound in compound_names else '', *map(cell, measure(node))]))
        if paper == alherz_paper:
            for identity, row in alherz_rows:
                for prop, amount, unit in experimental_values(row):
                    body.append(table_row([link(identities[identity]['name']), prop, cell(amount), unit,
                                           'experiment', cell(row['solvent'] + '; ' + row['ref_electrode']), provenance]))
        body += ['', '## Observations']
        for node in nodes:
            if (node, RDF.type, QN.Observation) in graph:
                compound = val(node, QN.ofCompound)
                target = link(compound_names[compound]) if compound in compound_names else ''
                body.append('- ' + target + ' | ' + ' | '.join(cell(x) for x in (value(node, QN.observationKind), value(node, QN.outcome), condition(val(node, QN.underCondition)), page(node))))
        meta = {'type': 'paper', 'doi': value(paper, SCHEMA.identifier), 'year': value(paper, SCHEMA.datePublished), 'review_tier': value(paper, QN.simReviewTier)}
        (out / 'Papers' / (paper_names[paper] + '.md')).write_text(yaml_note(meta, '\n'.join(body)), encoding='utf-8')

    # ponytail: resolve old citation IDs only when the saved prompt uniquely identifies a note.
    title_lookup = defaultdict(list)
    for identity, item in identities.items():
        if item['source'] == 'kg':
            for title in {value(node, SCHEMA.name) for node in nodes_by_identity[identity]}:
                title_lookup[title].append(identity)
    citations = {}
    for run in runs:
        prompts = sorted((run_dir / run).glob('round_*/prompt*.txt'))
        mappings = defaultdict(lambda: defaultdict(set))
        for prompt_path in prompts:
            match = re.fullmatch(r'round_(\d+)', prompt_path.parent.name)
            if not match:
                continue
            number = int(match.group(1))
            for line_text in prompt_path.read_text().splitlines():
                m = re.match(r'^(D\d+) (\S+) E2=', line_text)
                if m and len(by_smiles.get(m.group(2), [])) == 1:
                    mappings[number][m.group(1)].add(identities[by_smiles[m.group(2)][0]]['name'])
                m = re.match(r'^(K\d+) (.*?) (?:\S* )?\[', line_text)
                if m and len(title_lookup.get(m.group(2).strip(), [])) == 1:
                    mappings[number][m.group(1)].add(identities[title_lookup[m.group(2).strip()][0]]['name'])
        citations[run] = {number: {key: next(iter(values)) for key, values in mapping.items() if len(values) == 1}
                          for number, mapping in mappings.items()}

    def f_v2(row):
        if row.get('E2_eV') is None or row.get('dE_bind_kcal') is None:
            return None
        return (line['a'] * float(row['E2_eV']) + line['b'] - float(row['dE_bind_kcal'])) / line['sigma']

    top_scores = []
    for identity, item in sorted(identities.items()):
        node = item['node']
        ref = item.get('reference')
        latest = item['history'][-1] if item['history'] else None
        numeric = ref or (latest[3] if latest else {})
        e2 = float(numeric['E2_eV']) if numeric.get('E2_eV') is not None else None
        bind = float(numeric['dE_bind_kcal']) if numeric.get('dE_bind_kcal') is not None else None
        margin = (float(ref['E_O2_eV']) - e2) if ref else (latest[3].get('margin') if latest else None)
        cid = value(node, QN.pubchemCID) or item.get('name_cid') or next((row.get('pubchem_cid') for _, _, _, row in reversed(item['history']) if row.get('pubchem_cid') is not None), None)
        detached = numeric.get('co2_detached')
        if isinstance(detached, str):
            detached = {'true': True, 'false': False}.get(detached.lower())
        if detached is False and f_v2(numeric) is not None:
            top_scores.append((f_v2(numeric), item['name']))
        flags = sorted({flag for _, row in item['high'] for flag in row.get('flags', [])}) if item['high'] else None
        aliases = sorted({x for x in (item['key'], item['smiles'], item['title'], item.get('reference_title'), ('Cand ' + item['key'][:8]) if item['history'] and item['key'] else None, *(value(n, SCHEMA.name) for n in nodes_by_identity[identity]), *item.get('table_names', set())) if x})
        meta = {'type': 'compound', 'smiles': item['smiles'], 'inchikey': item['key'], 'pubchem_cid': cid,
                'skeleton': item['skeleton'], 'E2_eV': e2, 'dE_bind_kcal': bind,
                'f_v2': f_v2(numeric), 'o2_margin_V': margin, 'co2_detached': detached,
                'highlevel_flags': flags, 'aliases': aliases, 'source': item['source']}
        nonquinone = bool(item['smiles'] and Chem.MolFromSmiles(item['smiles']) and not structures.is_quinone(item['smiles']))
        if nonquinone:
            meta['quinone'] = False
            if any('quinone' in value(n, QN.skeleton).casefold() for n in nodes_by_identity[identity]):
                meta['skeleton_check'] = 'mismatch'
        if item.get('reference_names'):
            meta['reference_name_matches'] = sorted(item['reference_names'])
        if item.get('unverified_names'):
            meta['pubchem_name_unverified'] = sorted(item['unverified_names'])
        if item.get('smiles_source'):
            meta['smiles_source'] = item['smiles_source']
        if item['history']:
            meta['runs'] = sorted({entry[0] for entry in item['history']})
        if item['source'] == 'loop' and latest:
            meta.update(arm=latest[1], run=latest[0], round=latest[2])
        body = ['# ' + clean(item['title']), '', 'Family: ' + link(family_names[item['family']])]
        if nonquinone:
            body += ['', 'Not a quinone (outside the design domain)']
        ref_family = (ref or {}).get('family')
        if ref_family and ref_family != item['family']:
            body += ['', 'Reference family: ' + link(family_names[ref_family])]
        other_names = sorted(({value(n, SCHEMA.name) for n in nodes_by_identity[identity]} | {item.get('reference_title')}) - {None, '', item['title']})
        if other_names:
            body += ['', 'Also reported as: ' + ', '.join(clean(name) for name in other_names)]
        if item.get('reference_names'):
            body += ['', 'Name resolution: reference-name (' + ', '.join(sorted(item['reference_names'])) + ')']
        if item.get('unverified_names'):
            body += ['', 'PubChem name matches (unverified): ' + ', '.join(sorted(item['unverified_names']))]
        molecule = Chem.MolFromSmiles(item['smiles']) if item['smiles'] else None
        if item['smiles'] and molecule is None:
            body += ['', '## Structure', 'Structure unavailable: invalid SMILES.']
        if molecule is not None:
            key = item['key'] or Chem.MolToInchiKey(molecule)
            candidates = geometries.get(key, [])
            low = next((data for data in candidates if data.get('states', {}).get('Q', {}).get('converged') is True and data['states']['Q'].get('geom_converged') is True and data['states']['Q'].get('xyz')), None)
            best = [structures.attached_adduct(data) for data in candidates]
            best = [adduct for adduct in best if adduct]
            if best:
                low = {**(low or {}), 'adducts': {'best': min(best, key=lambda x: x['energy'])}}
            source, has_adduct = structures.write_assets(out / 'Structures', item['name'], item['smiles'], low, high_geometry.get(key))
            body += ['', '## Structure', f"![[{item['name']}.png]]", f"![[{item['name']}.xyz]]", f'Geometry: {source}']
            if has_adduct:
                body += ['', '### CO2 adduct (Q²⁻·CO₂)', f"![[{item['name']} + CO2.xyz]]"]
        body += ['', '## Literature measurements and observations']
        for compound in nodes_by_identity[identity]:
            for result in by_compound[compound]:
                paper = val(result, QN.fromPaper)
                paper_link = link(paper_names[paper]) if paper in paper_names else 'unknown paper'
                details = measure(result) if (result, RDF.type, QN.Measurement) in graph else [value(result, QN.observationKind), value(result, QN.outcome), condition(val(result, QN.underCondition)), page(result)]
                body.append('- ' + paper_link + ': ' + ' | '.join(cell(x) for x in details))
                quote = clean(val(val(result, QN.hasEvidence), QN.quote))
                if quote:
                    body.append('> ' + (quote[:199] + '…' if len(quote) > 200 else quote))
        table_rows = [row for table_identity, row in alherz_rows if table_identity == identity]
        if table_rows:
            body += ['', '## Alherz 2022 Table 1 measurements']
            for row in table_rows:
                for prop, amount, unit in experimental_values(row):
                    body.append(f'- {link(paper_names[alherz_paper])}: {prop} | {amount} | {unit} | {row["solvent"]} | {provenance}')
        if ref:
            body += ['', '## Reference DFT', f"- E2_eV: {ref['E2_eV']}; dE_bind_kcal: {ref['dE_bind_kcal']}; CO2 detached: {ref['co2_detached']}; family: {cell(ref['family'])}", '- f_v2 is recomputed from the fixed v2 line; energies are electronic, not free energies.']
        if item['high']:
            body += ['', '## High-level']
            for source, row in item['high']:
                body.append(f"- {source}: E2_V={row.get('E2_V')}; dG_bind_1M_kcal={row.get('dG_bind_1M_kcal')}; O2_margin_V={row.get('O2_margin_V')}; flags={cell(row.get('flags', []))}")
        if item['history']:
            body += ['', '## Loop history', '- f_v2 in frontmatter is recomputed from the fixed v2 line when energies are available; history f is the recorded run score.']
            for run, arm, number, row in item['history']:
                mapping = citations[run].get(number, {})
                cites = ', '.join(f'{cell(c)}: {link(mapping[c])}' if c in mapping else cell(c) for c in row.get('cited_ids', []))
                body += [f"- {link(run_names[run])}, {cell(arm)}, round {number}: f={row.get('f')}, margin={row.get('margin')}, PubChem CID={row.get('pubchem_cid')}", f"  - Hypothesis: {cell(row.get('hypothesis'))}", f'  - Cited IDs: {cites or "none"}']
        (out / 'Compounds' / (item['name'] + '.md')).write_text(yaml_note(meta, '\n'.join(body)), encoding='utf-8')

    for run, records in runs.items():
        body = ['# ' + run, '', '| Round | Arm | Compound | f (recorded) | O2 margin (V) | PubChem CID |', '|---:|---|---|---:|---:|---:|']
        for record in records:
            for result in record.get('results', []):
                ids = by_key.get(structure_key(result.get('smiles'), result.get('inchikey')), []) or by_smiles.get(result.get('smiles'), [])
                target = link(identities[ids[0]]['name']) if ids else ''
                body.append(table_row([cell(record.get('round')), cell(record.get('arm') or 'llm'), target, cell(result.get('f')), cell(result.get('margin')), cell(result.get('pubchem_cid'))]))
        (out / 'Runs' / (run_names[run] + '.md')).write_text(yaml_note({'type': 'run', 'run': run}, '\n'.join(body)), encoding='utf-8')

    for family, members in sorted(family_members.items()):
        skeleton_links = ''.join('Skeleton: ' + link(family_names[s]) + '\n\n' for s in sorted(family_skeletons[family]))
        body = '# ' + clean(family) + '\n\n' + skeleton_links + '\n'.join('- ' + link(identities[i]['name']) for i in members)
        (out / 'Families' / (family_names[family] + '.md')).write_text(yaml_note({'type': 'family', 'family': family}, body), encoding='utf-8')

    # ponytail: Dataview does not contribute graph edges, so keep explicit lists too.
    static_families = '\n'.join('- ' + link(family_names[f]) for f in sorted(family_names))
    static_runs = '\n'.join('- ' + link(run_names[r]) for r in sorted(run_names))
    static_top = '\n'.join('- ' + link(name) for _, name in sorted(top_scores, key=lambda x: (-x[0], x[1].casefold(), x[1]))[:10])
    by_year = defaultdict(list)
    for paper in papers:
        by_year[value(paper, SCHEMA.datePublished) or 'Unknown'].append(paper_names[paper])
    static_papers = '\n\n'.join('### ' + year + '\n' + '\n'.join('- ' + link(name) for name in sorted(by_year[year], key=str.casefold)) for year in sorted(by_year, reverse=True))
    index = f'''# Quinone evidence vault

{len(papers)} paper notes, {len(identities)} compound notes, {len(runs)} loop run notes. f_v2 is recomputed from the fixed v2 electronic-energy line; it is not a high-level free energy. Historical run f may use a different line.

## Families (static)
{static_families}

## Runs (static)
{static_runs}

## Top 10 compounds (static)
{static_top}

## Papers by year (static)
{static_papers}

## Highest f_v2
```dataview
TABLE f_v2, o2_margin_V, source FROM "Compounds" WHERE f_v2 != null AND co2_detached != null AND !co2_detached SORT f_v2 DESC
```

## Oxygen-feasible
```dataview
TABLE f_v2, o2_margin_V FROM "Compounds" WHERE o2_margin_V >= 0.15 AND co2_detached != null AND !co2_detached SORT f_v2 DESC
```

## Loop candidates by run
```dataview
TABLE rows.file.link AS Candidates, rows.f_v2 AS f_v2, rows.o2_margin_V AS o2_margin_V FROM "Compounds" FLATTEN runs AS run WHERE run != null GROUP BY run
```

## Papers by year
```dataview
TABLE rows.file.link AS Papers FROM "Papers" GROUP BY year SORT year DESC
```
'''
    (out / 'Index.md').write_text(index, encoding='utf-8')
    readme = Path(__file__).with_name('vault_README.md').read_text(encoding='utf-8')
    (out / 'README.md').write_text(readme.replace('<!-- FAMILY_HUB_LINKS -->', static_families), encoding='utf-8')
    shutil.copytree(Path(__file__).with_name('assets'), out / 'Images')  # README diagrams; embedded with a plain Markdown link
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ['# Unresolved compound names', '', '| Name | Reason |', '|---|---|']
        lines += [f'| {cell(name)} | {cell(reason)} |' for name, reason in sorted(unresolved, key=lambda row: (row[0].casefold(), row[0], row[1]))]
        lines += ['', '## Papers without extracted compounds', '']
        lines += [f'- {clean(value(p, SCHEMA.name))} (DOI: {value(p, SCHEMA.identifier)})' for p in no_compound_papers]
        report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'papers': len(papers), 'compounds': len(identities), 'runs': len(runs), 'name_lookup': dict(sorted(name_counts.items()))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lookup-names', action='store_true')
    args = parser.parse_args()
    print(json.dumps(export(lookup_names=args.lookup_names, report_path=ROOT / '.omc/research/unresolved_names.md'), sort_keys=True))
