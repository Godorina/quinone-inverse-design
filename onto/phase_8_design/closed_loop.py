"""Three-round hypothesis generation and evaluation, with resumable round artifacts."""
import os
import argparse
import csv
import json
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from generate import _inchikey, call_llm, check, context, prompt
from loop import edit


def o2_feasible(rows):
    """Parents for the random arm: O2 margin >= 0.15 V and CO2 attached (reference rows say o2_margin_V, loop rows say margin)."""
    return [x for x in rows if x.get('margin', x.get('o2_margin_V')) >= .15 and not x['co2_detached']]

def score(row, line):
    f = (line['a'] * row['E2_eV'] + line['b'] - row['dE_bind_kcal']) / line['sigma']
    margin = row['E_O2_eV'] - row['E2_eV']
    return {**row, 'f': f, 'margin': margin, 'success': f >= 2 and margin >= .15 and not row['co2_detached']}


def loop_prompt(ctx, history, per_round=5):
    previous = [p['smiles'] for r in history for p in r['accepted']]
    evidence = prompt(ctx, previous).split('DFT evidence:\n', 1)[1]
    feedback = [{'results': r['results'], 'rejected': r['rejected']} for r in history]
    return (f'Propose exactly {per_round} testable hypotheses to exceed the tradeoff line: f >= 2, O2 margin >= 0.15 V, and no CO2 detachment. DFT will decide; proof of success is not required. '
            'Cite D/K evidence supporting the direction. Return insufficient_evidence only when no evidence can be cited. '
            'Use reference parents; add, replace, remove or move only allowed substituents F, Cl, Br, NH2, OH (no CN: every CN reference detached CO2). '
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
    def maximum(rows, number, oxygen=False):
        results = next((r['results'] for r in rows if r['round'] == number), [])
        values = [x['f'] for x in results if not oxygen or x['margin'] >= .15]
        return f'{max(values):.3f}' if values else 'N/A'
    lines = [f'| round | {arm_a} max f | {arm_a} O2 max f | {arm_b} max f | {arm_b} O2 max f |', '|---|---:|---:|---:|---:|']
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
    lines += ['', f"Reference best f: {max(r['f'] for r in ctx['dft']):.2f} (all), {max((r['f'] for r in o2_feasible(ctx['dft'])), default=float('nan')):.2f} (O2-feasible; compare with the O2-pass column)", f"Proposals attempted: {sum(len(r['accepted']) + len(r['rejected']) for r in history)}", f'Rejection counts: {dict(failures)}', f"Total LLM cost USD: {sum(r['cost'] for r in history):.6f}", '실행 1회, 통계 비교 없음']
    (out / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv=None, llm=None, evaluator=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--per-round', type=int, default=5)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--extra-ref', type=Path, nargs='+', default=[])
    parser.add_argument('--arm', choices=['llm', 'random'], default='llm')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--compare', nargs=2, metavar=('A', 'B'))
    args = parser.parse_args(argv)
    if args.compare:
        print(compare_runs(*args.compare), end='')
        return
    if args.rounds < 1 or args.per_round < 1 or (args.out and args.resume):
        parser.error('rounds and per-round must be positive; choose out or resume')
    out = args.resume or args.out or Path(__file__).with_name('runs') / ('loop-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True, exist_ok=True)
    ctx, history = context(), []
    add_extra_refs(ctx, args.extra_ref)
    llm, evaluator = llm or call_llm, evaluator or evaluate
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
                    key = _inchikey(smiles) if isinstance(smiles, str) else None
                    reason = 'duplicate' if key in ctx['extra_seen'] else check(proposal, ctx, seen)
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
            for _ in range(2000):
                if len(accepted) >= args.per_round:
                    break
                parent = rng.choice(parents)
                smiles = edit(parent['smiles'], rng.choice(['add', 'replace', 'remove', 'move']), substituents=sorted(ctx['allowed_subst']), rng=rng)
                proposal = {'parent_id': parent.get('parent_id', parent.get('id')), 'smiles': smiles, 'edits': ['random_edit'], 'cited_ids': [], 'hypothesis': 'B0 random edit'}
                key = _inchikey(smiles) if isinstance(smiles, str) else None
                reason = 'duplicate' if key in ctx['extra_seen'] else check(proposal, ctx, seen)
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
        results = [{**p, **score(by_key[_inchikey(p['smiles'])], ctx['line'])} for p in accepted]
        scores = [x['f'] for r in history for x in r['results']] + [x['f'] for x in results]
        record = {'round': number, 'accepted': accepted, 'rejected': rejected, 'results': results, 'best_f': max(scores) if scores else None, 'cost': cost, 'arm': args.arm}
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
