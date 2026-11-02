"""Small DFT geometry helpers for the phase-7 quinone benchmark."""

import json
import time
from pathlib import Path

import numpy as np
from pyscf import dft, gto
from pyscf.geomopt import geometric_solver
from rdkit import Chem
from rdkit.Chem import AllChem


def embed(smiles, seed=0):
    """Embed an RDKit molecule with hydrogens and return Angstrom coordinates."""
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise ValueError(f"could not embed {smiles!r}")
    AllChem.MMFFOptimizeMolecule(mol)
    conformer = mol.GetConformer()
    return [atom.GetSymbol() for atom in mol.GetAtoms()], np.array(conformer.GetPositions())


def co2_adduct(symbols, coords, o_index):
    """Place a bent CO2 group 1.45 Angstrom from carbonyl oxygen ``o_index``."""
    coords = np.asarray(coords, dtype=float)
    oxygen = coords[o_index]
    carbon = coords[min((index for index, symbol in enumerate(symbols) if symbol == "C"),
                        key=lambda index: np.linalg.norm(coords[index] - oxygen))]
    direction = oxygen - carbon
    direction /= np.linalg.norm(direction)
    axis = np.cross(direction, [1.0, 0.0, 0.0])
    if np.linalg.norm(axis) < 1e-6:
        axis = np.cross(direction, [0.0, 1.0, 0.0])
    axis /= np.linalg.norm(axis)
    co2_c = oxygen + 1.45 * direction
    half_angle = np.deg2rad(65.0)
    co2_o1 = co2_c + 1.16 * (direction * np.cos(half_angle) + axis * np.sin(half_angle))
    co2_o2 = co2_c + 1.16 * (direction * np.cos(half_angle) - axis * np.sin(half_angle))
    return list(symbols) + ["C", "O", "O"], np.vstack([coords, co2_c, co2_o1, co2_o2])


def write_xyz_text(symbols, coords):
    return f"{len(symbols)}\n\n" + "\n".join(
        f"{symbol} {x:.10f} {y:.10f} {z:.10f}" for symbol, (x, y, z) in zip(symbols, coords)
    ) + "\n"


def write_xyz(path, symbols, coords):
    Path(path).write_text(write_xyz_text(symbols, coords), encoding="utf-8")


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _method(mol, spin, xc, disp, solvent, gpu):
    if gpu:
        from gpu4pyscf import dft as gpu_dft
        method = gpu_dft.RKS(mol, xc=xc) if spin == 0 else gpu_dft.UKS(mol, xc=xc)
    else:
        method = dft.RKS(mol, xc=xc) if spin == 0 else dft.UKS(mol, xc=xc)
    method.disp = disp
    if solvent:
        method = method.SMD()
        method.with_solvent.solvent = solvent
    return method


def _molecule(symbols, coords, charge, spin, basis):
    return gto.M(atom=list(zip(symbols, coords)), charge=charge, spin=spin, basis=basis,
                 unit="Angstrom", verbose=0)


def optimize(symbols, coords, charge, spin, xc="b3lyp", disp="d3bj", basis="def2-svp",
             solvent="acetonitrile", gpu=True):
    """Optimize one state and return results instead of propagating calculation errors."""
    started, steps = time.monotonic(), [0]
    result = {"energy": None, "xyz": None, "seconds": 0.0, "steps": 0, "converged": False, "geom_converged": False,
              "max_gpu_memory": 0, "error": None}
    memory_pool = None
    try:
        if gpu:
            import cupy
            memory_pool = cupy.get_default_memory_pool()
            memory_pool.free_all_blocks()
        mol = _molecule(symbols, coords, charge, spin, basis)
        method = _method(mol, spin, xc, disp, solvent, gpu)
        method.kernel()
        if not method.converged:
            # ponytail: one level-shift retry; diagnose persistent SCF failures before adding heuristics.
            method.level_shift = 0.2
            method.kernel()
        if not method.converged:
            raise RuntimeError("SCF did not converge")
        geom_converged, optimized = geometric_solver.kernel(method, callback=lambda _: steps.__setitem__(0, steps[0] + 1))
        method = _method(optimized, spin, xc, disp, solvent, gpu)
        energy = method.kernel()
        if not method.converged:
            method.level_shift = 0.2
            energy = method.kernel()
        result.update({"energy": float(energy), "xyz": write_xyz_text(
            [optimized.atom_symbol(i) for i in range(optimized.natm)], optimized.atom_coords(unit="Angstrom")),
            "steps": steps[0], "converged": bool(method.converged), "geom_converged": bool(geom_converged)})
        if not method.converged:
            result["error"] = "SCF did not converge"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    if memory_pool is not None:
        # ponytail: pool capacity approximates peak use; add a profiler only when memory is constrained.
        result["max_gpu_memory"] = memory_pool.total_bytes()
    result["seconds"] = time.monotonic() - started
    return result
