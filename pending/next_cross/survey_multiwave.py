#!/usr/bin/env python3
"""survey_multiwave.py — for lens candidates: JWST instruments (MAST), other MAST collections, radio/mm (NRAO TAP: VLA/VLBA/ALMA), X-ray (HEASARC chanmaster/xmmmaster)
and literature volume (OpenAlex title+abstract mentions; top cited paper).  Public queries, Mozilla UA, no account, no email."""
import json, collections, time, requests, io, csv
from astroquery.mast import Observations
import astropy.units as u
from astropy.coordinates import SkyCoord
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
Observations._session.headers.update({"User-Agent": UA}); S = requests.Session(); S.headers["User-Agent"] = UA
C = [("SMACS J0723.3-7327", None, 150, "SMACS 0723"), ("Abell 2744", None, 150, "Abell 2744"), ("MACS J0416.1-2403", None, 150, "MACS J0416"), ("MACS J1149.5+2223", None, 150, "MACS J1149"),
     ("MACS J0138.0-2155", None, 100, "MACS J0138"), ("PLCK G165.7+67.0", None, 100, "PLCK G165.7"), ("Abell S1063", None, 150, "Abell S1063"), ("MACS J0717.5+3745", None, 150, "MACS J0717"),
     ("RX J1131-1231", "11h31m51.6s -12d31m57s", 40, "RX J1131-1231"), ("SPT-CL J0615-5746", "06h15m55s -57d46m", 80, "SPT-CL J0615-5746"), ("Abell 370", None, 150, "Abell 370")]
def pos(name, s):
    return SkyCoord(s, frame="icrs") if s else SkyCoord.from_name(name)
def tap(url, q, to=120):
    r = S.get(url, params=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=to); r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))
out = []
for name, s, rad, key in C:
    rec = dict(name=name)
    try:
        p = pos(name, s); rec["ra"], rec["dec"] = p.ra.deg, p.dec.deg
        t = Observations.query_region(p, radius=rad * u.arcsec)
        col = collections.Counter(str(c) for c in t["obs_collection"]); rec["mast_collections"] = dict(col)
        j = t[[str(c).upper() == "JWST" for c in t["obs_collection"]]]
        rec["jwst_instruments"] = dict(collections.Counter(str(x).split("/")[0] for x in j["instrument_name"])); rec["jwst_programs"] = len({str(x) for x in j["proposal_id"]})
        rec["jwst_all4"] = all(k in rec["jwst_instruments"] for k in ("NIRCAM", "NIRSPEC", "MIRI", "NIRISS"))
        rec["jpeg_nircam"] = [str(x) for x, i in zip(j["jpegURL"], j["instrument_name"]) if "NIRCAM" in str(i) and str(x) not in ("--", "")][:6]
    except Exception as e: rec["mast_error"] = f"{type(e).__name__}: {str(e)[:100]}"
    try:
        r = tap("https://data-query.nrao.edu/tap/sync", f"SELECT facility_name,project_code,configuration,freq_min,freq_max,access_estsize FROM tap_schema.obscore WHERE 1=CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',{rec['ra']},{rec['dec']},{rad/3600*1.5}))")
        rec["nrao_rows"] = len(r); rec["nrao_facilities"] = dict(collections.Counter(x["facility_name"] for x in r))
        rec["nrao_projects"] = sorted({x["project_code"] for x in r})[:12]
    except Exception as e: rec["nrao_error"] = f"{type(e).__name__}: {str(e)[:100]}"
    for tab, lab in (("chanmaster", "chandra"), ("xmmmaster", "xmm")):
        try:
            r = tap("https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync", f"SELECT TOP 500 obsid FROM {tab} WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{rec['ra']},{rec['dec']},{rad/3600*1.5}))")
            rec[lab + "_obs"] = len(r)
        except Exception as e: rec[lab + "_error"] = f"{type(e).__name__}: {str(e)[:80]}"
    try:
        w = S.get("https://api.openalex.org/works", params={"filter": f"title_and_abstract.search:\"{key}\"", "sort": "cited_by_count:desc", "per-page": 3}, timeout=60).json()
        rec["papers_title_abstract"] = w["meta"]["count"]; rec["top_papers"] = [(x["display_name"][:90], x["cited_by_count"], x["publication_year"]) for x in w["results"]]
    except Exception as e: rec["oa_error"] = f"{type(e).__name__}: {str(e)[:100]}"
    print(json.dumps(rec, ensure_ascii=False), flush=True); out.append(rec); time.sleep(1)
json.dump(out, open("multiwave_survey.json", "w"), indent=1, ensure_ascii=False)
