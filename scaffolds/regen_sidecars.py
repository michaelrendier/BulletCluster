#!/usr/bin/env python3
"""regen_sidecars.py (2026-11-20): add sky-coordinate sidecars (<png>.wcs.json) to scaffold PNGs.
Composites: re-run make_scaffold.composite() on exactly the filters named in each existing composite's .txt, into a scratch dir, check the regenerated PNG equals the
existing one pixel for pixel (so the sidecar describes the image the gallery shows), then copy only the sidecars.  Raw PNGs: sidecar from the mosaic header (no data read).
One composite at a time with a pause; stops if the kernel reports the Telescope Data device offline.   Usage: BulletCluster/.venv/bin/python regen_sidecars.py SCRATCH TARGET ROOT [--new TAG FILTERSTEMS...]"""
import sys, os, re, glob, json, time, subprocess, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_scaffold as M
scratch, target, root = sys.argv[1:4]; HERE = os.path.dirname(os.path.abspath(__file__)); fc = f"{HERE}/{target}/false_color"
def drive_ok():
    out = subprocess.run("dmesg 2>/dev/null | tail -30", shell=True, capture_output=True, text=True).stdout
    return "device offline" not in out and os.path.isdir(root)
def find(stem):
    m = glob.glob(f"{root}/**/{stem}_i2d.fits", recursive=True) + glob.glob(f"{root}/**/*{stem}_i2d.fits", recursive=True)
    return sorted(set(m), key=len)[0] if m else None
only = [a for a in sys.argv[4:] if not a.startswith("--")]
for txt in sorted(glob.glob(f"{fc}/*_rgb_lupton.txt")):
    tag = os.path.basename(txt)[:-len("_rgb_lupton.txt")]
    if only and tag not in only: continue
    if os.path.exists(f"{fc}/{tag}_rgb_lupton.png.wcs.json"): print(tag, "already has sidecar"); continue
    stems = [s.strip() for g in re.search(r"channels \(blue -> red\): (.*)", open(txt).read()).group(1).split("|") for s in g.split(",")]
    files = [find(s) for s in stems]
    if None in files: print(tag, "MISSING files", [s for s, f in zip(stems, files) if f is None]); continue
    if not drive_ok(): print("drive offline; stopping"); break
    out = f"{scratch}/regen/{target}"; shutil.rmtree(out, ignore_errors=True); t0 = time.time()
    M.composite(files, out, tag)
    ok = True
    for suf in ("_rgb_lupton.png", "_rgb_lupton_nosky.png"):
        a, b = np.array(Image.open(f"{out}/false_color/{tag}{suf}")), np.array(Image.open(f"{fc}/{tag}{suf}"))
        same = a.shape == b.shape and int(np.abs(a.astype(int) - b.astype(int)).max()) == 0
        print(f"  {tag}{suf}: shape {a.shape} vs {b.shape}  identical={same}"); ok &= same
        if same: shutil.copy(f"{out}/false_color/{tag}{suf}.wcs.json", f"{fc}/{tag}{suf}.wcs.json")
    print(tag, "done in", round(time.time() - t0), "s; sidecars installed" if ok else "; NOT installed (images differ)", flush=True); time.sleep(15)
# raw PNG sidecars from headers only
n = 0
for rp in sorted(glob.glob(f"{HERE}/{target}/raw/*_raw.png")):
    if os.path.exists(rp + ".wcs.json"): continue
    base = os.path.basename(rp)[:-len("_raw.png")]; f = find(base)
    if not f: continue
    from astropy.io import fits
    from astropy.wcs import WCS
    with fits.open(f, memmap=True) as h:
        sci = h["SCI"]; ny, nx = sci.shape; w = WCS(sci.header)
    fct = max(1, int(np.ceil(max(ny, nx) / M.RAWMAX))); oy, ox = ny // fct, nx // fct
    w2 = w.deepcopy(); w2.wcs.crpix = (np.array(w.wcs.crpix) - 0.5 - (fct - 1) / 2) / fct + 0.5
    pm = w.pixel_scale_matrix * fct
    im = Image.open(rp)
    if im.size != (ox, oy): print("  raw size mismatch", base, im.size, (ox, oy)); continue
    M.write_wcs(rp, w.wcs.crval, pm, w2.wcs.crpix, oy, ox); n += 1
print(target, "raw sidecars written:", n)
