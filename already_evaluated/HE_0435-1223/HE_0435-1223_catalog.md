# HE 0435−1223 — download catalog (2026-10-22)

Target RA 69.56208° Dec −12.28722° (04ʰ38ᵐ14.9ˢ −12°17′14″), quad lensed quasar z≈1.69, lens z≈0.45, sparse field with a few neighbours.
Data root: `/media/rendier/Telescope Data/BulletCluster/EinsteinCrosses/HE_0435-1223/<TELESCOPE>/`. One script per telescope sits beside this file.
Rules: Mozilla user agent on every request; ONE download at a time, in the order below; nothing runs without Cody's go; user email is never sent anywhere without his explicit say-so.
Sizes were measured from the MAST product lists / NRAO TAP on 2026-10-22. Downloaded 2026-10-22: HST, JWST, ALMA (below); VLA pending an NRAO account.

| # | Telescope | Script | What | Size | Status |
|---|---|---|---|---|---|
| 1 | **JWST** (imaging scaffold) | `download_JWST.py` | whole level-3: NIRCam F150W/F115W (1442 MB each), F277W/F356W (344 MB each), MIRI F560W/F1280W/F1800W/F2550W i2d (37.8 MB each), NIRSpec IFU G140M/F100LP s3d (62.8 + 40.9 MB), x1d, catalogs, segmentation maps | **4.37 GB** (28 files) | **DONE 2026-10-22 11:16** |
| 2 | HST | `download_HST.py` | ACS/WFC F814W + F555W drc (326.7 MB each), WFC3/IR F160W (21.4) + F140W (26.2) drz, point/segment catalogs | **0.71 GB** (12 files) | **DONE 2026-10-22 11:00** |
| 3 | VLA / EVLA | `download_VLA.py` | 12B-030, C band 4.7–6.5 cm, full polarization RR RL LR LL, two execution blocks (MJD 56226, 56240) | **≈ 47.4 GB** (archive estimate: 25.5 + 21.9) | pending: NRAO portal needs an account + email |
| 4 | ALMA (optional) | `download_ALMA.py` | 2024.1.00291.S, 11 member blocks, 0.87–3.38 mm, XX/YY only (no polarization products) | **0.95 GB** (21 files; public DataLink URLs, no email; 7 member OUS, README + product tar + auxiliary tar each) | **DONE 2026-10-22 11:45** |

## JWST detail
GO-1198 (NIRCam ×4 filters; NIRSpec IFU G140M/F100LP, observations o008 + o012) and GO-2046 (MIRI ×4 filters). NIRISS: no public observation. No JWST imaging polarimeter exists.
Plate scales: NIRCam SW 0.031″/px, LW 0.063″/px; mosaic 10442×4932 px (SW). The target is inside every mosaic. `--cutout --half 45` gives 128/128/31/31 MB (90″ box) if time matters.
Not fetched: uncal / rate / cal / per-detector i2d (tens of GB).

## HST detail
Programs 9744 (ACS), 12889 (WFC3/IR F160W), 13732 (WFC3/IR F140W + G141). No polarizer (POL) data in the field. Not fetched: WFC3/UVIS F275W (programs 11732, 12324, 13113), G141 grism, flt/raw/ima.

## Radio detail
- VLA 12B-030 is the only full-polarization radio data in the field. NRAO TAP `access_estsize` is an archive estimate for the whole execution block, not a measured download.
- Also in the cone, not queued: VLBA BS275D (RR only, 19.9 cm, ≈ 3.5 TB estimate).
- ALMA rows carry only XX, YY. Use only if sub-mm continuum helps the ptychography; otherwise skip.

## Files beside this catalog
`he0435_common.py` (shared helpers, HTTP-Range cutouts), `telescope_download.py` (resumable whole-file downloader), `nrao_holdings_2026-10-22.csv`, `alma_holdings_2026-10-22.csv`.
Run `python3 download_<TELESCOPE>.py --dry-run` (JWST/HST) or `--list` (VLA/ALMA) for read-only sizes.

## Data acknowledgement (NRAO)
The National Radio Astronomy Observatory and Green Bank Observatory are facilities of the U.S. National Science Foundation operated under cooperative agreement by Associated Universities, Inc. (also in `BulletCluster/NOTICE`; any paper using the VLA 12B-030 data must carry it).
