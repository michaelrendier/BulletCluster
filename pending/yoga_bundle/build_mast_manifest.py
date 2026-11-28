#!/usr/bin/env python3
"""build_mast_manifest.py NAME RA DEC -- list public MAST products (JWST or HST) near a position and write jobs/NAME/manifest.json.
Needs astroquery (run `.venv/bin/pip install astroquery astropy`). Read-only; Mozilla UA. Sizes in MAST product lists are often stale: run_job.sh passes
--trust-server-size to the downloader, which replaces them with the server's Content-Length.
  python3 build_mast_manifest.py jwst_9637_DESJ0408 62.09132 -53.90026 --collection JWST --programs 9637 --calib 2,3 --subgroups CAL,I2D,CRF,RATE
Per-exposure frames (what weak-lensing shape measurement and ptychography need): JWST `CAL` (calibrated), `CRF` (cosmic-ray flagged), `RATE` (slope); HST `FLC`/`FLT`.
Mosaics: JWST `I2D`; HST `DRZ`/`DRC`. Catalogs: `CAT`."""
import argparse, json, os, urllib.parse
import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("ra", type=float); ap.add_argument("dec", type=float)
ap.add_argument("--collection", default="JWST"); ap.add_argument("--radius-arcsec", type=float, default=120)
ap.add_argument("--programs", default=""); ap.add_argument("--calib", default="2,3"); ap.add_argument("--subgroups", default="CAL,CRF,I2D,CAT")
ap.add_argument("--instruments", default=""); a = ap.parse_args()
Observations._session.headers["User-Agent"] = os.environ.get("CLAUDE_UA") or "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
o = Observations.query_region(SkyCoord(a.ra * u.deg, a.dec * u.deg), radius=a.radius_arcsec * u.arcsec)
progs, insts = set(filter(None, a.programs.split(","))), {x.upper() for x in a.instruments.split(",") if x}
rows = [r for r in o if str(r["obs_collection"]).upper() == a.collection.upper() and str(r["dataRights"]) == "PUBLIC"
        and (not progs or str(r["proposal_id"]) in progs) and (not insts or str(r["instrument_name"]).split("/")[0].upper() in insts)]
ids = [str(r["obsid"]) for r in rows]; prog = {str(r["obsid"]): str(r["proposal_id"]) for r in rows}
calib, subs, items, seen = set(a.calib.split(",")), set(a.subgroups.split(",")), [], set()
for i in range(0, len(ids), 15):
    for _ in range(4):
        try:
            pl = Observations.get_product_list(ids[i:i + 15]); break
        except Exception as e:
            print("retry", e)
    else:
        continue
    for p in pl:
        fn = str(p["productFilename"])
        if str(p["calib_level"]) not in calib or str(p["productSubGroupDescription"]) not in subs or fn in seen:
            continue
        seen.add(fn)
        items.append({"url": "https://mast.stsci.edu/api/v0.1/Download/file?uri=" + urllib.parse.quote(str(p["dataURI"]), safe=""),
                      "dest": f"{a.collection}/{a.name}/{prog.get(str(p['parent_obsid']), 'x')}/{fn}", "size": int(p["size"] or 0)})
items.sort(key=lambda x: x["dest"])
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs", a.name); os.makedirs(d, exist_ok=True)
json.dump(items, open(os.path.join(d, "manifest.json"), "w"), indent=1)
print(f"{len(rows)} observations, {len(items)} files, {sum(i['size'] for i in items) / 1e9:.1f} GB (MAST list sizes)")
