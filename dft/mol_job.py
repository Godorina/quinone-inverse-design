# Source: ~/atomistic-agent-runs/quinone-bench/Fc_p1/mol_job.py
"""Molecular DFT job runner (copied into each job directory as mol_job.py).

Usage on the compute host:  python mol_job.py job.json
Self-contained on purpose: it only needs pyscf (and gpu4pyscf for device="gpu"),
so it runs in the cluster's environment without this package installed.
Writes result.json; never raises past main() so a failure is always recorded.
"""

import json
import sys
import time
import traceback

import numpy as np

HARTREE_TO_KCAL = 627.509474
J_PER_MOL_PER_EH = 2625499.639


def qrrho_vib_entropy(freq_cm, temperature, nu0=100.0, alpha=4, bav=1.0e-44):
    """Grimme's quasi-RRHO vibrational entropy (Chem. Eur. J. 2012, 18, 9955), in Eh/K.

    Each mode's harmonic entropy is blended with a free-rotor entropy using
    w = 1 / (1 + (nu0/nu)^alpha), so very soft modes stop dominating -TS.
    Returns (S_qrrho, S_harmonic) for the given real, positive frequencies.
    """
    h, kb, c, r = 6.62607015e-34, 1.380649e-23, 2.99792458e10, 8.314462618
    nu = np.asarray(freq_cm, dtype=float)
    if nu.size == 0:
        return 0.0, 0.0
    x = h * c * nu / (kb * temperature)
    s_ho = r * (x / np.expm1(x) - np.log1p(-np.exp(-x)))
    mu = h / (8 * np.pi ** 2 * nu * c)
    mu_eff = mu * bav / (mu + bav)
    s_rot = r * (0.5 + np.log(np.sqrt(8 * np.pi ** 3 * mu_eff * kb * temperature / h ** 2)))
    w = 1.0 / (1.0 + (nu0 / nu) ** alpha)
    return float((w * s_ho + (1 - w) * s_rot).sum() / J_PER_MOL_PER_EH), float(s_ho.sum() / J_PER_MOL_PER_EH)


def _to_numpy(a):
    return a.get() if hasattr(a, "get") else np.asarray(a)


def sg1_prune_light_atoms(nuc, rads, n_ang, radii=None):
    """SG-1 pruning where it is defined (H-Ar); heavier atoms (e.g. Fe) keep the full angular grid.

    pyscf's sg1_prune indexes a radius table that stops at Ar and fails for Z > 18.
    """
    from pyscf.dft import gen_grid
    if nuc <= 18:
        # pyscf passes radii=None; let sg1_prune use its own SG-1 radius table then.
        return gen_grid.sg1_prune(nuc, rads, n_ang) if radii is None else gen_grid.sg1_prune(nuc, rads, n_ang, radii)
    return np.repeat(n_ang, len(rads))


def build(spec, atom):
    from pyscf import gto
    mol = gto.M(atom=atom, charge=spec["charge"], spin=spec["spin"], basis=spec["basis"],
                verbose=spec.get("verbose", 4), output=spec.get("log", "pyscf.log"),
                max_memory=spec.get("max_memory_mb", 32000))
    if spec.get("device", "gpu") == "gpu":
        from gpu4pyscf import dft
    else:
        from pyscf import dft
    mf = (dft.RKS if spec["spin"] == 0 else dft.UKS)(mol, xc=spec["xc"])
    if spec.get("disp"):
        mf.disp = spec["disp"]
    mf.grids.level = spec.get("grids_level", 3)
    if spec.get("grids_atom"):
        mf.grids.atom_grid = tuple(spec["grids_atom"])          # e.g. (99, 590)
    if spec.get("nlc_grids_atom") and hasattr(mf, "nlcgrids"):
        mf.nlcgrids.atom_grid = tuple(spec["nlc_grids_atom"])   # e.g. (50, 194) for VV10
        if spec.get("nlc_grids_prune") == "sg1":
            mf.nlcgrids.prune = sg1_prune_light_atoms
    mf.conv_tol = spec.get("conv_tol", 1e-10)
    mf.max_cycle = spec.get("max_cycle", 100)
    if spec.get("level_shift"):
        mf.level_shift = spec["level_shift"]
    if spec.get("density_fit", False):  # an approximation: only when the profile chooses it
        mf = mf.density_fit(auxbasis=spec.get("auxbasis"))
    sol = spec.get("solvent")
    if sol:
        model = sol["model"].lower()
        if model == "smd":
            mf = mf.SMD()
            mf.with_solvent.solvent = sol["name"]
        elif model in ("pcm", "c-pcm", "iefpcm", "ief-pcm"):
            mf = mf.PCM()
            mf.with_solvent.method = {"pcm": "C-PCM", "c-pcm": "C-PCM"}.get(model, "IEF-PCM")
            mf.with_solvent.eps = float(sol["eps"])
        else:
            raise ValueError(f"unsupported solvent model {sol['model']}")
    return mol, mf


def thermo_analysis(mf, mol, spec):
    from pyscf.hessian import thermo
    hess = _to_numpy(mf.Hessian().kernel())
    ha = thermo.harmonic_analysis(mol, hess)
    freq_cm = np.asarray(ha["freq_wavenumber"])
    if np.iscomplexobj(freq_cm):
        signed = np.where(np.abs(freq_cm.imag) > 1e-6, -np.abs(freq_cm.imag), freq_cm.real)
    else:
        signed = freq_cm
    freq_au = np.asarray(ha["freq_au"])
    keep = signed > 0
    real_au = (freq_au.real if np.iscomplexobj(freq_au) else freq_au)[keep]
    cutoff = spec.get("qh_cutoff_cm")
    if cutoff:
        # Quasi-harmonic (Truhlar): raise real modes below the cutoff to the cutoff.
        au_per_cm = (real_au / signed[keep]).mean() if keep.any() else 0.0
        real_au = np.maximum(real_au, cutoff * au_per_cm)
    temperature = spec.get("temperature", 298.15)
    t = thermo.thermo(mf, real_au, temperature, spec.get("pressure", 101325))
    val = lambda k: float(t[k][0])  # noqa: E731
    g = val("G_tot")
    model = spec.get("thermo_model", "rrho")
    out = {"freq_cm": [round(float(f), 2) for f in signed], "n_imag": int((signed < 0).sum()),
           "zpe_Eh": val("ZPE"), "H_Eh": val("H_tot"), "G_rrho_Eh": g, "temperature": temperature,
           "pressure_Pa": spec.get("pressure", 101325), "qh_cutoff_cm": cutoff, "thermo_model": model}
    if model == "mrrho":
        s_q, s_ho = qrrho_vib_entropy(signed[keep], temperature)
        out["S_vib_harmonic_Eh_K"], out["S_vib_qrrho_Eh_K"] = s_ho, s_q
        g = g + temperature * (s_ho - s_q)   # swap the harmonic vibrational entropy for the quasi-RRHO one
    elif model != "rrho":
        raise ValueError(f"unknown thermo_model {model}")
    out.update(G_Eh=g, G_corr_Eh=g - float(mf.e_tot))
    return out


def run(spec):
    out = {"name": spec.get("name"), "task": spec["task"], "status": "running", "spec": spec}
    t0 = time.time()
    mol, mf = build(spec, spec["xyz"])
    out["nao"] = int(mol.nao)
    if "opt" in spec["task"]:
        from pyscf.geomopt import geometric_solver
        conv, mol_eq = geometric_solver.kernel(mf, maxsteps=spec.get("opt_maxsteps", 200))
        out["opt_converged"] = bool(conv)
        coords = mol_eq.atom_coords(unit="Angstrom")
        out["xyz_final"] = "\n".join(f"{mol_eq.atom_pure_symbol(i)} {x:.8f} {y:.8f} {z:.8f}"
                                     for i, (x, y, z) in enumerate(coords))
        mol, mf = build(spec, out["xyz_final"])
    e = float(mf.kernel())
    out.update(energy_Eh=e, scf_converged=bool(mf.converged))
    if spec["spin"] > 0:
        try:
            s2, mult = mf.spin_square()
            out["s2"], out["s2_ideal"] = float(s2), spec["spin"] / 2 * (spec["spin"] / 2 + 1)
        except Exception as err:  # spin contamination is diagnostic only
            out["s2_error"] = str(err)[:200]
    if getattr(mf, "with_df", None) is not None:
        out["auxbasis"] = str(getattr(mf.with_df, "auxbasis", None))
    if "freq" in spec["task"]:
        out["thermo"] = thermo_analysis(mf, mol, spec)
    out["wall_s"] = round(time.time() - t0, 1)
    out["status"] = "ok" if out["scf_converged"] and out.get("opt_converged", True) else "not_converged"
    return out


def main(path):
    spec = json.load(open(path))
    try:
        import pyscf
        res = run(spec)
        res["versions"] = {"pyscf": pyscf.__version__}
        try:
            import gpu4pyscf
            res["versions"]["gpu4pyscf"] = gpu4pyscf.__version__
        except ImportError:
            pass
    except Exception as e:  # always leave a result behind for diagnosis
        res = {"name": spec.get("name"), "task": spec.get("task"), "status": "error",
               "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()[-3000:], "spec": spec}
    json.dump(res, open("result.json", "w"), indent=1)
    return 0 if res["status"] == "ok" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "job.json"))
