#!/usr/bin/env python3
"""Manifest of the public JWST level-3 IMAGING products (I2D mosaics + source catalogs) within 120 arcsec of Sgr A*, for the dust target D5.
Imaging programs only (NIRCam, MIRI imaging); the MIRI/NIRSpec IFU cube programs (1266, 2075, 2491, 3166, 6095) are a later, separate list.
Run in BulletCluster/.venv; read-only against MAST; writes manifest.json beside this file."""
import json, os, urllib.parse, astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/media/rendier/Telescope Data/BulletCluster/Dust/Sagittarius_A_star/JWST"
Observations._session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
PROGS = {"10678", "1939", "1306", "2772", "3571", "2235", "4515", "5368", "9257"}
c = SkyCoord(266.41684 * u.deg, -29.00781 * u.deg)
o = Observations.query_region(c, radius=120 * u.arcsec)
j = o[(o["obs_collection"] == "JWST") & (o["calib_level"] == 3) & (o["dataRights"] == "PUBLIC")]
rows = [r for r in j if str(r["proposal_id"]) in PROGS and str(r["instrument_name"]).split("/")[0] in ("NIRCAM", "MIRI") and "CH" not in str(r["filters"])]
print("imaging level-3 public obs:", len(rows))
seen, items = set(), []
ids = [str(r["obsid"]) for r in rows]
prog_of = {str(r["obsid"]): str(r["proposal_id"]) for r in rows}
for i in range(0, len(ids), 15):
    for attempt in range(4):
        try:
            pl = Observations.get_product_list(ids[i:i + 15]); break
        except Exception as e:
            print("retry", e)
    else:
        continue
    for p in pl:
        if str(p["calib_level"]) != "3" or str(p["productSubGroupDescription"]) not in ("I2D", "CAT"):
            continue
        fn = str(p["productFilename"])
        if fn in seen:
            continue
        seen.add(fn)
        pid = prog_of.get(str(p["parent_obsid"]), "unknown")
        items.append({"url": "https://mast.stsci.edu/api/v0.1/Download/file?uri=" + urllib.parse.quote(str(p["dataURI"]), safe=""),
                      "dest": f"{ROOT}/{pid}/{fn}", "size": int(p["size"])})
items.sort(key=lambda x: (x["dest"].split("/")[-2], x["size"]))
json.dump(items, open(os.path.join(HERE, "manifest.json"), "w"), indent=1)
tot = sum(x["size"] for x in items)
print(len(items), "files,", round(tot / 1e9, 2), "GB")
by = {}
for x in items:
    by.setdefault(x["dest"].split("/")[-2], [0, 0]); by[x["dest"].split("/")[-2]][0] += 1; by[x["dest"].split("/")[-2]][1] += x["size"]
for k, v in sorted(by.items()):
    print(" ", k, v[0], "files", round(v[1] / 1e9, 2), "GB")
