"""Small numpy GP and diverse UCB selection on Morgan/Tanimoto fingerprints."""
import csv
import json
import math
import sys
from pathlib import Path
import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'onto/phase_8_design'))
from generate import context, _inchikey
from closed_loop import score

FP = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def fp(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if not mol: raise ValueError('Invalid SMILES: ' + smiles)
    return FP.GetFingerprint(mol)


def similarity(a, b): return DataStructs.TanimotoSimilarity(fp(a), fp(b))


def kernel(a, b):
    return np.array([DataStructs.BulkTanimotoSimilarity(x, b) for x in a], dtype=float)


class GP:
    def __init__(self, smiles, y, noise=1e-5):
        if not smiles or len(smiles) != len(y): raise ValueError('Training data required')
        self.fps = [fp(x) for x in smiles]
        values = np.asarray(y, dtype=float)
        if not np.isfinite(values).all(): raise ValueError('Nonfinite training labels')
        self.mean = values.mean()
        # ponytail: exact GP is cubic in training size; replace with an approximation when this grows large.
        self.chol = np.linalg.cholesky(kernel(self.fps, self.fps) + noise * np.eye(len(values)))
        self.alpha = np.linalg.solve(self.chol.T, np.linalg.solve(self.chol, values - self.mean))

    def predict(self, smiles):
        xs = [fp(s) for s in smiles]
        k = kernel(xs, self.fps)
        mean = self.mean + k @ self.alpha
        v = np.linalg.solve(self.chol, k.T)
        return mean, np.sqrt(np.maximum(1 - np.sum(v * v, axis=0), 0))


def select(smiles, means, stds, batch, kappa=2., threshold=.7, order=None):
    if batch < 0: raise ValueError('batch must be nonnegative')
    fps = [fp(s) for s in smiles]
    order = list(order) if order is not None else sorted(range(len(smiles)), key=lambda i: (-(means[i] + kappa * stds[i]), i))
    chosen = []
    for i in order:
        if all(DataStructs.TanimotoSimilarity(fps[i], fps[j]) < threshold for j in chosen):
            chosen.append(i)
            if len(chosen) == batch: break
    return chosen if batch else []


def training_rows(extra=()):
    line = json.loads((ROOT / 'dft/runs/ref_set/lines.json').read_text())['v2']
    ctx = context()
    results = list(ctx['dft'])
    for path in sorted((ROOT / 'onto/phase_8_design/runs').glob('*/ledger.jsonl')):
        for text in path.read_text().splitlines():
            results.extend(json.loads(text).get('results', []))
    results.extend(extra)
    by_key = {}
    for row in results:
        try:
            if row.get('co2_detached') is not False: continue
            if not all(math.isfinite(float(row[k])) for k in ('E2_eV', 'dE_bind_kcal')): continue
            smiles = row['smiles']; key = _inchikey(smiles)
            if not key or (row.get('inchikey') and row['inchikey'] != key): continue
            y = (line['a'] * float(row['E2_eV']) + line['b'] - float(row['dE_bind_kcal'])) / line['sigma']
            by_key.setdefault(key, {'smiles': smiles, 'inchikey': key, 'f': y})
        except (KeyError, TypeError, ValueError): continue
    return list(by_key.values())
