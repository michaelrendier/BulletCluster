# Sagittarius A* and the Galactic Center dust: read-only survey, 2026-11-27

Position RA 17h45m40.04s, Dec −29°00′28.2″. Nothing here was downloaded except the manifest in `SgrA_star/` (see the end). Queries: MAST (astroquery, radius 120″), NRAO TAP `tap_schema.obscore` (radius 0.02° = 1.2′). Purpose and scope: `Dust_catalog.md` D5. **Not EHT** (Cody, 2026-11-27: not applicable to the dust; to be studied later as one of the last PTorrent in situ targets).

## JWST
1,324 observations within 120″, in 22 programs. Public level-3 (calibrated mosaics and cubes) exist for 17 of them; JWST Sgr A* is **not resolved** (the 2 µm PSF is about 0.06″ = 60,000 µas; the horizon-scale shadow is about 50 µas). What JWST does resolve is the surroundings: the nuclear star cluster, the mini-spiral, IRS 13, IRS 3, the dust and ionized gas, and the variable point source Sgr A* itself (flare monitoring). JWST has no imaging polarimeter; MAST has no polarizer-filter data within 60″.

| program | PI, title | instrument | public level-3 | what it is for |
|---|---|---|---|---|
| 10678 | Schödel, NIRCam Legacy Survey of the Galactic Center | NIRCam F212N F480M, MIRI F770W | 4.5 GB mosaics | the wide dust and gas scaffold |
| 1939 | Lu, The Galactic Center | NIRCam F115W F212N F323N F405N F444W, NIRSpec IFU | 8.0 GB mosaics + 2.3 GB cubes | broad-band and narrow-band scaffold |
| 2235 / 3559 | Yusef-Zadeh, Sgr A* monitoring | NIRCam F210M F480M | 0.4 GB (2235); 3559 level 2 only | flares, time series |
| 4572 / 7532 / 12603 | Haggard, Hora, Michail, Sgr A* with Chandra | MIRI MRS | 4572 level 3 + level 2; 7532 level 2; 12603 not public | mid-IR spectrum of the flares |
| 1306, 2772, 4515 | van der Marel, astrometry | NIRCam | 1.7, 1.7, 3.4 GB | astrometric mosaics |
| 5368, 9257 | Do, nuclear star cluster proper motions | NIRCam F212N F480M | 3.1, 15.8 GB | multi-epoch, deep |
| 3571 | Yusef-Zadeh, YSO candidates | MIRI F560W F770W F1000W F1280W F1500W | 0.9 GB | dust emission 5.6–15 µm (the best dust spectrum of the lot) |
| 1266, 2075, 2491, 3166 | MIRI/NIRSpec IFU of the Galactic Center | cubes | 2.6, 3.1, 4.4, 3.2 GB | PAH and dust features, H₂: a later, separate list |
| 10961, 11052, 12575, 6095, 7928 | binaries, proper motions, positrons, calibration | | level 3 not public or not relevant | skipped |

## Other MAST collections within 120″
HST 1,147 observations (+ 407 HLA, 26 HLSP), Swift 1,770, ROMAN 213, TESS 2, SDSS 5, PS1 5, GALEX 1. Polarizer filters: none.

## NRAO (TAP, within 1.2′): 1,264,194 observation rows
Dominated by VLBA 0.7 cm (VLBI: not for the dust, and enormous: access_estsize sums to tens of PB), GMVA 3 mm, ALMA (100,685 rows XX/YY; 26,724 rows full-polarization XX XY YX YY, 0.1–0.7 cm) and EVLA full-polarization (RR RL LR LL) at 0.7, 2.0 and 3.5 cm (projects 14A-209, 13A-534 and others). `access_estsize` overcounts (rows are scans), so sizes are scale only. Raw visibilities are infeasible; for the dust the useful forms are calibrated images or small calibrated measurement sets of chosen EVLA and ALMA full-polarization projects, to be listed project by project (a second pass).

## Public radio and submm image products worth a look (not measured)
MeerKAT 1.28 GHz Galactic Center mosaic (Heywood+2022, 6.5 deg², 4″, with an 8″ spectral-index mosaic); ACES (ALMA CMZ Exploration Survey, 3 mm dust continuum, about 2.5″, 2026 data release, project page); Planck 353 GHz (already on disk); SOFIA/HAWC+ and JCMT POL-2 (to check). Sizes not found.

## Downloaded
`SgrA_star/manifest.json`: 118 files, **39.46 GB**, public JWST level-3 imaging (I2D + catalog) of programs 10678, 1939, 1306, 2772, 3571, 2235, 4515, 5368, 9257, destination `/media/rendier/Telescope Data/BulletCluster/Dust/Sagittarius_A_star/JWST/<program>/`. Started 2026-11-27 22:19 with the telescope-download skill (nice 19, ionice idle, 30 Mbit/s cap, one stream, 20 GB free-space guard).
