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
