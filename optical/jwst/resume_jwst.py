#!/usr/bin/env python3
"""
resume_jwst.py — Resume JWST Program 4598 download (Bullet Cluster, Bradač 2025)
8 NIRCam filters: F090W F115W F150W F200W F277W F356W F410M F444W
Downloads only i2d (calibrated drizzled mosaic) products — highest-level science files.
Skips already-downloaded files by size check.
"""

from astroquery.mast import Observations
from pathlib import Path
import sys

BASE = Path("/media/rendier/0123-4567/ThePlace/BulletCluster/optical/jwst/4598/mastDownload")

print("Querying MAST for program 4598 observations...")
obs = Observations.query_criteria(
    proposal_id="4598",
    obs_collection="JWST",
    dataproduct_type="image",
)
print(f"Found {len(obs)} observations")

if len(obs) == 0:
    print("No observations found. Trying by coordinates...")
    obs = Observations.query_criteria(
        s_ra=[104.3, 104.9],
        s_dec=[-56.2, -55.7],
        obs_collection="JWST",
        proposal_id="4598",
    )
    print(f"Found {len(obs)} observations by coordinates")

print("\nObservations:")
for o in obs:
    print(f"  {o['obs_id']}  {o['filters']}  {o['t_exptime']:.0f}s")

print("\nQuerying data products (i2d only)...")
products = Observations.get_product_list(obs)

# Mosaic-level i2d files have dashes: jw04598-o001_t001_nircam_clear-f444w_i2d.fits
# Individual detector files have no dashes: jw04598001001_..._nrca2_i2d.fits
# We want ONLY the mosaic-level (level 3) combined drizzled mosaics.
i2d = products[
    (products['productType'] == 'SCIENCE') &
    [fn.endswith('_i2d.fits') and 'nircam_clear' in fn
     for fn in products['productFilename']]
]

print(f"Found {len(i2d)} i2d products:")
for p in i2d:
    print(f"  {p['productFilename']}  {p['size']/1e6:.0f} MB")

# Check which are already downloaded
already = set()
for f in BASE.rglob("*_i2d.fits"):
    already.add(f.name)
    print(f"  [HAVE] {f.name}  {f.stat().st_size/1e6:.0f} MB")

to_download = i2d[[p['productFilename'] not in already for p in i2d]]
print(f"\n{len(to_download)} files to download  ({sum(to_download['size'])/1e9:.2f} GB)")

if len(to_download) == 0:
    print("All i2d files already downloaded.")
    sys.exit(0)

print("\nStarting download...")
manifest = Observations.download_products(
    to_download,
    download_dir=str(BASE.parent),
    flat=False,
)

print("\nDownload complete. Manifest:")
for row in manifest:
    print(f"  {row['Status']}  {row['Local Path']}")
