# Ptychography, the L_(I|O) Path of the Photon, and the Polarization Vector Field from Data — Huchra's Lens (Q2237+0305)

**DRAFT — started 2026-10-17. Nothing in this draft has been evaluated on data yet.** A Fourth Age paper
(*One Paper. One Claim. One Prediction. One Engine. One Wiki.*). Canonical copy: `BulletCluster/huchras_lens/DRAFT_PAPER.md`;
mirror: `FourthAgePapers/HuchrasLens/DRAFT_PAPER.md`.

> **Assistant note (read this first).** This draft is written by a transformer (Claude Sonnet 5.5, Claude Code) working with
> Cody Michael Allison (Michael Rendier; the standing authorship block is in the memory file `user_profile.md`). The
> `cs-paper-code-conventions` skill is running (`ContextPlease/claude/skills/cs-paper-code-conventions/`). Every number below
> was produced by a query or a script on 2026-10-17 and says which. Statements that are Cody's hypotheses are labelled
> HYPOTHESIS; statements I recall without having checked them are labelled UNVERIFIED. Where something does not exist yet, the
> draft says "does not exist". Nothing here claims a result: the BulletCluster project already retracted a set of claims that
> the project's own nulls refuted (`BulletCluster/Cleanup/RETRACTED.md`), and this paper is built so that cannot happen again
> (§9, Required controls).

Provenance classes (from `BulletCluster/lensing_validation/EINSTEIN_CROSS_DATA_CATALOG.md`): **SYNTHETIC** tests the code,
**CALIBRATION** tests the pipeline, **RESULT** tests the hypothesis. This draft contains only **ARCHIVE QUERY** facts and
**FEASIBILITY PROBE** measurements, which are none of the three.

---

## 0. The claim, the prediction, the engine (Fourth Age protocol)

| pillar | state |
|---|---|
| **Claim** | HYPOTHESIS (Cody): *gravity is a shape, not a stuff.* If no scattering "stuff" lies on the photon paths of the four images, the polarization carried by the light stays in phase across the images; if photons scatter on a "graviton/dust" medium, the polarization performs a random walk and the images fall out of phase. Falsifiable only once Stokes data and the scattering model exist (§7, §10). |
| **Prediction (Ptolemy / 0_RB)** | **NOT RUN.** See §8: the model is identified exactly, but it has no mapping to an optical observable, so it cannot honestly emit a number. |
| **Engine** | does not exist as one piece; the parts that exist and the parts that do not are in §10. |
| **Wiki page** | written last (Fourth Age rule). |

What this paper tests (Cody, 2026-10-17): **ptychography**; the **dynamic Lagrangian** L_(I|O), i.e. the path *inside the refractive
index*, the actual path and not the assumed stationary one; and the **polarization vector field**, compared with models that have
yet to be built. Lensing is the setting in which all three appear together.

## 1. The target

| field | value | how known |
|---|---|---|
| name | Q2237+0305, "Huchra's Lens", "the Einstein Cross"; SIMBAD main id `QSO J2240+0321` | SIMBAD TAP, 2026-10-17 |
| position (ICRS) | RA 340.125975°, Dec +3.3585083° | SIMBAD TAP |
| z_lens, z_source | 0.0394, 1.695 | `EINSTEIN_CROSS_DATA_CATALOG.md` (not re-verified today) |
| why it is the target | the original Einstein Cross; delays are HOURS, so useless for Δt and the cleanest pure-geometry case | same catalog |
| "most heavily cited" | Huchra et al. 1985, AJ 90, 691, *2237+0305 — a new and unusual gravitational lens*: **330** citations (OpenAlex), **174** (INSPIRE). Refsdal-cross papers: 85–121 (OpenAlex). Both services undercount astronomy against ADS (needs a token). | OpenAlex / INSPIRE API, 2026-10-17 :CALCULATED |

A different object also called an Einstein Cross, HerS-3 (ALMA/NOEMA/VLA/HST, ApJ 2025), appeared in the first web search and is not
the target. Bullet Cluster is off the table for now; its machinery is reused (§10).

## 2. Which telescopes resolved it

Rule: an instrument counts only if it separates the four images, which lie within about 2 arcsec. Everything else is recorded as
coverage, not fetched. Census taken by archive query on 2026-10-17 (files in `catalog/`).

| archive / telescope | what is there | size | note |
|---|---|---|---|
| **HST** (MAST) | 4 720 target-named ObsCore rows in all; **3 121 per-exposure (calib_level 2) products** from ACS (656), WFC3 (1 424), WFPC2 (387), NICMOS (468), WFPC (90), FOC (48), STIS (48) | **60.8 GiB** per-exposure; 43.4 GiB more as drizzled products (not wanted) | proposals seen: 1059 1116 2502 2996 3068 3087 3799 5236 5937 7495 8252 11225 11791 13113 13801 |
| **Chandra ACIS-S** (HEASARC `chanmaster`) | **40 ObsIDs**, 835.5 ks, MJD 51 793.7–58 496.5 | not published | first ObsID 431 ("EINSTEIN CROSS", 30.7 ks) |
| **ALMA** | one member OUS, project 2021.1.00675.S, Band 7 (287–301 GHz), 0.207″, 2 993.8 s, released 2023-10-21, `/XX/YY/` | not published | the finest polarization-capable data found, see §7 |
| **ESO** (VLT UT1–UT4, NTT, MPG/ESO 2.2 m) | 494 science frames: GROND 175, FORS1 117, ISAAC 70, SINFONI 48, X-shooter 48, GIRAFFE 26, FORS2 8, EMMI 2 | ≈3.1 GB | GROND (≈1″ seeing) is the marginal case, flagged per frame by recorded seeing |
| coverage only, not fetched | XMM-Newton EPIC (3 ObsIDs), HST COS (2.5″ aperture, 161 products), GALEX, SDSS, PS1, TESS, IUE | — | PSF or aperture too large |
| **pending, unconfirmed** | VLA (Falco et al. 1996 resolved all four images at 3.6 cm; the NRAO TAP returned nothing); OGLE photometry; CFHT, NOT, Keck, Gemini, Subaru, Magellan, Calar Alto, Apache Point, Liverpool, Maidanak | — | UNVERIFIED: the list of ground telescopes is my expectation from the lensing literature, not a query result |

The requirement "every telescope that ever resolved it" is therefore **not yet met**; the pending row is the work remaining.
The regular dataset file is `PTorrent/ptorrents/einstein_cross_q2237_alltelescopes.ptorrent` (parses with `ptorrent_core.ptfile`,
preflight passes).

## 3. The design constraint: evaluate where the data sits

**Constraint (Cody, 2026-10-17): evaluation happens on the data on the archive servers; nothing is downloaded and staged.**
This is the point of the engineering. Clarified the same day: *no staging* is not *no reading*; a bounded chunk read into memory,
evaluated and discarded is allowed (every read is a transfer). The accounting is bytes read per source and nothing persisted but the result. It is also what the PTorrent spec already says of `evaluation`: *the computation travels
to the data; the data never moves here.*

What the archives actually offer (measured today), as a ladder; the cheapest rung that answers the question wins:

| rung | touches | cost | status |
|---|---|---|---|
| 0 | ADQL/TAP queries (the only archive-side compute found) | KB | works at MAST, HEASARC, ESO, ALMA |
| 1 | catalogs already computed on the server (HST `POINT-CAT`, `SEGMENT-CAT`, `FLT_HLET`) | KB | listed, not read |
| 2 | FITS headers and auxiliary files (WCS; `SPT`, `JIT`/`JIF` jitter; `ASN` association) | 10²–10³ KB per exposure | header walk measured |
| 3 | pixel cutouts by HTTP range reads of `FLC`/`FLT` | KB of pixels | measured |
| 4 | whole files | 168 MB per WFC3/UVIS frame | forbidden by the constraint |

**Feasibility probe (FEASIBILITY PROBE, not a result).** The MAST download API answers `Range` requests with HTTP 206, and the public
bucket `stpubdata/hst/public/…` answers anonymously with `Accept-Ranges: bytes`. Evaluating a 64×64 cutout of one frame:

```
file 168382080 bytes, 17 HDUs, header walk used 21 requests, 241920 bytes
target in HDU 4 EXTVER 2 at pixel x=2035.5 y=1086.1 of [4096, 2051]; BITPIX -32
cutout (64, 64) read with 64 requests, 16384 bytes; total transferred 258304 bytes = 0.1534% of the file, 44.7 s
on-the-server evaluation: median 1.638, peak 10139.191 at cutout (11,60), sum(cut-median) 50828.5 e-/s, units ELECTRONS
```

Reading, kept honest: 85 requests and 258 KB (0.15 %) of one 168 MB frame reached RAM; 94 % of that was the sequential header walk,
which can be cut; the 44.7 s was sequential and not optimised; the peak was not identified with an image A–D and nothing was
calibrated. **"On the server" here means the bytes stay at the archive and only the requested ranges reach RAM; no compute runs at
MAST or AWS.** If the constraint is meant literally (code running at the archive), only rung 0 qualifies today. Script and log:
`PTorrent/in_situ/huchras_lens/probe/insitu_probe.py`, `probe_log/insitu_probe_2026-10-17.txt`.

**Read economics, measured on one 168 MB frame (public S3, 2026-10-17):** 0.49 s latency per request; 4.9 MB/s single-stream, parallel
reads add no bandwidth; whole frame ≈ 34 s; header walk plus one coalesced 1 MiB row block ≈ 2.3 s. Rule: coalesce reads whose gap is
below latency × bandwidth ≈ 2.4 MB. For the 3 121 HST per-exposure frames: whole files ≈ 3.7 h of pure transfer, ranged ≈ 12 min.
Per-archive access methods, `robots.txt` verdicts and options: `PTorrent/in_situ/huchras_lens/ACCESS_OUTLINE.md`.

**`robots.txt` (2026-10-17):** `mast.stsci.edu` disallows a generic agent entirely (`Disallow: /`); HEASARC disallows `/xamin` and `/vo/`
(its TAP); ESO imposes a 333 s `Crawl-delay`; ALMA and CADC allow. The PTorrent core's robots gate would refuse MAST and HEASARC. A
decision is open (ACCESS_OUTLINE §3). Chandra and HST bytes also sit in anonymous public buckets (`nasa-heasarc`, `stpubdata`).

## 4. What file types the dataset contains

One WFC3/UVIS observation (`hst_11791_02_wfc3_uvis_f218w_ib0r02`) has 92 products (full list in `catalog/`): `FLC` (CTE-corrected
per exposure, 168 MB), `FLT` (168 MB), `RAW` (35 MB), `DRC`/`DRZ` (drizzled), `SPT` (support/pointing summary, 104 KB), `JIT`/`JIF`
(jitter), `ASN` (association: which exposures form the dither set), `TRL`, `LOG`, `FLT_HLET`, `POINT-CAT`, `SEGMENT-CAT`, `CRC`/`CRJ`,
JPEG previews. Chandra: event lists and images (FITS), not yet inventoried. ALMA: measurement sets and cubes, not yet inventoried
(range-read adapter undecided). ESO: raw FITS frames and, for SINFONI/GIRAFFE, IFU products.

## 5. Ptychography

Ptychography reconstructs phase from **overlapping** intensity measurements at **known probe positions**. Astronomically that is many
dithered exposures plus a PSF model; it does **not** work from a mosaic (`EINSTEIN_CROSS_DATA_CATALOG.md` §1).

* **What the archive supplies:** per-exposure `FLC`/`FLT` frames; the dither set from `ASN`; probe positions from the WCS in each
  header and the `SPT`/`JIT` jitter summaries. Whether those positions are accurate enough to be sub-pixel "scan positions" is **open**.
* **What it does not supply:** the probe (PSF). TinyTim and WebbPSF are generated, not fetched; neither is installed here (`webbpsf` and
  `photutils` missing; no `tiny1`). A PSF is CALIBRATION, never RESULT.
* **Already on disk, wrong class:** `BulletCluster/lensing_validation/data.premigration/A5_q2237+0305` holds **35 GB of drizzled**
  mosaics; drizzling resamples away the sub-pixel offsets. It stays useful for astrometry only.
* **Existing ptychography code:** a 1-D ePIE variant for CMB power spectra (`FourthAgePapers/Experiments/FractalBoundary/ptychography.py`)
  and `BulletCluster/xray/lio_vs_ptychography.py` (a validation script with B-mode nulls). **No 2-D image ptychography exists.**

### 5b. Observer geometry: the Earth's orbit (COMPUTED, `earth_geometry()` in the downloader, astropy built-in ephemeris, offline)

Cody: *"ensure parallax is taken into account due to Earth's ellipse."* Computed for Q2237+0305 (RA 340.125975°, Dec +3.3585083°) over one year:

| effect | value | what it means here |
|---|---|---|
| Earth's speed / distance | 29.27–30.30 km/s; 0.982–1.018 au | the ellipse (e ≈ 0.017) is in the numbers, not a circle |
| annual aberration of the apparent position | **3.8″ to 20.7″** over the year | large absolute shift; HST headers carry `VAFACTOR` (found in a real local file) and JWST carries `VA_SCALE`, so the pipelines correct it. Whether the correction is adequate for ptychography is **to be checked** per file, not assumed |
| differential aberration across the field | 0.50 mas over the 5″ cross (0.0125 WFC3/UVIS pixel); 16 mas over a 162″ chip (0.41 pixel) | negligible across the cross itself; **not** negligible for registering field stars on the same chip |
| parallax baseline | 0.19–1.01 au (the target is near the ecliptic) | |
| parallax of foreground **PSF stars** | up to 20.3 mas (0.51 px) at 50 pc; 10.1 mas (0.25 px) at 100 pc; 3.4 mas at 300 pc; 1.0 mas at 1 kpc | an empirical PSF built from field stars at different epochs moves with the season |
| parallax of Q2237 (z = 1.695) and the lens galaxy (z = 0.039, ≈170 Mpc) | ≈ 10⁻⁵ mas | zero |
| light-time to the barycentre | −488 … +492 s | timing only; the delays here are hours |
| observatory offset from Earth's centre | HST 4.6×10⁻⁵ au; JWST at L2 ≈ 1.0×10⁻² au | JWST adds a baseline for nearby stars; parallax from it is ≈ 1 % of the Earth-orbit term |

Consequence for the catalog: every observation row keeps its epoch (`t_min`, `t_max`), its computed Earth state, and, after download,
whatever spacecraft-state, velocity-aberration, WCS and dither keywords its headers carry (`--geometry-pass`). Gaia positions, parallaxes
and proper motions of the field stars (the `gaia/` bucket exists) are the natural scaffold for the stars; not yet in the manifest.

## 6. L_(I|O): the path of the photon

L_(I|O) − L is identified with −ψ(θ), the Fermat potential (established GR, not a new operator); the lens equation is β = θ − α(θ);
the difference between the clean path θ and the actual (bent) source position β is the measured L_(I|O) deviation. Time delay:
Δt ≈ D[(θ−β)²/2 − ψ(θ)]. The machinery is `ValaQuenta/modules/l_io_photon_path` (Kaiser–Squires shear→κ, Poisson solve for ψ, deflection
α, lens equation).

**Two different "vector fields" in this paper — do not conflate them.** The vector field in the figure below is the **deflection field
α** (the "slingshot" field, |α| plotted with arrows): it comes from the mass map and says where the photon's path is bent. It is **not**
polarization; no polarization data existed for that run. The **polarization vector field** of the title (Stokes Q/U per image) is a
separate observable, and §7 records that no input for it has been found.

**The figure (κ, L_(I|O)−L, |α|; 176×78 grid, 1.93″/px; titled "Bullet Cluster — L_(I|O) Photon Path Engine (GR)").** Per Cody
(2026-10-17) it was **run on synthetic data**, so its class is **SYNTHETIC**. Two flags: (1) the figure's own title reads "on real
JWST F444W shear" and its κ panel "real BG shear", which contradicts that; the title should be corrected at the source; (2) its
generating script was not located this session, and the retraction record treats a figure without generating code as an orphan, not
evidence (`RETRACTED.md` RT2). What a SYNTHETIC run establishes, by this project's own rule, is that **the code maps a photon through a
lens**: input mass → ψ → deflection field → β = θ − α, with the gradient of the path visible. That tests the pipeline. It is not a
RESULT and cannot by itself bear on the hypothesis of §0: a synthetic input encodes the mass distribution that was put in, so the
output cannot distinguish a "shape" from a "stuff". Cody's reading is that the run shows the hypothesis to be at least partially
correct; recorded here as his reading (HYPOTHESIS), not as a finding.

**What the figure's panels show, decoded from the rendered pixels** (`probe_log/figure_decode_2026-10-17.py`, FEASIBILITY-class
reading of an image, not of the underlying arrays; colour limits κ ±0.19 and −ψ ±42.4 estimated from the colourbar geometry):

* **Panel 2 is −ψ(θ), the potential, not a photon count** (its own title: "L_(I|O) − L := −ψ(θ)"). Photon number per source follows
  the **magnification**, μ = 1/((1−κ)² − |γ|²) ≈ 1 + 2κ for small κ, γ (established lensing; UNVERIFIED by citation here). That is a
  second derivative of ψ, i.e. it is read from **panel 1**, and it is not plotted.
* **Panel 2 is the double integral of panel 1.** If ∇²ψ = 2κ, then ∇²(−ψ) = −2κ. Measured between the two decoded panels:
  corr(κ, ∇²(−ψ)) = −0.11, −0.35, −0.63, −0.80 after Gaussian smoothing of 3, 6, 10, 16 image pixels. The negative sign, strengthening with
  scale, is the Poisson relation showing through, and a SYNTHETIC or a real input would show it equally: it is the operator.
* **Panel 2 is dominated by one large-scale gradient:** 80 % of its variance sits at scales above 25 pixels, against 9 % for κ
  (the "ψ integrates noise into a smooth gradient" point, `REAL_RESULTS.md` R5).
* **The two dark-blue lobes of panel 1** (map ≈ (112, 22) and (120, 40); RGB (5,48,97), the bottom end of the scale, κ ≈ −0.19,
  saturated) are **negative κ: relative underdensity**. At those positions −ψ is +0.7 and +10.4 against a panel mean of +14.2:
  unremarkable, they do not stand out in panel 2. About 1.5 % of panel-1 pixels are at the darkest-blue end and 0.9 % at the
  darkest-red end: near-symmetric extremes, noise-like.
* **Reading for photons:** with μ ≈ 1 + 2κ, positive κ (red) concentrates photons and negative κ (these lobes) spreads them, the opposite
  of "photons pass through the dark spot". Only relative to the field mean (mass-sheet degeneracy). Deflections point toward positive κ.
* **What the figure can support:** the operator chain κ → ψ → α → β reproduces itself. That the path is slaved to the mass
  distribution is the premise of GR lensing, so it cannot by itself separate "shape" from "stuff". The thin-lens map has no interior
  path, so it cannot show photons "through" versus "around"; that needs the n(x) path (§10).

Two cautions carried from the audit:

1. **Kaiser–Squires is a weak-lensing linear inversion (κ ≪ 1).** A quad lens is strong-regime. The Bullet pipeline must **not** be fed
   Q2237. The route is the ψ → α → β chain run **forward** on a published lens model and checked against the measured image positions
   (CALIBRATION), and only then anything of our own (RESULT).
2. **ψ is a double integral of κ and integrates noise into a smooth gradient** (`REAL_RESULTS.md` R5). Every ψ needs its B-mode null.

**The dynamic Lagrangian** (Cody): the actual path inside the refractive index n(x) rather than the stationary-action path. This
paper has no implementation of it; defining n(x) for the lens (and the dust) is part of the missing machinery (§10).

## 7. Polarization

HYPOTHESIS (Cody): a dust/"graviton" medium scatters photons and random-walks their polarization; being in phase across the four
images would indicate that there is no "stuff" on those paths. Baseline for the comparison (UNVERIFIED, from memory, to be cited):
gravitational lensing does not itself rotate the polarization angle at the order relevant here, so a difference between images points
at the propagation medium, Faraday rotation, or microlensing of polarized source structure.

**The data inventory is negative, and is recorded as a negative:**

| band | finding (2026-10-17) |
|---|---|
| HST optical/UV | **none.** The filter lists of the 172 target-named HST observations contain no polarizer element (ACS `POL*V`, WFPC2 `POLQ`, NICMOS `POL*S`, FOC polarizers): CLEAR and F-series only (`catalog/hst_filters_by_instrument_…json`). |
| ESO | **none.** No polarimetric mode among the science frames (`dbo.raw`). |
| ALMA Band 7 | **the finest polarization-capable data found:** 0.207″, `/XX/YY/`; cross-hands not advertised, so Stokes I and Q derivable, U not. |
| VLA | unknown (pending); the quasar is radio-quiet (≈0.7 mJy), so Q/U may be a non-detection. |
| Chandra, XMM | intensity and spectra only. |
| literature | two web searches found no published polarimetry of Q2237+0305 (UNVERIFIED as a statement about the literature). |

**Consequence:** the "polarization vector field from data" has **no verified input** today. The paper cannot test its polarization claim
on the archives checked. What would change that: archive Stokes data not yet found (VLA, other ground telescopes, ALMA cross-hand
products), published polarimetry, or a new observation. Scale caution: intrinsic quasar polarization is typically small, so a
random-walk signature needs sensitivity this archive set does not show.

Foreground for any polarization measurement: Planck 353/217 GHz and Faraday-sky maps (catalog §4). On 2026-10-17 the local copies were
hash-verified identical to the SD card and removed; the copies now live on `/media/rendier/0123-4567/` (and must be retrieved from
there or re-downloaded when this step is reached).

## 8. The prediction pillar: which monad, and why no number

Cody asked for the prediction to come from the **scaled Mind's Eye boxkite monad**, with the model notated. Identification:

| item | value |
|---|---|
| file | `VAPMIP/scaled_mind_eye_boxkite_kernel_monad.py` (267 lines; "running a boxkite") |
| class | `MindEyeBoxKiteKernel` (`hub_report`, `throw_fiber`, `run_boxkite`), composing `GaugeEye`/`GaugeHands` over one `BoxKite` |
| sha256 (first 16) | `e9016cd8ac4570c9` |
| depends on | `rotary_rerun_monad.py` (`f70810dd724da978`), `19D_boxkite_context_monad.py` (`29e4c1f028390616`), `ValaQuenta/modules/box_kite/maths.py` (last commit `16db8da`) |
| repository state | VAPMIP HEAD `147e29b` (2026-10-17); ValaQuenta HEAD `fde11c1` |
| first written | 2026-09-23/24 (commit `e1f06bd`) |
| not to be confused with | `ptolemy_monad.py` (scalar boxkite, WordNet sentence context); the scalar and scaled kites are different objects |

**Status: NOT RUN, and why.**

1. Its outputs (`fixed_point_weight`, `is_zero_divisor`, `a_matrix_basin_windspeed`, `sigma_self`, the Γ companion) are defined on
   grammatical slots. There is **no mapping from any of them to an optical or polarization observable**. A prediction needs that
   mapping first, stated before any data is examined.
2. The kernel throws **static, hub-anchored fibers**, one chart at a time. Cody's corrections of 2026-10-13 say the scaled kite must
   *move* as De Marrais's kite moves under G2, and warn against inserting static functionality into it. A known kernel issue
   (`throw_fiber` b vs b+8) is recorded as unfixed in the project notes.
3. Producing a number anyway would be fabrication. Per the Fourth Age rule the prediction is committed (in `01_predictions.ipynb`)
   **before** data is examined; that cannot happen until 1 and 2 are settled.

## 9. Required controls (the lessons of the Bullet Cluster audit, applied in advance)

From `REAL_RESULTS.md` and `RETRACTED.md`: figures without generating code are orphans and are not evidence; a model comparison is not a
measurement; a test can be biased toward its own null (R2); κ and ψ were noise. So for this paper:

* **Every J gets a null that runs through the identical pipeline:** blank-sky cutouts from the same frame; the same cutout at an
  offset position; for polarization, Q/U rotated by 45° (the B-mode analogue); for ψ, the B-mode. Recorded beside the result.
* **Every figure has generating code in the repository** before it is cited.
* **Refuted claims are removed, not annotated**, and recorded once in a retraction file.
* **Provenance class on every number**, in the same sentence.
* **Pre-registration:** predictions committed before data examination.
* **Pipeline calibration first:** the forward lens model must reproduce the measured image positions before anything of ours is a RESULT.

## 10. Machinery map

| piece | state |
|---|---|
| PTorrent core: parse, preflight, Engine (`add/start/items/events`), σ-face, jexpr, `.peval` writer | **exists** (`PTorrent/core/python/ptorrent_core`) |
| regular dataset `.ptorrent` for Q2237 | **exists** (this session) |
| archive census (TAP; HST products via MAST CAOM) | **exists** as scripts + `catalog/` |
| HTTP range-read FITS header walk + cutout read | **probe only** (`probe/insitu_probe.py`); not in the core; the spec's `s3_fits` adapter is **not built** (core README: FITS/HDF5/TAP evaluation adapters not yet built) |
| `in_situ.ptorrent` format (rungs, items, bytes-read accounting, queue states) | **design only** (`PTorrent/in_situ/huchras_lens/README.md`) |
| console In Situ layer (queue right, detail bottom, `\t` focus, tabs on top) | **design discussed; nothing built**; an existing curses shell + wizard + settings is the base (`PTorrent/releases/curses/ptorrent_gui`) |
| κ→ψ→α→β chain | **exists** (`ValaQuenta/modules/l_io_photon_path`), weak-lensing only |
| forward lens model for Q2237 (published model) | **does not exist here** |
| dynamic Lagrangian L_(I|O) with a refractive index n(x) | **does not exist** |
| 2-D image ptychography (ePIE or equivalent) | **does not exist** (1-D CMB variant only) |
| PSF generator (TinyTim/WebbPSF) | **not installed** |
| Stokes Q/U data | **none found** (§7) |
| dust/"graviton" scattering model for polarization random walk | **does not exist** (Cody: to be built) |
| monad observable mapping + moving (G2) scaled kite for a prediction | **does not exist** (§8) |
| GenerationalLineage | **not yet used in this paper.** When it is, its section goes *before* its results (standing rule). |

## 11. Log of the experiment, 2026-10-17

1. Primer read (`hist_prime/PTorrent/CONTEXT_PRIMER_2026-10-17_INSITU_EVALUATION_EINSTEIN_CROSS.md`); `.clauderc_context_1` topic added.
2. Target chosen by measured citations (OpenAlex/INSPIRE); coordinates from SIMBAD.
3. Telescope census by archive query (MAST, HEASARC, ESO, ALMA); NRAO and CADC returned nothing usable.
4. Regular `.ptorrent` written and validated.
5. Polarization inventory taken: negative at every verified archive.
6. SD card `/media/rendier/0123-4567/` identified as holding a July copy of ThePlace including telescope data; `/media/rendier/Datasets`
   is gone. Five Planck/Faraday files (4.48 GiB) hash-verified identical on the card and deleted locally; local A2–A5 kept (not on the card).
7. Existing local Q2237 data found: 35 GB, drizzled, wrong class for ptychography.
8. In situ feasibility probe (§3); product-type census (§4).
9. Monad identified (§8); prediction not run.
10. Access outline written: per-archive methods, `robots.txt` verdicts, read economics (`ACCESS_OUTLINE.md`). Disclosure: several dozen
    requests were made to MAST and HEASARC endpoints before their `robots.txt` was read; recorded, and not to be repeated.
11. JWST: a web search found no JWST program on Q2237+0305, and the 36″ MAST census returned no JWST row. Not a settled finding: the
    downloader's stage `jwst` queries a 2′ radius over all instruments and records the result either way.
12. The downloader was extended **in place** (`BulletCluster/lensing_validation/download_validation_targets.py`, mode `--huchra
    {jwst,pol,hst,all}`): one stage at a time, tiered per-exposure products (not drizzled), polarimetric selection, observer
    geometry, robots verdict logged, one-download-at-a-time lock, data kept off the system partition. 15 offline tests pass
    (`test_huchra_mode.py`). It has **not** been run against MAST (MAST's wildcard `robots.txt` is `Disallow: /`).
13. Output directory `BulletCluster/huchras_lens/` and input-design directory `PTorrent/in_situ/huchras_lens/` created.

## 12. Open items, in the order they gate the paper

1. The pending telescopes (VLA, ground archives) must be queried; the HST per-exposure manifest must be paged (a cone query returned
   2 239 of 4 720 rows; the aggregate counts are complete).
2. Stokes data: does any exist? Without it §7 cannot be tested.
3. Decide the first J for a cutout and its controls (§9).
4. Define the observable mapping and the moving scaled kite before any prediction is committed (§8).
5. Build the forward lens model and pass the calibration (§6).
6. ~~Decide whether "on the server" may mean streamed ranges~~ **Settled by Cody 2026-10-17:** bounded reads into memory are allowed; staging is not.
7. Choose the `robots.txt` route for MAST and HEASARC (honour and route via the buckets; ask the helpdesks; run inside a science platform;
   or a documented-API exception, which is not compliance).

## Appendix A. ContextPlease files and context used

ContextPlease is the portable record of this project's accumulated context: the `~/.clauderc*` files, primers, skills, wikis and
references, kept so that any model can come up to speed without re-deriving them. Used here:

* primer: `claude/hist_prime/PTorrent/CONTEXT_PRIMER_2026-10-17_INSITU_EVALUATION_EINSTEIN_CROSS.md`; `claude/hist_prime/BulletCluster/CLAUDE_PRIMER.md`
* `.clauderc_context_1` (current state), `.clauderc_licenses` (licences and archive acknowledgements, created 2026-10-17), `.clauderc_citations`
* skills: `nes-viewport` (console layout), `cs-paper-code-conventions` (this draft), `walk-the-hallway` (not used for this paper)
* wikis: `claude/hist_wiki/ValaQuenta/wiki/toolbox/34_l_io_photon_path.md`; VAPMIP `docs/wiki/Scaled-Kite-English-Thought-Center-Context.md`
* in the repositories: `BulletCluster/Cleanup/{ASSESSMENT,REAL_RESULTS,RETRACTED}.md`, `BulletCluster/lensing_validation/EINSTEIN_CROSS_DATA_CATALOG.md`,
  `PTorrent/spec/ptorrent-format-v1.2.md`, `PTorrent/ptorrents/einstein_cross_q2237_alltelescopes.ptorrent`

## Appendix B. Acknowledgements and citations owed (wording to be verified at each archive before publication; see `.clauderc_licenses`)

HST/MAST (STScI), Chandra Data Archive, XMM-Newton Science Archive, ESO archive (programme IDs per frame), ALMA (`ADS/JAO.ALMA#2021.1.00675.S`),
SIMBAD (Wenger et al. 2000), VizieR, HEASARC, OpenAlex, INSPIRE; Huchra et al. 1985 AJ 90 691; Falco et al. 1996 (VLA).
