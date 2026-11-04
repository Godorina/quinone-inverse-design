"""MLP binding calibration and E2-GP prescreen; no DFT execution."""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from rdkit import Chem

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'onto/phase_8_design'),str(ROOT/'dft')]
from generate import context, _inchikey
from loop import t0
from run_set import carbonyl_sites, _done
from dft import embed
from o2_calibration import classify
from tier1 import atomic_json, COMMON, CALIB, load_calibration
import surrogate

OUT=ROOT/'dft/runs/funnel_mlp'
MODEL=ROOT/'models/ckpt_epoch_82.pkl'
BAM_PYTHON=Path('/home/hgpark/Desktop/localLLM/qwen3.8/env-bam/bin/python')
BAM_SOURCE=Path('/home/hgpark/whlee/hgpark/ver2_261101/BAM-torch')
LIBRARY=Path(__file__).with_name('library.csv')
CANDIDATES=Path(__file__).with_name('dft_candidates.csv')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unsupported(smiles):
    mol=Chem.MolFromSmiles(smiles)
    if not mol: return 'invalid_smiles'
    # Br is absent from the documented training set. Other non-v2 atoms are excluded.
    bad=sorted({a.GetSymbol() for a in mol.GetAtoms()}-{'C','H','N','O','F','Cl','S'})
    if bad: return 'unsupported_element:'+','.join(bad)
    reason=t0(smiles)
    return 'outside_domain:'+reason if reason else None


def training_records():
    """One latest available DFT label per InChIKey; E2 can exist for detached adducts."""
    rows=list(context()['dft'])
    for path in sorted((ROOT/'onto/phase_8_design/runs').glob('*/ledger.jsonl')):
        for text in path.read_text().splitlines(): rows.extend(json.loads(text).get('results',[]))
    records={}
    for row in rows:
        try:
            smiles=row['smiles']; key=_inchikey(smiles)
            if not key or (row.get('inchikey') and row['inchikey']!=key): continue
            e2=float(row['E2_eV'])
            if not math.isfinite(e2): continue
            item={'inchikey':key,'smiles':smiles,'E2_eV':e2}
            if row.get('co2_detached') is False:
                binding=float(row['dE_bind_kcal'])
                if math.isfinite(binding): item['dE_bind_kcal']=binding
            # Preserve an attached binding label if another run detached.
            if key in records and 'dE_bind_kcal' in records[key] and 'dE_bind_kcal' not in item:
                item['dE_bind_kcal']=records[key]['dE_bind_kcal']
            records[key]=item
        except (KeyError,TypeError,ValueError): continue
    return list(records.values())


def fit_calibration(rows):
    if len(rows)<3: raise ValueError('At least three matched attached molecules required')
    x=np.asarray([r['mlp_ev'] for r in rows],float); y=np.asarray([r['dft_kcal'] for r in rows],float)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.ptp(x)<1e-10: raise ValueError('Invalid or constant calibration data')
    def fit(a,b):
        X=np.column_stack((a,np.ones(len(a))))
        if np.linalg.matrix_rank(X)<2: raise ValueError('Insufficient independent calibration points')
        return np.linalg.lstsq(X,b,rcond=None)[0]
    alpha,beta=fit(x,y); residual=y-(alpha*x+beta)
    loo=[]
    for i in range(len(x)):
        keep=np.arange(len(x))!=i
        a,b=fit(x[keep],y[keep]); loo.append(float(y[i]-(a*x[i]+b)))
    den=float(np.sum((y-y.mean())**2)); slices={}
    for field in ('class','training_core'):
        groups=defaultdict(list)
        for row,r in zip(rows,residual): groups[row.get(field,'unknown')].append(float(r))
        if field=='training_core':
            for k in ('seen','new','unknown'): groups.setdefault(k,[])
        slices[field]={k:{'n':len(v),'mean_residual':float(np.mean(v)) if v else None,'rmse':float(np.sqrt(np.mean(np.square(v)))) if v else None} for k,v in sorted(groups.items())}
    return {'n':len(rows),'alpha':float(alpha),'beta':float(beta),'r2':float(1-np.sum(residual**2)/den) if den else None,
            'rmse':float(np.sqrt(np.mean(residual**2))),'loo_rmse':float(np.sqrt(np.mean(np.square(loo)))),
            'baseline_loo_rmse':float(np.sqrt(np.mean(((y-y.mean())*len(y)/(len(y)-1))**2))), 'slices':slices}


def calibration_warning(calib):
    return calib['r2'] is None or calib['r2'] < .5 or calib['loo_rmse'] > .8 * calib['baseline_loo_rmse']


def validate_calibration(calib,model_sha,config=None):
    if calib.get('model_sha256')!=model_sha or (config is not None and calib.get('config')!=config):
        raise ValueError('Calibration does not match the model and relaxation settings')
    if not all(math.isfinite(float(calib[k])) for k in ('alpha','beta','loo_rmse')): raise ValueError('Invalid calibration')


def oxygen_plausible(margin,std): return margin+std >= .15


def pick_candidates(rows,n=50,control_n=10,seed=0,kappa=1.):
    pool=[r for r in rows if oxygen_plausible(r['margin_pred'],r['e2_std'])]
    smiles=[r['smiles'] for r in pool]; mean=[r['f_pred'] for r in pool]; std=[r['f_std'] for r in pool]
    picked=surrogate.select(smiles,mean,std,n,kappa=kappa) if pool and n else []
    order=list(range(len(pool))); random.Random(seed).shuffle(order)
    random_indices=surrogate.select(smiles,mean,std,control_n,order=order) if pool and control_n else []
    return [pool[i] for i in picked], [pool[i] for i in random_indices]


def gp_e2(records):
    model=surrogate.GP([r['smiles'] for r in records],[r['E2_eV'] for r in records])
    y=np.asarray([r['E2_eV'] for r in records]); n=len(y)
    if n<3: raise ValueError('At least three E2 training molecules required')
    inv=np.linalg.solve(model.chol.T,np.linalg.solve(model.chol,np.eye(n))); d=np.diag(inv)
    # Recompute the constant mean for each left-out point.
    loo_mean=(y.sum()-y)/(n-1)
    errors=model.alpha/d-(loo_mean-model.mean)*np.sum(inv,axis=1)/d
    rmse=float(np.sqrt(np.mean(errors**2)))
    scale=rmse / float(np.sqrt(np.mean(1/d)))
    return model,rmse,scale


def build_jobs(rows):
    jobs=[]; skipped=defaultdict(int)
    for row in rows:
        reason=unsupported(row['smiles'])
        if reason: skipped[reason]+=1; continue
        key=_inchikey(row['smiles'])
        if not key or (row.get('inchikey') and row['inchikey']!=key): skipped['inchikey_mismatch']+=1; continue
        try:
            symbols,coords=embed(row['smiles']); sites=carbonyl_sites(row['smiles'])
            if not sites: skipped['no_carbonyl']+=1; continue
            jobs.append({'inchikey':key,'smiles':row['smiles'],'symbols':symbols,'coords':coords.tolist(),'sites':sites})
        except (ValueError,RuntimeError) as exc:
            skipped['embedding_failed']+=1
    return jobs,dict(skipped)


def launch(rows,args,config):
    jobs,skipped=build_jobs(rows)
    args.out.mkdir(parents=True,exist_ok=True)
    task={'out':str(args.out.resolve()),'checkpoint':str(args.model.resolve()),'device':args.device,
          'fmax':args.fmax,'maxsteps':args.maxsteps,'config':config,'items':jobs}
    jobfile=args.out/'_jobs.json'; atomic_json(jobfile,task)
    env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONNOUSERSITE']='1'
    env['PYTHONPATH']=str(BAM_SOURCE)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    subprocess.run([str(args.bam_python),str(Path(__file__).with_name('mlp_worker.py')),str(jobfile)],env=env,check=True)
    report=json.loads((args.out/'_last_worker_report.json').read_text())
    print('skipped:',json.dumps(skipped,sort_keys=True))
    errors=[r for r in report if r.get('error')]
    incomplete=sum(not r.get('complete') for r in report)
    print(f'Worker: {len(report)} processed, {incomplete} incomplete, {len(errors)} errors')
    if errors: raise RuntimeError(f'MLP worker errors; inspect {args.out / "_last_worker_report.json"}')


def read_mlp(out,keys,config):
    results={}
    for key in keys:
        path=out/(key+'.json')
        if not path.exists(): continue
        data=json.loads(path.read_text())
        if data.get('config')!=config: raise ValueError(f'Mismatched MLP checkpoint: {path}')
        if data.get('complete') and not data.get('detached') and math.isfinite(float(data.get('delta_e_mlp_ev',float('nan')))):
            results[key]=float(data['delta_e_mlp_ev'])
    return results


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=['smiles','inchikey','core','substituents','sa_score','E2_pred_eV','E2_std_eV','raw_margin','margin_pred','o2_calibration','binding_pred_kcal','f_pred','f_std','ucb','survives']
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)


def main():
    p=argparse.ArgumentParser(); mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--calibrate',action='store_true'); mode.add_argument('--screen',action='store_true'); mode.add_argument('--candidates',action='store_true')
    p.add_argument('--library',type=Path,default=LIBRARY); p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--model',type=Path,default=MODEL); p.add_argument('--bam-python',type=Path,default=BAM_PYTHON)
    p.add_argument('--device',default='cuda:1'); p.add_argument('--fmax',type=float,default=.05); p.add_argument('--maxsteps',type=int,default=300)
    p.add_argument('--limit',type=int); p.add_argument('--n',type=int,default=50); p.add_argument('--control-n',type=int,default=10)
    p.add_argument('--seed',type=int,default=0); p.add_argument('--kappa',type=float,default=1.)
    p.add_argument('--training-cores',type=Path,help='JSON array of independently verified training-core labels')
    args=p.parse_args()
    if args.maxsteps<1 or args.fmax<=0 or args.n<1 or args.control_n<0 or (args.limit is not None and args.limit<1): p.error('invalid count or relaxation settings')
    model_sha=sha(args.model)
    config=hashlib.sha256(json.dumps({'model':model_sha,'fmax':args.fmax,'maxsteps':args.maxsteps,'version':1},sort_keys=True).encode()).hexdigest()
    records=training_records()
    if args.calibrate:
        attached=[r for r in records if 'dE_bind_kcal' in r]
        launch(attached[:args.limit],args,config)
        mlp=read_mlp(args.out,[r['inchikey'] for r in attached],config)
        # Without original training-core provenance, unknown is honest; optional verified labels enable the requested slices.
        cores=set(json.loads(args.training_cores.read_text())) if args.training_cores else None
        from enumerate import classify_core
        paired=[]
        for r in attached:
            if r['inchikey'] not in mlp: continue
            try: core=classify_core(r['smiles'])
            except ValueError: core=None
            group=('seen' if core in cores else 'new') if cores is not None and core else 'unknown'
            paired.append({'mlp_ev':mlp[r['inchikey']],'dft_kcal':r['dE_bind_kcal'],'class':classify(r['smiles']),'training_core':group,'inchikey':r['inchikey']})
        result=fit_calibration(paired); result.update(model_sha256=model_sha,config=config,training_cores=sorted(cores) if cores is not None else None,inchikeys=[r['inchikey'] for r in paired])
        atomic_json(args.out/'calibration.json',result); print(json.dumps(result,indent=2))
        if calibration_warning(result): print('WARNING: R² < 0.5 or LOO RMSE > 0.8 × mean-only baseline; ranking power is weak')
        return
    with args.library.open() as f: library=list(csv.DictReader(f))
    if args.limit is not None: library=library[:args.limit]
    if args.screen:
        launch(library,args,config); return
    calibration=json.loads((args.out/'calibration.json').read_text()); validate_calibration(calibration,model_sha,config)
    if calibration['loo_rmse']>3.2: print('WARNING: LOO RMSE > 3.2 kcal/mol; ranking power is weak')
    mlp=read_mlp(args.out,[r['inchikey'] for r in library],config)
    candidates=[r for r in library if r['inchikey'] in mlp and not unsupported(r['smiles'])]
    if not candidates: raise ValueError('No completed attached MLP results')
    model,loo,scale=gp_e2(records); mu,std=model.predict([r['smiles'] for r in candidates]); std=std*scale
    common=json.loads(COMMON.read_text())['states']
    if not all(_done(common.get(k)) for k in ('O2', 'O2_radical_anion')):
        raise ValueError('O2 reference states are incomplete')
    oxygen=(common['O2_radical_anion']['energy']-common['O2']['energy'])*27.2114
    calibration_o2=load_calibration(CALIB) if CALIB.exists() else None
    line=json.loads((ROOT/'dft/runs/ref_set/lines.json').read_text())['v2']
    scored=[]
    for row,e2,e2sd in zip(candidates,mu,std):
        raw=oxygen-float(e2); margin=raw+(calibration_o2[classify(row['smiles'])]['mean_shift'] if calibration_o2 else 0.)
        binding=calibration['alpha']*mlp[row['inchikey']]+calibration['beta']
        f=(line['a']*float(e2)+line['b']-binding)/line['sigma']
        fstd=math.hypot(line['a']*float(e2sd),calibration['loo_rmse'])/line['sigma']
        scored.append({**row,'E2_pred_eV':float(e2),'E2_std_eV':float(e2sd),'raw_margin':raw,'margin_pred':margin,'e2_std':float(e2sd),
                       'o2_calibration':'calibrated' if calibration_o2 else 'uncalibrated','binding_pred_kcal':binding,'f_pred':f,'f_std':fstd,'ucb':f+args.kappa*fstd,'survives':True})
    selected,control=pick_candidates(scored,args.n,args.control_n,args.seed,args.kappa)
    write_csv(CANDIDATES,selected); write_csv(CANDIDATES.with_name('dft_candidates_random.csv'),control)
    atomic_json(args.out/'candidates_manifest.json', {'model_sha256':model_sha,'config':config,
                'library_sha256':sha(args.library),'binding_calibration_sha256':sha(args.out/'calibration.json'),
                'e2_loo_rmse_ev':loo,'e2_std_scale':scale,'e2_training_keys':sorted(r['inchikey'] for r in records),
                'o2_calibration_sha256':sha(CALIB) if calibration_o2 else None,'line_sha256':sha(ROOT/'dft/runs/ref_set/lines.json'),
                'seed':args.seed,'kappa':args.kappa,'selected':len(selected),'random_control':len(control)})
    print(json.dumps({'e2_training_n':len(records),'e2_loo_rmse_ev':loo,'o2':'calibrated' if calibration_o2 else 'uncalibrated','screened_attached':len(scored),'o2_plausible':sum(oxygen_plausible(r['margin_pred'],r['e2_std']) for r in scored),'selected':len(selected),'random_control':len(control),'seed':args.seed},indent=2))

if __name__=='__main__': main()
