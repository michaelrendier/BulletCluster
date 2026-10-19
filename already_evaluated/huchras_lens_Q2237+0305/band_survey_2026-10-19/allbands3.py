import warnings; warnings.filterwarnings("ignore")
import json, astropy.units as u
from astropy.coordinates import SkyCoord
UA="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
c=SkyCoord(ra=340.1258,dec=3.3578,unit="deg"); out={}
def p(*a): print(*a, flush=True)
# 1 HEASARC
import pyvo
s=pyvo.dal.TAPService("https://heasarc.gsfc.nasa.gov/xamin/vo/tap"); s._session.headers["User-Agent"]=UA
tabs="agilecat egret3 fermi3fgl fermi3fhl fermifhl fermilpsc fermilgrb fermilblaz fermigbrst intbsc integralao swbat105m swbat157m swbatagn60 swbatsfxt swiftgrb nustarssc nustarssc2 maxigsc7yr saxwfccat saxwfccat2 sax2to10 saxao roshri roshritotal hriphot ipcphot rosmaster euvecat2 swift2sxps swiftlsxps swiftmastr wfcpoint hesscat suzakuwam xrismmastr ascamaster einstein2e chanmaster xmmmaster xmmssc galextdsc".split()
for n in tabs:
    for rc,dc in (("ra","dec"),):
        try:
            r=s.search(f"SELECT TOP 5 * FROM {n} WHERE 1=CONTAINS(POINT('ICRS',{rc},{dc}),CIRCLE('ICRS',340.1258,3.3578,0.08))",timeout=25)
            out["HEASARC/"+n]=len(r); p("HEASARC",n,len(r))
        except Exception as e:
            out["HEASARC/"+n]="ERR "+str(e)[:50].replace("\n"," "); p("HEASARC",n,"ERR",str(e)[:60].replace("\n"," "))
# 2 NED retry
try:
    from astroquery.ipac.ned import Ned
    Ned.TIMEOUT=240
    t=Ned.get_table("Q2237+0305",table="photometry")
    fc=[k for k in t.colnames if 'Frequency' in k][0]
    import collections
    def band(nu):
        for lo,n in ((1e19,"gamma"),(1e16,"X-ray"),(7.5e14,"UV"),(4e14,"optical"),(3e12,"IR"),(3e11,"submm/mm"),(3e8,"radio cm-m"),(0,"radio<300MHz")):
            if nu>=lo: return n
    cnt=collections.Counter()
    for r in t:
        try: cnt[band(float(r[fc]))]+=1
        except Exception: pass
    out["NED_photometry"]=dict(cnt); out["NED_rows"]=len(t); p("NED",len(t),dict(cnt))
except Exception as e: out["NED"]="ERR "+str(e)[:80]; p("NED ERR",str(e)[:100])
# 3 VizieR all catalogs at the position
try:
    from astroquery.vizier import Vizier
    Vizier.TIMEOUT=240
    v=Vizier(row_limit=3).query_region(c,radius=3*u.arcsec)
    cats=[(k,len(t),(t.meta.get('description') or '')[:70]) for k,t in zip(v.keys(),v)]
    out["VizieR_catalogs"]=cats; p("VizieR tables",len(cats))
    for x in cats[:200]: p("  ",x)
except Exception as e: out["VizieR"]="ERR "+str(e)[:80]; p("VizieR ERR",str(e)[:100])
json.dump(out,open("allbands3.json","w"),indent=1,default=str)
p("DONE")
