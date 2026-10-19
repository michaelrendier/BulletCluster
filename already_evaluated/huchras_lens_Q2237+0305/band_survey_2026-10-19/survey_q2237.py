import warnings; warnings.filterwarnings("ignore")
import astropy.units as u
from astropy.coordinates import SkyCoord
UA="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
c=SkyCoord(ra=340.1258,dec=3.3578,unit="deg")   # Q2237+0305 (Huchra's Lens) ~ 22h40m30.3s +03d21m31s
def tryit(name,f):
    try: print(name,"->",f())
    except Exception as e: print(name,"ERR",type(e).__name__,str(e)[:120])
import pyvo
def tap(url,q,name):
    def f():
        s=pyvo.dal.TAPService(url); s._session.headers["User-Agent"]=UA
        r=s.search(q,timeout=60); return len(r), r.to_table()[:5].pformat(max_width=140) if len(r) else ""
    tryit(name,f)
tap("https://almascience.eso.org/tap",
    "SELECT TOP 50 project_code,band_list,t_resolution,s_resolution FROM ivoa.obscore WHERE 1=CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',340.1258,3.3578,0.05))","ALMA")
tap("https://data-query.nrao.edu/tap","SELECT TOP 50 * FROM tap.obscore WHERE 1=CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',340.1258,3.3578,0.05))","NRAO")
tap("https://heasarc.gsfc.nasa.gov/xamin/vo/tap","SELECT TOP 30 name,obsid,exposure FROM chanmaster WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',340.1258,3.3578,0.1))","Chandra")
tap("https://heasarc.gsfc.nasa.gov/xamin/vo/tap","SELECT TOP 30 name,obsid,duration FROM xmmmaster WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',340.1258,3.3578,0.2))","XMM")
from astroquery.ipac.irsa import Irsa
tryit("IRSA spitzer",lambda: len(Irsa.query_region(c,catalog="spitzer_irac_sh" if False else "slphotdr4_wsm" if False else "irsa_obs" if False else "wise_allwise_p3as_psd",radius=0.01*u.deg)))
