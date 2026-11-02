import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from closed_loop import main, score


def test_score():
    value = score({'E2_eV': -2, 'E_O2_eV': -1.7, 'dE_bind_kcal': -6, 'co2_detached': False}, {'a': 1, 'b': 0, 'sigma': 2})
    assert value['f'] == 2 and abs(value['margin'] - .3) < 1e-8 and value['success']


def test_rounds_resume_and_feedback():
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory)
        prompts, evaluations = [], []
        smiles = ['O=C1C=C(Cl)C(=O)C=C1', 'NC1=C(Br)C(=O)C(Br)=C(Br)C1=O', 'NC1=C(Cl)C(=O)C(Cl)=C(Cl)C1=O']
        def llm(text):
            prompts.append(text)
            return {'structured_output': {'proposals': [{'parent_id': 'D01', 'smiles': smiles[len(prompts)-1], 'cited_ids': ['K001']}, {'smiles': 'c1ccccc1'}]}, 'total_cost_usd': .1}
        def evaluate(path):
            evaluations.append(path)
            import csv
            from rdkit import Chem
            rows = list(csv.DictReader((path / 'input.csv').open()))
            return {'molecules': [{'inchikey': Chem.MolToInchiKey(Chem.MolFromSmiles(r['smiles'])), 'E2_eV': -2, 'E_O2_eV': -1.7, 'dE_bind_kcal': -30, 'co2_detached': False} for r in rows]}
        main(['--rounds', '1', '--per-round', '1', '--out', str(out)], llm=llm, evaluator=evaluate, lookup=lambda _: {'cid': None, 'status': 'not_found'})
        main(['--rounds', '3', '--per-round', '1', '--resume', str(out)], llm=llm, evaluator=evaluate, lookup=lambda _: {'cid': None, 'status': 'not_found'})
        history = [json.loads(line) for line in (out / 'ledger.jsonl').read_text().splitlines()]
        assert len(history) == 3 and len(prompts) == 3 and len(evaluations) == 3
        assert smiles[0] in prompts[1] and 'not_quinone' in prompts[1] and '"f"' in prompts[1]
        best = [r['best_f'] for r in history]
        assert best == sorted(best)
        assert '통계 비교 없음' in (out / 'report.md').read_text()


def test_empty_round_skips_evaluation():
    with tempfile.TemporaryDirectory() as directory:
        main(['--rounds', '1', '--out', directory], llm=lambda _: {'structured_output': {'proposals': [{'smiles': 'c1ccccc1'}]}}, evaluator=lambda _: 1 / 0)
        assert len(Path(directory, 'ledger.jsonl').read_text().splitlines()) == 1


if __name__ == '__main__':
    test_score()
    test_rounds_resume_and_feedback()
    test_empty_round_skips_evaluation()
    print('3 passed')
