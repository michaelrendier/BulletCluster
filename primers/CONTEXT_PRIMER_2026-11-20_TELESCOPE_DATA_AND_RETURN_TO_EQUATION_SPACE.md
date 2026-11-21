# Context primer, 2026-11-20: telescope data ledger (what is used, what can go) and the way back to Equation Space

Purpose (the author's): make sure nothing we need is lost, then return to the tree rendering of Equation Space. Written at the end of a long session; read this first, then `../TODO.md`, `../DATA_VERIFIED_2026-11-20.md`, `../pending/nrao_downloads/README.md`.

## 0. Standing rules (the author's, 2026-11-20)
- **All JWST data stays** ("the JWST is too much information behind a pixel": the mosaics are each target's scaffold and the per-pixel baseline). Radio data stays (needed for ptychography). **Anything with a question about future use stays.** Nothing is deleted without the author's explicit go; I never delete from `Telescope Data`.
- **Ptychography and L_(I|O) are parked** until the gravity mapping (does the photon's path prefer compressed or uncompressed space, and which is "denser") exists to apply to the path. Dust targets get ONLY the shear and polarization fields (no ptychography). Huchra's Lens (Q2237) was dropped (no polarization); its download code stays but is unused.
- **Python:** system python is broken; every repo gets its own `.venv` (standing OK to create one with what the repo needs). Telescope work uses `BulletCluster/.venv` (has astropy, reproject, photutils, scipy, sep, scikit-image, casatools/casatasks; `requirements-witcheshat.txt`).
- **Drive:** `Telescope Data` is `/dev/sda1`, ext4, mounted `noatime`, 916 GB, 525 used, **345 GB free**. Its USB-SATA bridge dropped off the bus twice under sustained load (2026-11-17 and 2026-11-20): one heavy job at a time, `ionice -c3 nice`. `/media/rendier/SDCard` (235 GB) is empty overflow. The 750 GB "Telescope2Data" drive is not mounted.
- Telescope downloads: Mozilla user agent, one at a time, the author's go first, never send his email to NRAO, public sources only, record under `already_evaluated/`.

## 1. Data ledger (everything on `Telescope Data`, sizes of FITS from the verified inventory; 5,835 FITS, 5,830 intact, the 5 bad are truncated JWST partials in `_sd_card_orphans`)
KEEP = stays. CANDIDATE = identified as discardable under the author's test (not pertinent to ptychography AND evaluated or useless AND no doubt); **none deleted; the author has not said go.**

| data | where | size | used for | status |
|---|---|---|---|---|
| JWST, all targets | `BCData/JWST` 12.6, `BCData/JWST_scaffold_level3` 20.2, `Dust/Pillars_of_Creation/JWST_2739` 21.4, `EinsteinCrosses/HE_0435-1223` 17.8, `SDSS_J1004+4112` 6.0, `RX_J1131-1231` 0.1, `Galaxy_Controls/JWST_SPARC_IFU` 16.8, `CrabNebula` 11.8 GB | 106.9 GB | scaffolds (composites), shear fields, per-pixel baseline | **KEEP, all** (10 files are duplicated by name between `BCData/JWST` and `JWST_scaffold_level3`; kept under the rule) |
| Bullet JWST per-exposure frames | `BCData/JWST` (5 cal, 5 crf, 4 rate) | tiny | ptychography input | KEEP; about 450 more were lost in the 2026-11-04 theft and are re-downloadable from MAST (program 4598) when ptychography starts |
| Lenstool model, Bullet (Rihtarsic+2026) | `BCData/Lensing/CANUCS_Rihtarsic2026/Bullet_Cluster_lens_model.zip` | 23 GB | the published shear/kappa control (validates the shear code) | **KEEP** |
| VLA 12B-030, HE 0435 (two calibrated measurement sets) | `HE_0435-1223/VLA` | 40 GB | radio, ptychography, possible polarization | **KEEP** |
| VLA 11A-268, AH919, GBT x2 (Crab) | `CrabNebula/data/nrao` | 19 GB | Crab polarization over time | **KEEP** |
| ALMA 2023.1.00675.S (Pillars), 2018.1.01162.S (Orion), 2024.1.00291.S (HE 0435) | `Dust/*/ALMA_*`, `HE_0435-1223/ALMA` | 26 + 16 + 0.9 GB | raw ASDM, full-polarization correlations present; need CASA calibration | **KEEP** |
| MeerKAT MGCLS DR1 (Bullet, Stokes I) | `BCData/MeerKAT/MGCLS_DR1` | 1.5 GB | radio | **KEEP** |
| MeerKAT `synthetic/` (simulated Q/U, not data) | `BCData/MeerKAT/synthetic` | 1.2 GB | engine tests | KEEP (cannot confirm the code regenerates it identically) |
| HST polarizers, Crab (ACS F606W POL0V/60V/120V 2003; NICMOS POL0L/120L/240L 1997; WFPC2 POLQ 1996) | `CrabNebula/data/hst_*` | 0.6 GB | the Crab polarization map (done) | **KEEP** (the only optical polarization control; per-exposure frames) |
| HST NICMOS polarization, Orion BN/KL (prog 9752) | `Dust/Orion_BNKL_OMC1/HST_9752_NICMOS_POL` | 1.0 GB | dust polarization control (no map built yet) | **KEEP** |
| Planck 353 GHz IQU, 217 GHz IQU, Commander dust polarization, Faraday sky | `Dust/planck_foreground_validation` | 4.8 GB | real polarization over every dust target at about 5 arcmin (not yet used) | **KEEP** |
| Planck SMICA CMB, 545/857 GHz maps | `Planck/SMICA_R3.00` 2.4, `BCData/Planck` 1.2 GB | 3.6 GB | Bullet foreground work | KEEP (doubt) |
| Planck SZ tarball (already extracted next to it) | `BCData/Planck/COM_CompMap_Compton-SZMap_R2.01.tgz` | 12.2 GB | redundant source archive | **CANDIDATE after verifying the extraction is complete** (needs a full 12 GB read) |
| Chandra (Bullet, 10 ObsIDs) | `BCData/Chandra` | 0.2 GB | X-ray | KEEP |
| SPARC rotation curves | `SPARC` | 1.3 GB | galaxy controls | KEEP |
| HST, Bullet (ACS, WFC3 mosaics) | `BCData/HST` | 3.7 GB | Bullet control | KEEP |
| HST, Pillars of Creation (prog 13926): 49.6 GB mosaics + 24.9 GB per-exposure | `Dust/Pillars_of_Creation/HST_13926` | 70 GB on disk | nothing: dust gets only shear and polarization, no HST polarizers, JWST is the scaffold; no code reads it | **CANDIDATE** (re-fetch: `already_evaluated/Dust/Dust_catalog.md`) |
| HST, Q2237 drizzled mosaics (`drz`/`drc`) | `EinsteinCrosses/Q2237+0305/hst` | 36.7 GB | nothing: target dropped, mosaics are not ptychography inputs | **CANDIDATE** (re-fetch: `already_evaluated/huchras_lens_Q2237+0305/RECIPE.md`) |
| Q2237 per-exposure frames (635), support files, Chandra (40 ObsIDs), XMM (3) | same directory | 15.6 + 14.7 + 2.6 GB | the only complete per-exposure HST set: TEST DATA for the ptychography code | **KEEP** |
| HST mosaics: HE 0435 (61.4), SDSS J1004 (61.5), RX J1131 (22.8) | `EinsteinCrosses/*` | 145.7 GB | possible multi-band input for L_(I|O) later | KEEP (doubt; re-downloadable from MAST) |
| `_sd_card_orphans_2026-11-12` | drive root | 1.2 GB | contains 5 truncated JWST partials | KEEP (JWST rule) |

If the two CANDIDATE HST items (about 107 GB) went, free space would be about 452 GB (about 464 GB with the Planck tarball).

## 2. What each evaluation used (all code and results in this repository)
| result | inputs | where |
|---|---|---|
| Verified inventory | every FITS opened, size against headers | `DATA_VERIFIED_2026-11-20.md/_fits.csv`, `lensing_validation/inventory_verified*.py` |
| Scaffold composites + sidecars (sky to pixel, every PNG) | JWST `i2d` mosaics | `scaffolds/make_scaffold.py`, `regen_sidecars.py`, `bullet_scaffold.py` (Bullet was added to the gallery) |
| Shear from JWST | Bullet F200W (o001), Crab F150W2+F162M, HE 0435 F150W (jw01198-o007), Pillars F200W | `scaffolds/overlays/shear_measure.py`, `shear_cells.py`, `run_shear_all.sh` |
| Shear validation | the Lenstool zip: tangential ellipticity +0.05 to +0.07 at 30-120 arcsec, direction agreement z = 5.6 (gamma sign convention fixed from the model alone) | `shear_validate_bullet.py` |
| Crab polarization | ACS drizzled POL0V/60V/120V (same grid), NICMOS cal frames; ideal-polarizer Stokes; NICMOS agrees to 9.8 deg rms after one fitted offset | `pol_crab.py`, `CrabNebula/pol_*.json` |
| Gallery, overlays, report, zoomable SVG viewers (Pillars shear, Crab polarization) | the above | `scaffolds/gallery.html`, `overlay_report.html`, `overlays/viewers/`, `build_overlays.py`, `make_field_svg.py` |

Large temporary files lived in `/tmp` and are lost on reboot (regenerate: `shear_measure.py` takes 15-90 s per mosaic; the Lenstool maps come out of the zip with `unzip -p`).

## 3. Honest state of the results (read before reusing)
- **Pillars shear is NOT lensing:** 54% of 41,270 objects lie within 20 deg of one direction along the mosaic's pixel x-axis (111 sigma), an instrument/processing signature shared by the Crab (1.6 deg, 9 sigma) and HE 0435 (4.7 deg, 3.2 sigma); Bullet has none and passes validation. Only 3 of 309 cells deviate more than 20 deg, at faint image edges and corners, not near bright stars. Cause unknown; the six follow-up tests are in `../TODO.md`.
- **Crab polarization:** the angle zero point is ASSUMED (V3 offset -38.15 deg from two papers; a third uses -69.6); instrumental polarization (about 2%) not corrected (acstools has the corrections; its install was blocked, needs the author's OK).
- **No real polarization exists yet** for Bullet (MeerKAT is Stokes I only), HE 0435 (VLA and ALMA unreduced), or Pillars (ALMA raw).
- The drawn orientation vectors are axial (mod 180 deg): a harpoon's head side is a drawing convention.

## 4. Downloads recorded, none made
- **NRAO:** 10 requests, sizes and matching in `../pending/nrao_downloads/README.md`; keyed links only in the gitignored `links_PRIVATE.md` (master copy on the author's Desktop). Megabyte ones (AH919, AGBT19B_352, AGBT18B_338) and most of 11A-268 are on disk. **Still to download: 2,618.0 GB** in six requests (12B-380 360, 12A-486 192.4, the author's "11B-341" 920.9, 15B-252 525.0, 22B-192 494.2, 25A-385 125.5). No single drive holds them; plan = download, evaluate, discard, project by project. **The Crab project 14B-341 is not yet requested; the author will request it** (take the two 2014-11-12 blocks first). Next step when told: list each request read-only to confirm the matching and real sizes.
- **Not yet received:** more Gemini download links. JWST per-exposure frames for ptychography are to be fetched later.

## 5. Open decisions
1. The cleanup (section 1 candidates): on hold; the author said do the shear/overlay follow-ups first.
2. Pillars shear follow-up and what the deviations are (TODO).
3. Remaining SVG viewers: Bullet, Crab shear, HE 0435 (then wire into the gallery; the gallery picks up any `viewers/*.html` carrying `gallery-target`).
4. The gravity mapping for the photon path (parks L_(I|O) and ptychography).

## 6. Way back to Equation Space (the tree rendering) 
Repository: `FourthAgePapers/EquationSpace/` (its `TODO.md` has the running log); sedenion address/walk/zero-divisor code is mirrored in `SedenionSpectralRelativity/EquationSpace/` (standing rule: all sedenion I/O, hyperindexing and address code lives there). What exists: walk address faithful (3,461/3,461); the three generators A, S, G = e1, e2, e4 reach only indices 0-7, are a Fano TRIANGLE not a line, and their associator is nonzero ((AS)G = +e7, A(SG) = -e7); a fourth generator K = e8 completes the 32-element loop but its meaning (rotation or doubling) is the author's to name; the 65 Archimedes Python equations are classified by circle kind (tests 8, `14_table_65.md`); factorial rings (test 9: reading R, radius, is the natural one; V(2m) = pi^m/m!); zero divisors sit among D16 roots on exactly 42 assessors and not in E8+E8; matrix flow (the nine flows of dx/dt = Ax, each = scale + quarter turn + boost) is the 30th GenerationalLineage toolset; `unit_tree.py` is a first 3D node graph of the F = ma family (unit space and ASS space).
Next (the author's goal): the full tree (graph) of all stable equations with unit decomposition and the A/S/G decomposition, as a node-type graph where F = ma can recur (S = Q/t is entropy; force is the operator, newton the unit); give every Archimedes equation an A/S/G/K word and so an address (K assigned from behaviour), then render in 3D with the `spatial-simulation` skill (the ASS-count embedding is too coarse: use the Fano walk address); the author will run a matrix-flow pass over all the work later.
