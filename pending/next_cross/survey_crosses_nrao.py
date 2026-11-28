import collections, csv, io, json, sys, time, requests
from astropy.coordinates import SkyCoord
UA="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"; S=requests.Session(); S.headers["User-Agent"]=UA
POS={"DES J0408-5354":(62.09132,-53.90026),"H1413+117":(213.94271,11.49539),"PKS 1830-211":(278.41642,-21.06094),"MG 0414+0534":(63.65736,5.57842),"WFI J2033-4723":(308.42475,-47.39519),"SDSS J0924+0219":(141.23255,2.32366),"B1422+231":(216.1588,22.9336),"B0218+357":(35.2728,35.9372)}
for n,(ra,dec) in POS.items():
    q=("SELECT facility_name,instrument_name,pol_states,em_min,t_min,obs_publisher_did,project_code FROM tap_schema.obscore "
       f"WHERE 1=CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',{ra},{dec},0.002))")
    try:
        r=S.post("https://data-query.nrao.edu/tap/sync",data=dict(REQUEST="doQuery",LANG="ADQL",FORMAT="csv",QUERY=q),timeout=900); r.raise_for_status()
        rows=list(csv.DictReader(io.StringIO(r.text)))
        full=[x for x in rows if any(k in x["pol_states"] for k in ("RL","LR","XY","YX"))]
        g=collections.defaultdict(lambda:[0,set(),set()])
        for x in full:
            k=(x["instrument_name"],x["project_code"] or x["obs_publisher_did"][-20:]); g[k][0]+=1
            try: g[k][1].add(round(float(x["em_min"])*100,2))
            except Exception: pass
            try: g[k][2].add(time.strftime("%Y-%m",time.gmtime((float(x["t_min"])-40587)*86400)))
            except Exception: pass
        print(json.dumps({"name":n,"rows":len(rows),"fullpol_rows":len(full),"projects":[{"inst":k[0],"project":k[1],"rows":v[0],"lambda_cm":sorted(v[1])[:3],"dates":sorted(v[2])[:3]} for k,v in sorted(g.items(),key=lambda kv:-kv[1][0])[:6]]}),flush=True)
    except Exception as e: print(json.dumps({"name":n,"error":f"{type(e).__name__}: {str(e)[:90]}"}),flush=True)
