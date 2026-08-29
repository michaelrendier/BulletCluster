# Einstein Cross data catalog — ptychography / L_(I|O) / polarization

**Written 2026-08-18.** A REQUIREMENTS CHECKLIST, not an inventory. Nothing here
claims a dataset exists until the `verified` column says so against an archive
query. Rows marked **MAY NOT EXIST** are flagged because the physics says the
observation is probably impossible, not because nobody looked.

> **PROVENANCE RULE.** Every number produced from this data carries its class in
> the same sentence: SYNTHETIC tests the code, CALIBRATION tests the pipeline,
> RESULT tests the hypothesis. Never report the first two as results.

---

## 0. The five targets

| key | object | z_lens | z_src | scale | why it is in the set |
|---|---|---|---|---|---|
| A1 | MACS J1149.5+2223 (SN Refsdal) | 0.544 | 1.49 | cluster | the reappearance SX was PREDICTED from lens models — the only prospective test in the set |
| A2 | SDSS J1004+4112 | 0.68 | 1.734 | cluster | ~15" separation, long measured delays; bridges cluster and galaxy scale |
| A3 | RX J1131−1231 | 0.295 | 0.658 | galaxy | best-characterised Fermat potential, long delays |
| A4 | HE 0435−1223 | 0.454 | 1.689 | galaxy | independent system — exists so A3 cannot be a fluke |
| A5 | Q2237+0305 (Huchra's Lens) | 0.0394 | 1.695 | galaxy | the original Einstein Cross. Delays are HOURS, so useless for dt — the cleanest pure-geometry case |

---

## 1. PTYCHOGRAPHY — and the current download is the wrong product

Ptychography reconstructs phase from **overlapping** intensity measurements with
**known probe positions**. Astronomically that means many dithered exposures
plus a PSF model. It does **not** work from a mosaic.

> **THE DOWNLOAD SCRIPT IS FETCHING THE WRONG FILES FOR THIS.** Its own banner
> reads *"products: drizzled mosaics only ('_i2d.fits', '_drz.fits',
> '_drc.fits')"*. Drizzling RESAMPLES and COMBINES the dithers — it destroys
> exactly the per-exposure sub-pixel offsets ptychography needs. The 190 GB
> already downloaded is the right targets in the wrong product class.
> **Fix: `--all-products`.**

| need | product | instrument | notes |
|---|---|---|---|
| individual dithered frames | `_flt`, `_flc` | HST ACS/WFC3/WFPC2 | flat-fielded, NOT drizzled. `_flc` = CTE-corrected |
| individual dithered frames | `_cal`, `_rate` | JWST NIRCam/MIRI | stage-2 per-exposure |
| dither pattern / WCS | headers of the above | — | the "probe positions". Must be sub-pixel accurate |
| PSF model (the probe) | TinyTim / WebbPSF | — | generated, not downloaded. **CALIBRATION** |
| pixel-area / distortion maps | IDCTAB, `_npl` | — | needed before any position is trusted |
| read noise / gain | instrument handbook | — | sets the noise floor of the phase retrieval |

**Minimum viable per target:** ≥ 4 dithered exposures in one filter with
sub-pixel offsets, plus a PSF model at the field position. More filters buys
chromatic phase; more epochs buys microlensing separation.

---

## 2. L_(I|O) PHOTON PATH — mostly catalogue, not imaging

The Fermat potential difference is what L_(I|O) − L is:
`dt ≈ D[(θ−β)²/2 − ψ(θ)]`. To evaluate it per target you need:

| need | source | verified |
|---|---|---|
| image positions θ (4 images, milliarcsec) | HST astrometry / VLBI where radio-loud | ☐ |
| measured time delays Δt | COSMOGRAIL, H0LiCOW/TDCOSMO published curves | ☐ |
| lens redshift z_l, source redshift z_s | spectroscopy (published) | ☐ |
| lens light profile / ellipticity | HST imaging, already have | ☐ |
| line-of-sight convergence κ_ext | weak-lensing + number counts | ☐ |
| stellar velocity dispersion σ_v | Keck/VLT spectroscopy | ☐ |
| **published lens model to run FORWARD against** | TDCOSMO data releases | ☐ |

> **Caveat from the download script, kept because it is load-bearing:** a quad
> lens is the STRONG regime (κ ~ 1). Kaiser–Squires is a linear inversion valid
> for κ ≪ 1. Do **not** feed these to `bounded_lensing_pipeline()` and expect
> meaning — run the ψ → α → β chain FORWARD on a published model instead.
>
> A5 has delays of HOURS. It cannot test dt. It is in the set for geometry only.

---

## 3. POLARIZATION VECTOR FIELD — and where it does not exist

Needs Stokes **I, Q, U** at minimum; V for circular.

| band | instrument | product | status |
|---|---|---|---|
| radio | VLA / VLBA full-Stokes | `.ms`, Q/U cubes | **MAY NOT EXIST** — A3/A4/A5 are radio-QUIET quasars. Check NVSS/FIRST/VLASS first; expect non-detections |
| radio | MERLIN / EVN | — | only if the source is radio-loud |
| mm | ALMA full-pol | Band 3–7 Q/U | check ALMA archive per target |
| optical | HST ACS/WFC POL0V, POL60V, POL120V | `_flt` per polarizer | the workhorse. Needs all three angles |
| optical | HST WFPC2 POLQ | — | older, A5 has WFPC2 coverage |
| optical | VLT FORS2 imaging polarimetry | — | ground, seeing-limited |
| NIR | HST NICMOS POL0S/POL120S/POL240S | — | if NIR polarimetry is wanted |
| X-ray | IXPE | — | **ALMOST CERTAINLY IMPOSSIBLE.** IXPE needs bright sources; these quasars are orders of magnitude too faint. Do not budget for it |
| X-ray | Chandra / XMM | I only | **no polarimetry** — imaging and spectra only |

**Honest summary of section 3:** a full radio-through-X-ray polarization vector
field for all five targets is very likely **not obtainable from existing
archives.** The realistic product is HST optical polarimetry where it exists,
plus radio Q/U for whichever target turns out to be radio-loud. State that
before promising a vector field.

---

## 4. Supporting, all bands

| need | why |
|---|---|
| Galactic extinction map (SFD/Planck) | de-redden before any colour or polarization angle |
| Galactic foreground polarization (Planck 353 GHz) | **subtract it** — otherwise the foreground IS your signal. Already on disk: `mm_sz/planck` |
| Faraday rotation map | radio polarization angle is meaningless without RM |
| PSF stars in-field | empirical PSF check against TinyTim/WebbPSF |
| microlensing light curves (OGLE/COSMOGRAIL) | A5 especially — microlensing corrupts flux ratios |

---

## 5. The checklist, per target

Copy this block per target and fill it in. **Nothing is a RESULT until the
control column is also filled.**

```
TARGET: ____________________
  [ ] dithered _flt/_flc or _cal/_rate    n = ____ exposures, filter ______
  [ ] PSF model generated                 TinyTim / WebbPSF   [CALIBRATION]
  [ ] distortion + pixel-area maps
  [ ] image positions theta (4)           source: __________
  [ ] time delays dt                      source: __________  (A5: N/A)
  [ ] z_lens, z_src
  [ ] published lens model                source: __________
  [ ] kappa_ext estimate
  [ ] Stokes I/Q/U optical                instrument: _______  or NOT AVAILABLE
  [ ] Stokes I/Q/U radio                  instrument: _______  or NOT AVAILABLE
  [ ] Galactic foreground subtracted      Planck 353
  [ ] CONTROL run + recorded
  provenance of every number below: SYNTHETIC / CALIBRATION / RESULT
```

---

## 6. What to do next, in order

1. **Re-run the download with `--all-products`** for group A. The drizzled
   mosaics already on disk stay useful for astrometry; the per-exposure frames
   are what ptychography needs and are not yet present.
2. **Query, do not assume.** Before adding a polarization row to any target,
   query the archive. Sections 3's "MAY NOT EXIST" rows exist so a negative is
   recorded as a negative rather than as a gap.
3. **Forward-model first.** Run ψ → α → β on a published lens model and check it
   reproduces the measured image positions. That is CALIBRATION. Only after it
   closes does anything computed from our own reconstruction become a RESULT.
