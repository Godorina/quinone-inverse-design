"""BAM environment worker: model-only dianion/adduct relaxations, JSON I/O."""
import argparse
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path
import numpy as np


def save(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, allow_nan=False))
    os.replace(temp, path)


def relax(symbols, coords, calc, fmax=.05, maxsteps=300):
    from ase import Atoms
    from ase.optimize import FIRE, LBFGS
    atoms = Atoms(symbols=symbols, positions=coords); atoms.calc = calc
    start = time.monotonic()
    # Split one shared step budget across FIRE and LBFGS.
    with FIRE(atoms, logfile=None) as fire:
        fire.run(fmax=fmax, steps=maxsteps // 2)
        nf = fire.get_number_of_steps()
    with LBFGS(atoms, logfile=None) as opt:
        opt.run(fmax=fmax, steps=maxsteps - nf)
        nl = opt.get_number_of_steps()
    force = float(np.linalg.norm(atoms.get_forces(), axis=1).max())
    return {'symbols': symbols, 'coords': atoms.positions.tolist(), 'energy_ev': float(atoms.get_potential_energy()),
            'converged': force <= fmax, 'steps': nf+nl, 'fire_steps': nf, 'lbfgs_steps': nl,
            'fmax': force, 'seconds': time.monotonic()-start}


def place_co2(symbols, coords, index):
    # Same geometry as dft.co2_adduct; this environment need not import PySCF/RDKit.
    coords = np.asarray(coords, dtype=float); oxygen = coords[index]
    carbon = min((i for i, s in enumerate(symbols) if s == 'C'), key=lambda i: np.linalg.norm(coords[i] - oxygen))
    direction = oxygen - coords[carbon]; direction /= np.linalg.norm(direction)
    axis = np.cross(direction, [1., 0., 0.])
    if np.linalg.norm(axis) < 1e-6: axis = np.cross(direction, [0., 1., 0.])
    axis /= np.linalg.norm(axis)
    c = oxygen + 1.45 * direction; angle = np.deg2rad(65.)
    a = c + 1.16 * (direction * np.cos(angle) + axis * np.sin(angle))
    b = c + 1.16 * (direction * np.cos(angle) - axis * np.sin(angle))
    return list(symbols) + ['C','O','O'], np.vstack([coords,c,a,b])


def best_attached(adducts):
    good = [a for a in adducts.values() if a.get('converged') and not a.get('detached') and math.isfinite(a['energy_ev'])]
    return min(good, key=lambda a:a['energy_ev']) if good else None


def run_one(job, path, calc, co2_energy, config, fmax, maxsteps):
    path = Path(path)
    if path.exists():
        data = json.loads(path.read_text())
        if data['config'] != config or data['smiles'] != job['smiles'] or data['inchikey'] != job['inchikey']:
            raise ValueError('Checkpoint/input settings changed; use a new output directory')
    else:
        data = {'inchikey':job['inchikey'], 'smiles':job['smiles'], 'config':config, 'states':{}, 'adducts':{}}
    states = data['states']
    if not states.get('Q2',{}).get('converged'):
        previous = states.get('Q2', {})
        states['Q2'] = relax(job['symbols'],previous.get('coords', job['coords']),calc,fmax,maxsteps); save(path,data)
    q = states['Q2']
    if not q['converged']: return data
    for site in job['sites']:
        key = str(site)
        if not data['adducts'].get(key,{}).get('converged'):
            symbols, coords = place_co2(q['symbols'],q['coords'],site)
            previous = data['adducts'].get(key, {})
            result = relax(symbols,previous.get('coords', coords),calc,fmax,maxsteps)
            result['o_index'] = site
            result['oc_distance_angstrom'] = float(np.linalg.norm(np.asarray(result['coords'][site]) - np.asarray(result['coords'][-3])))
            result['detached'] = result['oc_distance_angstrom'] > 2.0
            data['adducts'][key] = result; save(path,data)
    if data['adducts'] and all(a.get('converged') for a in data['adducts'].values()):
        best = best_attached(data['adducts'])
        data['complete'] = True
        data['detached'] = best is None
        if best is not None:
            data['delta_e_mlp_ev'] = best['energy_ev'] - q['energy_ev'] - co2_energy
            data['best_o_index'] = best['o_index']
        save(path,data)
    return data


def configure_device(device, torch):
    """BAM ignores CUDA indices; set and check its current CUDA device explicitly."""
    if device == 'cpu':
        return device
    match = re.fullmatch(r'cuda:(\d+)', device)
    if not match:
        raise ValueError('Use cpu or an explicit cuda:N device')
    index = int(match.group(1))
    if not torch.cuda.is_available() or index >= torch.cuda.device_count():
        raise RuntimeError(f'Requested {device} is not available in CUDA_VISIBLE_DEVICES')
    torch.cuda.set_device(index)
    if torch.cuda.current_device() != index:
        raise RuntimeError(f'Could not select {device}')
    return device


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('jobfile',type=Path); args=parser.parse_args()
    job=json.loads(args.jobfile.read_text()); out=Path(job['out']); out.mkdir(parents=True,exist_ok=True)
    import torch
    from bam_torch.tase.base_calculator import RACECalculator
    device=configure_device(job['device'],torch)
    ckpt=job['checkpoint']; calc=RACECalculator(model=ckpt,device=device)
    if device != 'cpu' and (calc.device.type != 'cuda' or torch.cuda.current_device() != int(device.split(':')[1])):
        raise RuntimeError(f'Calculator did not use requested device {device}')
    weights=torch.load(ckpt,map_location='cpu',weights_only=False)
    pss=weights['per_head_scale_shift'][0]; calc.e_corr=sum(map(float,pss))/len(pss); calc.element_wise=False
    # CO2 is outside training; the one common reference is absorbed by fitted intercept.
    co2path=out/'_co2.json'; config=job['config']
    if co2path.exists():
        ref=json.loads(co2path.read_text())
        if ref['config'] != config: raise ValueError('CO2 checkpoint settings changed')
    else: ref={'config':config}
    if not ref.get('result',{}).get('converged'):
        ref['result']=relax(['O','C','O'], [[-1.16,0,0],[0,0,0],[1.16,0,0]],calc,job['fmax'],job['maxsteps']); save(co2path,ref)
    if not ref['result']['converged']: raise RuntimeError('MLP CO2 reference did not converge')
    outcomes=[]
    for item in job['items']:
        try:
            result=run_one(item,out/(item['inchikey']+'.json'),calc,ref['result']['energy_ev'],config,job['fmax'],job['maxsteps'])
            outcomes.append({'inchikey':item['inchikey'],'complete':result.get('complete',False),'detached':result.get('detached')})
        except Exception as exc:
            outcomes.append({'inchikey':item['inchikey'],'error':str(exc)})
        print(json.dumps(outcomes[-1]),flush=True)
    save(out/'_last_worker_report.json', outcomes)

if __name__=='__main__': main()
