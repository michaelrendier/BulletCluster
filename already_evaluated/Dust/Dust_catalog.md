# Dust — download catalog (2026-10-25)

Purpose (Cody): test whether dust randomises the polarization of individual photons toward a random walk, as opposed to leaving field-state (aligned) polarization lines. At least 5 targets are wanted (6 acceptable); 3 are catalogued below, 2–3 more are to come from Cody. Nothing here is downloaded. Sizes were measured from MAST product lists on 2026-10-25 unless marked *not measured*.
Data root: `/media/rendier/Telescope Data/BulletCluster/Dust/<TARGET>/<TELESCOPE>/`. Rules as for the lensing directory: Mozilla user agent, one download at a time, Cody's go before any download, his email is never sent without his say-so.

| # | Target | Why it is a dust test | Polarization data that exists |
|---|---|---|---|
| D1 | Zodiacal light | interplanetary dust scattering sunlight; a whole-sky, single-scattering-dominated polarization curve | SOHO/LASCO C2/C3 polarizer sequences (+60°, 0°, −60° plus clear); STEREO SECCHI COR polarizer sequences |
| D2 | Pillars of Creation (M16) | dense dust column, both optical/IR images and sub-mm polarization | SOFIA/HAWC+ 89 and 154 µm, JCMT POL-2 850 µm (BISTRO), Planck 353 GHz. No optical polarimetry found |
| D3 | DART impact, Didymos–Dimorphos | an ejecta cloud of known start time whose optical depth falls with time, observed for months | VLT/FORS2 imaging polarimetry + spectropolarimetry, NOT/ALFOSC (pre- and post-impact); HST WFC3 polarization is not used (F350LP imaging) |
| D4–D6 | to be chosen by Cody | | |

## D1 — Zodiacal light
| telescope | what | size | access |
|---|---|---|---|
| SOHO/LASCO C3 (and C2) | polarizer-wheel sequences 1996–present, K/F separation papers use +60/0/−60 | *not measured* (FITS 1024², order 2 MB each) | NRL LASCO archive / SDAC (verify URL before the survey) |
| STEREO SECCHI COR1/COR2 | polarized sequences, F-corona at larger elongation | *not measured* | UKSSDC / NASA STEREO archive |
| Literature tables | Helios, Pioneer 10, Leinert et al. 1976, Blackwell & Petford 1966 polarization-vs-elongation | tables | papers (arXiv 2009.04820, 2202.11533 give the LASCO baseline) |
Notes: few measurements exist between roughly 14° and 21° elongation. Elongation = scattering angle, so the polarization curve is a phase function, not a column-density series. It is a single-scattering baseline for the other targets.

## D2 — Pillars of Creation (RA 18h18m51s, Dec −13°49′30″)
| telescope | what | size |
|---|---|---|
| HST WFPC2, prog 5773 (1995, the original image) | F502N, F547M, F656N, F673N; combined drz per filter, WF 56 MB + PC 13 MB | ≈ 0.35 GB (all filters, combined only); 3.9 GB with per-visit drz |
| HST WFC3 + ACS, prog 13926 (2014) | UVIS F502N/F657N/F673N, IR F110W/F160W, ACS F658N | visit-level drz/drc 15.2 GB; per-exposure flc/flt a further 35 GB |
| JWST NIRCam, prog 2739 (2022) | level-3 mosaics F090W, F187N, F200W (5.42 GB each); F335M, F444W, F444W+F470N (0.94 GB each) | 19.1 GB for all NIRCam |
| JWST MIRI, prog 2739 | F770W, F1130W, F1500W mosaics | 0.45 GB (0.15 GB each) |
| SOFIA/HAWC+ | 89 and 154 µm polarization maps (Sarkar, Looney et al. 2025) | *not measured* (Illinois databank IDB-6987399; SOFIA archive at IRSA) |
| JCMT POL-2 | 850 µm Stokes I/Q/U (Pattle et al. 2018; BISTRO) | *not measured* (CADC) |
| Planck | 353 GHz Stokes maps | *not measured* |
Minimum useful set: HST 5773 combined (0.35 GB) + HST 13926 F657N/F673N visit drc (≈ 1.4 GB) + JWST F200W + F444W + MIRI F770W (6.5 GB) + the HAWC+ and POL-2 maps. Other HST programs on the field (10533, 9091, 7216, 11981 …) are available if more epochs/filters are wanted.
"Before and after Hubble and JWST" is read here as the HST view (1995, 2014) and the JWST view (2022). If a pre-HST ground-based epoch is meant, it still needs choosing.

## D3 — DART impact (Dimorphos, 2022-09-26)
| telescope | what | size |
|---|---|---|
| HST WFC3/UVIS prog 16674 | F350LP, 290 exposures, 2022-09-26 → 2022-10-08 (ejecta evolution) | drc 5.35 GB (drz 5.35 GB; flc/flt 4.2 GB each) |
| HST WFC3/UVIS progs 17289, 17292, 17293, 17297, 17330 | F350LP, 2022-12 → 2023-07 (tail, long-term) | 282 exposures, *not measured* (≈ 1 MB-class drc per exposure scale of 16674: ≈ 5 GB) |
| JWST prog 1245 | NIRCam 24 (F070W, F322W2+F323N), MIRI IFU 12, NIRSpec 3; 2022-09-26 → 2022-12-09 | cal 0.98, i2d 0.27, s3d 3.46 GB (uncal 5.1 GB not needed) |
| VLT/FORS2 | imaging polarimetry (BVRI, mostly B and R) pre-impact to +4 months; spectropolarimetry (Bagnulo et al. 2023; Gray et al. 2024) | *not measured* (ESO archive; query by programme before download) |
| NOT/ALFOSC | B and R polarimetry (Gray et al. 2024) | *not measured* (NOT archive) |
| VLT/MUSE | spectra, 11 nights 2022-09-26 → 10-25 (Opitom et al. 2023) | *not measured* (ESO archive) |
| LICIACube | close-range ejecta plume images | *not measured* (PDS Small Bodies Node) |
Notes: published results already show the polarization dropped about 1 percentage point (blue) and 0.5 (red) after impact and kept rising with phase angle afterwards; the ejecta cloud was reported optically thin to the surface after 9.9 h (B) and 7.3 d (R). The post-impact series is a time series of falling column density, which is what a random-walk-versus-alignment test needs.

## Test definition (SUGGESTION, not adopted)
- State the prediction in numbers before reading any data: what polarization degree and angle scatter, as a function of optical depth or number of scatterings, a random walk predicts, and what the aligned-grain / single-scattering account predicts. Without this, a measured p and χ fit either story.
- The incumbent accounts: single scattering gives p(phase angle) (Mie/Rayleigh); multiple scattering depolarises; aligned grains give dichroic extinction and polarized emission along the field (the Pillars show an ordered field along the pillars in 850 µm). The test has to discriminate against all three.
- Falsification criterion to agree: which observation, in which target, would count against the random-walk claim.

## Not queued
Everything else on the fields (Spitzer, Chandra, TESS). Add on request.
