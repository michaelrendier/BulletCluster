# NRAO requests for the Crab control set, version 2 (2026-11-17): nebula AND pulsar polarization over time
Select these in the Archive Access Tool (Title Text: crab). I never send your email or login anywhere; you pass the links, I check real sizes, then download one at a time. Free space on this drive: ~366 GB, so anything over ~100 GB I flag first.

## 1. Nebula, full polarization (time series 2006–2014)
| project | instrument | epochs | bands | blocks | note |
|---|---|---|---|---|---|
| 12B-380 | EVLA | 2012-11-26, 11-27 | 14.2 cm | 2 | same band, two days |
| 12A-486 | EVLA | 2012-07-14 → 08-26 | 6.5 cm (Crab J2000, 08-20 and 08-26) | 3 | one block is likely a 3C144 calibrator: keep, it calibrates |
| 11A-268 | EVLA | 2011-05-12, 2011-07-10 | 1.3 / 7 cm | 2 | smaller; earlier epoch |
| 14B-341 | EVLA | 2014-10-19, 10-21, 11-12 (×2) | 2.2, 1.7, 9.1, 23.5 cm | 4 | **take the two 2014-11-12 blocks (9.1 and 23.5 cm) first**; the 2.2/1.7 cm blocks are very large; if the portal only offers the whole project, tell me the size before you queue it |
| AH919 | VLA | 2006-09-30 → 2007-03-21 | (check) | 6 | oldest radio epoch, pulsar + nebula with Integral; check pol states on the portal |

## 2. Pulsar polarization over time (new in v2)
| project | instrument | epochs | bands | blocks | what it is |
|---|---|---|---|---|---|
| AH919 | VLA | 2006-09 → 2007-03 | | 6 | (same project as above) |
| 15B-252 | EVLA | 2016-01-02, 01-05, 01-06, 01-07, 01-11 | 14.9, 7.4, 4.9 cm | 5 | interpulse low→high frequency; five frequencies in ten days |
| 22B-192 | EVLA | 2022-12-18, 12-29 | 3.5 / 3.7 / 7.5 cm | 2 | new emission components |
| 25A-385 | EVLA | 2025-03-31, 04-04, 04-08 | 3.5 / 3.7 cm (8–12 GHz) | 3 | PI N. Lewandowska: DM and polarimetry of single pulses |
| AGBT19B_352 | GBT | 2020-02-14 → 02-17 | | 2 | high-time-resolution polarimetry of the pulsar |
| AGBT18B_338 | GBT | 2018-09-28 | | 1 | broadband giant pulses (optional; check for Stokes products) |

## 3. More Crab-pulsar EVLA blocks that are in the archive but not in a project whose title contains "crab"
Found by position in the NRAO TAP (full polarization). Search the portal by Source Name `Crab` / `B0531+21` / `PSR B0531+21` / `0534+2200`, or by date; I do not have their project codes.
2011-11-10 (2 blocks, 5.6 cm, 'Crab pulsar') · 2017-01-16 (2 blocks, 3.5 cm, PSR B0531+21) · 2023-08-24 (6.5 / 7.5 cm, B0531+21) · 2024-06-14 and 2024-07-04 (14.2 cm, 0534+2200) · 28 cm 'Crab' blocks 2019-11-21, 2020-05-31, 2021-09-19/20, 2022-03-21, 2022-04-09.
Together with section 2 the pulsar epochs run 2006, 2011, 2016, 2017, 2020, 2022, 2023, 2024, 2025.

## 4. Optical pulsar polarization (already on disk)
The HST ACS F606W-POL0V/60V/120V exposures of 2003-08-08/09 contain the pulsar (the Moran et al. 2013 data); WFPC2 1996 and NICMOS 1997 also. No download needed.

## 5. Skipped (agreed)
BL182, BM439 (VLBA), 14B-373 (370 MHz shell: check pol states if wanted), ALMA 2012.1.01099.S / 2015.1.00188.S / 2016.1.00123.S, and the 3C144 / Taurus A calibrator blocks (listed only as calibration).


## Sizes of the delivered requests (the author, 2026-11-17/18; recorded 2026-11-20)
12B-380 360 GB (basic measurement set, uncalibrated) · 12A-486 192.4 GB · 11A-268 21.4 GB (19.29 GB on disk) · 14B-341 920.9 GB (the author wrote "11B-341") · AH919 179.1 MB (on disk) · 15B-252 525.0 GB · 22B-192 494.2 GB · 25A-385 125.5 GB · AGBT19B_352 16.5 MB (on disk) · AGBT18B_338 31.3 MB (on disk). Still to download: 2,618.0 GB. Request numbers and the matching to projects: `../../pending/nrao_downloads/README.md`.
