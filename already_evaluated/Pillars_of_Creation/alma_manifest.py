import sys,re,json,urllib.request,urllib.parse,csv,io
UA="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
proj, out, root = sys.argv[1], sys.argv[2], sys.argv[3]
def get(u, data=None):
    req=urllib.request.Request(u,data=data,headers={"User-Agent":UA}); return urllib.request.urlopen(req,timeout=120).read().decode()
q="SELECT DISTINCT member_ous_uid FROM ivoa.obscore WHERE proposal_id='%s'"%proj
r=get("https://almascience.eso.org/tap/sync", urllib.parse.urlencode({"REQUEST":"doQuery","LANG":"ADQL","FORMAT":"csv","QUERY":q}).encode())
mous=[x["member_ous_uid"] for x in csv.DictReader(io.StringIO(r))]
man=[]; seen=set(); tot=0
for m in mous:
    t=get("https://almascience.org/datalink/sync?ID="+urllib.parse.quote(m,safe=":/"))
    for row in re.findall(r'<TR>(.*?)</TR>',t,re.S):
        c=[x for x in re.findall(r'<TD>(.*?)</TD>',row,re.S)]
        if len(c)<7: continue
        url=c[1].replace('&amp;','&'); 
        try: size=int(c[-3])
        except: continue
        if size<10_000_000 or url in seen: continue          # skip the small html/readme rows; keep the data tarballs
        seen.add(url); fn=url.split('/')[-1].split('?')[0]; man.append({"url":url,"dest":f"{root}/{fn}","size":size}); tot+=size
json.dump(man,open(out,"w"),indent=0); print(proj,len(mous),"MOUS",len(man),"files",round(tot/1e9,2),"GB")
for x in man[:3]: print("  ",x["url"][:120],x["size"])
