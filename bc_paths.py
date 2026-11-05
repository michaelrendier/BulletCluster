# SPDX-License-Identifier: GPL-3.0-only
"""One place for where the Bullet Cluster telescope data lives (changed 2026-11-04).

The data root is  $BC_DATA_ROOT  (default: the Telescope Data disk).  The OLD layout used by the scripts
(xray/chandra, optical/jwst, radio/meerkat, ...) is mapped onto the layout on that disk:

    BCData/{JWST, JWST_scaffold_level3, HST, Chandra, MeerKAT, Planck, ...}

    import bc_paths;  bc_paths.dir("optical/jwst")  ->  <root>/JWST
"""
import os
from pathlib import Path

ROOT = Path(os.environ.get("BC_DATA_ROOT", "/media/rendier/Telescope Data/BulletCluster/BCData"))

LAYOUT = {
    "xray/chandra": "Chandra", "xray/xmm": "XMM", "xray/nustar": "NuSTAR", "xray/rosat": "ROSAT",
    "optical/hst": "HST", "optical/jwst": "JWST", "optical/lensing": "Lensing",
    "mm_sz/planck": "Planck", "mm_sz/act": "ACT", "mm_sz/spt": "SPT",
    "radio/meerkat": "MeerKAT", "radio/atca": "ATCA", "radio/vla": "VLA", "radio/askap": "ASKAP",
    "gamma/fermi": "Fermi",
}
REPO = Path(__file__).resolve().parent


def dir(old: str) -> Path:
    """Directory for an old-layout key such as 'optical/jwst'."""
    return ROOT / LAYOUT.get(old.strip("/"), old.strip("/"))
