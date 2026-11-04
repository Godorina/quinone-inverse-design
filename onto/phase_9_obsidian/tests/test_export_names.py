"""A truncated note name must not end in a space or dot: Obsidian trims link text, so such links break."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export import filename


def test_truncated_name_has_no_trailing_space():
    name = filename('Towards Immobilized Quinones ' + 'x' * 70 + ' Carbon Capture from Air')
    assert len(name) <= 100 and name == name.strip(' .')


if __name__ == '__main__':
    test_truncated_name_has_no_trailing_space()
    print('names ok')
