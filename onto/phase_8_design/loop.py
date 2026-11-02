"""Small, injectable closed-loop scaffold; real xTB and LLM adapters come later."""

import json
import random
from collections import Counter

from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator


QUINONES = ("O=C1C=CC(=O)C=C1", "O=C1C(=O)c2ccccc2C=C1", "O=C1C=CC2=CC=CC=C2C1=O",
            "O=C1C=CC(=O)c2ccccc21", "O=C1c2ccccc2C(=O)c2ccccc21", "O=C1C(=O)c2ccccc2-c2ccccc21")
NON_METALS = {1, 5, 6, 7, 8, 9, 14, 15, 16, 17, 34, 35, 53}
FP = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def _mol(value, smarts=False):
    return Chem.MolFromSmarts(value) if smarts else Chem.MolFromSmiles(value)


def _positions(mol):
    return [atom.GetIdx() for atom in mol.GetAtoms()
            if atom.IsInRing() and atom.GetAtomicNum() == 6 and atom.GetTotalNumHs()]


def _choose(items, rng, selected=None):
    if not items:
        return None
    if selected in items:
        return selected
    return rng.choice(items)


def _substituent(substituents, rng, selected=None):
    if not substituents:
        return None
    return selected or _choose(substituents, rng)


def _add(mol, position, substituent):
    frag = _mol(substituent)
    if frag is None or frag.GetNumAtoms() != 1 or position is None:
        return None
    joined = Chem.CombineMols(mol, frag)
    editable = Chem.RWMol(joined)
    editable.AddBond(position, mol.GetNumAtoms(), Chem.BondType.SINGLE)
    try:
        Chem.SanitizeMol(editable)
        return Chem.MolToSmiles(editable)
    except Exception:
        return None


def _external_neighbors(mol):
    return [(atom.GetIdx(), neighbor.GetIdx()) for atom in mol.GetAtoms() if atom.IsInRing()
            for neighbor in atom.GetNeighbors() if not neighbor.IsInRing() and neighbor.GetAtomicNum() != 8]


def _remove(mol, ring_idx, sub_idx):
    editable = Chem.RWMol(mol)
    editable.RemoveBond(ring_idx, sub_idx)
    editable.RemoveAtom(sub_idx)
    try:
        Chem.SanitizeMol(editable)
        return Chem.MolToSmiles(editable)
    except Exception:
        return None


def edit(smiles, op, *, substituents=(), rng=None, position=None, bond=None, substituent=None):
    """Apply one fixed substituent edit, returning canonical SMILES or ``None``."""
    mol = _mol(smiles)
    if mol is None:
        return None
    rng = rng or random
    positions = _positions(mol)
    if op == "add":
        return _add(mol, _choose(positions, rng, position), _substituent(substituents, rng, substituent))
    external = _external_neighbors(mol)
    if op == "remove":
        picked = _choose(external, rng, bond)
        return _remove(mol, *picked) if picked else None
    if op in {"replace", "move"}:
        picked = _choose(external, rng, bond)
        if not picked:
            return None
        old = mol.GetAtomWithIdx(picked[1]).GetSymbol()
        reduced = _remove(mol, *picked)
        if reduced is None:
            return None
        new_mol = _mol(reduced)
        destination = _choose(_positions(new_mol), rng, position)
        return _add(new_mol, destination, _substituent(substituents, rng, substituent) if op == "replace" else old)
    return None


def t0(smiles):
    """Return a rejection reason, or ``None`` for a small, metal-free quinone."""
    mol = _mol(smiles)
    if mol is None:
        return "invalid_smiles"
    if any(atom.GetAtomicNum() not in NON_METALS for atom in mol.GetAtoms()):
        return "metal"
    if mol.GetNumHeavyAtoms() > 40:
        return "too_many_heavy_atoms"
    if not any(mol.HasSubstructMatch(_mol(pattern, smarts=True)) for pattern in QUINONES):
        return "not_quinone"
    return None


def _pattern(value):
    return _mol(value, smarts=True) or _mol(value)


def in_domain(smiles, cores_smarts, allowed_subst, ref_fps):
    """Check the phase-7 core, substituent, and fingerprint support contract."""
    mol = _mol(smiles)
    if mol is None:
        return "out_of_domain_core"
    patterns = [_pattern(core) for core in cores_smarts]
    match = next((mol.GetSubstructMatch(pattern) for pattern in patterns
                  if pattern and mol.HasSubstructMatch(pattern)), ())
    if not match:
        return "out_of_domain_core"
    core_atoms = set(match)
    for atom in mol.GetAtoms():
        if atom.GetIdx() in core_atoms:
            continue
        if any(neighbor.GetIdx() in core_atoms for neighbor in atom.GetNeighbors()):
            subst = Chem.MolFragmentToSmiles(mol, [atom.GetIdx()], canonical=True)
            if subst not in allowed_subst and atom.GetSymbol() not in allowed_subst:
                return "unregistered_substituent"
    candidate = FP.GetFingerprint(mol)
    refs = [FP.GetFingerprint(_mol(ref)) if isinstance(ref, str) else ref for ref in ref_fps]
    if not refs or max(DataStructs.TanimotoSimilarity(candidate, ref) for ref in refs) < 0.4:
        return "out_of_domain_similarity"
    return None


def objective(E2, dG, a, b, sigma, o2_E, margin=0.15):
    if sigma == 0 or E2 < o2_E + margin:
        return None
    return (a * E2 + b - dG) / sigma


def _score(evaluate, smiles):
    try:
        value = evaluate(smiles)
    except Exception as exc:
        return None, {"reason": f"calculation_fail: {type(exc).__name__}"}
    if isinstance(value, (int, float)):
        return float(value), {"f": float(value)}
    if not isinstance(value, dict):
        return None, {"reason": "calculation_fail" if value is None else str(value)}
    if value.get("reason"):
        return None, value
    score = value.get("f")
    if score is None and all(key in value for key in ("E2", "dG", "a", "b", "sigma", "o2_E")):
        score = objective(value["E2"], value["dG"], value["a"], value["b"], value["sigma"], value["o2_E"])
    return score, value if score is not None else {**value, "reason": "o2_fail"}


def run(propose, evaluate, start, budget=80, rounds=8, k=5, feedback=True, ledger_path="ledger.jsonl",
        cores_smarts=None, allowed_subst=None, ref_fps=None):
    """Run exactly ``budget`` proposals and return the running-best score curve."""
    start_records = []
    for item in start:
        smiles = item["smiles"] if isinstance(item, dict) else item
        score = item.get("f") if isinstance(item, dict) else None
        if score is None and t0(smiles) is None:
            score, _ = _score(evaluate, smiles)
        if score is not None:
            start_records.append({"smiles": smiles, "f": float(score)})
    best = max((record["f"] for record in start_records), default=float("-inf"))
    seen = {record["smiles"] for record in start_records}
    start_smiles = sorted(seen)
    failures, curve, exhausted, pending = Counter(), [], False, []
    cores_smarts = cores_smarts or QUINONES
    allowed_subst = set() if allowed_subst is None else allowed_subst
    ref_fps = ref_fps or [record["smiles"] for record in start_records]
    ledger_path = str(ledger_path)
    with open(ledger_path, "w", encoding="utf-8") as ledger:
        for step in range(budget):
            round_index = step * rounds // budget
            if feedback:
                context = {"top": sorted(start_records, key=lambda record: record["f"], reverse=True)[:k],
                           "failures": dict(failures), "previous_smiles": sorted(seen),
                           "start_smiles": start_smiles, "round": round_index}
            else:
                context = {"previous_smiles": sorted(seen),
                           "start_smiles": start_smiles, "round": round_index}
            # ponytail: JSONL is the only ledger; add RDF when runs must query each other.
            if not exhausted and not pending:
                pending = list(propose(context))
            item = pending.pop(0) if pending and not exhausted else {"reason": "insufficient_evidence"}
            proposal = item.get("smiles") if isinstance(item, dict) else None
            row = {"step": step + 1, "round": round_index + 1, "proposal": proposal,
                   "t0": None, "domain": None, "E2": None, "dG": None, "f": None, "reason": None}
            if isinstance(item, dict) and item.get("reason") == "insufficient_evidence":
                reason = "insufficient_evidence"
                exhausted = True
            elif not isinstance(proposal, str) or not proposal:
                reason = "invalid_smiles"
            elif proposal in seen:
                reason = "duplicate"
            else:
                reason = t0(proposal)
                row["t0"] = reason
            if reason is None:
                row["domain"] = in_domain(proposal, cores_smarts, allowed_subst, ref_fps)
                if row["domain"]:
                    reason = "out_of_domain"
                else:
                    score, details = _score(evaluate, proposal)
                    row.update({key: details.get(key) for key in ("E2", "dG")})
                    reason = details.get("reason") if score is None else None
                    row["f"] = score
                    if score is not None:
                        seen.add(proposal)
                        start_records.append({"smiles": proposal, "f": float(score)})
                        best = max(best, float(score))
            if reason:
                failures[reason] += 1
            row["reason"], row["best_f"] = reason, best
            ledger.write(json.dumps(row, sort_keys=True) + "\n")
            curve.append(best)
    return curve


def auc(best_curve, start_best):
    return sum(value - start_best for value in best_curve)


def random_proposer(allowed_subst, seed=0):
    """B0 baseline: uniformly choose a parent and fixed edit operation."""
    # ponytail: one seeded stdlib RNG is enough until paired-run orchestration exists.
    rng = random.Random(seed)

    def propose(context):
        parents = context.get("top", []) or [{"smiles": smiles} for smiles in context["start_smiles"]]
        if not parents:
            return [{"reason": "insufficient_evidence"}]
        parent = rng.choice(parents)["smiles"]
        return [{"smiles": edit(parent, rng.choice(["add", "replace", "remove", "move"]),
                                substituents=allowed_subst, rng=rng)}]

    return propose
