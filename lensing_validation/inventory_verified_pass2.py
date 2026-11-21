#!/usr/bin/env python3
"""inventory_verified_pass2.py (2026-11-20): second pass over the files pass 1 could not judge. Pass 1 compared compressed size with implied
uncompressed size (every .gz 'mismatch') and used memmap on scaled images (402 'unreadable'). Here: memmap=False; gz files compared by the
gzip trailer ISIZE (mod 2^32) and, for files under 6 GB, a full gzip CRC read.  Usage: python inventory_verified_pass2.py PASS1.csv OUT.csv"""
import sys, os, csv, gzip, struct, warnings, zlib
import pandas as pd
from astropy.io import fits
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1]); todo = d[d.ok != "ok"]
KEYS = ["INSTRUME", "DETECTOR", "FILTER", "PUPIL", "FILTER1", "FILTER2", "FILTNAM1", "OPT_ELEM", "TARGNAME", "TARGPROP", "PROPOSID", "PROGRAM", "DATE-OBS", "EXPTIME", "TELESCOP"]
rows = []
for i, r in enumerate(todo.itertuples(), 1):
    p = r.path; o = {"path": p, "size": os.path.getsize(p), "ok": "", "err": ""}
    try:
        gz = p.endswith(".gz")
        with fits.open(p, memmap=False, lazy_load_hdus=True) as h:
            need = 0; hd = {}
            for x in h:
                need += x.filebytes()
                for k in KEYS:
                    if k in x.header and k not in hd: hd[k] = str(x.header[k])
            o.update(hd); o["nhdu"] = len(h); o["implied"] = need
        if gz:
            with open(p, "rb") as f: f.seek(-4, 2); isize = struct.unpack("<I", f.read(4))[0]
            o["ok"] = "ok" if isize % 2 ** 32 == need % 2 ** 32 or abs(isize - need) < 5760 else "GZ_ISIZE_MISMATCH"
            if o["ok"] == "ok" and o["size"] < 6e9:
                try:
                    with gzip.open(p, "rb") as g:
                        while g.read(1 << 24): pass
                except (EOFError, OSError, zlib.error) as e: o["ok"] = "GZ_CRC_FAIL"; o["err"] = str(e)[:100]
        else:
            o["ok"] = "ok" if need <= o["size"] and o["size"] - need < 5760 else "SIZE_MISMATCH"
    except Exception as e:
        o["ok"] = "UNREADABLE"; o["err"] = str(e)[:120]
    rows.append(o)
    if i % 50 == 0: print(i, len(todo), p, flush=True)
cols = ["path", "size", "ok", "err", "nhdu", "implied"] + KEYS
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.DictWriter(fh, cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
c = pd.Series([r["ok"] for r in rows]).value_counts().to_dict(); print("done", len(rows), c)
