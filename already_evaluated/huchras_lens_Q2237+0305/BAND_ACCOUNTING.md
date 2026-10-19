# Q2237+0305 — every band, what is on record (survey 2026-10-19; metadata only, nothing downloaded)

Purpose (Cody): a full accounting from radio to gamma, to test for frequency-dependent propagation (a refractive index) or a mass-dependent surface term. Method: positional queries (r ≈ 3″–5′) to MAST, HEASARC (44 tables), VizieR (216 catalogue tables), plus the literature. Scripts and raw output: `band_survey_2026-10-19/`.
**Confirmed** = a query returned rows at the position. **Literature** = from a paper, not re-queried. **Not checked** = no query succeeded. A zero is a non-detection in THAT catalogue only.

| band | what exists | resolves the 4 images? | status |
|---|---|---|---|
| gamma | Fermi 3FGL/3FHL/FHL/LPSC/GRB/blazar, EGRET, AGILE, INTEGRAL, Swift BAT (105m, 157m, AGN, GRB), OSSE: 0 rows | n/a | non-detection in every point-source catalogue; raw event data not checked |
| hard X-ray | NuSTAR SSC, MAXI, BeppoSAX WFC/MECS: 0 rows | n/a | non-detection |
| X-ray | Chandra: 30+ obs (obsids 11534–11538 …), CSC 1.1 / 2.0 / 2.1 sources; XMM: 3 obs (0110960101, 0781210201, 0823730101), 3XMM / 4XMM-DR9…DR13 sources; ROSAT HRI pointed (3 catalogue rows); ASCA, Suzaku, Swift XRT, Einstein: 0 | Chandra yes; others no | confirmed |
| UV | GALEX (2 obs, AIS source), XMM-OM (OM serendipitous, 5 catalogue releases), HST ACS/SBC, STIS, FOC, IUE | HST yes | confirmed; HST already on card |
| optical | HST WFPC2/ACS/WFC3/STIS (card), Gaia DR3 (source + 3 epoch-photometry rows), Pan-STARRS DR1/DR2, SDSS DR9/12/16, SkyMapper DR4, APASS, UCAC/GSC, TESS, Hubble Source Catalog; ESO, CFHT, Gemini observation logs list the position | HST, Gaia (partly), AO/ground (logs only) | confirmed; ground monitoring campaigns (GLITP, OGLE) = literature, not fetched |
| near IR | 2MASS PSC, UKIDSS LAS DR9 (2 rows), HST NICMOS (card) | NICMOS yes | confirmed |
| mid IR | WISE all-sky, AllWISE, unWISE, CatWISE2020, Spitzer band-merged list (II/368) | no (6″) | confirmed |
| far IR / submm | Herschel SPIRE 250 µm point-source catalogue: 1 row (VIII/112) | no (18″) | confirmed; unexpected, worth a look |
| mm | not checked | | |
| radio | LOFAR LoTSS-DR3 raw component (J/A+A/707/A198), 144 MHz, 1 row; VLA 8.4 GHz and 1.4 GHz, MERLIN 5 GHz (literature, Falco 1996; astro-ph/0011142); NVSS, TGSS, GLEAM: 0 | VLA 8.4 GHz yes, MERLIN yes, LOFAR no (6″) | LoTSS confirmed; VLA/MERLIN holdings NOT confirmed (NRAO archive timed out) |
| HI 21 cm (lens galaxy, 1.366 GHz) | All-Digital HI catalogue row at the position (J/AJ/138/1938) — a nearby galaxy catalogue match, not yet read | no | to read |

Failed: NED photometry (parse error on the response, twice), NRAO TAP (timeout), ALMA TAP (column name), IRSA direct queries.

## What the accounting supports
- Image-by-image comparison across frequency is possible only where the telescope separates the images: HST (UV-IR), Chandra (X-ray), VLA/MERLIN (radio), partly Gaia. Everywhere else one blended flux per band.
- Known frequency-dependent effects that a refractive term must be separated from: chromatic microlensing (source size grows with wavelength), dust extinction in the lens galaxy (image-dependent), plasma dispersion in the lens galaxy (radio, ∝ ν⁻²), and intrinsic variability with time delays of a few hours.
- Candidates to fetch next, one at a time: (1) VLA 8.4 GHz + MERLIN 5 GHz visibilities, (2) Chandra evt files for the best-resolved epochs, (3) Gaia epoch photometry (3 rows, tiny), (4) Herschel SPIRE cutout. Nothing queued.
