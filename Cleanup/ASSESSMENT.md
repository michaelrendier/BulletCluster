# BulletCluster — Honest Assessment

**2026-08-17.** Full read of all 39 project Python files, all 26 markdown files, the data
holdings, and the load-bearing figures. Written after auditing rather than before.

---

## 1. State of the repository, in one paragraph

The **infrastructure is good**, the **nulls are rigorous and correctly diagnosed**, and the
**claims layer was never corrected after the nulls refuted it**. There is one solid data
product (Chandra), one genuinely valuable methodological finding (R2), and a set of honest
nulls. There is no result bearing on wave vs particle dark matter, and the central
zero-free-parameter prediction has never been run on observational data. What went wrong was
not the science — it was a documentation policy that kept refuted claims in the live files.

Detail: [`REAL_RESULTS.md`](REAL_RESULTS.md) · [`RETRACTED.md`](RETRACTED.md)

---

## 2. The single most useful finding of this audit

**The cause of nulls N1–N4 is fixable today, with data already on disk.**

Every one of those nulls traces to one thing: **DM_NW is off-field**, so κ was measured from
too little area with too few background galaxies. Verified directly, by WCS:

```
JWST 4598 tile o001_t001   FOV 5.67' x 2.52'   DM_NW at y=2728.6 of ny=2505   OUTSIDE
JWST 4598 tile o002_t010   a different pointing — all reference points at negative x
ALL 424 JWST i2d files     files covering DM_NW:  0
```

So **completing the JWST download cannot fix it, and neither can re-drizzling.** Program
4598's footprint excludes the main cluster's mass peak. That is a property of the program,
not of the download.

But:

```
HST 10200  j90701010_drz.fits   DM_NW INSIDE   DM_SE INSIDE   CENTROID INSIDE   4222x4325
           j90701020_drz.fits   DM_NW INSIDE   DM_SE INSIDE   CENTROID INSIDE
           j90702020_drz.fits   DM_NW INSIDE   DM_SE INSIDE   CENTROID INSIDE
```

**HST covers all of it, and it is already downloaded.** It is also the instrument Clowe et al.
2006 used, so it is the literature-comparable route as well as the available one.

**Action:** point the weak-lensing pipeline (`source_extract.py` → `l_io_lensing.py` →
`kappa_EB_test.py`) at HST 10200 instead of the JWST single tile, and rerun the
pre-registered thresholds unchanged (`kappa E/B >> 1`, `psi_E/psi_B >> 1`). This is the
highest-value next step in the repository and it needs no new data.

Caveat to check, not assume: ACS is shallower in the NIR than NIRCam, so background source
density per unit area will be lower. The field is ~4x larger in each dimension and contains
both halos, which is the trade — but the source count has to be measured, not assumed, and
the completeness limit checked (that is what killed the magnification-bias option).

---

## 3. Is other telescope data necessary? — direct answer

### REQUIRED, and genuinely blocking

**Real MeerKAT/SARAO Stokes Q/U.** This is the only thing that enables the repository's one
zero-free-parameter prediction. Verified on the files: MGCLS DR1 has **`NAXIS4 = 1`** on the
STOKES axis — Stokes I only, no Q, no U. The Q/U cubes present are synthetic and inject the
answer at the DM peaks.

**I contradicted myself on this and the correct answer is: it is required.** Earlier I said
radio data was unnecessary for the ptychography framing. That was wrong, and wrong twice
over: the RM-ratio test *is* the repo's central claim and needs Q/U absolutely; and
`ptychography_polarization.py` is neither ptychography nor polarization — it is an RGB
composite of three intensity filters, as `L_IO_SPECIFICATION.md` §6 already states. So the
question I answered was malformed and the answer I gave was misleading.

**And Q/U alone is now insufficient**, which is new since the project plan was written.
R2 measured the Galactic Faraday foreground at the sightline as common-mode and additive
(18.27 ± 19.669 rad/m², all five reference points in ONE HEALPix pixel because the map's
6.87′ pixel cannot resolve the 2.89′ DM separation). A common additive offset does not cancel
in a *ratio* — it drags the ratio toward 1, the particle verdict. **Foreground subtraction is
a second requirement, not an optional refinement.**

### ALREADY ON DISK — no acquisition needed

| dataset | state |
|---|---|
| Chandra X-ray | `xray/bullet_chandra_0.5-7keV.fits`, 576.6 ks, 1,013,663 counts, 10 ObsIDs |
| HST 10200 | 4 drizzled images, **covers both DM halos** — the unblock in §2 |
| JWST 4598 | complete as of today; 424 i2d, 2 tiles — does **not** cover DM_NW |
| MeerKAT MGCLS Stokes I | 2.7 GB, real, I only |
| Planck MILCA y-map + 545/857 | real; the SZ weighting for any 3D deprojection |
| Galactic Faraday sky (Hutschenreuter 2022) | real; the R2 foreground measurement |

### WOULD HELP — not blocking

- **Published κ from Clowe+2006 / Bradač+2006.** Not on disk. Needed for comparison against a
  literature-accepted mass map. The Clowe Σ-map is 185 × 185 px at 8.5 kpc/pixel; I found no
  clean archive download, so it likely means contacting the authors.
- **ALMA/VLA polarimetry of a polarized background source** behind the cluster — the
  differential-Faraday path (precedent: PKS 1830−211, ALMA differential polarimetry between
  two lensed images, RM to a few × 10⁵ rad m⁻²). Requires a polarized source to exist there;
  unverified.
- **Rubin/LSST**, on a multi-year horizon. Dec −55.94 is inside WFD (−65 to +5), survey began
  2026-06-29. Its 9.6 deg² field solves the area problem outright and its 3-day cadence is the
  only realistic route to a lensed *variable* — which is the sole observable that breaks the
  mass-sheet degeneracy. It **cannot** resolve Einstein crosses (0.7–0.8″ seeing vs 1–2″
  crosses), so it complements JWST rather than replacing it.

### NOT NEEDED — closed off

- **Gaia.** Parallax at z = 0.296 (~1 Gpc) is ~1 nanoarcsecond against Gaia's ~20 μas floor —
  four orders of magnitude short. Useful only for the astrometric reference frame and
  foreground-star rejection. Not for cluster 3D structure.
- **More JWST filters for "polarization."** JWST has no polarimetric mode in any instrument.
  Ever. This is not a gap to be filled.
- **Ptychography from JWST dithers.** Requires coherent illumination; astronomical sources are
  mutually incoherent, so there is no phase to retrieve. `L_IO_SPECIFICATION.md` §6 makes the
  better point instead: weak lensing is *already* a truncated ptychography, and the honest
  extension is **flexion** (third shape moments) — which needs no new data, only a re-run of
  extraction, and works in the weak regime.
- **3D mass from lensing alone.** κ is a projection; any 3D distribution with the same
  projection lenses identically. 3D requires multiple line-of-sight weightings (ρ from
  lensing, n² from X-ray, nT from SZ) — all three of which are on disk. But the Bullet is
  mid-merger, so equilibrium deprojection is invalid; its 3D orientation comes from **shock
  geometry** instead.

---

## 4. Why the images could not be regenerated — and the fix

Six of the eight figures the README cited as results have **no generating code anywhere in the
repository**. They cannot be reproduced, cannot be checked against the nulls, and cannot be
updated when the data improves. That is why they survived refutation: there was nothing to
re-run that would have shown them changing.

Cody's diagnosis of the cause is correct and is adopted here: exploratory code was written
somewhere ephemeral and the output was kept while the code was lost. **A persistent working
directory is the fix** — text is negligible in size next to 250 GB of FITS, and a work
directory full of experimental engines is both provenance and a record of what had to be
learned. The model is `Ptolemy2/working`: experiment there, promote what works into the
codebase, never let the notepad pollute the product.

**Rule for this repo going forward: a figure with no committed generating script is not a
result.** It is an illustration, and it goes under "Figures on disk" with that label.

---

## 5. What I got wrong in this session, plainly

- Said MeerKAT radio data was unnecessary, then said it was integral. **It is required.**
  §3 above is the resolved answer.
- Proposed magnification bias without first checking the precondition. The catalog's median
  flux sits almost on the detection limit, so the count-slope fit runs inside the
  incompleteness regime and my α = 0.870 is unreliable.
- Mapped "how many photons through a pixel" onto escape-time colouring, which is the wrong
  quantity. Cody's own 2026-08-14 note already had it right — a density accumulation buffer
  (Buddhabrot), with `(x,y,t)` so arrival time is carried.
- Read the README's "Already Confirmed" list as results, when the 2026-08-14 nulls had
  already refuted most of it. That is the failure this document exists to prevent recurring.
