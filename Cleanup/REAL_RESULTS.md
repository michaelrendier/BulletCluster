# BulletCluster — Actual Results

**Audited 2026-08-17.** Every item on this page is a measurement on **real observational
data**, with code in the repo that reproduces it, and its limits stated.

Nothing here comes from `radio/meerkat/synthetic/`. Nothing here is a demonstration that a
method runs. What was removed, and why, is in `RETRACTED.md`.

**Summary: one data product, one methodological finding, one measurement, five nulls, one
negative control, two infrastructure fixes.** All of it real. None of it confirms the
Abrikosov hypothesis, and none of it refutes it either.

---

## R1 — Chandra X-ray mosaic  [DATA PRODUCT]

```
xray/bullet_chandra_0.5-7keV.fits   (+ .png)
576.6 ks   1,013,663 counts   all 10 ObsIDs   common 2"/pix WCS
```

Bow shock and cold front cleanly resolved. Built by `xray/make_chandra_map.py`.

**Limits, stated in the code:** exposure-weighted **counts**, not surface brightness. No
exposure map, no vignetting correction, no background subtraction, no point-source removal.
**Adequate for morphology and correlation. NOT for photometry, temperature, or flux.**
CIAO `merge_obs`/`fluximage` required if flux is ever needed.

This is the single most solid thing in the repository.

---

## R2 — The RM-ratio test is biased toward its own null hypothesis  [METHODOLOGICAL, and the most important result here]

Code: `lensing_validation/bullet_polarization_foreground.py`
Data: Hutschenreuter et al. 2022 Galactic Faraday sky (D4/D6), Planck 353/217 GHz I/Q/U
Output: `artifacts/bullet_polarization_foreground.json`

The engine's whole prediction is `RM(DM)/RM(gas)` against a threshold of 0.95. Both terms
sit behind the same Milky Way Faraday screen, and the screen was **assumed to cancel in the
ratio**. It does not:

> A common **additive** foreground does not cancel in a **ratio** — it drags the ratio
> toward 1, which is the *particle* verdict. The test is biased toward the answer it was
> built to refute.

Measured, at the Bullet sightline (l = 266.019, b = −21.257):

```
RM_galactic          18.274 +/- 19.669 rad/m^2      <- sigma EXCEEDS the value
map pixel             6.871 arcmin
DM_NW <-> DM_SE       2.891 arcmin
n_distinct_pixels     1
gradient          0.114 rad/m^2 per arcmin  (0.25 deg disc)
```

**All five reference points — DM_NW, DM_SE, GAS_NW, GAS_SE, CENTROID — fall in ONE HEALPix
pixel (2142697).** The Galactic Faraday map at nside 512 cannot resolve the DM separation
at all.

**⚠ CORRECTED 2026-08-17 — the resolution ceiling.** An earlier version of this entry
claimed the foreground *is* common-mode across the transect. **That was a limit artifact.**
The DM separation (2.891′) is *below* the map pixel (6.871′), so a gradient could not have
been detected if one existed; and σ (19.669) **exceeds** the value (18.274), so the
foreground RM is not significantly different from zero at 1σ.

- **Wrong:** "the foreground is uniform across the transect."
- **Right:** "the foreground is **unresolved** at 6.87′. Uniformity is untested."

What stands, because it is analytic rather than measured: a common **additive** offset does
not cancel in a **ratio** — it drags the ratio toward 1, the particle verdict. Cluster ICM
rotation measures run 1e1–1e3 rad/m², so at the low end an ~18 rad/m² offset is comparable to
the signal. **So Q/U acquisition remains necessary-but-insufficient**, and the reason is now
better stated: the foreground must be *resolved*, not merely *estimated*.

**Different method required, not a better version of this one:** a high-density RM grid
(POSSUM/ASKAP, or targeted polarimetry). See `DATA_REQUIREMENTS.md` §0 for why re-reading
Hutschenreuter cannot settle it.

**Therefore: acquiring real Stokes Q/U is necessary but NOT sufficient.** The foreground
has to be subtracted before the 0.95 threshold means anything. That requirement did not
exist in the project plan before this script ran.

A sanity check that also passed, worth keeping: HEALPix RING ordering verified by
mean |RM| in the Galactic plane (187.4) vs the polar cap (4.1) — the correct sign and
magnitude, so the ordering assumption is not silently wrong.

---

## R3 — Radio halo spectral index and power spectrum  [MEASUREMENT + NULL]

Code: `radio/halo_spectral_and_power.py`
Data: **real** MeerKAT MGCLS L-band, 10 planes, 996.6–1656.2 MHz
Output: `radio/bullet_spectral_index.fits`

```
spectral index alpha   median -1.55   16-84%  [-3.42, -0.67]     (synchrotron)
P(k) ~ k^-1.22 over 170-2002 kpc
largest excess         +1.91 sigma at 417 kpc
```

**No preferred scale. No standing-wave surface.**

**Limits, both recorded in the code:** the slope is shallower than Kolmogorov (−3.67), so
noise contributes to it; and 15″ = 67 kpc/beam while the predicted fuzzy-DM structure is
~1 kpc — **two orders of magnitude too coarse to reach the predicted scale.** This test
cannot reach the thing it was aimed at, so the null is weak evidence about the hypothesis
and strong evidence about the instrument.

---

## R4 — κ is noise-dominated  [NULL]

Code: `xray/kappa_EB_test.py`. Lensing produces E-mode only; B-mode (shear rotated 45°)
carries no lensing signal by construction, so E/B is the null.

```
rms(kappa_E) 0.07186    rms(kappa_B) 0.07023    ratio 1.023
P_E/P_B across k: 2.33, 0.98, 1.65, 1.55, 2.12, 0.81   -> scatter, no peak
correlation length   E 6.0 px    B 7.0 px
```

The pipeline reproduces the shipped `kappa.npy` to **1.11e-16** — this is the same map, not
a reimplementation, so the null applies to every product derived from it.

**The blob field is smoothed shape noise.** This does not refute wave DM; it says this map
cannot test it.

---

## R5 — ψ is integrated noise; the smooth gradient is the operator  [NULL]

Code: `xray/lio_vs_ptychography.py`. `psi_k = -2 kappa_k / k^2` — the `1/k²` is a brutal
low-pass that manufactures a large-scale gradient from **any** input.

```
psi rms        E 14.054   B 19.412   E/B 0.724    <- B LARGER than E
psi peak-peak  E 75.114   B 77.310   E/B 0.972
power in 3 lowest k    psi_E 0.893   psi_B 0.945    (kappa_E 0.133)
```

**89% of ψ's power sits in three wavenumbers.** A smooth large-scale gradient in ψ is
guaranteed by the operator and is not evidence of anything.

This null is what retires the "gradient" imagery. See `RETRACTED.md`.

---

## R6 — Emission does not track L_(I|O)  [NULL]

All |z| < 2 against a circular-shift null, and E and B agree throughout:

```
emission vs kappa_E   r= 0.0376  z= 1.34      kappa_B    r= 0.0367  z= 1.32
emission vs psi_E     r= 0.0151  z= 0.24      psi_B      r=-0.1333  z=-1.87
emission vs |alpha|_E r=-0.0223  z=-0.71      |alpha|_B  r= 0.0436  z= 1.04
```

The visual agreement between the ptychography composite and L_(I|O) **is not present as a
correlation.** Two maps dominated by one large-scale mode look aligned regardless of
content. That the B-mode tracks as well as the E-mode is the tell.

---

## R7 — Shape test inconclusive, with an identified cause  [DIAGNOSTIC]

Code: `xray/kappa_vs_xray_vs_nfw.py`. Does the gradient track the real X-ray gas or the NFW
model placed at DM_NW/DM_SE? Those are spatially separated, so they are distinguishable.

```
X-ray template   z = -1.98        NFW template   z = -1.30      neither preferred
templates ARE separable:  X-ray vs NFW  r = 0.277   -> the method has power
DM_NW  px = (76.6, 84.8)   ** OUTSIDE THE FIELD **   (ny = 78)
DM_SE  px = (123.7, 12.6)  inside, 12 px from the edge
```

The reference mosaic is **one tile**, 5.66′ × 2.51′. The test was asked to find a halo that
is not in the image.

**R4–R7 are one disease, not four failures:** single-tile footprint, DM_NW off-field, too
few background galaxies. κ noisy → ψ integrated noise → every correlation meaningless.

**Pre-registered thresholds for the re-run** (scripts rerun unchanged, no tuning):
`psi_E/psi_B >> 1` (now 0.724) and `kappa E/B >> 1` (now 1.023). Only then are strong-lensing
steps worth attempting.

---

## R8 — The hand-drawn constraint never entered the pipeline  [NEGATIVE CONTROL, PASSED]

`The_Bullet_Cluster-defined.png` is a hand-annotated constraint band. Verified by grep:
**no code reads it.** It cannot have leaked into any output. This is a real control and it
passed — worth keeping precisely because the failure mode it guards against is severe.

---

## R9 — Download infrastructure  [ENGINEERING]

Two real faults found and fixed, both in `jwst_resume_download.py`:

- `Observations.get_product_list()` on all 292 observations at once **hung ~7 hours at 0%
  CPU with zero files written** — astroquery puts no timeout on the call. Now batched
  (15/call) with retry and per-batch logging, so a stall is visible immediately.
- The product filter was `endswith((".fits", "_drz.fits", "_cal.fits", "_i2d.fits"))` — a
  bare `".fits"` **subsumes every other pattern**, so the mask did nothing: 43,326 products
  passed (~118 MB each, terabytes) instead of the intended ~14 GB.

Added 2026-08-17: `netgate.py` — pauses on signal loss rather than aborting, so a network
switch costs one TCP handshake instead of a full re-query.

---

## What all of this does and does not support

**Supports:** that the Chandra morphology is solid; that the current κ map cannot test the
hypothesis and the reason is field size; that the central RM-ratio test has a
previously-unquantified bias toward the particle verdict.

**Does not support:** any claim about wave vs particle dark matter. The zero-free-parameter
prediction has never been run on observational data, because the data it needs does not
exist on disk.

**Does not refute the hypothesis either.** Every null here is a null about an *instrument*
or a *footprint*, not about the physics. R3 and R4 both say so explicitly.
