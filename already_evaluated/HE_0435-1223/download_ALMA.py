#!/usr/bin/env python3
"""HE 0435-1223 — ALMA (OPTIONAL, XX/YY only: no polarization products). Writes only to ./ALMA/.

Holdings (alma_holdings_2026-10-22.csv): programme 2024.1.00291.S, 11 member blocks, 0.5-0.7 GB each (archive estimate),
bands from 0.87 to 3.38 mm. Same access rule as VLA: the NRAO/ALMA portal route needs the user's email, never sent by this script.
  python3 download_ALMA.py --list       # read-only
  python3 download_ALMA.py              # after pasting direct links, one per line, into ALMA/links.txt
"""
import argparse, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import he0435_common as C

OUT = os.path.join(C.ROOT, "ALMA")
a = argparse.ArgumentParser(); a.add_argument("--list", action="store_true"); a = a.parse_args()
os.makedirs(OUT, exist_ok=True)
if a.list:
    seen = {}
    for r in csv.DictReader(open(os.path.join(C.ROOT, "alma_holdings_2026-10-22.csv"))):
        seen.setdefault(r["obs_publisher_did"], r)
    tot = 0
    for k, r in seen.items():
        g = int(r["access_estsize"] or 0) / 1e6; tot += g
        print(f"{k}  {r['project_code']}  {float(r['em_min'])*1e3:.2f} mm  est {g:.2f} GB")
    print(f"TOTAL ~ {tot:.1f} GB"); sys.exit(0)
lf = os.path.join(OUT, "links.txt")
if not os.path.exists(lf):
    sys.exit("ALMA/links.txt missing: request the blocks first (see --list).")
links = [l.strip() for l in open(lf) if l.strip() and not l.startswith("#")]
man = [{"url": u, "dest": os.path.join(OUT, os.path.basename(u.split("?")[0]) or f"alma_{i}.tar")} for i, u in enumerate(links)]
sys.exit(C.run_manifest(man, os.path.join(OUT, "alma_state.json")))
