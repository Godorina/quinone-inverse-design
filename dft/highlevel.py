"""Composite high-level calculations, restartable per molecule/state/level."""
import argparse
import csv
import json
import numpy as np
import multiprocessing as mp
import os
import traceback
from pathlib import Path

from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dft/runs/highlevel'
REF = ROOT / 'dft/runs/ref_set'
FC = Path(__file__).with_name('highlevel_fc.json')
EV = 27.2114
SMILES = ['O=C1C(F)=C(Cl)C(=O)C(Cl)=C1',
          'O=C1C(F)=C(Cl)C(=O)C(Cl)=C1F',
          'O=C1C(F)=C(Cl)C(=O)C=C1Cl',
          'O=C1C(Cl)=C(Cl)C(=O)C(Cl)=C1Cl']
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
        good = [v for v in low['adducts'].values() if v.get('converged') and v.get('geom_converged') and not v.get('error') and v.get('xyz') and v.get('energy') is not None]
        result = min(good, key=lambda v: v['energy'])
        site = result['o_index']
    else:
        result = low['states'][state]
        if not result.get('converged') or not result.get('geom_converged') or result.get('error'):
            raise ValueError(f'low-level {state} did not converge')
        site = None
    return '\n'.join(result['xyz'].splitlines()[2:]).strip(), site


def inputs():
    items = []
    for smiles in SMILES:
        key = Chem.MolToInchiKey(Chem.MolFromSmiles(smiles))
        matches = sorted((ROOT / 'onto/phase_8_design/runs').glob(f'loop-*/round_*/{key}.json'))
        path = REF / f'{key}.json' if smiles == SMILES[-1] else matches[-1]
        items.append({'id': key, 'smiles': smiles, 'source': str(path), 'low': read(path)})
    return items


def jobs(out=OUT):
    from pyscf import gto
    items = inputs()
    common = read(REF / '_common.json')
    tasks = []
    for item in items + [{'id': 'CO2', 'low': common, 'source': str(REF / '_common.json')}]:
        for state in (['CO2'] if item['id'] == 'CO2' else list(STATES)[:-1]):
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


def summarize(out=OUT):
    out = Path(out)
    fc = read(FC)['Fc_oxidation_eV']
    ref_summary = read(REF / 'summary.json')
    line = ref_summary['line']
    common = read(REF / '_common.json')['states']
    co2 = common['CO2']['energy']
    o2 = (common['O2_radical_anion']['energy'] - common['O2']['energy']) * EV
    rows = []
    for item in inputs():
        low = item['low']
        rad, dian = (low['states'][s]['energy'] for s in ('Q_radical_anion', 'Q_dianion'))
        e2 = (dian - rad) * EV
        adduct = min((v for v in low['adducts'].values() if v.get('converged') and v.get('geom_converged') and not v.get('error')), key=lambda v: v['energy'])
        bind = (adduct['energy'] - dian - co2) * 627.5
        margin = o2 - e2
        f = (line['a'] * e2 + line['b'] - bind) / line['sigma']
        row = {'id': item['id'], 'smiles': item['smiles'], 'low_source': item['source'],
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
             '| InChIKey | 저수준 f | 저수준 O₂ 여유 (V) | ΔE 결합 (kcal/mol) | 고수준 E2 (V) | ΔG 결합 1 M (kcal/mol) | 고수준 O₂ 여유 (V) | 경고 |',
             '|---|---:|---:|---:|---:|---:|---:|---|']
    for row in rows:
        lines.append('| ' + ' | '.join([row['id']] + [fmt(row.get(k)) for k in ('low_f', 'low_O2_margin_V', 'low_dE_bind_kcal', 'E2_V', 'dG_bind_1M_kcal', 'O2_margin_V')] + [', '.join(row.get('flags', [])) or '—']) + ' |')
    lines += ['', f"chloranil 실험: E2 {exp['exp_E2_V']} V, ΔG {exp['exp_dG_bind_kcal']} kcal/mol; 계산−실험: E2 {fmt(chloranil.get('difference_E2_V'))} V, ΔG {fmt(chloranil.get('difference_dG_bind_1M_kcal'))} kcal/mol."]
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpus', default='0,1')
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    if not args.summary:
        tasks = jobs(args.out)
        gpus = args.gpus.split(',')
        ctx = mp.get_context('spawn')
        queue = ctx.Queue()
        for gpu in gpus:
            queue.put(gpu)
        with ctx.Pool(len(gpus), initializer=_init, initargs=(queue,)) as pool:
            pool.map(run_job, tasks, chunksize=1)
    summarize(args.out)


if __name__ == '__main__':
    main()
