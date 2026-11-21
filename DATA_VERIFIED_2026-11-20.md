# Telescope Data drive: verified inventory, 2026-11-20

Rule as in `DATA_INVENTORY.md`: nothing is taken from a state file or a "completed" note. Scripts: `lensing_validation/inventory_verified.py` (pass 1) and `inventory_verified_pass2.py` (pass 2). Table: `DATA_VERIFIED_2026-11-20_fits.csv` (one row per FITS file).

**Result:** 5,835 FITS files under `/media/rendier/Telescope Data`; 5,830 verified (every HDU read, bytes implied by the headers match the file; gzip files by the gzip trailer size and, under 6 GB, a full CRC read). 5 failed: truncated partial JWST 4598 `i2d` files in `_sd_card_orphans_2026-11-12/` (known partials, not in any target directory). Pass 1 flagged 742 more files; all 742 were artifacts of the check (compressed versus uncompressed size on every `.gz`; a memory-map limit on scaled images) and 737 passed pass 2. Not verified by this pass: tar/tgz/zip archives (listed only), ALMA raw ASDM, VLA measurement sets.

## What is on disk, by target
| target | JWST | HST | other | per-exposure frames |
|---|---|---|---|---|
| Bullet Cluster | NIRCam 14 + 18 mosaics, NIRISS 5 | ACS 12, WFC3 4 mosaics | Chandra 10 ObsIDs, MeerKAT Stokes I (+ simulated Q/U, not data), Planck, **Rihtaršič+2026 Lenstool model (zip, 24.5 GB: κ, γ1, γ2, γ, ψ, deflection at 50 mas; multiple-image catalogues)** | JWST: only NIRCam 5 cal, 5 crf, 4 rate (about 450 lost in the 2026-11-04 theft) |
| HE 0435-1223 | NIRCam 87, MIRI 20 mosaics, NIRSpec 2 IFU cubes | ACS 30, WFC3 220, NICMOS 5 (mosaics) | ALMA 2024.1.00291.S tars, VLA 12B-030 two `.ms.tgz` (22 + 19 GB) | none |
| Q2237+0305 | none exists | 635 frames (ACS 120, WFC3 255, WFPC2 230, WFPC 38, NICMOS 51, STIS 49, FOC 22) + mosaics | Chandra 40 ObsIDs, XMM 3 observations | HST only |
| SDSS J1004+4112 | NIRCam 43 mosaics | ACS 65, WFC3 154, NICMOS 35 (mosaics) | none | none |
| RX J1131-1231 | MIRI 16 mosaics | ACS 140, WFC3 21, NICMOS 9 (mosaics) | none | none |
| Crab | NIRCam F150W2+F162M (8.92 GB, now complete) and F480M, MIRI 17 mosaics in 7 filters | ACS F606W POL0V/60V/120V: 6 flc + 3 drc; NICMOS POL0L/120L/240L (cal/ima/raw); WFPC2 F547M-POLQ 6 exposures | VLA 11A-268 two `.ms.tgz` (9.6 GB each), AH919 pipeline products only, GBT AGBT18B_338, AGBT19B_352 tars | HST polarizer frames |
| Pillars of Creation (dust) | NIRCam 6 mosaics, MIRI 3 | WFC3 108 mosaics + 176 per-exposure (no polarizer) | ALMA 2023.1.00675.S raw ASDM, full-pol correlations in its tables (XX XY YX YY) | HST WFC3 |
| Orion BN/KL (dust) | none | NICMOS prog 9752: POL0L/120L/240L, 48 visits, 144 per-exposure + 60 mosaics | ALMA 2018.1.01162.S raw ASDM, full-pol correlations in its tables | NICMOS |
| JWST SPARC IFU controls | NIRCam 22, MIRI 51 mosaics, 163 MIRI + 5 NIRSpec s3d cubes | none | SPARC 1.3 GB | none |
| Planck | | | 353 GHz I/Q/U (R3.01, 2 GB), Commander dust polarization Q/U, 217 GHz IQU, Galactic Faraday sky, SMICA CMB | |

## Corrections to earlier notes
* `DATA_INVENTORY.md` (2026-11-04) lists a citable lensing control map as "not on disk": it is now on disk (`BCData/Lensing/CANUCS_Rihtarsic2026/Bullet_Cluster_lens_model.zip`, 24,490,750,993 bytes, equal to the logged HTTP length; central directory read, CRC not tested).
* The Crab NIRCam F150W2+F162M mosaic that stopped at 2.66 of 8.92 GB on 2026-11-17 is now 8,919,956,160 bytes and passes the header-size test.
