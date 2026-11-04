import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_set import run_selected, summarize
from test_run_set import fake_record, result

def test_resume_and_line(tmp_path):
    common = {'states': {'CO2': result(-20), 'O2': result(-30), 'O2_radical_anion': result(-29.5)}}
    (tmp_path / '_common.json').write_text(json.dumps(common))
    run_selected([], tmp_path, False, common_path=tmp_path / '_common.json')
    for i in range(12):
        (tmp_path / f'KEY{i:02d}.json').write_text(json.dumps(fake_record(i)))
    old = {'a': 1, 'b': 2, 'sigma': 3, 'n': 12}
    (tmp_path / 'summary.json').write_text(json.dumps({'line': old}))
    summary = summarize(tmp_path)
    assert summary['line_v1'] == old
    assert summary['family_residuals']
    assert summarize(tmp_path)['line_v1'] == old

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as d:
        test_resume_and_line(Path(d))
    print('1 passed')
