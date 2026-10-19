#!/usr/bin/env python3
"""fetch_chandra_q2237.py — every Chandra ACIS-S observation of Q2237+0305 (40 obsids, 2000-2019): the CDA 'primary' products
(evt2, bpix, fov, aspect solution asol1, ephemeris, images). Resumable (curl -C -), one file at a time, 2 s between requests, Mozilla UA, backoff on errors.
Writes the file list with sizes to already_evaluated/huchras_lens_Q2237+0305/chandra_manifest.tsv.   python3 fetch_chandra_q2237.py [--dir DIR]"""
import argparse, os, re, subprocess, sys, time, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
OBSIDS = [431, 1632, 6831, 6832, 6833, 6834, 6835, 6836, 6837, 6838, 6839, 6840, 11534, 11535, 11536, 11537, 11538, 11539, 12831, 12832, 13191, 13195, 13960, 13961,
          14513, 14514, 14515, 14516, 14517, 14518, 16316, 16317, 18804, 19638, 19639, 19640, 19641, 19642, 19643, 22042]
BASE = "https://cxc.cfa.harvard.edu/cdaftp/byobsid"
ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="/media/rendier/0123-4567/BulletCluster/huchras_lens/data/chandra"); a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(HERE, "..", "already_evaluated", "huchras_lens_Q2237+0305", "chandra_manifest.tsv")
def log(*x): print(time.strftime("[%F %T]"), *x, flush=True)
def get(url, tries=5):
    for t in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
        except Exception as e:
            log("   retry", t + 1, url, type(e).__name__, str(e)[:60]); time.sleep(min(900, 30 * 2 ** t))
    return None
rows = []
for o in OBSIDS:
    d = f"{BASE}/{o % 10}/{o}/primary/"
    page = get(d); time.sleep(2)
    if page is None: log("no listing for", o); continue
    for m in re.finditer(r'href="([^"/]+\.fits\.gz)"', page.decode("utf-8", "replace")):
        rows.append((o, m.group(1), "?", d + m.group(1)))   # the listing carries no sizes; actual sizes are in FILES after the run
log("files listed:", len(rows))
os.makedirs(os.path.dirname(MAN), exist_ok=True)
with open(MAN, "w") as f:
    f.write("obsid\tfilename\tsize\turl\n"); [f.write("\t".join(map(str, r)) + "\n") for r in rows]
for i, (o, fn, sz, url) in enumerate(rows, 1):
    dest = os.path.join(a.dir, str(o), fn); os.makedirs(os.path.dirname(dest), exist_ok=True)
    for t in range(6):
        free = os.statvfs(a.dir).f_bavail * os.statvfs(a.dir).f_frsize
        if free < 10e9: log("free space below 10 GB; stopping"); sys.exit(3)
        log(f"[{i}/{len(rows)}] {o} {fn} ({sz})")
        rc = subprocess.call(["curl", "-s", "-S", "-f", "-C", "-", "-A", UA, "--connect-timeout", "30", "--max-time", "1800", "-o", dest, url])
        if rc == 0: break
        log("   curl rc", rc, "backing off"); time.sleep(min(900, 30 * 2 ** t))
    time.sleep(2)
with open(MAN.replace("manifest", "files"), "w") as f:
    f.write("obsid\tfilename\tbytes\n")
    for o, fn, _, _ in rows:
        pth = os.path.join(a.dir, str(o), fn); f.write(f"{o}\t{fn}\t{os.path.getsize(pth) if os.path.exists(pth) else -1}\n")
log("done")
