# BulletCluster — Session Context Primer
# Read this at the start of every new session.
# Last updated: 2026-06-30

## What this project is

Ainulindale / PtolemyHolcus σ=½ ZD boundary experiment.
The Bullet Cluster (1E 0657-558) is the test bed for the **Abrikosov Lattice dark matter hypothesis**:

- Dark matter = Abrikosov vortex (zero-divisor / wave / |Ψ|=0 core)
- Baryonic gas = condensate (|Ψ|≠0, electromagnetically coupled)
- The collision = Meissner-Abrikosov phase separation

**The prediction (zero free parameters, set before seeing real Q/U):**
- If DM = vortex (wave): NO Faraday screen at DM peaks → RM(DM)/RM(gas) < 0.95
- If DM = plasma (particle): Faraday screen present → RM(DM)/RM(gas) ≥ 0.95

Engine verified on synthetic: wave=0.861, particle=0.967. Threshold=0.95.

---

## Directory layout

```
/media/rendier/0123-4567/ThePlace/BulletCluster/     (was: bullet_cluster)
├── README.md                     full project description
├── CLAUDE_PRIMER.md              THIS FILE
├── .gitignore                    excludes large data files
├── *.png                         all generated visualizations (committed)
├── *.svg                         topology overlays (committed)
├── holcus_sigma.py               Holcus prime hash experiment
├── holcus_sigma_result.txt       all key terms → γ₀,γ₁,γ₂ (Δ=0)
├── download_bullet_cluster.py    original data download script
├── jwst_resume_download.py       RESUMABLE JWST download (run in background)
├── engine/
│   ├── bullet_engine.py          orchestrator
│   ├── modules/
│   │   ├── constants.py          fixed values, NO free params
│   │   ├── synthetic.py          Q/U cube models (wave + particle)
│   │   └── transect.py           measurement pipeline
│   ├── ptorrent/
│   │   ├── ptorrent.py           full pipeline (--real for real data)
│   │   └── sarao_download.py     SARAO/IDIA retrieval
│   ├── notebooks/                00-06 analysis notebooks
│   └── output/                   diagnostic_summary.json
├── radio/meerkat/
│   ├── MGCLS_DR1/                Stokes I ONLY — 2.7 GB (NOT committed)
│   └── synthetic/                Q/U cubes (committed — small)
├── mm_sz/planck/
│   └── COM_CompMap_YSZ_R2.01/   milca_ymaps.fits (577 MB, NOT committed)
├── optical/
│   ├── jwst/4598/                PARTIAL — F444W 288 MB / 13.7 GB total
│   └── hst/10200/                PARTIAL — j90702020 stalled
├── xray/chandra/                 merged_xray.fits (NOT committed)
├── gamma/                        gamma data (NOT committed)
└── viewer/
    ├── index.html                multi-layer viewer (localhost:8888)
    └── layers/                   all PNG layers (committed)
```

---

## ⚠ ENVIRONMENT — USE THE VENV (2026-08-14)

**All telescope data work runs in `.venv`. Do not use the system python for it.**

```bash
source env.sh      # activate
./env.sh check     # verify the stack imports
```

**Why:** the system Python has numpy 2.4.6 (pip, `~/.local`) shadowing numpy
1.26.4 (apt), and every apt-built C extension is still linked against 1.x. Six
packages were **unimportable**: `bottleneck`, `numcodecs`, `zarr`, `reproject`,
`aplpy`, `pandas` — plus `scikit-learn`, and `NLTK` (the 2026-08-06 primer already
recorded NLTK as broken for this reason; it is the same fault, not a separate one).
pip refuses to repair it in place — PEP 668, externally managed.

Fix applied: the five apt packages that astropy uses only as **optional
accelerators** were removed (zero functional loss — they could not be imported
anyway); everything else lives in the venv.

Verified working in `.venv`: numpy 2.5.2 · scipy 1.18.0 · matplotlib 3.11.1 ·
astropy 8.0.1 · astroquery 0.4.11 · pandas 3.0.5 · sklearn 1.9.0 ·
reproject 0.21.0 · photutils 3.0.0 · regions 0.12 · numcodecs 0.16.5

**CIAO** is *not* installed and is not needed for morphology. Install it (conda,
userspace, no sudo) only if exposure maps, vignetting correction, background
subtraction, or spectral/flux work are required.

---

## X-RAY — CHANDRA MAP BUILT (2026-08-14)

`xray/bullet_chandra_0.5-7keV.fits` + `.png` — **576.6 ks, 1,013,663 counts**,
all 10 ObsIDs merged onto a common 2″/pix WCS grid. The bullet's bow shock and
cold front are cleanly resolved. Scripts: `xray/make_chandra_map.py` (build),
`xray/plot_chandra_map.py` (quicklook — imports matplotlib/scipy **before**
astropy deliberately).

⚠ **Exposure-weighted COUNTS mosaic, not surface brightness.** No exposure map,
no vignetting correction, no background subtraction, no point-source removal.
**Adequate for morphology and correlation. NOT adequate for photometry,
temperature, or flux.** Use CIAO `merge_obs`/`fluximage` if flux is ever needed.

**Purpose — the shape test.** Does the polarization gradient track the *X-ray gas*
(real Chandra data) or the *NFW model* placed at `DM_NW`/`DM_SE` in
`constants.py`? Those two are **spatially separated** — that separation is the
entire published Bullet Cluster result — so they are cleanly distinguishable:

```
gradient tracks X-ray  -> CONVERGENT: eye and algorithm found the same real feature
gradient tracks NFW    -> CIRCULAR:   it is synthetic.py's injection
```

Note `The_Bullet_Cluster-defined.png` (the hand-drawn constraint band) is **never
read by any code** — verified by grep. It cannot have leaked into any output.

---

## ADDENDUM 2026-08-14 — five nulls, one cause

> ⚠ **POLICY WITHDRAWN 2026-08-17.** This read: *"Addenda, not corrections. Every prior
> result stands as written; these sit beneath them."*
>
> **That policy was the fault.** These nulls **do** refute earlier claims, and leaving those
> claims in place — annotated but present — meant they kept being read as results for weeks,
> including by later Claude sessions working from this directory. A refuted claim left in a
> file is still a claim, to a human skimming and to any automated reader ingesting the tree.
>
> **The rule now:** when a measurement refutes a claim, the claim is **removed** from the
> live files and preserved once in [`Cleanup/RETRACTED.md`](Cleanup/RETRACTED.md).
> Failures stay in the **code** — that part was right. Refuted **claims** do not stay in the
> **docs**.

**Formal spec written: [`L_IO_SPECIFICATION.md`](L_IO_SPECIFICATION.md)** — each
step of L_(I|O), its prerequisites, its regime of validity, and the mandatory
null for each. Read it before reading a result out of any step.

### N1. kappa is noise dominated — E/B = 1.023
`xray/kappa_EB_test.py`. Lensing produces **E-mode only**; B-mode (shear rotated
45°) carries no lensing signal by construction.
```
rms(kappa_E) 0.07186    rms(kappa_B) 0.07023    ratio 1.023
P_E/P_B across k: 2.33, 0.98, 1.65, 1.55, 2.12, 0.81  -> scatter, no peak
correlation length  E 6.0 px   B 7.0 px
```
The pipeline reproduces the shipped `kappa.npy` to **1.11e-16**, so this is the
same map, not a reimplementation. **The blob field is smoothed shape noise.**
This does *not* refute wave DM — it says this map cannot test it.

### N2. psi is INTEGRATED noise — the smooth gradient is the operator
`xray/lio_vs_ptychography.py`. `psi_k = −2 kappa_k / k²`; the `1/k²` manufactures
a large-scale gradient from any input.
```
psi rms        E 14.054   B 19.412   E/B 0.724   <- B LARGER than E
psi peak-peak  E 75.114   B 77.310   E/B 0.972
power in 3 lowest k   psi_E 0.893  psi_B 0.945   (kappa_E 0.133)
```
**89% of psi's power is in three wavenumbers.** The slingshot map's middle panel
is a guaranteed artefact of ∇⁻², not the Fermat potential emerging from data.

### N3. Emission does not track L_(I|O)
All |z| < 2 against a shift null, and **E and B agree throughout**:
```
emission vs kappa_E  r=0.0376 z=1.34      kappa_B  r=0.0367 z=1.32
emission vs psi_E    r=0.0151 z=0.24      psi_B    r=-0.1333 z=-1.87
emission vs |alpha|_E r=-0.0223 z=-0.71   |alpha|_B r=0.0436 z=1.04
```
The visual agreement between ptychography and L_(I|O) is not present as a
correlation. Two maps dominated by one large-scale mode look aligned regardless.

### N4. Shape test inconclusive — the main halo is off-field
`xray/kappa_vs_xray_vs_nfw.py`. Neither template preferred (X-ray z = −1.98,
NFW z = −1.30); the templates *are* separable (X-ray vs NFW r = 0.277), so the
method has power.
```
DM NW  px=(76.6, 84.8)  ** OUTSIDE **  (ny = 78)
DM SE  px=(123.7, 12.6) inside, 12 px from the edge
```
Reference mosaic is **one tile** — 5.66′ × 2.51′. The test was asked to find a
halo not in the image.

### N5. Radio halo shows no preferred scale
`radio/halo_spectral_and_power.py`, real MeerKAT L-band, 10 planes 996.6–1656.2 MHz.
```
spectral index  alpha median -1.55, 16-84% [-3.42, -0.67]   (synchrotron) -> bullet_spectral_index.fits
P(k) ~ k^-1.22 over 170-2002 kpc;  largest excess +1.91 sigma at 417 kpc
```
No pond surface. ⚠ Two caveats: the slope is **shallower than Kolmogorov**
(-3.67), so noise contributes; and **15″ = 67 kpc/beam while fuzzy-DM structure
is ~1 kpc** — two orders of magnitude too coarse. This test cannot reach the
predicted scale.

### THE SINGLE CAUSE
N1–N4 are one disease: **single-tile footprint, DM_NW off-field, too few
background galaxies.** kappa noisy → psi integrated noise → every correlation
meaningless. Not four independent failures.

**Pre-registered thresholds for the re-run** (scripts rerun unchanged):
`psi_E/psi_B` **>> 1** (now 0.724) and `kappa` E/B **>> 1** (now 1.023). Only then
are steps 5–9 worth attempting.

### Also settled
- **The hand-drawn constraint never entered the pipeline.** `grep`: no code reads
  `The_Bullet_Cluster-defined.png`. It cannot have leaked into any output.
- **The MeerKAT Q/U cubes are synthetic**, generated by `synthetic.py` which
  injects ΔRM *at the DM peaks*. Any polarization-gradient shape agreeing with
  `DM_NW`/`DM_SE` is circular **by construction of the test harness** — which is
  correct practice for a harness, and only a problem if its output is read as a
  finding.
- **Chandra map built**: `xray/bullet_chandra_0.5-7keV.fits`, 576.6 ks,
  1,013,663 counts, all 10 ObsIDs. Exposure-weighted counts, not surface
  brightness — morphology only.
- **Flexion is not computable from existing products.** `source_extract.py`
  keeps only E1/E2 (second moments). Flexion needs **third** moments and is the
  one focusing observable that works in the weak regime.
- **Download bug fixed**: `get_product_list()` on all 292 observations at once
  hung for ~7 h at 0% CPU, 0 files written. Now batched (15/call) with retry.

---

## TODO — Prioritised

### CRITICAL — blocks the science result

- [ ] **Real MeerKAT Stokes Q/U cubes**
  - MGCLS DR1 has NO Q/U for Bullet Cluster (Stokes I only)
  - **Option A**: Register at idia.ac.za → requestExport the 4 Q+U product files (~4 GB)
    - Auth: Keycloak OIDC, email=the.wandering.god@gmail.com
    - CBIDs: 1714520847, 1729849518, 1731635518, 1746534518 (S-band + UHF, 2024/2025)
    - GraphQL: https://archive.sarao.ac.za/graphql
    - Mozilla UA required: Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0
  - **Option B**: Email MGCLS PI directly
    - PI: Tiziana Venturi, INAF Bologna (tiziana.venturi@inaf.it)
    - Request: Bullet Cluster Q/U cubes from MGCLS DR1 or newer observation
    - Cite: testing zero-free-parameter wave DM prediction (Faraday rotation ratio test)
  - When Q/U arrives: drop in radio/meerkat/, run engine/ptorrent/ptorrent.py --real

- [ ] **Run RM ratio on real data when Q/U lands**
  - Expected result (Abrikosov prediction): ratio < 0.95
  - Engine ready — just needs real Q/U input

### HIGH — optical completeness

- [ ] **JWST Program 4598 — complete mosaic**
  - jwst_resume_download.py is running in background (nohup)
  - Target: all 14 filters, ~13.7 GB total
  - F444W was at 288 MB when stalled — resume script handles partial files
  - State tracked in jwst_download_state.json — survives power loss
  - When complete: regenerate viewer/layers/optical_jwst.png

- [ ] **HST Program 10200 — complete j90702020**
  - j90702020_drz.fits was last incomplete file
  - Resume: python3 download_bullet_cluster.py --hst or via MAST direct
  - When complete: regenerate viewer/layers/optical_hst.png

### MEDIUM — enhanced analysis

- [ ] **Real κ map at high resolution → Δκ fringe extraction**
  - Have NFW model (dm_topography.png, Clowe+2006)
  - Need: high-res convergence from full JWST weak lensing catalog
  - Subtract NFW → look for interference rings (lcdrm_polarization_map.png top-right)
  - Second independent test of wave vs particle DM

- [ ] **Laplacian shell spacing measurement**
  - dm_laplacian_topo.png shows ∇²κ zero-crossing shells
  - Even spacing → wave/ΛCDRM; exponential decay → NFW/CDM
  - Measure shell spacings on current κ map

- [ ] **THERMAL IMAGING of the L_(I|O) photon paths — density buffer, not escape time**
  *(added 2026-08-14, Cody. This is a rendering change, not a physics change.)*
  - **The problem:** the current temperature-sweep gradient colours by *escape
    velocity* — one scalar per pixel, "how fast do I leave". Monotone gradients hide
    interior structure by construction.
  - **The fix:** colour by **how many times a photon path crosses each pixel**.
    An accumulation buffer over trajectories, not a per-pixel escape time:
    ```
    escape time  ->  how fast do I LEAVE?   scalar per pixel   (current)
    density      ->  where do I DWELL?      accumulation buffer (wanted)
    ```
  - **Prior art, and it is exact:** this is the **Buddhabrot** (Melinda Green, 1993) —
    render by accumulating the density of points visited by orbits rather than by
    escape-time colormap. The **Nebulabrot** variant drives R/G/B from different
    iteration budgets and reads as a genuine thermal image.
  - **Why it matters here specifically:** an escape-time render of a lensing field
    shows the *deflection*. A density render shows the **caustic surface itself** —
    caustics are exactly where many paths pile onto the same pixel. Phase 20
    (parallax: four eyes, two caustics, line focus) is already about caustics; this
    is the instrument that makes them directly visible instead of inferred.
  - **Implementation:** for each source pixel, integrate the L_(I|O) path and
    increment every cell it crosses. Hottest pixel = most crossings = caustic.
    Do NOT normalise per-path — the whole signal is the pile-up.
  - **Why L_(I|O) and not a plain Lagrangian:** a start/stop Lagrangian gives only
    endpoints. L_(I|O) carries the whole bent path, so it is the only object here
    with a trajectory to accumulate. The density render is what *uses* the extra
    information L_(I|O) was built to carry.
  - Cross-ref: `VAPMIP/.claude/scratchpad/2026-08-13_apex_path/` (the same
    escape-vs-density distinction found in the cam sweep), Ainulindale/wiki/82
    (`l_io_photon_path`), Ainulindale/wiki/85 (the apex path).

  - **ADDENDUM 2026-08-14 (Cody) — NOT JUST HOW MANY. *WHEN*.**
    *(Addendum, not a correction. The crossing-count design above stands.)*
    - The buffer must be **(x, y, t)**, not (x, y). Accumulate the crossing AND
      its arrival time. A spatial density map finds the caustic; a
      time-resolved one measures the **time delays**, which is the observable.
    - **Precedent: SN Refsdal** (Kelly et al.), in MACS J1149.5+2223 — the first
      multiply-imaged supernova. Four images in an Einstein cross around a
      cluster elliptical, seen Nov 2014. Lens models predicted a reappearance
      elsewhere in the cluster potential; it was **detected 11 Dec 2015**, as
      predicted. (Models also indicate an earlier appearance in the 1990s that
      nobody was watching for.) Named for Sjur Refsdal, who proposed measuring
      H0 from a lensed supernova's time delays in **1964** — the method waited
      fifty years for its source.
    - **Multiple timescales in ONE system**: days-to-weeks between the four
      cross images (galaxy-scale potential), ~1 year to decades between cluster
      -scale images. A time-resolved buffer captures all of them at once.
    - ⚠ **THE IDENTIFICATION — L_(I|O) *IS* THE FERMAT POTENTIAL, EXACTLY.**
      Standard lensing arrival time:
      ```
      t(θ) ∝ [ ½|θ − β|²  −  ψ(θ) ]        <- the FERMAT POTENTIAL
                \_______/    \____/
                 clean L      the bend
      L_(I|O)  =     L      −  ψ_Fermat
      ```
      Not an analogy — the same expression. Consequences:
        * **Images form at ∇t = 0** — the stationary points of L_(I|O).
          So an Einstein cross is L_(I|O)'s stationary set, made visible.
        * **The time delays ARE the values of L_(I|O)** at those points.
          Four images = four samples of the functional, from one source.
        * Image parities (minimum / saddle / maximum) are the catastrophe
          classification — cf. Ainulindale/wiki/74, *Lagrangians are
          catastrophe theory*. Morse: n_min − n_saddle + n_max = 1, so a
          "4-image" cross is really 5 with one demagnified near the centre.
    - **Why this beats the transect for our purposes:** the transect is defined
      from the DM band midpoint — a model-dependent choice, so the observer
      picks the sampling. In a lensed system **the lens geometry picks it**, and
      the source is its own control. No source model is assumed.
    - Ties to the dynamic path integral (discussion 2026-08-14): a time-resolved
      buffer is the action-density profile along the path, which is precisely the
      quantity a total-action formalism integrates away.

- [ ] **Band coherence on real shear catalog**
  - band_coherence.png currently on model/synthetic
  - When full JWST mosaic complete: run on real background galaxy ellipticities
  - 450 background galaxies already detected in partial F277W data

### LOW — polish

- [ ] **IDIA registration** (idia.ac.za / ilifu.ac.za) when on good connectivity
- [ ] **Wiki pages** — create per claim list (see README.md)
- [ ] **Regenerate optical layers** once full data arrives
- [ ] **Blender visualisation** of Abrikosov vortex structure on DM topography

---

## Engine diagnostic — VERIFIED WORKING

```python
cd /media/rendier/0123-4567/ThePlace/BulletCluster/engine
python3 bullet_engine.py

# Results (deterministic, fixed seed):
# Wave model:     ratio = 0.861  →  NO FARADAY SCREEN  ✓
# Particle model: ratio = 0.967  →  SCREEN DETECTED    ✓
# Threshold: RM_RATIO_THRESHOLD = 0.95
```

## Key fixes made in prior session (DO NOT revert)

1. transect.py — transect direction was PERPENDICULAR (wrong), fixed to ALONG merger axis
2. transect.py — RA sign: d_ra = -sin(PA)*half/cos(dec)  [East = -RA]
3. transect.py — diagnostic: RM(DM)/RM(gas) ratio (not ΔRM which gave false positive)
4. transect.py — _proj sign matches sample_points convention (NW=positive)
5. transect.py — gas reference: exact interpolated value, not window median
6. synthetic.py — turbulence: 8→2 rad/m²/px (beam-averaged ICM scale)
7. synthetic.py — DM screen scale: 1.5'→0.4' (projected NFW r_s for bullet sub-cluster)
8. constants.py — RM_RATIO_THRESHOLD = 0.95 added

## Key constants (DO NOT change without physics justification)

```
RA0  = 104.6098   DEC0 = -55.9446   (X-ray centroid)
DM_NW = (104.6383, -55.9252)        (Clowe+2006 Table 1)
DM_SE = (104.5726, -55.9563)
GAS_NW = (104.625, -55.930)         (Markevitch+2002)
GAS_SE = (104.569, -55.961)
MERGER_PA_DEG = 135.0               (NW→SE position angle)
RM_RATIO_THRESHOLD = 0.95
```

## SARAO archive access

```
GraphQL:  https://archive.sarao.ac.za/graphql
Auth:     Keycloak OIDC
Email:    the.wandering.god@gmail.com
Status:   NO IDIA groups yet (skasa.groups=[]) → requestExport destination blocked
CBIDs:    1714520847, 1729849518, 1731635518, 1746534518 (S+UHF, 2024/2025)
Products: 13,926 total, 3.15 TB — need only Q+U cubes (~4-8 files, ~4 GB)
UA req:   Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0
```

## Ainulindale cross-references

- wiki/32 — Superconducting Medium (dark energy = superconducting current)
- wiki/72 — Cosmic Telescope (primes = mirror segments; zeros = lens)
- wiki/75 — Abrikosov Lattice (formal identification; Nobel 2003; the Lock)
- wiki/73 — Why σ=½ (six engines; Abrikosov Lattice as corollary)
- AbrikosovTree/README.md — prime factorization tree, ZD cascade, Zeta Index

## Git / GitHub

```
Remote:  https://github.com/michaelrendier/BulletCluster
Branch:  main
Local:   /media/rendier/0123-4567/ThePlace/BulletCluster/
```

Large data files are gitignored (*.fits, *.tgz, raw TIF).
All generated images and engine code are committed.
