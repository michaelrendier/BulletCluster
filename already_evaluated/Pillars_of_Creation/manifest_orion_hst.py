import json, sys, astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
Observations._session.headers["User-Agent"]="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
ROOT="/media/rendier/Telescope Data/BulletCluster/Dust/Orion_BNKL_OMC1"
o=Observations.query_region(SkyCoord("05h35m14.1s -05d22m22s"), radius=30*u.arcsec); o=o[(o["obs_collection"]=="HST")&(o["proposal_id"].astype(str)=="9752")]
p=Observations.get_product_list(o); man=[]; seen=set(); tot=0
for r in p:
    f=str(r["productFilename"])
    if f in seen or str(r["productType"])=="AUXILIARY" and False: continue
    if str(r["productSubGroupDescription"]) in ("PREVIEW",) : continue
    seen.add(f); sz=int(r["size"] or 0); tot+=sz
    man.append({"url":"https://mast.stsci.edu/api/v0.1/Download/file?uri="+str(r["dataURI"]),"dest":f"{ROOT}/HST_9752_NICMOS_POL/{str(r['obs_id'])}/{f}","size":sz})
json.dump(man,open(sys.argv[1],"w")); print(len(man),"files",round(tot/1e9,2),"GB")
