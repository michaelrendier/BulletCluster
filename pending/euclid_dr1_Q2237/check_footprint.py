import warnings; warnings.filterwarnings("ignore")
import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.esa.euclid import Euclid
c=SkyCoord(ra=340.1258,dec=3.3578,unit="deg")
try:
    r=Euclid.cone_search(c,radius=5*u.arcmin,table_name="catalogue.mer_catalogue",ra_column_name="right_ascension",dec_column_name="declination",columns="*",async_job=False)
    print("mer rows",len(r.get_results()) if hasattr(r,'get_results') else r)
except Exception as e: print("cone ERR",type(e).__name__,str(e)[:200])
try:
    r=Euclid.launch_job("SELECT TOP 5 observation_id,instrument_name,filter_name,ra,dec FROM sedm.observation WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',340.1258,3.3578,0.3))")
    print(r.get_results())
except Exception as e: print("obs ERR",type(e).__name__,str(e)[:200])
