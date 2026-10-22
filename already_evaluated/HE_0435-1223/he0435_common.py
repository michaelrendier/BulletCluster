#!/usr/bin/env python3
"""Shared helpers for the HE 0435-1223 per-telescope download scripts.

Target: HE 0435-1223  RA 69.56208  Dec -12.28722 (ICRS).  Data root = the directory this file lives in; each telescope
writes only to its own sub-directory (JWST/, HST/, VLA/, ALMA/).

Two retrieval modes, both resumable and both sending a Mozilla user agent:
  * whole file   -> telescope_download.py (HTTP Range resume, sha256 in STATE)
  * sky cutout   -> HTTP Range reads of only the pixel rows inside the box (MAST serves byte ranges, tested 2026-10-22)
"""
import os, sys, json, subprocess
import numpy as np

RA, DEC = 69.56208, -12.28722
ROOT = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
MAST = "https://mast.stsci.edu/api/v0.1/Download/file?uri="


def mast_url(uri):
    return MAST + uri


def open_remote(url):
    from astropy.io import fits
    return fits.open(url, use_fsspec=True, lazy_load_hdus=True,
                     fsspec_kwargs={"client_kwargs": {"headers": {"User-Agent": UA}}})


def plan_cutout(url, half_arcsec, exts):
    """Return (pixel box, bytes to fetch) for a square cutout centred on the target. Reads headers only."""
    from astropy.wcs import WCS
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    from astropy.nddata import Cutout2D
    h = open_remote(url)
    sci = h["SCI"]
    w = WCS(sci.header)
    pos = SkyCoord(RA * u.deg, DEC * u.deg)
    scale = np.sqrt(abs(np.linalg.det(w.pixel_scale_matrix))) * 3600.0
    n = int(round(2 * half_arcsec / scale))
    ny, nx = sci.shape
    x, y = w.world_to_pixel(pos)
    x0, y0 = max(0, int(x - n // 2)), max(0, int(y - n // 2))
    x1, y1 = min(nx, x0 + n), min(ny, y0 + n)
    nbytes = sum((y1 - y0) * (x1 - x0) * abs(h[e].header["BITPIX"]) // 8 for e in exts if e in h)
    return (x0, x1, y0, y1), nbytes, scale, (ny, nx)


def write_cutout(url, out, half_arcsec, exts=("SCI", "ERR", "WHT", "CON")):
    """Fetch only the box; write a multi-extension FITS with the WCS shifted. Skips if `out` exists."""
    from astropy.io import fits
    from astropy.wcs import WCS
    if os.path.exists(out):
        print("have", out); return
    (x0, x1, y0, y1), nbytes, scale, shape = plan_cutout(url, half_arcsec, exts)
    h = open_remote(url)
    hdus = [fits.PrimaryHDU(header=h[0].header)]
    for e in exts:
        if e not in h:
            continue
        d = h[e].section[..., y0:y1, x0:x1]
        hd = h[e].header.copy()
        if "CRPIX1" in hd:
            hd["CRPIX1"] -= x0
            hd["CRPIX2"] -= y0
        hd["CUTBOX"] = f"x{x0}:{x1} y{y0}:{y1} of {shape[1]}x{shape[0]}"
        hdus.append(fits.ImageHDU(np.asarray(d), header=hd, name=e))
    tmp = out + ".part"
    fits.HDUList(hdus).writeto(tmp, overwrite=True)
    os.replace(tmp, out)
    print("wrote", out, f"{os.path.getsize(out)/1e6:.1f} MB (box {x1-x0}x{y1-y0} px @ {scale:.4f}\"/px)")


def run_manifest(manifest, state, extra=()):
    """Whole-file downloads through telescope_download.py (resumable, free-space guard, 15-min status line)."""
    json.dump(manifest, open(state.replace("state", "manifest"), "w"), indent=1)
    cmd = [sys.executable, os.path.join(ROOT, "telescope_download.py"), state.replace("state", "manifest"),
           "--state", state, "--min-free-gb", "20", *extra]
    return subprocess.call(cmd)
