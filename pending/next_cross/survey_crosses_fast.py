#!/usr/bin/env python3
"""survey_crosses_fast.py -- the fast half of survey_crosses.py: positions, JWST and HST-polarizer coverage (MAST) and Euclid DR1/Q1 tiles (IRSA CAOM). Read-only, Mozilla UA."""
import collections, csv, io, json, sys, requests, astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
sys.argv = [sys.argv[0]]
exec(open("survey_crosses.py").read().split("def tap")[0].split("NAMES =")[1].join(["NAMES =", ""]) if False else "")
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
Observations._session.headers["User-Agent"] = UA
S = requests.Session(); S.headers["User-Agent"] = UA
src = open("survey_crosses.py").read()
NAMES = eval(src.split("NAMES = ")[1].split("\ndef tap")[0])
def tap(url, q, to=120):
    r = S.post(url, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=to); r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))
out = []
for name in NAMES:
    rec = {"name": name}
    try:
        p = SkyCoord.from_name(name); rec["ra"], rec["dec"] = round(p.ra.deg, 5), round(p.dec.deg, 5)
    except Exception as e:
        rec["unresolved"] = str(e)[:60]; out.append(rec); print(json.dumps(rec), flush=True); continue
    try:
        t = Observations.query_region(p, radius=60 * u.arcsec)
        j = t[[str(c).upper() == "JWST" for c in t["obs_collection"]]]
        rec["jwst_obs"] = len(j); rec["jwst_programs"] = sorted({str(x) for x in j["proposal_id"]})
        rec["jwst_instruments"] = dict(collections.Counter(str(x).split("/")[0] for x in j["instrument_name"]))
        h = t[[str(c).upper() == "HST" for c in t["obs_collection"]]]
        rec["hst_obs"] = len(h)
        rec["hst_pol"] = sum(1 for f in h["filters"] if "POL" in str(f).upper())
    except Exception as e:
        rec["mast_error"] = f"{type(e).__name__}: {str(e)[:80]}"
    for tab in ("euclid.plane_euclid_dr1", "euclid.plane_euclid_q1"):
        try:
            r = tap("https://irsa.ipac.caltech.edu/TAP/sync", f"SELECT energy_bandpassname FROM {tab} WHERE CONTAINS(POINT('ICRS',{p.ra.deg},{p.dec.deg}),poly)=1")
            rec[tab.split(".")[1]] = {"tiles": len(r), "bands": sorted({x["energy_bandpassname"] for x in r})}
        except Exception as e:
            rec[tab.split(".")[1] + "_error"] = f"{type(e).__name__}: {str(e)[:80]}"
    out.append(rec); print(json.dumps(rec), flush=True)
json.dump(out, open("crosses_fast.json", "w"), indent=1)
