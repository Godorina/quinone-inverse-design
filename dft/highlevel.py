"""Composite high-level calculations, restartable per molecule/state/level."""
import argparse
import csv
import json
import math
import numpy as np
import multiprocessing as mp
import os
import shutil
import statistics
import traceback
from pathlib import Path

from rdkit import Chem
from run_set import best_adduct
from o2_calibration import classify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dft/runs/highlevel'
REF = ROOT / 'dft/runs/ref_set'
FC = Path(__file__).with_name('highlevel_fc.json')
PUBCHEM_CACHE = ROOT / 'onto/data/pubchem_cache.json'
EV = 27.2114
class CandidateSet(list):
    """SMILES list with the exact low-level source used for each candidate."""
    def __init__(self, entries):
        super().__init__(smiles for smiles, _ in entries)
        self.sources = dict(entries)


_REFERENCE = 'dft/runs/ref_set/UGNWTBMOAKPKBL-UHFFFAOYSA-N.json'
_CHLORANIL = 'O=C1C(Cl)=C(Cl)C(=O)C(Cl)=C1Cl'
SMILES = CandidateSet([
    ('O=C1C(F)=C(Cl)C(=O)C(Cl)=C1', 'onto/phase_8_design/runs/loop-20261031-151304/round_1/QCOVIANIHBBUDY-UHFFFAOYSA-N.json'),
    ('O=C1C(F)=C(Cl)C(=O)C(Cl)=C1F', 'onto/phase_8_design/runs/loop-20261031-151304/round_1/KOQCAJNJSQGENA-UHFFFAOYSA-N.json'),
    ('O=C1C(F)=C(Cl)C(=O)C=C1Cl', 'onto/phase_8_design/runs/loop-20261102-003356/round_2/SJZRFNPTPXVJLK-UHFFFAOYSA-N.json'),
    (_CHLORANIL, _REFERENCE),
])
# name -> (SMILES and their exact sources, output folder, selected exchange line)
SETS = {'v1': (SMILES, OUT, 'v1'),
        'v2': (CandidateSet([
            ('O=C1C=CC(=O)c2nc3cnc(F)cc3nc21', 'onto/phase_8_design/runs/loop-20261102-212436/round_3/METHVWQPJYOAPU-UHFFFAOYSA-N.json'),
            ('O=C1C=CC(=O)c2nc3nccnc3nc21', 'onto/phase_8_design/runs/loop-20261102-212436/round_2/CAVKVIOROYYCTO-UHFFFAOYSA-N.json'),
            (_CHLORANIL, _REFERENCE),
        ]), ROOT / 'dft/runs/highlevel_v2', 'v2')}
CALIB = CandidateSet([
    ('O=C1C=CC(=O)c2nccnc21', 'dft/runs/ref_set/GHLUWAJFYKILGZ-UHFFFAOYSA-N.json'),
    ('O=C1C(=O)c2cccnc2-c2ncccc21', 'dft/runs/ref_set/KCALAFIVPCAXJI-UHFFFAOYSA-N.json'),
    ('O=C1c2ccsc2C(=O)c2ccsc21', 'dft/runs/ref_set/SIUXRPJYVQQBAF-UHFFFAOYSA-N.json'),
    ('O=C1C=CC(=O)c2nc(-c3ccccc3)c(-c3ccccc3)nc21', 'dft/runs/ref_set/VNBZDYJWROOJRD-UHFFFAOYSA-N.json'),
    ('O=C1c2ccccc2C(=O)c2ccccc21', 'dft/runs/ref_set/RZVHIXYEVGDQDX-UHFFFAOYSA-N.json'),
    ('O=C1C(Cl)=C(Cl)C(=O)c2ccccc21', 'dft/runs/ref_set/SVPKNMBRVBMTLB-UHFFFAOYSA-N.json'),
    ('O=C1C(F)=C(F)C(=O)C(F)=C1F', 'dft/runs/ref_set/JKLYZOGJWVAIQS-UHFFFAOYSA-N.json'),
    ('O=C1C(=O)c2ccccc2-c2ccccc21', 'dft/runs/ref_set/YYVYAPXYZVYDHN-UHFFFAOYSA-N.json'),
    ('O=C1C=C(Cl)C(=O)C(Cl)=C1', 'dft/runs/ref_set/JCARTGJGWCGSSU-UHFFFAOYSA-N.json'),
])
SETS['calib'] = (CALIB, ROOT / 'dft/runs/highlevel_calib', None)
CALIB_STATES = ('Q_radical_anion', 'Q_dianion')

STATES = {'Q': (0, 0), 'Q_radical_anion': (-1, 1), 'Q_dianion': (-2, 0),
          'adduct': (-2, 0), 'CO2': (0, 0)}


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)


def start_geometry(low, state):
    if state == 'adduct':
        result = best_adduct(low['adducts'])
        site = result['o_index']
    else:
        result = low['states'][state]
        if not result.get('converged') or not result.get('geom_converged') or result.get('error'):
            raise ValueError(f'low-level {state} did not converge')
        site = None
    return '\n'.join(result['xyz'].splitlines()[2:]).strip(), site


def inputs(smiles_list=SMILES):
    items = []
    for smiles in smiles_list:
        key = Chem.MolToInchiKey(Chem.MolFromSmiles(smiles))
        path = ROOT / smiles_list.sources[smiles]
        items.append({'id': key, 'smiles': smiles, 'source': str(path), 'low': read(path)})
    return items


def jobs(out=OUT, smiles_list=SMILES, states=None):
    from pyscf import gto
    items = inputs(smiles_list)
    if states is None:
        common = read(REF / '_common.json')
        items += [{'id': 'CO2', 'low': common, 'source': str(REF / '_common.json')}]
    tasks = []
    for item in items:
        for state in (['CO2'] if item['id'] == 'CO2' else (states or list(STATES)[:-1])):
            xyz, site = start_geometry(item['low'], state)
            charge, spin = STATES[state]
            nao = gto.M(atom=xyz, basis='def2-tzvpd', charge=charge, spin=spin, verbose=0).nao
            for level in ('tz', 'svp'):
                spec = {'name': f"{item['id']}_{state}_{level}", 'xyz': xyz, 'charge': charge,
                        'spin': spin, 'task': 'opt' if level == 'tz' else 'opt+freq',
                        'xc': 'wb97m_v', 'basis': 'def2-tzvpd' if level == 'tz' else 'def2-svp',
                        'grids_atom': [99, 590], 'nlc_grids_atom': [50, 194],
                        'nlc_grids_prune': 'sg1', 'thermo_model': 'mrrho', 'temperature': 298.15,
                        'density_fit': True, 'solvent': {'model': 'smd', 'name': 'acetonitrile'},
                        'log': str(Path(out) / item['id'] / f'{state}_{level}.log')}
                tasks.append({'path': str(Path(out) / item['id'] / f'{state}_{level}.json'),
                              'spec': spec, 'source': item['source'], 'o_index': site, 'nao_tz': nao})
    return sorted(tasks, key=lambda task: task['nao_tz'], reverse=True)


def run_job(job, runner=None):
    path = Path(job['path'])
    if path.exists() and read(path).get('status') == 'ok':
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if runner is None:
            from mol_job import run
            runner = run
        result = runner(job['spec'])
    except Exception as exc:
        result = {'status': 'error', 'error': f'{type(exc).__name__}: {exc}',
                  'traceback': traceback.format_exc()}
    result.update(source=job['source'], o_index=job['o_index'], nao_tz=job['nao_tz'])
    save(path, result)


def _init(queue):
    os.environ['CUDA_VISIBLE_DEVICES'] = queue.get()



def _co2_distance(result):
    """O(carbonyl, o_index) to C(CO2) distance in the optimized adduct; CO2 atoms are the last three (C, O, O)."""
    rows = [line.split() for line in result['xyz_final'].strip().splitlines()]
    xyz = np.array([[float(v) for v in r[1:4]] for r in rows])
    return float(np.linalg.norm(xyz[int(result['o_index'])] - xyz[len(rows) - 3]))

def composite(out, key, fc):
    out = Path(out)
    values, flags, adduct_tz = {}, [], None
    for state in STATES:
        folder = out / ('CO2' if state == 'CO2' else key)
        try:
            tz, svp = (read(folder / f'{state}_{level}.json') for level in ('tz', 'svp'))
            if tz['status'] != 'ok' or svp['status'] != 'ok':  # failed or unconverged job (mol_job reports it via status)
                flags.append(f"failed:{state}:{tz['status']}/{svp['status']}")
                continue
            if tz.get('opt_converged') is False or svp.get('opt_converged') is False:  # unconverged geometry: not usable
                flags.append(f'not_converged:{state}')
                continue
            if 'opt_converged' not in tz or 'opt_converged' not in svp:  # kept but visible: convergence was not recorded
                flags.append(f'convergence_unknown:{state}')
            if svp['thermo'].get('n_imag', 0):  # kept, but a composite G with an imaginary mode is suspect
                flags.append(f"imag:{state}:{svp['thermo']['n_imag']}")
            values[state] = tz['energy_Eh'] + svp['thermo']['G_corr_Eh']
            if state == 'adduct':
                adduct_tz = tz
        except (OSError, KeyError, ValueError):
            continue
    if adduct_tz is not None and 'xyz_final' not in adduct_tz:
        flags.append('co2_unchecked')
    if adduct_tz is not None and 'xyz_final' in adduct_tz and _co2_distance(adduct_tz) > 2.0:  # CO2 left the carbonyl O at the high level
        flags.append(f'co2_detached:{_co2_distance(adduct_tz):.2f}A')
        values.pop('adduct')
    row = {'G_Eh': values, 'flags': flags}
    if {'Q', 'Q_radical_anion'} <= values.keys():
        row['E1_V'] = -(values['Q_radical_anion'] - values['Q']) * EV - fc
    if {'Q_radical_anion', 'Q_dianion'} <= values.keys():
        row['E2_V'] = -(values['Q_dianion'] - values['Q_radical_anion']) * EV - fc
        row['O2_margin_V'] = row['E2_V'] + 1.23
        row['O2_pass'] = row['O2_margin_V'] >= 0.15
    if {'adduct', 'Q_dianion', 'CO2'} <= values.keys():
        row['dG_bind_1atm_kcal'] = (values['adduct'] - values['Q_dianion'] - values['CO2']) * 627.5
        row['dG_bind_1M_kcal'] = row['dG_bind_1atm_kcal'] - 1.894
    return row


def summarize(out=OUT, smiles_list=SMILES, line_key='v1'):
    out = Path(out)
    fc = read(FC)['Fc_oxidation_eV']
    line = read(REF / 'lines.json')[line_key]
    common = read(REF / '_common.json')['states']
    co2 = common['CO2']['energy']
    o2 = (common['O2_radical_anion']['energy'] - common['O2']['energy']) * EV
    rows = []
    cache = read(PUBCHEM_CACHE) if PUBCHEM_CACHE.exists() else {}
    for item in inputs(smiles_list):
        low = item['low']
        rad, dian = (low['states'][s]['energy'] for s in ('Q_radical_anion', 'Q_dianion'))
        e2 = (dian - rad) * EV
        adduct = best_adduct(low['adducts'])
        bind = (adduct['energy'] - dian - co2) * 627.5
        margin = o2 - e2
        f = (line['a'] * e2 + line['b'] - bind) / line['sigma']
        row = {'id': item['id'], 'smiles': item['smiles'], 'low_source': item['source'],
               'pubchem_cid': cache.get(item['id'], {}).get('cid'),
               'o_index': adduct['o_index'], 'low_f': f, 'low_O2_margin_V': margin,
               'low_dE_bind_kcal': bind, **composite(out, item['id'], fc)}
        rows.append(row)
    with (ROOT / 'onto/phase_4b_extend/alherz2022_table1.csv').open(newline='') as handle:
        exp = next(r for r in csv.DictReader(handle) if r['entry'] == '4ClQ')
    chloranil = rows[-1]
    chloranil['experiment'] = {'E2_V': float(exp['exp_E2_V']), 'dG_bind_1M_kcal': float(exp['exp_dG_bind_kcal'])}
    for field in ('E2_V', 'dG_bind_1M_kcal'):
        if field in chloranil:
            chloranil['difference_' + field] = chloranil[field] - chloranil['experiment'][field]
    summary = {'Fc_oxidation_eV': fc, 'molecules': rows}
    save(out / 'summary.json', summary)
    def fmt(value):
        return '—' if value is None else f'{value:.3f}'
    lines = ['# 고수준 비교', '', '저수준 f와 O₂ 여유는 B3LYP 전자 에너지 기준; 고수준은 Fc 및 실험 O₂ 기준.', '',
             '| InChIKey | PubChem CID | 저수준 f | 저수준 O₂ 여유 (V) | ΔE 결합 (kcal/mol) | 고수준 E2 (V) | ΔG 결합 1 M (kcal/mol) | 고수준 O₂ 여유 (V) | 경고 |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in rows:
        lines.append('| ' + ' | '.join([row['id'], str(row['pubchem_cid']) if row['pubchem_cid'] is not None else '—'] + [fmt(row.get(k)) for k in ('low_f', 'low_O2_margin_V', 'low_dE_bind_kcal', 'E2_V', 'dG_bind_1M_kcal', 'O2_margin_V')] + [', '.join(row.get('flags', [])) or '—']) + ' |')
    lines += ['', f"chloranil 실험: E2 {exp['exp_E2_V']} V, ΔG {exp['exp_dG_bind_kcal']} kcal/mol; 계산−실험: E2 {fmt(chloranil.get('difference_E2_V'))} V, ΔG {fmt(chloranil.get('difference_dG_bind_1M_kcal'))} kcal/mol."]
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    return summary


def summarize_calib(out, smiles_list=CALIB, calibration_path=REF / 'o2_calib.json'):
    """Produce a calibration only when every new calculation is usable."""
    out = Path(out)
    fc = read(FC)['Fc_oxidation_eV']
    common = read(REF / '_common.json')['states']
    o2 = (common['O2_radical_anion']['energy'] - common['O2']['energy']) * EV
    rows = {}

    def add(item, high):
        if high.get('flags') or 'E2_V' not in high or 'O2_margin_V' not in high:
            raise ValueError(f"Incomplete or flagged calibration result: {item['id']}")
        rad, dian = (item['low']['states'][s]['energy'] for s in CALIB_STATES)
        e2 = (dian - rad) * EV
        low_margin = o2 - e2
        if not all(math.isfinite(v) for v in (e2, low_margin, high['E2_V'], high['O2_margin_V'])):
            raise ValueError(f"Non-finite calibration result: {item['id']}")
        row = {'id': item['id'], 'smiles': item['smiles'], 'class': classify(item['smiles']),
               'low_source': item['source'], 'low_E2_eV': e2, 'low_O2_margin_V': low_margin,
               'E2_V': high['E2_V'], 'O2_margin_V': high['O2_margin_V'],
               'shift_V': high['O2_margin_V'] - low_margin}
        if row['id'] in rows:
            if rows[row['id']] != row:
                raise ValueError(f"Conflicting calibration result: {row['id']}")
            return
        rows[row['id']] = row

    for item in inputs(smiles_list):
        add(item, composite(out, item['id'], fc))
    for name in ('v1', 'v2'):
        candidates, previous_out, _ = SETS[name]
        previous = {row['id']: row for row in read(previous_out / 'summary.json')['molecules']}
        for item in inputs(candidates):
            add(item, previous[item['id']])
    calibration = {}
    for category in ('carbocyclic', 'heterocyclic'):
        shifts = [r['shift_V'] for r in rows.values() if r['class'] == category]
        if len(shifts) < 2:
            raise ValueError(f'Insufficient {category} calibration results')
        # ponytail: use one shift per class; consider an E2 slope if residuals demand it.
        calibration[category] = {'mean_shift': statistics.mean(shifts), 'sd': statistics.stdev(shifts), 'n': len(shifts)}
    summary = {'Fc_oxidation_eV': fc, 'molecules': list(rows.values()), 'calibration': calibration}
    save(out / 'summary.json', summary)
    lines = ['# O₂ calibration', '', '| InChIKey | class | low E2 (eV) | low margin (V) | high E2 (V) | high margin (V) | shift (V) |', '|---|---|---:|---:|---:|---:|---:|']
    for r in rows.values():
        lines.append(f"| {r['id']} | {r['class']} | {r['low_E2_eV']:.3f} | {r['low_O2_margin_V']:.3f} | {r['E2_V']:.3f} | {r['O2_margin_V']:.3f} | {r['shift_V']:.3f} |")
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    save(calibration_path, calibration)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpus', default='0,1')
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--set', choices=SETS, default='v1')
    args = parser.parse_args()
    smiles_list, out, line_key = SETS[args.set]
    for name in (() if args.set == 'calib' else ('CO2', inputs(smiles_list)[-1]['id'])):  # reuse finished CO2/chloranil jobs from the v1 folder
        if out != OUT and (OUT / name).exists() and not (out / name).exists():
            shutil.copytree(OUT / name, out / name)
    if not args.summary:
        tasks = jobs(out, smiles_list, states=CALIB_STATES if args.set == 'calib' else None)
        gpus = args.gpus.split(',')
        ctx = mp.get_context('spawn')
        queue = ctx.Queue()
        for gpu in gpus:
            queue.put(gpu)
        with ctx.Pool(len(gpus), initializer=_init, initargs=(queue,)) as pool:
            pool.map(run_job, tasks, chunksize=1)
    if args.set == 'calib':
        summarize_calib(out, smiles_list)
    else:
        summarize(out, smiles_list, line_key)


if __name__ == '__main__':
    main()
