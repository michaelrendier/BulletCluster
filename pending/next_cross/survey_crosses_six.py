import collections, csv, io, json, requests, astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
UA="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"; Observations._session.headers["User-Agent"]=UA
S=requests.Session(); S.headers["User-Agent"]=UA
POS={"RX J1131-1231":"11h31m51.6s -12d31m57s","B1422+231":"14h24m38.1s +22d56m01s","B1608+656":"16h09m13.96s +65d32m29s","RX J0911+0551":"09h11m27.5s +05d50m52s","B0712+472":"07h16m03.58s +47d08m50s","B0218+357":"02h21m05.48s +35d56m13.8s"}
for n,s in POS.items():
    p=SkyCoord(s); rec={"name":n,"ra":round(p.ra.deg,5),"dec":round(p.dec.deg,5)}
    t=Observations.query_region(p,radius=60*u.arcsec); j=t[[str(c).upper()=="JWST" for c in t["obs_collection"]]]; h=t[[str(c).upper()=="HST" for c in t["obs_collection"]]]
    rec["jwst"]=len(j); rec["jwst_programs"]=sorted({str(x) for x in j["proposal_id"]}); rec["hst"]=len(h); rec["hst_pol"]=sum(1 for f in h["filters"] if "POL" in str(f).upper())
    r=S.post("https://irsa.ipac.caltech.edu/TAP/sync",data=dict(REQUEST="doQuery",LANG="ADQL",FORMAT="csv",QUERY=f"SELECT energy_bandpassname FROM euclid.plane_euclid_dr1 WHERE CONTAINS(POINT('ICRS',{p.ra.deg},{p.dec.deg}),poly)=1"),timeout=120)
    rec["euclid_dr1_tiles"]=len(list(csv.DictReader(io.StringIO(r.text))))
    print(json.dumps(rec),flush=True)
