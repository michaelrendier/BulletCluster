#!/usr/bin/env python3
"""survey_jwst_lenses.py — which candidate lenses has JWST observed, with which of its four instruments (MAST, public query, Mozilla UA)."""
import json, sys, collections, time
from astroquery.mast import Observations
import astropy.coordinates as coord, astropy.units as u
from astropy.coordinates import SkyCoord
import requests
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
Observations._session.headers.update({"User-Agent": UA})
CANDS = [  # name, kind, search radius arcsec
 ("SMACS J0723.3-7327", "cluster", 120), ("Abell 2744", "cluster", 150), ("MACS J0416.1-2403", "cluster", 150), ("MACS J1149.5+2223", "cluster (Refsdal)", 150),
 ("RX J1131-1231", "quad quasar, single lens galaxy", 40), ("HE 0435-1223", "quad quasar, single lens galaxy", 40), ("PG 1115+080", "quad quasar, single lens galaxy", 40),
 ("H1413+117", "Cloverleaf quad quasar", 40), ("B1608+656", "quad radio source, lens pair", 40), ("SDSS J1004+4112", "cluster quad quasar", 60),
 ("Cosmic Horseshoe", "near-complete ring, single massive galaxy", 40), ("SPT0615-JD", "Cosmic Gems arc, cluster", 80), ("WHL0137-08", "Sunrise arc / Earendel, cluster", 80),
 ("MG 0414+0534", "quad lensed radio source", 40), ("SDP.81", "Einstein ring (submm)", 40), ("Cosmic Eye", "lensed galaxy ring", 40),
 ("HS 0810+2554", "quad quasar", 40), ("WFI 2033-4723", "quad quasar", 40), ("B1422+231", "quad quasar", 40), ("Q0957+561", "twin quasar", 40),
 ("SDSS J0946+1006", "double Einstein ring", 40), ("Abell 1689", "cluster", 150), ("Abell 370", "cluster", 150), ("El Gordo", "cluster", 150), ("MACS J0647.7+7015", "cluster", 100)]
out = []
for name, kind, rad in CANDS:
    rec = dict(name=name, kind=kind)
    try:
        t = Observations.query_object(name, radius=rad * u.arcsec)
        j = t[[str(c).upper() == "JWST" for c in t["obs_collection"]]] if len(t) else t
        rec["jwst_obs"] = len(j)
        rec["instruments"] = dict(collections.Counter(str(x).split("/")[0] for x in j["instrument_name"]))
        rec["programs"] = sorted({str(x) for x in j["proposal_id"]}) if len(j) else []
        rec["hst_obs"] = int(sum(str(c).upper() == "HST" for c in t["obs_collection"])) if len(t) else 0
        rec["jpeg"] = [str(x) for x in j["jpegURL"] if str(x) not in ("--", "")][:3] if len(j) else []
        if len(t):
            rec["ra"], rec["dec"] = float(t["s_ra"][0]), float(t["s_dec"][0])
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:120]}"
    print(json.dumps(rec, ensure_ascii=False), flush=True); out.append(rec); time.sleep(1.5)
json.dump(out, open("jwst_survey.json", "w"), indent=1, ensure_ascii=False)
