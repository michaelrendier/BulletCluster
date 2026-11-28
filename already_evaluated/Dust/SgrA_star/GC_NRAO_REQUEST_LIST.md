# Galactic Center (Sgr A*) NRAO full-polarization projects to request (2026-11-27)

Source: NRAO TAP query (`survey_fullpol.py`), full-polarization rows (RL/LR) within 1.2′ of Sgr A*, EVLA and VLA; ALMA listed below. Dates are observation dates. **Sizes are unknown until requested**: request per project and look at the size NRAO reports before accepting; ask for calibrated products where offered. Cm-band polarization here traces synchrotron emission and Faraday rotation (the magnetic field), not thermal dust; it serves as the Galactic Center magnetic-field control. These are the cleanest time series.

## EVLA (request these first, in this order)

| # | project | rows | observed | bands (cm) | configuration | why |
|---|---|---|---|---|---|---|
| 1 | 13A-534 | 3491 | 2013-06-30 to 2014-02-22 | 1.95, 3.46 | A, B, C | 8 months, A/B/C configurations: the largest multi-epoch, multi-configuration full-polarization set (the projects' science goals were not looked up; they are chosen by coverage) |
| 2 | 14A-209 | 2907 | 2014-04-25 to 2015-02-20 | 0.69, 1.95, 3.46 | A, B, D | 10 months, three bands (0.7, 2, 3.5 cm), A/B/D: the second multi-epoch set |
| 3 | BY143 | 1452 | 2018-09-21 to 2018-10-27 | 0.69, 3.46 | D | Sep-Oct 2018, D configuration (D configuration favours extended emission), 0.7 and 3.5 cm |
| 4 | 18A-416 | 1030 | 2018-03-04 to 2018-04-23 | 0.75, 3.54 | A | 2018, A configuration, 0.75 and 3.5 cm |
| 5 | 22A-327 | 910 | 2022-05-28 to 2022-06-12 | 1.03, 1.66, 2.48 | A | 2022, A configuration, 1.0 to 2.5 cm (recent epoch) |
| 6 | 23A-079 | 735 | 2023-01-30 to 2023-04-18 | 0.75, 1.03, 1.66 | B | 2023, B configuration, 0.75 to 1.7 cm |
| 7 | 12A-339 | 768 | 2012-05-18 to 2012-08-04 | 0.77, 1.11, 1.61, 2.46 | B, CnB | 2012, B/CnB, 0.8 to 2.5 cm (early EVLA wideband) |
| 8 | 14B-154 | 658 | 2015-02-26 to 2015-03-31 | 0.75, 1.48, 3.69 | B | 2015, B, 0.75 / 1.5 / 3.7 cm |
| 9 | 25A-314 | 248 | 2025-04-04 to 2025-04-09 | 0.75, 1.03 | D | 2025, D configuration, 0.75 and 1.0 cm (latest short-spacing epoch) |
| 10 | 26A-153 | 241 | 2026-04-22 to 2026-04-30 | 3.54 | A | April 2026, A configuration, 3.5 cm (most recent) |

## Older VLA (decades of baseline; request one or two for the long time series)

| project | rows | observed | bands (cm) |
|---|---|---|---|
| AB1127 | 771 | 2004-06-11 to 2004-09-04 | 0.69 |
| AY185 | 1176 | 2008-05-05 to 2008-07-26 | 0.69, 1.33, 3.53 |
| AP355 | 822 | 1997-10-20 to 1997-10-27 | 0.69, 2.0 |
| AZ136 | 339 | 2001-10-03 to 2003-01-04 | 0.69, 1.33, 2.0, 3.53 |
| AY176 | 611 | 2007-04-01 to 2007-04-04 | 0.69, 1.33 |
| AY178 | 453 | 2007-07-20 to 2007-09-09 | 0.69, 1.35 |

## ALMA (non-VLBI; millimetre: thermal dust and magnetised gas)

| project | rows | observed | wavelength (cm) |
|---|---|---|---|
| 2013.1.00764.S | 292 | 2015-04-08 to 2015-05-28 | 0.13 |
| 2023.1.01064.P | 1298 | 2024-04-26 to 2024-04-27 | 0.71 |
| 2022.1.01293.P | 1030 | 2023-04-29 to 2023-04-30 | 0.34 |
| 2024.1.01044.P | 636 | 2025-04-20 to 2025-05-01 | 0.71 |

Not listed on purpose: the ALMA projects ending in `.V` (VLBI phasing runs for the Event Horizon Telescope campaigns) and all VLBA/GMVA data (VLBI). EHT is deferred to the last PTorrent in situ targets.

## How to request
In the NRAO Archive Access Tool, search by project code, select the execution blocks you want and submit; each request gets an e-mail with a keyed link. Send the e-mails (or links) over and the files can be listed and downloaded one at a time on the laptop with `nrao_fetch.py --add-link`. For a first test take 14A-209 or BY143.
