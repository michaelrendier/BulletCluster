#!/usr/bin/env python3
"""bullet_scaffold.py (2026-11-20): add the Bullet Cluster to the scaffold gallery (it was the one target excluded).  NIRCam program 4598 pointing o001, filters F090W..F444W.
Same make_scaffold.composite() as every other scaffold; outputs scaffolds/BulletCluster/{raw,false_color}/ with sidecars.  Usage: BulletCluster/.venv/bin/python bullet_scaffold.py"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_scaffold as M
R = "/media/rendier/Telescope Data/BulletCluster/BCData/JWST_scaffold_level3/data/jwst"
files = [f"{R}/jw04598-o001_t001_nircam_clear-{f}_i2d.fits" for f in ("f090w", "f115w", "f150w", "f200w", "f277w", "f356w", "f444w")]
assert all(os.path.exists(f) for f in files), [f for f in files if not os.path.exists(f)]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BulletCluster")
print(M.composite(files, out, "BulletCluster_nircam_o001"))
