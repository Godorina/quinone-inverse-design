"""DFT smoke check: water B3LYP/def2-SVP/SMD(MeCN) on CPU (PySCF) and GPU (gpu4pyscf) must agree."""
import time, cupy
from pyscf import gto, dft
from gpu4pyscf import dft as gdft
m=gto.M(atom='O 0 0 0; H 0 0.757 0.587; H 0 -0.757 0.587', basis='def2-svp', verbose=0)
t=time.time(); c=dft.RKS(m, xc='b3lyp').SMD(); c.with_solvent.solvent='acetonitrile'; ec=c.kernel(); print(f'CPU E={ec:.6f} {time.time()-t:.1f}s')
free,total=cupy.cuda.Device(0).mem_info; print(f'GPU0 free {free/2**30:.1f}/{total/2**30:.1f} GiB')
t=time.time(); g=gdft.RKS(m, xc='b3lyp').SMD(); g.with_solvent.solvent='acetonitrile'; eg=float(g.kernel()); print(f'E={eg:.6f} {time.time()-t:.1f}s dE={abs(eg-ec)*627.5:.4f} kcal/mol')
assert abs(eg-ec)*627.5 < 0.01, 'CPU and GPU energies disagree'
