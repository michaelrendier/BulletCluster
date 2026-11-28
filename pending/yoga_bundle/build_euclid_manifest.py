#!/usr/bin/env python3
"""build_euclid_manifest.py NAME RA DEC [--radius-arcmin 5] [--products mosaic,stack,all] [--bands VIS,Y,J,H,G,R,I,Z] -- list Euclid DR1 files (IRSA CAOM tables) whose
footprint contains a position and write jobs/NAME/manifest.json (relative dests, server sizes). Read-only, stdlib only, Mozilla UA.
  python3 build_euclid_manifest.py euclid_DESJ0408_5354 62.09132 -53.90026
Products: `science`+`noise`+`weight`+`auxiliary` of the MER tile mosaics (VIS, NISP Y/J/H, DECam G/R/I/Z) and the VIS/NISP stacked frames with their PSF files.
Use --kinds science,noise,weight to leave out the large `auxiliary` background and mask maps."""
import argparse, csv, io, json, os, sys, urllib.parse, urllib.request
UA = os.environ.get("CLAUDE_UA") or "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("ra", type=float); ap.add_argument("dec", type=float)
ap.add_argument("--kinds", default="science,noise,weight,auxiliary"); ap.add_argument("--bands", default="")
a = ap.parse_args()
q = ("SELECT o.collection,o.instrument_name,p.energy_bandpassname,a.producttype,a.uri,a.contentlength FROM euclid.plane_euclid_dr1 p "
     "JOIN euclid.observation_euclid_dr1 o ON p.obsid=o.obsid JOIN euclid.artifact_euclid_dr1 a ON a.planeid=p.planeid "
     f"WHERE CONTAINS(POINT('ICRS',{a.ra},{a.dec}),p.poly)=1")
req = urllib.request.Request("https://irsa.ipac.caltech.edu/TAP/sync", data=urllib.parse.urlencode(dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q)).encode(), headers={"User-Agent": UA})
rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(req, timeout=300).read().decode())))
kinds = set(a.kinds.split(",")); bands = set(filter(None, a.bands.split(",")))
items, seen = [], set()
for r in rows:
    if r["producttype"] not in kinds or (bands and r["energy_bandpassname"] not in bands) or r["uri"] in seen:
        continue
    seen.add(r["uri"])
    coll = "stacked" if "Stacked" in r["collection"] else "mer_" + r["collection"].split("_")[2]
    items.append({"url": "https://irsa.ipac.caltech.edu/" + r["uri"], "dest": f"EuclidDR1/{a.name}/{coll}/{r['instrument_name']}/{os.path.basename(r['uri'])}", "size": int(r["contentlength"] or 0)})
items.sort(key=lambda x: x["dest"])
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs", a.name), exist_ok=True)
json.dump(items, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs", a.name, "manifest.json"), "w"), indent=1)
print(f"{len(items)} files, {sum(i['size'] for i in items) / 1e9:.1f} GB")
