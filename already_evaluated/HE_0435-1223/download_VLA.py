#!/usr/bin/env python3
"""HE 0435-1223 — VLA / EVLA full polarization (RR RL LR LL). Writes only to ./VLA/.

Holdings (NRAO TAP, 0.02 deg cone, queried 2026-10-22; nrao_holdings_2026-10-22.csv):
  12B-030  EVLA  C band 4.7-6.5 cm  two execution blocks, archive estimate 21.9 + 25.5 = 47.4 GB, MJD 56226 / 56240
Also in the cone, NOT queued: VLBA BS275D (RR only, 19.9 cm, est. 3.5 TB).
The NRAO portal's download form REQUIRES the user's email (it mails a retrieval link). This script never sends one:
  1. python3 download_VLA.py --list            prints the two blocks + portal URLs (read-only)
  2. Cody requests the blocks on the portal himself, or tells Claude to submit with his email (explicit go).
  3. Paste the mailed direct links, one per line, into VLA/links.txt, then:  python3 download_VLA.py
     (resumable; free-space guard; 15-minute status line)
"""
import argparse, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import he0435_common as C

OUT = os.path.join(C.ROOT, "VLA")
a = argparse.ArgumentParser(); a.add_argument("--list", action="store_true"); a = a.parse_args()
os.makedirs(OUT, exist_ok=True)
if a.list:
    seen = {}
    for r in csv.DictReader(open(os.path.join(C.ROOT, "nrao_holdings_2026-10-22.csv"))):
        if r["project_code"] == "12B-030": seen.setdefault(r["obs_publisher_did"], r)
    tot = 0
    for k, r in seen.items():
        g = int(r["access_estsize"]) / 1e6; tot += g
        print(f"{k}  {r['pol_states']}  est {g:.1f} GB\n   {r['access_url']}")
    print(f"TOTAL ~ {tot:.1f} GB (archive estimate)"); sys.exit(0)
lf = os.path.join(OUT, "links.txt")
if not os.path.exists(lf):
    sys.exit("VLA/links.txt missing: request the blocks on the NRAO portal first (see --list and the docstring).")
links = [l.strip() for l in open(lf) if l.strip() and not l.startswith("#")]
man = [{"url": u, "dest": os.path.join(OUT, os.path.basename(u.split("?")[0]) or f"vla_{i}.tar")} for i, u in enumerate(links)]
sys.exit(C.run_manifest(man, os.path.join(OUT, "vla_state.json")))
