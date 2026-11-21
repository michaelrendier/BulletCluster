#!/usr/bin/env python3
"""pol_crab.py (2026-11-20): real optical/NIR polarization of the Crab Nebula from HST polarizer images.
Reads only; writes JSON + a quick-look PNG under ./CrabNebula/.  Run: ValaQuenta/.venv/bin/python pol_crab.py

ACS/WFC F606W + POL0V/POL60V/POL120V (prog 9787, 2003-08-08/09), drizzled DRC on one common grid (checked: same shape, CRVAL, CRPIX).
  Ideal-polarizer Stokes (ACS Instrument Handbook sec. 6.1; formulas as in arXiv:0706.1944):
      I = 2/3 (I0 + I60 + I120);  Q = 2/3 (2 I0 - I60 - I120);  U = 2/sqrt(3) (I60 - I120);  chi_instr = 1/2 atan2(U, Q)
  Sky angle, position angle from North through East:  chi_sky = chi_instr - 38.15 deg + PA_V3   (the POL0V zero point relative to V3 used by arXiv:1311.4896; arXiv:0711.1495 uses -38 deg).  ASSUMED; the Data Handbook value was not re-checked here.
  NOT applied: the instrumental polarization (~2 %) and cross-polarization leakage corrections (acstools polarization_tools carries them; not installed).
NICMOS camera 2 POL0L/POL120L/POL240L (prog 7238, 1997-12-15): ideal polarizers at 0, 120, 240 deg:
      I = 2/3 sum I_k;  Q = 2/3 (2 I0 - I120 - I240);  U = 2/sqrt(3) (I240 - I120)
  Its zero point to the sky is not taken from a handbook here: chi_sky = chi_instr + ORIENTAT + delta, with delta fitted so the NICMOS field agrees with ACS where they overlap (synchrotron angle should not depend on wavelength). The fitted delta and the residual scatter are reported: the scatter is the test, delta is a convention.
Noise: Poisson counts only (ignores read noise, drizzle correlation, systematics), so SNR is optimistic.
"""
import os, json, glob, warnings
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp
warnings.filterwarnings("ignore")
DATA = "/media/rendier/Telescope Data/CrabNebula/data"
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "CrabNebula"); os.makedirs(OUT, exist_ok=True)
ACS_OFFSET = -38.15

def cells(I, Q, U, sI, sQ, sU, w, block, snr_i=8.0, snr_p=3.0):
    ny, nx = I.shape; out = []
    for y0 in range(0, ny - block + 1, block):
        for x0 in range(0, nx - block + 1, block):
            sl = (slice(y0, y0 + block), slice(x0, x0 + block))
            ok = np.isfinite(I[sl]) & np.isfinite(Q[sl]) & np.isfinite(U[sl])
            if ok.mean() < 0.9: continue
            i, q, u = I[sl][ok].sum(), Q[sl][ok].sum(), U[sl][ok].sum()
            si, sq, su = np.sqrt((sI[sl][ok] ** 2).sum()), np.sqrt((sQ[sl][ok] ** 2).sum()), np.sqrt((sU[sl][ok] ** 2).sum())
            if i <= 0 or i / si < snr_i: continue
            p = np.hypot(q, u) / i; sp = np.hypot(sq, su) / np.sqrt(2) / i
            if p / sp < snr_p: continue
            pdb = np.sqrt(max(p * p - sp * sp, 0.0))                  # debiased degree
            chi = 0.5 * np.degrees(np.arctan2(u, q))                  # instrument frame, deg
            ra, dec = w.wcs_pix2world(x0 + block / 2 - .5, y0 + block / 2 - .5, 0)
            out.append(dict(ra=float(ra), dec=float(dec), p=float(pdb), chi_instr=float(chi), I=float(i), snr_p=float(p / sp)))
    return out

# ---------------- ACS
f = {a: glob.glob(f"{DATA}/hst_acs_pol_2003/*pol{a}v_j8q410_drc.fits")[0] for a in ("0", "60", "120")}
H = {a: fits.open(f[a]) for a in f}
sci = {a: H[a]["SCI"].data.astype(np.float64) for a in f}; T = H["0"][0].header["EXPTIME"]
w = WCS(H["0"]["SCI"].header); pa_v3 = float(np.mean([H[a][0].header["PA_V3"] for a in H]))
I0, I60, I120 = sci["0"], sci["60"], sci["120"]
I = 2 / 3 * (I0 + I60 + I120); Q = 2 / 3 * (2 * I0 - I60 - I120); U = 2 / np.sqrt(3) * (I60 - I120)
sig = {a: np.sqrt(np.clip(sci[a], 0, None) * T + 25.0) / T for a in f}      # e/s, Poisson + a 5 e floor
sI = 2 / 3 * np.sqrt(sig["0"] ** 2 + sig["60"] ** 2 + sig["120"] ** 2)
sQ = 2 / 3 * np.sqrt(4 * sig["0"] ** 2 + sig["60"] ** 2 + sig["120"] ** 2); sU = 2 / np.sqrt(3) * np.sqrt(sig["60"] ** 2 + sig["120"] ** 2)
BLOCK = 24
acs = cells(I, Q, U, sI, sQ, sU, w, BLOCK)
for c in acs: c["pa"] = float((c.pop("chi_instr") + ACS_OFFSET + pa_v3) % 180)
json.dump(dict(instrument="HST ACS/WFC F606W POL0V/60V/120V", date="2003-08-08/09", block_px=BLOCK, pixel_arcsec=float(np.sqrt(abs(np.linalg.det(w.pixel_scale_matrix))) * 3600),
               pa_v3=pa_v3, zero_point_deg=ACS_OFFSET, convention="pa = position angle of the polarization (E-vector), degrees from North through East; ASSUMED zero point; instrumental polarization not corrected",
               cells=acs), open(f"{OUT}/pol_acs.json", "w"))
p = np.array([c["p"] for c in acs]); print(f"ACS: {len(acs)} cells; p median {np.median(p):.3f}, 90th pct {np.percentile(p, 90):.3f}; PA_V3 {pa_v3:.2f}")

# ---------------- NICMOS (camera 2, one cal frame per polarizer), reprojected onto the ACS WCS cutout
nf = {a: glob.glob(f"{DATA}/hst_nicmos_pol_1997/*cal.fits") for a in ("POL0L", "POL120L", "POL240L")}
frames = {}
for fp in glob.glob(f"{DATA}/hst_nicmos_pol_1997/*cal.fits"):
    h = fits.open(fp); frames[h[0].header["FILTER"]] = h
orient = float(frames["POL0L"][0].header["ORIENTAT"]); tN = frames["POL0L"][0].header["EXPTIME"]
tw = WCS(frames["POL0L"][1].header)
ref = tw; shape = frames["POL0L"][1].data.shape
dq = {k: frames[k]["DQ"].data for k in frames}
fl = {k: np.where(dq[k] == 0, frames[k]["SCI"].data.astype(np.float64), np.nan) for k in frames}
for k in fl: fl[k] = reproject_interp((fl[k], WCS(frames[k]["SCI"].header)), ref, shape_out=shape, return_footprint=False)
J0, J120, J240 = fl["POL0L"], fl["POL120L"], fl["POL240L"]
NI = 2 / 3 * (J0 + J120 + J240); NQ = 2 / 3 * (2 * J0 - J120 - J240); NU = 2 / np.sqrt(3) * (J240 - J120)
ns = np.sqrt(np.clip(NI, 0, None) * tN / 3 + 25) / tN * np.ones(shape)
nic = cells(NI, NQ, NU, ns, ns * 1.2, ns * 1.2, ref, 4, snr_i=10, snr_p=3)       # 4-pixel cells (NIC2 0.076 arcsec/px)
# fit delta: compare with ACS cells at the same sky position
from scipy.spatial import cKDTree
a_xy = np.array([[c["ra"], c["dec"]] for c in acs]); a_pa = np.radians([c["pa"] for c in acs]); a_p = np.array([c["p"] for c in acs])
tree = cKDTree(a_xy * [np.cos(np.radians(22.0)), 1.0])
d, j = [], []
for n in nic:
    dist, k = tree.query([n["ra"] * np.cos(np.radians(22.0)), n["dec"]])
    if dist < BLOCK * 0.03 / 3600 * 0.75: d.append(np.radians(0.5 * np.degrees(0)) ) ; j.append((n, k))
diffs = np.array([(((np.radians(n["chi_instr"] + orient) - a_pa[k]) + np.pi / 2) % np.pi) - np.pi / 2 for n, k in j]) if j else np.array([])
res = {}
if diffs.size >= 5:
    delta = 0.5 * np.arctan2(np.mean(np.sin(2 * diffs)), np.mean(np.cos(2 * diffs)))     # circular mean (axial)
    resid = (((diffs - delta) + np.pi / 2) % np.pi) - np.pi / 2
    res = dict(n_matched=int(diffs.size), delta_deg=float(np.degrees(delta)), residual_rms_deg=float(np.degrees(np.sqrt(np.mean(resid ** 2)))),
               raw_rms_deg_before_offset=float(np.degrees(np.sqrt(np.mean((((diffs - 0) + np.pi / 2) % np.pi - np.pi / 2) ** 2)))))
    for n in nic: n["pa"] = float((n.pop("chi_instr") + orient + np.degrees(delta)) % 180)
else:
    for n in nic: n["pa"] = float((n.pop("chi_instr") + orient) % 180)
    res = dict(n_matched=int(diffs.size))
json.dump(dict(instrument="HST NICMOS camera 2 POL0L/120L/240L", date="1997-12-15", block_px=4, orientat=orient, cross_check_vs_acs=res,
               convention="pa from North through East; zero point FITTED to ACS (a convention, not independent); residual_rms_deg is the test", cells=nic), open(f"{OUT}/pol_nicmos.json", "w"))
print("NICMOS:", len(nic), "cells;", res)
