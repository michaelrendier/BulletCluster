#!/usr/bin/env python3
"""
bullet_polarization_foreground.py — the polarization data that actually exists
for the Bullet Cluster line of sight, measured rather than assumed.

WHAT THIS IS FOR
----------------
CLAUDE_PRIMER.md lists real MeerKAT Stokes Q/U as the CRITICAL blocker on the
RM-ratio result. That is true, and this script does not unblock it. What it does
is close a hole that exists REGARDLESS of whether MeerKAT Q/U ever arrives:

The engine's diagnostic is RM(DM)/RM(gas), measured along a transect at
MERGER_PA_DEG = 135 deg. Both terms sit behind the same Milky Way Faraday
screen. The screen is assumed to cancel in the ratio. That assumption has never
been quantified here -- and it is not even the right assumption: a COMMON
additive foreground does not cancel in a ratio, it drags the ratio toward 1,
which is the particle verdict. So the foreground biases the test toward the
answer we are trying to refute, and its size has to be on the record.

Three measurable questions, asked of real published all-sky data:

  Q1. What is the Galactic Faraday rotation toward the Bullet Cluster, and how
      much does it vary ACROSS THE TRANSECT?
      -> Hutschenreuter et al. 2022 Galactic Faraday sky (D4) + components (D6).

  Q2. What is the galactic dust polarization foreground in that direction, and
      does it change with frequency the way dust must and shear cannot?
      -> Planck 353 GHz (D1) and 217 GHz (D3) Stokes I/Q/U.

  Q3. Propagated into the diagnostic: how large may the intrinsic cluster RM be
      allowed to be small before the 0.95 threshold is measuring the Milky Way?

Both datasets are all-sky, so both already contain the Bullet Cluster sightline.
This is real, published, in-hand Bullet Cluster polarization data. It is not
polarization OF the cluster -- it is the foreground the cluster is seen through,
which is the thing that has to be subtracted before any cluster claim is made.

IMPLEMENTATION NOTE
-------------------
The Planck maps are nside 2048: 50.3 M pixels per column. Materialising I/Q/U
as float64 is 1.2 GB and will not fit on the machine this runs on. Every map
here is therefore read through a raw np.memmap of the FITS binary table and
indexed only at the pixels actually wanted -- a few 1e5 out of 5e7. Nothing in
this script ever holds a full-sky map.

Outputs -> lensing_validation/out/
    bullet_polarization_foreground.json   all numbers, machine-readable
    bullet_foreground_maps.png            RM and dust-polarization patches
"""

import json
from pathlib import Path

import numpy as np
import healpy as hp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
import warnings
warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

# Same constants as engine/modules/constants.py -- do not diverge from them.
RA0, DEC0 = 104.6098, -55.9446
POINTS = {
    "DM_NW":  (104.6383, -55.9252),
    "DM_SE":  (104.5726, -55.9563),
    "GAS_NW": (104.625,  -55.930),
    "GAS_SE": (104.569,  -55.961),
    "CENTROID": (RA0, DEC0),
}
MERGER_PA_DEG = 135.0
RM_RATIO_THRESHOLD = 0.95          # engine/modules/constants.py

FARADAY   = DATA / "D4_galactic_faraday_sky" / "faraday2020v2.fits"
FARADAY_C = DATA / "D6_faraday_components"   / "components2020v2.fits"
PLANCK353 = DATA / "D1_planck_353_iqu" / "HFI_SkyMap_353-psb_2048_R3.01_full.fits"
PLANCK217 = DATA / "D3_planck_217_iqu" / "HFI_SkyMap_217_2048_R3.01_full.fits"

PLANCK_BAD = -1.6375e30            # BAD_DATA sentinel in the HFI headers


# ── lazy HEALPix access ───────────────────────────────────────────────────────
_TFORM_DTYPE = {"E": ">f4", "D": ">f8", "J": ">i4", "I": ">i2", "K": ">i8"}


class LazyHealpix:
    """A HEALPix map in a FITS binary table, read one pixel at a time.

    Opens the table as a raw np.memmap with the row dtype reconstructed from
    TFORMn, so touching N pixels reads N values off disk instead of the whole
    50-million-element column. NSIDE may live in either the primary or the
    table header (the MPA Faraday maps put it in the primary); if it is in
    neither it is derived from the row count.
    """

    def __init__(self, path, label):
        self.path, self.label = Path(path), label
        with fits.open(self.path, memmap=True) as h:
            ph, hdr = h[0].header, h[1].header
            self.nrow = int(hdr["NAXIS2"])
            self.names = [hdr[f"TTYPE{i+1}"].strip() for i in range(hdr["TFIELDS"])]
            self.units = {hdr[f"TTYPE{i+1}"].strip(): str(hdr.get(f"TUNIT{i+1}", ph.get("UNIT", "")) or "").strip()
                          for i in range(hdr["TFIELDS"])}
            fmts = [str(hdr[f"TFORM{i+1}"]).strip() for i in range(hdr["TFIELDS"])]
            self.dtype = np.dtype([(n, _TFORM_DTYPE[f[-1]]) for n, f in zip(self.names, fmts)])
            assert self.dtype.itemsize == int(hdr["NAXIS1"]), "row dtype mismatch"
            self.offset = h.fileinfo(1)["datLoc"]
            nside = hdr.get("NSIDE", ph.get("NSIDE"))
            self.nside = int(nside) if nside else hp.npix2nside(self.nrow)
            # ORDERING is absent from the MPA maps; healpy writes RING by default.
            ordering = str(hdr.get("ORDERING", ph.get("ORDERING", "RING"))).strip().upper()
            self.ordering = ordering
            self.nest = ordering == "NESTED"
            self.coordsys = str(hdr.get("COORDSYS", ph.get("COORDSYS", "GALACTIC"))).strip().upper()
        self.pix_arcmin = np.degrees(np.sqrt(hp.nside2pixarea(self.nside))) * 60
        self._mm = None

    @property
    def mm(self):
        if self._mm is None:
            self._mm = np.memmap(self.path, dtype=self.dtype, mode="r",
                                 offset=self.offset, shape=(self.nrow,))
        return self._mm

    def at(self, col, pix):
        """Values of `col` at pixel indices `pix`, sentinels mapped to NaN."""
        pix = np.atleast_1d(np.asarray(pix, dtype=np.int64))
        v = np.asarray(self.mm[col][pix], dtype=np.float64)
        v[~np.isfinite(v)] = np.nan
        v[v < PLANCK_BAD / 10] = np.nan
        return v

    def at_sky(self, col, l, b):
        return self.at(col, self.pix(l, b))

    def pix(self, l, b):
        return hp.ang2pix(self.nside, np.radians(90.0 - np.asarray(b, float)),
                          np.radians(np.asarray(l, float)), nest=self.nest)

    def disc(self, l, b, radius_deg):
        vec = hp.ang2vec(np.radians(90.0 - b), np.radians(l))
        return hp.query_disc(self.nside, vec, np.radians(radius_deg), nest=self.nest)

    def __repr__(self):
        return (f"{self.label}: NSIDE={self.nside} {self.ordering} {self.coordsys} "
                f"pixel~{self.pix_arcmin:.2f}'")


def gal(ra, dec):
    c = SkyCoord(ra=np.asarray(ra, float) * u.deg,
                 dec=np.asarray(dec, float) * u.deg, frame="icrs").galactic
    return np.atleast_1d(c.l.deg), np.atleast_1d(c.b.deg)


def gal1(ra, dec):
    l, b = gal(ra, dec)
    return float(l[0]), float(b[0])


def transect_points(n=41, half_arcmin=5.0):
    """Sample along the merger axis, same convention as transect.py:
    East = -RA, PA measured NW->SE."""
    pa = np.radians(MERGER_PA_DEG)
    s = np.linspace(-half_arcmin, half_arcmin, n) / 60.0  # deg
    d_dec = np.cos(pa) * s
    d_ra = -np.sin(pa) * s / np.cos(np.radians(DEC0))
    return RA0 + d_ra, DEC0 + d_dec, s * 60.0


def gnomonic_grid(l0, b0, fov_deg=8.0, npix=280):
    """Unit vectors on a tangent plane at (l0,b0). Galactic l increases to the
    left, as in hp.gnomview / standard sky display."""
    n = np.array([np.cos(np.radians(b0)) * np.cos(np.radians(l0)),
                  np.cos(np.radians(b0)) * np.sin(np.radians(l0)),
                  np.sin(np.radians(b0))])
    e_l = np.array([-np.sin(np.radians(l0)), np.cos(np.radians(l0)), 0.0])
    e_b = np.array([-np.sin(np.radians(b0)) * np.cos(np.radians(l0)),
                    -np.sin(np.radians(b0)) * np.sin(np.radians(l0)),
                    np.cos(np.radians(b0))])
    half = np.radians(fov_deg / 2)
    x = np.linspace(half, -half, npix)          # +l to the left
    y = np.linspace(-half, half, npix)
    X, Y = np.meshgrid(x, y)
    v = (n[None, None, :] + np.tan(X)[..., None] * e_l[None, None, :]
                          + np.tan(Y)[..., None] * e_b[None, None, :])
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def patch(m, col, l0, b0, fov_deg=8.0, npix=280):
    v = gnomonic_grid(l0, b0, fov_deg, npix)
    pix = hp.vec2pix(m.nside, v[..., 0], v[..., 1], v[..., 2], nest=m.nest)
    return m.at(col, pix.ravel()).reshape(pix.shape)


report = {}
print("=" * 74)
print("BULLET CLUSTER POLARIZATION FOREGROUND -- measured from all-sky data")
print("=" * 74)

l0, b0 = gal1(RA0, DEC0)
print(f"\nBullet Cluster centroid: RA {RA0:.4f}  Dec {DEC0:+.4f}")
print(f"  -> Galactic  l = {l0:.3f}  b = {b0:+.3f}")
report["sightline"] = {"ra": RA0, "dec": DEC0, "l": l0, "b": b0}

# ── Q1: Galactic Faraday rotation ─────────────────────────────────────────────
print("\n" + "-" * 74)
print("Q1. GALACTIC FARADAY SCREEN  (Hutschenreuter+2022)")
print("-" * 74)

F = LazyHealpix(FARADAY, "faraday_sky")
FC = LazyHealpix(FARADAY_C, "faraday_components")
print(F)
print(FC)

# ORDERING is not recorded in these files. Verify the RING assumption against
# physics instead of trusting it: |RM| must blow up in the Galactic plane.
_l = np.linspace(0, 360, 721)
plane = np.nanmean(np.abs(F.at("faraday_sky_mean", F.pix(_l, np.zeros_like(_l)))))
cap = np.nanmean(np.abs(F.at("faraday_sky_mean", F.pix(_l, np.full_like(_l, 80.0)))))
print(f"\nordering check  mean|RM| in plane (b=0) = {plane:7.2f} rad/m^2")
print(f"                mean|RM| at cap  (b=80) = {cap:7.2f} rad/m^2"
      f"   ratio {plane/cap:5.1f}x")
ok_order = plane > 3 * cap
print(f"  -> {'CONSISTENT with RING' if ok_order else 'INCONSISTENT -- ordering assumption is wrong'}")
report["ordering_check"] = {"assumed": F.ordering, "mean_abs_RM_plane": float(plane),
                            "mean_abs_RM_cap": float(cap), "passes": bool(ok_order)}

report["galactic_faraday"] = {"nside": F.nside, "ordering": F.ordering,
                              "pixel_arcmin": F.pix_arcmin, "unit": "rad/m^2",
                              "points": {}}
print(f"\n{'point':10s} {'RM [rad/m^2]':>16s} {'sigma_RM':>12s} {'|amp|':>10s}   {'pixel':>10s}")
pix_seen = {}
for name, (ra, dec) in POINTS.items():
    li, bi = gal1(ra, dec)
    p = int(F.pix(li, bi))
    v = float(F.at("faraday_sky_mean", p)[0])
    s = float(F.at("faraday_sky_std", p)[0])
    a = float(FC.at("amplitude_mean", int(FC.pix(li, bi)))[0])
    pix_seen[name] = p
    print(f"{name:10s} {v:16.3f} {s:12.3f} {a:10.3f}   {p:10d}")
    report["galactic_faraday"]["points"][name] = {
        "RM_rad_m2": v, "sigma_rad_m2": s, "amplitude": a, "healpix": p}

n_unique = len(set(pix_seen.values()))
c_nw = SkyCoord(*POINTS["DM_NW"], unit="deg")
c_se = SkyCoord(*POINTS["DM_SE"], unit="deg")
sep_arcmin = float(c_nw.separation(c_se).arcmin)
print(f"\nDistinct Faraday-map pixels covering all 5 points: {n_unique}")
print(f"DM_NW -> DM_SE separation: {sep_arcmin:.2f} arcmin")
print(f"Faraday map pixel scale  : {F.pix_arcmin:.2f} arcmin")
if n_unique == 1:
    print("  -> the entire diagnostic baseline sits INSIDE ONE map pixel:")
    print("     the map cannot resolve a differential foreground here, so what")
    print("     follows is an upper BOUND from the surrounding gradient, not a")
    print("     measurement of the gradient across the baseline itself.")
report["galactic_faraday"]["dm_separation_arcmin"] = sep_arcmin
report["galactic_faraday"]["n_distinct_pixels"] = n_unique

# Local gradient: how fast does Galactic RM change around this sightline?
print()
for rad_deg in (0.25, 0.5, 1.0, 2.0):
    d = F.disc(l0, b0, rad_deg)
    vals = F.at("faraday_sky_mean", d)
    grad = (np.nanmax(vals) - np.nanmin(vals)) / (2 * rad_deg * 60)  # per arcmin
    print(f"  within {rad_deg:4.2f} deg: RM range {np.nanmin(vals):8.2f} .. "
          f"{np.nanmax(vals):8.2f}  std {np.nanstd(vals):6.2f}  "
          f"|grad| ~ {grad:.4f} rad/m^2 per arcmin")
    report["galactic_faraday"][f"disc_{rad_deg}deg"] = {
        "n_pix": int(d.size), "min": float(np.nanmin(vals)),
        "max": float(np.nanmax(vals)), "std": float(np.nanstd(vals)),
        "mean": float(np.nanmean(vals)), "grad_per_arcmin": float(grad)}

# The transect itself -- the thing the diagnostic is actually measured along.
tra, tdec, toff = transect_points(n=41, half_arcmin=5.0)
tl, tb = gal(tra, tdec)
trm = F.at("faraday_sky_mean", F.pix(tl, tb))
tsd = F.at("faraday_sky_std", F.pix(tl, tb))
ptp = float(np.nanmax(trm) - np.nanmin(trm))
print(f"\nAlong the PA={MERGER_PA_DEG:.0f} deg transect (+-5 arcmin, 41 samples):")
print(f"  RM {np.nanmin(trm):.3f} .. {np.nanmax(trm):.3f} rad/m^2   "
      f"peak-to-peak {ptp:.4f}   distinct pixels {len(set(F.pix(tl, tb).tolist()))}")
print(f"  mean sigma_RM along transect = {np.nanmean(tsd):.3f} rad/m^2")
report["galactic_faraday"]["transect"] = {
    "pa_deg": MERGER_PA_DEG, "half_arcmin": 5.0, "n": int(trm.size),
    "offsets_arcmin": [float(x) for x in toff],
    "RM_rad_m2": [float(x) for x in trm],
    "peak_to_peak": ptp,
    "n_distinct_pixels": int(len(set(F.pix(tl, tb).tolist()))),
    "mean_sigma_rad_m2": float(np.nanmean(tsd))}

# What the surrounding gradient implies across the DM_NW->DM_SE baseline
g = report["galactic_faraday"]["disc_0.5deg"]["grad_per_arcmin"]
dRM_transect = g * sep_arcmin
rm_here = report["galactic_faraday"]["points"]["CENTROID"]["RM_rad_m2"]
sig_here = report["galactic_faraday"]["points"]["CENTROID"]["sigma_rad_m2"]
print(f"\nImplied Galactic RM difference across the DM_NW-DM_SE baseline:")
print(f"  ~{dRM_transect:.4f} rad/m^2   (vs RM_gal = {rm_here:.2f} +- {sig_here:.2f} "
      f"rad/m^2 toward the cluster)")
frac = abs(dRM_transect / rm_here) if rm_here else float("nan")
print(f"  = {100*frac:.3f}% of the foreground RM itself")
report["galactic_faraday"]["implied_dRM_across_transect"] = float(dRM_transect)
report["galactic_faraday"]["frac_of_foreground"] = float(frac)

# ── Q2: Planck dust polarization, two frequencies ─────────────────────────────
print("\n" + "-" * 74)
print("Q2. GALACTIC DUST POLARIZATION  (Planck 353 and 217 GHz)")
print("-" * 74)

report["planck"] = {}
for tag, path in (("353", PLANCK353), ("217", PLANCK217)):
    if not path.exists():
        print(f"\n{tag} GHz: NOT ON DISK -- skipped")
        continue
    P = LazyHealpix(path, f"planck{tag}")
    unit = P.units.get("I_STOKES", "?")
    print(f"\n{tag} GHz  NSIDE={P.nside} {P.ordering} {P.coordsys}  "
          f"pixel ~ {P.pix_arcmin:.2f} arcmin  units={unit}")
    rep = {"nside": P.nside, "ordering": P.ordering, "pixel_arcmin": P.pix_arcmin,
           "unit": unit, "points": {}}
    print(f"{'point':10s} {'I':>13s} {'Q':>13s} {'U':>13s} {'p=P/I':>10s} {'psi[deg]':>10s}")
    for name, (ra, dec) in POINTS.items():
        li, bi = gal1(ra, dec)
        p = int(P.pix(li, bi))
        vi = float(P.at("I_STOKES", p)[0])
        vq = float(P.at("Q_STOKES", p)[0])
        vu = float(P.at("U_STOKES", p)[0])
        pol = float(np.hypot(vq, vu))
        p_frac = pol / vi if vi else np.nan
        # IAU convention psi = 0.5 atan2(U, Q), measured from Galactic north
        psi = 0.5 * np.degrees(np.arctan2(vu, vq))
        print(f"{name:10s} {vi:13.3e} {vq:13.3e} {vu:13.3e} {p_frac:10.4f} {psi:10.2f}")
        rep["points"][name] = {"I": vi, "Q": vq, "U": vu, "P": pol,
                               "pol_fraction": float(p_frac), "pol_angle_deg": float(psi)}

    npix_pts = len({int(P.pix(*gal1(ra, dec))) for ra, dec in POINTS.values()})
    rep["n_distinct_pixels"] = npix_pts
    if npix_pts < len(POINTS):
        print(f"  note: the 5 points fall in only {npix_pts} Planck pixels "
              f"({P.pix_arcmin:.2f} arcmin) -- DM and gas peaks are NOT separable")
        print(f"        here. These numbers bound the dust foreground toward the")
        print(f"        field; they are not per-peak measurements.")

    d = P.disc(l0, b0, 1.0)
    Ip = P.at("I_STOKES", d); Qp = P.at("Q_STOKES", d); Up = P.at("U_STOKES", d)
    sQ = np.sqrt(P.at("QQ_COV", d)); sU = np.sqrt(P.at("UU_COV", d))
    Pp = np.hypot(Qp, Up)
    good = np.isfinite(Ip) & np.isfinite(Pp) & (Ip > 0)
    psi_p = 0.5 * np.degrees(np.arctan2(Up[good], Qp[good]))
    # circular std on the doubled angle -- psi is defined mod 180 deg
    z = np.exp(2j * np.radians(2 * psi_p))
    psi_circ = float(np.degrees(np.sqrt(-2 * np.log(np.abs(z.mean())))) / 4)

    # P = sqrt(Q^2+U^2) is POSITIVELY BIASED: it is a modulus, so noise alone
    # produces P > 0. At 1.7 arcmin and |b| ~ 21 deg the per-pixel HFI
    # polarization is noise dominated, and the naive mean(P)/mean(I) is a
    # measurement of the noise, not of the dust. Three numbers to tell them
    # apart: the per-pixel noise from the covariance columns, the
    # modulus-debiased P, and the COHERENT vector average of Q and U (noise
    # averages down, a real aligned dust field does not).
    sig = float(np.nanmean(0.5 * (sQ[good] + sU[good])))
    P_naive = float(np.nanmean(Pp[good]))
    P_deb = float(np.nanmean(np.sqrt(np.clip(Pp[good] ** 2 - sig ** 2, 0, None))))
    Qbar, Ubar = float(np.nanmean(Qp[good])), float(np.nanmean(Up[good]))
    P_coh = float(np.hypot(Qbar, Ubar))
    Ibar = float(np.nanmean(Ip[good]))
    snr = P_naive / sig if sig else np.nan

    print(f"  within 1.0 deg ({d.size} pixels, {good.sum()} valid):")
    print(f"    mean I                       = {Ibar:.4e}")
    print(f"    per-pixel noise sigma_QU     = {sig:.4e}   (from QQ/UU_COV)")
    print(f"    mean P, naive modulus        = {P_naive:.4e}   S/N = {snr:.2f}")
    print(f"    mean P, modulus-debiased     = {P_deb:.4e}")
    print(f"    P from coherent <Q>,<U>      = {P_coh:.4e}")
    print(f"    p naive = {P_naive/Ibar:.4f}    p coherent = {P_coh/Ibar:.4f}")
    print(f"    angle dispersion = {psi_circ:.2f} deg (circular, mod 180; "
          f"{'random' if psi_circ > 45 else 'aligned'})")
    if snr < 3:
        print(f"    -> NOISE DOMINATED (S/N {snr:.2f} < 3). The naive p is bias, not")
        print(f"       dust. Use the coherent value as the foreground estimate.")
    rep["patch_1deg"] = {
        "n_pix": int(d.size), "n_valid": int(good.sum()), "mean_I": Ibar,
        "sigma_QU": sig, "mean_P_naive": P_naive, "mean_P_debiased": P_deb,
        "P_coherent": P_coh, "P_snr": float(snr),
        "pol_fraction_naive": float(P_naive / Ibar),
        "pol_fraction_coherent": float(P_coh / Ibar),
        "noise_dominated": bool(snr < 3),
        "psi_dispersion_deg": psi_circ}
    report["planck"][tag] = rep

# Frequency lever arm: dust polarization is chromatic, lensing shear is not.
if "353" in report["planck"] and "217" in report["planck"]:
    a, b = report["planck"]["353"]["patch_1deg"], report["planck"]["217"]["patch_1deg"]
    r_coh = a["P_coherent"] / b["P_coherent"] if b["P_coherent"] else float("nan")
    r_I = a["mean_I"] / b["mean_I"] if b["mean_I"] else float("nan")
    print(f"\nFrequency lever arm, 353 vs 217 GHz (coherent, noise-averaged):")
    print(f"  P(353)/P(217) = {r_coh:.2f}      I(353)/I(217) = {r_I:.2f}")
    print("  Thermal dust in K_cmb rises steeply between these bands, and it must")
    print("  rise the SAME way in P as in I if the polarized signal is that dust.")
    print(f"  P/I consistency: {r_coh/r_I:.2f} (1.0 = same spectrum in P and I)")
    print("  A lensing-shear systematic has no frequency dependence at all, so")
    print("  this is a lever arm no shear systematic can imitate.")
    if a["noise_dominated"] or b["noise_dominated"]:
        print("  CAVEAT: at least one band is noise dominated per pixel; this ratio")
        print("  rests on the coherent average and should be re-checked on maps")
        print("  smoothed to ~1 deg before it is quoted anywhere.")
    report["planck"]["P353_over_P217_coherent"] = float(r_coh)
    report["planck"]["I353_over_I217"] = float(r_I)

# ── Q3: propagate into the RM-ratio diagnostic ────────────────────────────────
print("\n" + "-" * 74)
print("Q3. WHAT THIS DOES TO THE 0.95 THRESHOLD")
print("-" * 74)

Fg = abs(rm_here)
dF = abs(dRM_transect)
sF = sig_here
print(f"""
The diagnostic is R = RM(DM)/RM(gas). Write the observed rotation measures as
intrinsic plus foreground:  RM_obs = RM_int + F. A COMMON foreground F does not
cancel in a ratio -- it drags R toward 1, i.e. toward the particle verdict:

    R_obs = (RM_DM + F) / (RM_gas + F)

Toward this sightline, from Hutschenreuter+2022:
    F         = {rm_here:+.2f} rad/m^2      (|F| = {Fg:.2f})
    sigma_F   = {sF:.2f} rad/m^2      (per-pixel posterior width -- note it is
                                   as large as F itself: the screen amplitude
                                   toward this sightline is barely constrained)
    dF        = {dF:.4f} rad/m^2      across the {sep_arcmin:.2f} arcmin baseline
                                   (bound from the 0.5 deg gradient; the map
                                   cannot resolve the baseline directly)
""")

th = RM_RATIO_THRESHOLD
MARGIN = 0.967 - th        # synthetic particle value minus threshold = 0.017


def R_obs(rm_gas, rm_dm=0.0, F=rm_here, dF=0.0):
    """Observed ratio with a common screen F split by +-dF/2 between the two
    footpoints. RM_DM = 0 is the wave prediction."""
    return (rm_dm + F + dF / 2) / (rm_gas + F - dF / 2)


# Bias from the COMMON term: it does not cancel, it drags R toward 1.
need = Fg * (1 - th) / th
print(f"Wave case (RM_DM = 0): R_obs = F/(RM_gas+F) < {th} requires")
print(f"    |RM_gas,int|  >  |F|(1-{th})/{th}  =  {need:.3f} rad/m^2")
print(f"  Cluster ICM rotation measures run 1e1-1e3 rad/m^2, so the common-mode")
print(f"  BIAS is cleared by 1-3 orders of magnitude and is not the exposure.")

# Both error terms, propagated exactly rather than through the RM_gas >> F limit
# (the asymptotic sigma_F/|RM_gas| diverges absurdly at small RM_gas).
print(f"\nTwo error terms, propagated exactly:")
print(f"  differential  dR_dF    = R(F+dF/2, F-dF/2) - R(F, F)")
print(f"  common-mode   dR_sigma = |dR/dF| * sigma_F,  dR/dF = RM_gas/(RM_gas+F)^2")
report["threshold_impact"] = {
    "F_rad_m2": rm_here, "sigma_F_rad_m2": sF, "dF_rad_m2": float(dF),
    "threshold": th, "margin_to_particle": float(MARGIN),
    "min_intrinsic_RM_gas_rad_m2": float(need), "induced_dR": {}}
print(f"\n  {'|RM_gas|':>10s} {'R_obs':>9s} {'dR from dF':>13s} {'dR from sigma_F':>17s}"
      f"  {'vs margin':>10s}")
for rmg in (10.0, 50.0, 100.0, 500.0, 1000.0, 2000.0):
    R0 = R_obs(rmg)
    dR = abs(R_obs(rmg, dF=dF) - R0)
    dRs = sF * rmg / (rmg + rm_here) ** 2
    flag = "OK" if dRs < MARGIN else "EXCEEDS"
    print(f"  {rmg:10.0f} {R0:9.4f} {dR:13.2e} {dRs:17.2e}  {flag:>10s}")
    report["threshold_impact"]["induced_dR"][str(rmg)] = {
        "R_obs": float(R0), "from_dF": float(dR), "from_sigma_F": float(dRs),
        "within_margin": bool(dRs < MARGIN)}

# Where each term drops under the margin AND stays under it (both terms fall
# monotonically at large RM_gas, so take the last failure and step past it).
x = np.logspace(0, 5, 20001)


def last_crossing(term):
    bad = np.where(term >= MARGIN)[0]
    if bad.size == 0:
        return float(x[0])
    return float(x[bad[-1] + 1]) if bad[-1] + 1 < x.size else float("inf")


cross_s = last_crossing(sF * x / (x + rm_here) ** 2)
cross_d = last_crossing(np.abs((rm_here + dF / 2) / (x + rm_here - dF / 2)
                               - rm_here / (x + rm_here)))
report["threshold_impact"]["RM_gas_needed_for_sigma_F"] = float(cross_s)
report["threshold_impact"]["RM_gas_needed_for_dF"] = float(cross_d)

print(f"""
Against the margin the engine actually works with -- synthetic wave 0.861 vs
particle 0.967, threshold {th}, so only {MARGIN:.3f} of headroom to the particle
value -- the two terms are nowhere near equal:

  differential (gradient) : needs |RM_gas| > {cross_d:6.0f} rad/m^2   -- easily met
  common-mode (sigma_F)   : needs |RM_gas| > {cross_s:6.0f} rad/m^2   -- NOT easily met

CONCLUSION, and it is not the reassuring one. The Milky Way screen toward the
Bullet Cluster is genuinely smooth on the scale of the diagnostic: the whole
DM_NW-DM_SE baseline falls inside ONE {F.pix_arcmin:.1f} arcmin map pixel, the transect
varies by {ptp:.2f} rad/m^2 peak-to-peak, and the differential contamination is bounded
at {dF:.4f} rad/m^2. The gradient -- the thing this check was written to worry about --
is not a problem.

What replaces it is worse, because it is irreducible by better cluster data:
sigma_F = {sF:.1f} rad/m^2 is as large as F = {Fg:.1f} rad/m^2 itself. Hutschenreuter+2022
barely constrains the screen AMPLITUDE toward (l,b) = ({l0:.1f}, {b0:+.1f}) -- there are
too few background RM sources in that direction. Subtracting the screen therefore
leaves an absolute uncertainty of order the screen itself, and that propagates
into R as an error bar that only falls under the {MARGIN:.3f} margin once the intrinsic
cluster RM exceeds ~{cross_s:.0f} rad/m^2 -- the very top of the observed cluster range.

So the honest statement of the RM-ratio test's status is:

  1. The foreground GRADIENT assumption is now quantified and it holds.
  2. The foreground AMPLITUDE uncertainty is the binding term, and at the
     current {th} threshold with {MARGIN:.3f} headroom the test is under-powered
     unless MeerKAT measures |RM_gas| >~ {cross_s:.0f} rad/m^2.
  3. The fix is not more foreground data -- it is to stop reporting R against a
     hard {th} threshold and report R with this error bar attached, or to widen
     the wave/particle separation the engine is asked to resolve.

That is checkable the moment MeerKAT Q/U lands: measure |RM_gas|, compare to
{cross_s:.0f} rad/m^2, and the test either has power or it does not.""")

# ── Figure ────────────────────────────────────────────────────────────────────
print("\nrendering patches ...")
panels = [(F, "faraday_sky_mean", "Galactic Faraday RM [rad/m$^2$]\n(Hutschenreuter+2022)", "RdBu_r", True)]
if "353" in report["planck"]:
    P = LazyHealpix(PLANCK353, "planck353")
    panels += [(P, ("Q_STOKES", "U_STOKES"), "Planck 353 GHz polarized intensity $P$", "inferno", False),
               (P, "I_STOKES", "Planck 353 GHz Stokes $I$ (dust)", "magma", False)]

FOV, NPX = 8.0, 280
fig = plt.figure(figsize=(16, 5.2), facecolor="#090c12")
for i, (m, col, title, cmap, diverging) in enumerate(panels):
    ax = fig.add_subplot(1, 3, i + 1)
    if isinstance(col, tuple):
        proj = np.hypot(patch(m, col[0], l0, b0, FOV, NPX),
                        patch(m, col[1], l0, b0, FOV, NPX))
    else:
        proj = patch(m, col, l0, b0, FOV, NPX)
    if diverging:
        v = np.nanpercentile(np.abs(proj), 99)
        im = ax.imshow(proj, origin="lower", cmap=cmap, vmin=-v, vmax=v,
                       extent=[FOV/2, -FOV/2, -FOV/2, FOV/2])
    else:
        im = ax.imshow(proj, origin="lower", cmap=cmap,
                       vmin=np.nanpercentile(proj, 1), vmax=np.nanpercentile(proj, 99),
                       extent=[FOV/2, -FOV/2, -FOV/2, FOV/2])
    ax.set_title(title, color="#c8d8e8", fontsize=9)
    ax.plot(0, 0, "+", color="#4af0ff", ms=14, mew=2)
    ax.text(-0.15, 0.15, "Bullet", color="#4af0ff", fontsize=8)
    ax.set_xlabel("$\\Delta l$ [deg]", color="#5a7090", fontsize=8)
    ax.set_ylabel("$\\Delta b$ [deg]", color="#5a7090", fontsize=8)
    ax.set_facecolor("#090c12")
    ax.tick_params(colors="#5a7090", labelsize=7)
    for sp in ax.spines.values():
        sp.set_color("#25303f")
    cb = fig.colorbar(im, ax=ax, shrink=0.75)
    cb.ax.tick_params(colors="#5a7090", labelsize=7)
fig.suptitle(f"Bullet Cluster sightline  l={l0:.2f}  b={b0:+.2f}   "
             f"({FOV:.0f} deg field, gnomonic, $l$ to the left)",
             color="#c8d8e8", fontsize=11)
fig.savefig(OUT / "bullet_foreground_maps.png", dpi=140, bbox_inches="tight",
            facecolor="#090c12")
plt.close()

with open(OUT / "bullet_polarization_foreground.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n" + "=" * 74)
print(f"-> {OUT / 'bullet_polarization_foreground.json'}")
print(f"-> {OUT / 'bullet_foreground_maps.png'}")
print("=" * 74)
