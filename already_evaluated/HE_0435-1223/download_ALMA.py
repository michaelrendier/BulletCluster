#!/usr/bin/env python3
"""HE 0435-1223 — ALMA (XX/YY only: no polarization products). Writes only to ./ALMA/.

Programme 2024.1.00291.S, 7 member OUS, all Data Rights = Public (ALMA TAP, 0.02 deg cone, alma_mous_raw.csv).
Public DataLink gives direct URLs (no login, no email): per member the README, the product tar (#this) and the auxiliary tar.
Sizes below come from DataLink content_length, not an estimate.
  python3 download_ALMA.py --list       # read-only, prints the links and sizes
  python3 download_ALMA.py              # download (resumable, free-space guard, 15-min status line)
"""
import argparse, csv, os, sys, re, xml.etree.ElementTree as ET
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import he0435_common as C

OUT = os.path.join(C.ROOT, "ALMA")
a = argparse.ArgumentParser(); a.add_argument("--list", action="store_true"); a = a.parse_args()
os.makedirs(OUT, exist_ok=True)
NS = "{http://www.ivoa.net/xml/VOTable/v1.3}"
members = {}
for r in csv.DictReader(open(os.path.join(C.ROOT, "alma_mous_raw.csv"))):
    members.setdefault(r["member_ous_uid"], r)
man, tot = [], 0
for uid, r in members.items():
    x = requests.get(r["access_url"], headers={"User-Agent": C.UA}, timeout=90).text
    for tr in ET.fromstring(x).iter(NS + "TR"):
        td = [t.text or "" for t in tr.findall(NS + "TD")]
        url, sem, size = td[1], td[4], td[8]
        if url.startswith("https://") and sem in ("#this", "#auxiliary", "#documentation"):
            man.append({"url": url, "dest": os.path.join(OUT, url.rsplit("/", 1)[1]), "size": int(size) if size else None})
            tot += int(size or 0)
            if a.list: print(f"{sem:15s} {int(size or 0)/1e6:8.1f} MB  {url.rsplit('/',1)[1]}")
print(f"TOTAL ALMA {tot/1e6:.0f} MB in {len(man)} files ({len(members)} members)")
if a.list: sys.exit(0)
sys.exit(C.run_manifest(man, os.path.join(OUT, "alma_state.json")))
