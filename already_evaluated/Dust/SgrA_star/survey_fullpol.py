#!/usr/bin/env python3
"""Full-polarization projects (EVLA/VLA RL LR and ALMA XY YX) within 1.2 arcmin of Sgr A*, grouped by project: dates, wavelength, configuration, rows.
Read-only NRAO TAP query, Mozilla UA.  Writes fullpol_projects.json and prints a table."""
import csv, collections, io, json, os, time, requests
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
q = ("SELECT facility_name,instrument_name,project_code,pol_states,em_min,em_max,t_min,t_max,configuration,s_resolution,access_estsize FROM tap_schema.obscore "
     "WHERE 1=CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',266.41684,-29.00781,0.02)) "
     "AND (pol_states LIKE '%RL%' OR pol_states LIKE '%XY%') AND instrument_name <> 'VLBA'")
r = requests.post("https://data-query.nrao.edu/tap/sync", headers={"User-Agent": UA}, timeout=900, data=dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=q))
r.raise_for_status()
rows = list(csv.DictReader(io.StringIO(r.text)))
print(len(rows), "rows")
g = collections.defaultdict(lambda: {"rows": 0, "lam": set(), "t0": 9e9, "t1": 0, "cfg": set(), "res": [], "kb": 0.0, "inst": set()})
for x in rows:
    k = x["project_code"] or "?"
    d = g[k]; d["rows"] += 1; d["inst"].add(x["instrument_name"]); d["cfg"].add(x["configuration"])
    try: d["lam"].add(round(float(x["em_min"]) * 100, 2))
    except (TypeError, ValueError): pass
    try: d["t0"] = min(d["t0"], float(x["t_min"])); d["t1"] = max(d["t1"], float(x["t_max"]))
    except (TypeError, ValueError): pass
    try: d["res"].append(float(x["s_resolution"]))
    except (TypeError, ValueError): pass
    try: d["kb"] += float(x["access_estsize"])
    except (TypeError, ValueError): pass
date = lambda m: time.strftime("%Y-%m-%d", time.gmtime((m - 40587) * 86400)) if 0 < m < 9e8 else "?"
out = []
for k, d in sorted(g.items(), key=lambda kv: kv[1]["t0"]):
    out.append({"project": k, "inst": sorted(d["inst"]), "rows": d["rows"], "first": date(d["t0"]), "last": date(d["t1"]), "lambda_cm": sorted(d["lam"])[:6],
                "config": sorted(c for c in d["cfg"] if c)[:3], "beam_arcsec_min": round(min(d["res"]), 3) if d["res"] else None, "access_estsize_GB_overcount": round(d["kb"] / 1e6, 1)})
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fullpol_projects.json"), "w"), indent=1)
for o in out:
    print(o["project"], o["inst"], o["rows"], "rows", o["first"], "->", o["last"], "lam_cm", o["lambda_cm"], o["config"], "beam", o["beam_arcsec_min"])
