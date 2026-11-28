#!/usr/bin/env python3
"""survey_crosses.py -- Einstein crosses (quad lensed quasars) and bright rings: JWST (MAST), HST polarizer filters (MAST), radio/mm full polarization
(NRAO TAP: pol_states with RL/LR/XY/YX), Euclid DR1 and Q1 tile footprints (IRSA CAOM tables). Read-only, public queries, Mozilla UA, no account, no email.
Run in BulletCluster/.venv:   python3 survey_crosses.py > crosses_survey.json"""
import csv, collections, io, json, sys, time, requests, astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
Observations._session.headers["User-Agent"] = UA
S = requests.Session(); S.headers["User-Agent"] = UA
NAMES = ["Q2237+0305", "HE 0435-1223", "SDSS J1004+4112", "RX J1131-1231", "PG 1115+080", "B1422+231", "H1413+117", "MG 0414+0534", "B1608+656",
         "WFI J2033-4723", "HE 0230-2130", "SDSS J0924+0219", "RX J0911+0551", "B0712+472", "HS 0810+2554", "DES J0408-5354", "PS J0630-1201",
         "PKS 1830-211", "B0218+357", "CLASS B1555+375", "CLASS B1359+154", "SDSS J1330+1810", "SDSS J1138+0314", "HE 1104-1805", "Cosmic Horseshoe"]
def tap(url, q, to=180):
    r = S.post(url, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q), timeout=to); r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))
out = []
for name in NAMES:
    rec = {"name": name}
    try:
        p = SkyCoord.from_name(name); rec["ra"], rec["dec"] = round(p.ra.deg, 5), round(p.dec.deg, 5)
    except Exception as e:
        rec["unresolved"] = str(e)[:80]; out.append(rec); continue
    try:
        t = Observations.query_region(p, radius=60 * u.arcsec)
        j = t[[str(c).upper() == "JWST" for c in t["obs_collection"]]]
        rec["jwst_obs"] = len(j); rec["jwst_programs"] = sorted({str(x) for x in j["proposal_id"]})
        rec["jwst_instruments"] = dict(collections.Counter(str(x).split("/")[0] for x in j["instrument_name"]))
        h = t[[str(c).upper() == "HST" for c in t["obs_collection"]]]
        rec["hst_obs"] = len(h)
        rec["hst_polarizers"] = {f"{str(i).split(chr(47))[0]}:{f}": n for (i, f), n in collections.Counter((i, str(f)) for i, f in zip(h["instrument_name"], h["filters"]) if "POL" in str(f).upper()).items()}
    except Exception as e:
        rec["mast_error"] = f"{type(e).__name__}: {str(e)[:100]}"
    try:
        r = tap("https://data-query.nrao.edu/tap/sync",
                "SELECT facility_name,instrument_name,pol_states,em_min,t_min,obs_publisher_did FROM tap_schema.obscore "
                f"WHERE 1=CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',{p.ra.deg},{p.dec.deg},0.002))")
        rec["nrao_rows"] = len(r)
        full = [x for x in r if any(k in x["pol_states"] for k in ("RL", "LR", "XY", "YX"))]
        rec["nrao_fullpol_rows"] = len(full)
        g = collections.defaultdict(lambda: [0, set(), set()])
        for x in full:
            pid = "ALMA" if x["instrument_name"] == "ALMA" else x["obs_publisher_did"].split("/")[-1][:14]
            k = (x["instrument_name"], pid); g[k][0] += 1
            try: g[k][1].add(round(float(x["em_min"]) * 100, 1))
            except (TypeError, ValueError): pass
            try: g[k][2].add(time.strftime("%Y-%m", time.gmtime((float(x["t_min"]) - 40587) * 86400)))
            except (TypeError, ValueError): pass
        rec["nrao_fullpol_projects"] = [{"inst": k[0], "project": k[1], "rows": v[0], "lambda_cm": sorted(v[1])[:4], "dates": sorted(v[2])[:3]} for k, v in sorted(g.items(), key=lambda kv: -kv[1][0])[:8]]
    except Exception as e:
        rec["nrao_error"] = f"{type(e).__name__}: {str(e)[:100]}"
    for tab in ("euclid.plane_euclid_dr1", "euclid.plane_euclid_q1"):
        try:
            r = tap("https://irsa.ipac.caltech.edu/TAP/sync",
                    f"SELECT energy_bandpassname,calibrationlevel,provenance_project FROM {tab} WHERE CONTAINS(POINT('ICRS',{p.ra.deg},{p.dec.deg}),poly)=1")
            rec[tab.split(".")[1]] = {"tiles": len(r), "bands": sorted({x["energy_bandpassname"] for x in r}), "survey": sorted({x["provenance_project"] for x in r})}
        except Exception as e:
            rec[tab.split(".")[1] + "_error"] = f"{type(e).__name__}: {str(e)[:100]}"
    out.append(rec); print(json.dumps(rec), file=sys.stderr); sys.stderr.flush()
json.dump(out, sys.stdout, indent=1)
