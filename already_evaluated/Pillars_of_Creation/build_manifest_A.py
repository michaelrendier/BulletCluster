import json, sys, astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
Observations._session.headers["User-Agent"]="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
ROOT="/media/rendier/Telescope Data/BulletCluster/Dust/Pillars_of_Creation"
c=SkyCoord("18h18m51s -13d50m30s"); allo=Observations.query_region(c, radius=90*u.arcsec)
spec=[("HST","13926",{("3","DRC"),("3","DRZ"),("3","POINT-CAT"),("3","SEGMENT-CAT"),("3","WHT"),("3","ASN"),("2","FLC"),("2","FLT")}),
      ("JWST","2739",{("3","I2D"),("3","CAT"),("3","SEGM"),("3","ASN")})]
man=[]; seen=set(); tot=0
for coll,pid,keep in spec:
    o=allo[(allo["obs_collection"]==coll)&(allo["proposal_id"].astype(str)==pid)]; p=Observations.get_product_list(o)
    for r in p:
        sg=str(r["productSubGroupDescription"]) if str(r["productSubGroupDescription"])!='--' else str(r["productType"])
        if (str(r["calib_level"]),sg) not in keep: continue
        f=str(r["productFilename"])
        if f in seen: continue
        seen.add(f); sz=int(r["size"] or 0); tot+=sz
        man.append({"url":"https://mast.stsci.edu/api/v0.1/Download/file?uri="+str(r["dataURI"]),"dest":f"{ROOT}/{coll}_{pid}/{str(r['obs_id'])}/{f}","size":sz})
json.dump(man,open(sys.argv[1],"w"),indent=0); print(len(man),"files",round(tot/1e9,2),"GB")
