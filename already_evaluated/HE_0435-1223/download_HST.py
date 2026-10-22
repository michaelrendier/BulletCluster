#!/usr/bin/env python3
"""HE 0435-1223 — HST. Writes only to ./HST/.  Run AFTER download_JWST.py.

Level-3 drizzled products only (sizes from MAST 2026-10-22):
  ACS/WFC  F555W + F814W  prog 9744 (j8oi12 drc)  326.7 MB each      WFC3/IR F160W prog 12889  21.4 MB     F140W prog 13732  26.2 MB
plus the point/segment catalogs. No HST polarizer data exists in this field (POL filters: none within 60").
Not fetched: WFC3/UVIS F275W (progs 11732, 12324, 13113; many multi-ks visits), G141 grism, flt/raw/ima.
  python3 download_HST.py --dry-run
  python3 download_HST.py [--cutout --half 45]      # ACS only: SCI/WHT/CTX box instead of the 327 MB mosaics
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import he0435_common as C

OUT = os.path.join(C.ROOT, "HST")
H = "mast:HST/product/"
ACS = [("f814w", "hst_9744_12_acs_wfc_f814w_j8oi12"), ("f555w", "hst_9744_12_acs_wfc_f555w_j8oi12")]
WFC3 = [("f160w", "hst_12889_01_wfc3_ir_f160w_ibyg01", 21.4e6), ("f140w", "hst_13732_01_wfc3_ir_f140w_ico201", 26.2e6)]
CATS = [(f"{b}_{k}-cat.ecsv", 1.2e6) for _, b in ACS for k in ("point", "segment")] + \
       [(f"{b}_{k}-cat.ecsv", 0.5e6) for _, b, _ in WFC3 for k in ("point", "segment")]

a = argparse.ArgumentParser()
a.add_argument("--cutout", action="store_true"); a.add_argument("--half", type=float, default=45.0)
a.add_argument("--dry-run", action="store_true")
a = a.parse_args()
os.makedirs(OUT, exist_ok=True)
whole, total = [], 0.0
for f, b in ACS:
    if a.cutout:
        url = C.mast_url(f"{H}{b}_drc.fits")
        if a.dry_run:
            box, nb, sc, sh = C.plan_cutout(url, a.half, ("SCI", "WHT", "CTX")); total += nb
            print(f"ACS {f}: cutout {box[1]-box[0]}x{box[3]-box[2]} px = {nb/1e6:.0f} MB")
        else:
            C.write_cutout(url, os.path.join(OUT, f"acs_{f}_drc_cutout{int(2*a.half)}as.fits"), a.half, ("SCI", "WHT", "CTX"))
    else:
        whole.append((f"{H}{b}_drc.fits", f"acs_{f}_drc.fits", 326.7e6))
whole += [(f"{H}{b}_drz.fits", f"wfc3ir_{f}_drz.fits", s) for f, b, s in WFC3]
whole += [(H + n, n.replace("hst_", "").replace("_wfc_", "_").replace("_wfc3_ir_", "_wfc3ir_"), s) for n, s in CATS]
if a.dry_run:
    total += sum(s for *_, s in whole)
    for _, n, s in whole: print(f"{n}: {s/1e6:.1f} MB")
    print(f"TOTAL HST ~ {total/1e6:.0f} MB"); sys.exit(0)
man = [{"url": C.mast_url(u), "dest": os.path.join(OUT, n)} for u, n, _ in whole]
sys.exit(C.run_manifest(man, os.path.join(OUT, "hst_state.json")))
