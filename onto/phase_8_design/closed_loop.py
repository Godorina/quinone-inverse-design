"""Three-round hypothesis generation and evaluation, with resumable round artifacts."""
import os
import argparse
import csv
import hashlib
import math
import json
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from generate import SUBSTITUENTS, _inchikey, call_llm, check, context, prompt, sa_score
from loop import edit
from pubchem import lookup as pubchem_lookup

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'dft'))
from o2_calibration import classify


def o2_feasible(rows):
    """Parents for the random arm: O2 margin >= 0.15 V and CO2 attached (reference rows say o2_margin_V, loop rows say margin)."""
    return [x for x in rows if x.get('margin', x.get('o2_margin_V')) >= .15 and not x['co2_detached']]

def score(row, line, calibration=None):
    f = (line['a'] * row['E2_eV'] + line['b'] - row['dE_bind_kcal']) / line['sigma']
    margin = row['E_O2_eV'] - row['E2_eV']
    details = {}
    if calibration is not None:
        category = classify(row['smiles'])
        corrected = margin + calibration[category]['mean_shift']
        details = {'raw_margin': margin, 'calibrated_margin': corrected, 'o2_class': category}
        margin = corrected
    return {**row, **details, 'f': f, 'margin': margin, 'success': f >= 2 and margin >= .15 and not row['co2_detached']}


def loop_prompt(ctx, history, per_round=5):
    previous = [p['smiles'] for r in history for p in r['accepted']]
    evidence = prompt(ctx, previous).split('DFT evidence:\n', 1)[1]
    feedback = [{'results': r['results'], 'rejected': r['rejected']} for r in history]
    rules = ("Use reference parents; add, replace, remove or move only F, Cl, Br, NH2, OH. " if ctx.get("domain", "v2") == "v1" else "Use reference parents and neutral quinones with a ring 1,2- or 1,4-carbonyl pair, C/H/N/O/F/Cl/Br/S only and at most 30 heavy atoms. ")
    calibration_note = 'O2 margins are calibrated to high level. ' if ctx.get('o2_calibration') else ''
    return (calibration_note + f'Propose exactly {per_round} testable hypotheses to exceed the tradeoff line: f >= 2, O2 margin >= 0.15 V, and no CO2 detachment. DFT will decide; proof of success is not required. '
            'Cite D/K evidence supporting the direction. Return insufficient_evidence only when no evidence can be cited. '
            f"{rules}"
            'Return JSON proposals with parent_id, smiles, edits, cited_ids, hypothesis. '
            'Promote directions that increased f, avoid those that decreased f, and explain why in hypothesis. '
            f'Do not repeat SMILES: {json.dumps(previous)}\nHistory: {json.dumps(feedback)}\nDFT evidence:\n{evidence}')


def add_extra_refs(ctx, directories):
    ctx['extra_seen'] = set()
    for directory in directories:
        for path in sorted(directory.glob('round_*/*.json')):
            data = json.loads(path.read_text())
            states, adducts = data.get('states', {}), data.get('adducts', {})
            required = [states.get(k, {}) for k in ('Q', 'Q_radical_anion', 'Q_dianion')]
            if not isinstance(adducts, dict) or not adducts:
                continue
            calculations = required + list(adducts.values())
            if not all(isinstance(x, dict) and x.get('converged') is True and x.get('geom_converged') is True for x in calculations):
                continue
            smiles = data.get('smiles')
            key = _inchikey(smiles) if isinstance(smiles, str) else None
            if key:
                ctx['ref_fps'].append(smiles)
                ctx['extra_seen'].add(key)


def compare_runs(dir_a, dir_b):
    def read(directory):
        path = Path(directory)
        rows = [json.loads(line) for line in (path / 'ledger.jsonl').read_text().splitlines() if line.strip()]
        return rows, rows[0].get('arm', 'llm') if rows else 'unknown'
    a, arm_a = read(dir_a)
    b, arm_b = read(dir_b)
    calibrations = [r.get('o2_calib') for r in a + b]
    if calibrations and any(c != calibrations[0] for c in calibrations[1:]):
        raise ValueError('Cannot compare runs with different oxygen calibrations')
    recorded = [r.get('line') for r in a + b]
    known = [line for line in recorded if line is not None]
    if known and any(line != known[0] for line in known[1:]):
        raise ValueError('Cannot compare runs with different fitted lines')
    def maximum(rows, number, oxygen=False):
        results = next((r['results'] for r in rows if r['round'] == number), [])
        values = [x['f'] for x in results if not oxygen or x['margin'] >= .15]
        return f'{max(values):.3f}' if values else 'N/A'
    lines = [f'| round | {arm_a} max f | {arm_a} O2 max f | {arm_b} max f | {arm_b} O2 max f |', '|---|---:|---:|---:|---:|']
    if not recorded or any(line is None for line in recorded):
        lines.insert(0, 'WARNING: fitted line missing from legacy records; comparability is unverified.\n')
    for number in sorted({r['round'] for r in a + b}):
        lines.append(f'| {number} | {maximum(a, number)} | {maximum(a, number, True)} | {maximum(b, number)} | {maximum(b, number, True)} |')
    return '\n'.join(lines) + '\n'


def evaluate(path):
    root = Path(__file__).resolve().parents[2]
    subprocess.run([sys.executable, str(root / 'dft/run_set.py'), '--input', str(path / 'input.csv'), '--out', str(path), '--gpus', os.environ.get('LOOP_GPUS', '0,1')], check=True)  # LOOP_GPUS=0 when another job holds GPU1
    return json.loads((path / 'summary.json').read_text())


def report(out, history, ctx, arm):
    failures = Counter()
    lines = ['# Closed loop', '', f'Arm: {arm}', '', '| round | max f | O2-pass max f | mean f | successes | proposals |', '|---|---:|---:|---:|---:|---:|']
    for r in history:
        values = [x['f'] for x in r['results']]
        oxygen = [x['f'] for x in r['results'] if x['margin'] >= .15]
        lines.append(f"| {r['round']} | {max(values) if values else 'N/A'} | {max(oxygen) if oxygen else 'N/A'} | {sum(values)/len(values) if values else 'N/A'} | {sum(x['success'] for x in r['results'])} | {len(r['accepted']) + len(r['rejected'])} |")
        failures.update(x['reason'] for x in r['rejected'])
    evaluated = [x for r in history for x in r['results']]
    found = sum(x.get('pubchem_status') == 'found' for x in evaluated)
    unknown = sum(x.get('pubchem_status') not in ('found', 'not_found') for x in evaluated)
    lines += ['', f'평가 후보 중 PubChem 등록 {found}/{len(evaluated)} (조회 오류 또는 미조회 {unknown})', f"Reference best f: {max(r['f'] for r in ctx['dft']):.2f} (all), {max((r['f'] for r in o2_feasible(ctx['dft'])), default=float('nan')):.2f} (O2-feasible; compare with the O2-pass column)", f"Proposals attempted: {sum(len(r['accepted']) + len(r['rejected']) for r in history)}", f'Rejection counts: {dict(failures)}', f"Total LLM cost USD: {sum(r['cost'] for r in history):.6f}", '실행 1회, 통계 비교 없음']
    (out / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv=None, llm=None, evaluator=None, lookup=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--per-round', type=int, default=5)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--extra-ref', type=Path, nargs='+', default=[])
    parser.add_argument('--arm', choices=['llm', 'random'], default='llm')
    parser.add_argument('--domain', choices=['v1', 'v2'], default='v2')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--reject-pubchem', action='store_true')
    parser.add_argument('--o2-calib', type=Path)
    parser.add_argument('--compare', nargs=2, metavar=('A', 'B'))
    args = parser.parse_args(argv)
    if args.compare:
        print(compare_runs(*args.compare), end='')
        return
    if args.rounds < 1 or args.per_round < 1 or (args.out and args.resume):
        parser.error('rounds and per-round must be positive; choose out or resume')
    out = args.resume or args.out or Path(__file__).with_name('runs') / ('loop-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    config = {'arm': args.arm, 'domain': args.domain, 'seed': args.seed,
              'per_round': args.per_round, 'reject_pubchem': args.reject_pubchem,
              'extra_ref': [str(p.resolve()) for p in args.extra_ref]}
    calibration = None
    if args.o2_calib:
        try:
            content = args.o2_calib.read_bytes()
            calibration = json.loads(content)
            for category in ('carbocyclic', 'heterocyclic'):
                entry = calibration[category]
                if not math.isfinite(entry['mean_shift']) or not math.isfinite(entry['sd']) or entry['sd'] < 0 or not isinstance(entry['n'], int) or entry['n'] < 2:
                    raise ValueError('invalid calibration statistics')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            parser.error(f'invalid oxygen calibration: {exc}')
        config['o2_calib'] = {'path': str(args.o2_calib.resolve()), 'sha256': hashlib.sha256(content).hexdigest()}
    config_path = out / 'config.json'
    saved = json.loads(config_path.read_text()) if args.resume and config_path.exists() else None
    if args.resume and saved is None and calibration is not None:
        parser.error('cannot add oxygen calibration to a legacy run without config.json')
    if saved is not None and (saved.get('o2_calib') != config.get('o2_calib') or any(saved.get(key) != value for key, value in config.items())):
        parser.error('resume arguments differ from config.json; repeat the original arguments (including non-default options)')
    out.mkdir(parents=True, exist_ok=True)
    ctx, history = context(), []
    if saved is not None and saved.get('line') != ctx['line']:
        parser.error('resume fitted line differs from config.json')
    if not args.resume:
        config_path.write_text(json.dumps({**config, 'line': ctx['line']}, indent=2) + '\n', encoding='utf-8')
    if calibration is not None:
        ctx['o2_calibration'] = calibration
        for row in ctx['dft']:
            raw = row['o2_margin_V']
            row['o2_margin_V'] = raw + calibration[classify(row['smiles'])]['mean_shift']
            row['raw_o2_margin_V'] = raw
    ctx["domain"] = args.domain
    add_extra_refs(ctx, args.extra_ref)
    llm, evaluator, lookup = llm or call_llm, evaluator or evaluate, lookup or pubchem_lookup

    def filter_proposal(proposal, key, seen):
        reason = 'duplicate' if key in ctx['extra_seen'] else check(proposal, ctx, seen)
        if not reason and calibration is not None:
            try:
                classify(proposal['smiles'])
            except ValueError:
                return 'unclassifiable'
        return reason

    def annotate(proposal, key):
        result = lookup(key)
        return {**proposal, "pubchem_cid": result["cid"], "pubchem_status": result["status"], "sa_score": sa_score(proposal["smiles"])}
    for number in range(1, args.rounds + 1):
        path = out / f'round_{number}'
        path.mkdir(exist_ok=True)
        done = path / 'completed.json'
        if done.exists():
            history.append(json.loads(done.read_text()))
            continue
        seen = ctx['extra_seen'] | {_inchikey(p['smiles']) for r in history for p in r['accepted']}
        accepted, rejected, cost = [], [], 0
        if args.arm == 'llm':
            for attempt in range(1, 4):
                text = loop_prompt(ctx, history, args.per_round - len(accepted))
                if attempt > 1:
                    text += f"\nRejected proposals and reasons: {json.dumps(rejected)}\nAlready accepted SMILES: {json.dumps([p['smiles'] for p in accepted])}"
                (path / f'prompt_{attempt}.txt').write_text(text, encoding='utf-8')
                if args.dry_run:
                    return out
                response_path = path / f'response_{attempt}.json'
                legacy = path / 'response.json'
                if response_path.exists():
                    response = json.loads(response_path.read_text())
                elif attempt == 1 and legacy.exists():
                    response = json.loads(legacy.read_text())
                else:
                    response = llm(text)
                    response_path.write_text(json.dumps(response), encoding='utf-8')
                cost += response.get('total_cost_usd', 0)
                for proposal in response.get('structured_output', response).get('proposals', []):
                    smiles = proposal.get('smiles') if isinstance(proposal, dict) else None
                    if isinstance(proposal, dict):
                        proposal = {**proposal, 'sa_score': sa_score(smiles) if isinstance(smiles, str) else None}
                    key = _inchikey(smiles) if isinstance(smiles, str) else None
                    reason = filter_proposal(proposal, key, seen)
                    if not reason and len(accepted) < args.per_round:
                        proposal = annotate(proposal, key)
                        if args.reject_pubchem and proposal['pubchem_status'] == 'found':
                            reason = 'known_pubchem'
                    if reason:
                        rejected.append({**proposal, 'reason': reason})
                    elif len(accepted) >= args.per_round:
                        rejected.append({**proposal, 'reason': 'round_full'})
                    else:
                        seen.add(_inchikey(proposal['smiles']))
                        accepted.append(proposal)
                if len(accepted) >= args.per_round:
                    break
        else:
            if args.dry_run:
                return out
            # ponytail: a per-round seed makes interrupted runs reproducible without RNG checkpoints.
            rng = random.Random(f'{args.seed}:{number}')
            parents = list(ctx['dft']) + [x for r in history for x in r['results']]
            parents = sorted(o2_feasible(parents), key=lambda x: x['f'], reverse=True)[:5]  # same objective the LLM sees: f among O2-feasible only
            if not parents:
                raise RuntimeError('No O2-feasible parents available for the random arm')
            for _ in range(2000):
                if len(accepted) >= args.per_round:
                    break
                parent = rng.choice(parents)
                smiles = edit(parent['smiles'], rng.choice(['add', 'replace', 'remove', 'move', 'aza'] if args.domain == 'v2' else ['add', 'replace', 'remove', 'move']), substituents=SUBSTITUENTS if args.domain == 'v2' else sorted(ctx['allowed_subst']), rng=rng)
                proposal = {'parent_id': parent.get('parent_id', parent.get('id')), 'smiles': smiles, 'edits': ['random_edit'], 'cited_ids': [], 'hypothesis': 'B0 random edit', 'sa_score': sa_score(smiles) if smiles else None}
                key = _inchikey(smiles) if isinstance(smiles, str) else None
                reason = filter_proposal(proposal, key, seen)
                if not reason:
                    proposal = annotate(proposal, key)
                    if args.reject_pubchem and proposal['pubchem_status'] == 'found':
                        reason = 'known_pubchem'
                if reason:
                    rejected.append({**proposal, 'reason': reason})
                else:
                    seen.add(_inchikey(smiles))
                    accepted.append(proposal)
        with (path / 'input.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=['id', 'smiles'])
            writer.writeheader()
            writer.writerows({'id': f'R{number}-{i}', 'smiles': p['smiles']} for i, p in enumerate(accepted, 1))
        summary = evaluator(path) if accepted else {'molecules': []}
        by_key = {x['inchikey']: x for x in summary['molecules']}
        if any(_inchikey(p['smiles']) not in by_key for p in accepted):
            raise RuntimeError('Evaluation incomplete; resume after correcting failed calculations')
        results = [{**p, **score({**by_key[_inchikey(p['smiles'])], **({'smiles': p['smiles']} if calibration is not None else {})}, ctx['line'], calibration)} for p in accepted]
        scores = [x['f'] for r in history for x in r['results']] + [x['f'] for x in results]
        record = {'round': number, 'accepted': accepted, 'rejected': rejected, 'results': results, 'best_f': max(scores) if scores else None, 'cost': cost, 'arm': args.arm, 'line': dict(ctx['line'])}
        if calibration is not None:
            record['o2_calib'] = config['o2_calib']
        done.write_text(json.dumps(record), encoding='utf-8')
        history.append(record)
        (out / 'ledger.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in history), encoding='utf-8')
        report(out, history, ctx, args.arm)
    if history:
        (out / 'ledger.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in history), encoding='utf-8')
        report(out, history, ctx, args.arm)
    return out


if __name__ == '__main__':
    main()
