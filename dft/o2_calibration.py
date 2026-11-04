"""Shared classification for high-level oxygen-margin calibration."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'onto/phase_9_obsidian'))
from export import skeleton_from_smiles


def classify(smiles):
    skeleton = skeleton_from_smiles(smiles)
    if skeleton == 'NotReported':
        raise ValueError(f'Cannot classify quinone skeleton: {smiles}')
    return 'heterocyclic' if skeleton == 'HeterocyclicQuinone' else 'carbocyclic'
