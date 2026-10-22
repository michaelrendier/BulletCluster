#!/usr/bin/env python3
"""HE 0435-1223 — JWST (FIRST download: the imaging scaffold). Writes only to ./JWST/.

Programs: GO-1198 (NIRCam 4 filters, NIRSpec IFU G140M/F100LP, two observations) and GO-2046 (MIRI 4 filters).
Default (per Cody, 2026-10-22): WHOLE level-3 products — NIRCam i2d 1442/1442/344/344 MB, MIRI i2d 37.8 MB x4,
NIRSpec s3d 62.8 + 40.9 MB, x1d, catalogs, and the segmentation maps. Not fetched: uncal/rate/cal, per-detector i2d.
  --cutout shrinks the four NIRCam mosaics to a +-HALF" box (SCI, ERR, WHT, CON) by HTTP Range (128/128/31/31 MB).
Order: NIRCam F150W first (best SW scaffold), F115W, F277W, F356W, then MIRI, then NIRSpec.

  python3 download_JWST.py --dry-run           # sizes only, nothing written
  python3 download_JWST.py [--only nircam|miri|nirspec] [--cutout --half 45] [--no-segm]
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import he0435_common as C

OUT = os.path.join(C.ROOT, "JWST")
P1198, P2046 = "mast:JWST/product/jw01198-o007_t005_nircam_clear-", "mast:JWST/product/jw02046-o007_t006_miri_"
NIRCAM = ["f150w", "f115w", "f277w", "f356w"]
MIRI = ["f560w", "f1280w", "f1800w", "f2550w"]
NIRSPEC = [("o008", 62.8), ("o012", 40.9)]
SMALL = [(f"{P1198}{f}_cat.ecsv", f"nircam_{f}_cat.ecsv", 2e6) for f in NIRCAM] + \
        [(f"{P2046}{f}_cat.ecsv", f"miri_{f}_cat.ecsv", 3e5) for f in MIRI]

a = argparse.ArgumentParser()
a.add_argument("--half", type=float, default=45.0, help="cutout half-width, arcsec (default 45 = 90\" box)")
a.add_argument("--cutout", action="store_true", help="NIRCam cutouts instead of whole mosaics")
a.add_argument("--no-segm", action="store_true", help="skip segmentation maps (~530 MB)")
a.add_argument("--only", choices=["nircam", "miri", "nirspec"])
a.add_argument("--dry-run", action="store_true")
a = a.parse_args()
os.makedirs(OUT, exist_ok=True)
total = 0.0

SEGM_MB = {"f150w": 206.2, "f115w": 206.2, "f277w": 49.2, "f356w": 49.2}
NIRCAM_MB = {"f150w": 1442.3, "f115w": 1442.3, "f277w": 343.9, "f356w": 344.0}
whole = []
if a.only in (None, "nircam") and not a.cutout:
    whole += [(f"{P1198}{f}_i2d.fits", f"nircam_{f}_i2d.fits", NIRCAM_MB[f] * 1e6) for f in NIRCAM]
if a.only in (None, "nircam") and a.cutout:
    for f in NIRCAM:
        url = C.mast_url(f"{P1198}{f}_i2d.fits")
        if a.dry_run:
            box, nb, sc, sh = C.plan_cutout(url, a.half, ("SCI", "ERR", "WHT", "CON"))
            print(f"NIRCam {f}: cutout {box[1]-box[0]}x{box[3]-box[2]} px @ {sc:.4f}\"/px = {nb/1e6:.0f} MB (whole {sh[1]}x{sh[0]})")
            total += nb
        else:
            C.write_cutout(url, os.path.join(OUT, f"nircam_{f}_i2d_cutout{int(2*a.half)}as.fits"), a.half)

if a.only in (None, "miri"):
    whole += [(f"{P2046}{f}_i2d.fits", f"miri_{f}_i2d.fits", 37.8e6) for f in MIRI]
if a.only in (None, "nirspec"):
    for o, mb in NIRSPEC:
        b = f"mast:JWST/product/jw01198-{o}_t005_nirspec_g140m-f100lp_"
        whole += [(b + "s3d.fits", f"nirspec_{o}_s3d.fits", mb * 1e6), (b + "x1d.fits", f"nirspec_{o}_x1d.fits", 3e5)]
if a.only is None:
    whole += SMALL
    if not a.no_segm:
        whole += [(f"{P1198}{f}_segm.fits", f"nircam_{f}_segm.fits", SEGM_MB[f] * 1e6) for f in NIRCAM]
        whole += [(f"{P2046}{f}_segm.fits", f"miri_{f}_segm.fits", 5.5e6) for f in MIRI]
if a.dry_run:
    for _, n, s in whole:
        print(f"{n}: {s/1e6:.1f} MB"); total += s
    print(f"TOTAL JWST ~ {total/1e6:.0f} MB")
    sys.exit(0)
man = [{"url": C.mast_url(u), "dest": os.path.join(OUT, n)} for u, n, _ in whole]
sys.exit(C.run_manifest(man, os.path.join(OUT, "jwst_state.json")))
