#!/usr/bin/env python3
"""inventory_verified.py (2026-11-20): read-only verified inventory of every FITS file under the Telescope Data drive.
For each file: open every HDU, compare the bytes the headers imply with the file size (truncation test), read INSTRUME, DETECTOR,
FILTER/PUPIL/FILTER1/FILTER2/FILTNAM1/OPT_ELEM, target, program, date, and the product suffix. Nothing is taken from a state file.
Usage: ValaQuenta/.venv/bin/python inventory_verified.py OUT.csv [ROOT ...]"""
import sys, os, csv, warnings, re
from astropy.io import fits
warnings.filterwarnings("ignore")
out = sys.argv[1]; roots = sys.argv[2:] or ["/media/rendier/Telescope Data"]
KEYS = ["INSTRUME", "DETECTOR", "FILTER", "PUPIL", "FILTER1", "FILTER2", "FILTNAM1", "OPT_ELEM", "TARGNAME", "TARGPROP", "PROPOSID", "PROGRAM", "DATE-OBS", "EXPTIME", "TELESCOP"]
rows = []
n = 0
for root in roots:
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            if not f.lower().endswith((".fits", ".fit", ".fits.gz")): continue
            p = os.path.join(dp, f); n += 1
            r = {"path": p, "size": os.path.getsize(p), "suffix": re.sub(r"\.fits(\.gz)?$", "", f).split("_")[-1], "ok": "", "err": ""}
            try:
                with fits.open(p, memmap=True) as h:
                    need = sum(x.filebytes() for x in h)
                    r["nhdu"] = len(h); r["implied"] = need
                    r["ok"] = "ok" if need <= r["size"] and r["size"] - need < 2880 * 2 else "SIZE_MISMATCH"
                    hd = {}
                    for x in h:
                        for k in KEYS:
                            if k in x.header and k not in hd: hd[k] = str(x.header[k])
                    r.update(hd)
            except Exception as e:
                r["ok"] = "UNREADABLE"; r["err"] = str(e)[:120]
            rows.append(r)
            if n % 200 == 0: print(n, p, flush=True)
cols = ["path", "size", "suffix", "ok", "err", "nhdu", "implied"] + KEYS
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("done", n, "files;", sum(r["ok"] == "ok" for r in rows), "ok;", sum(r["ok"] == "SIZE_MISMATCH" for r in rows), "size mismatch;", sum(r["ok"] == "UNREADABLE" for r in rows), "unreadable")
