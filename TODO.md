# BulletCluster TODO

(created 2026-11-20; the repository had no TODO file)

## Pillars of Creation shear lines: follow up, and what the deviations represent  (OPEN)
Measured 2026-11-20 on the JWST NIRCam F200W mosaic (jw02739-o001, 41,270 detected objects; viewer `scaffolds/overlays/viewers/Pillars_shear.html`).
- **The field is not lensing.** 54% of objects are elongated within 20 deg of one direction, which lies along the mosaic's pixel x-axis (global vector 0.128 at 111 sigma; real weak lensing is ~0.01-0.05). The same alignment is in the Crab field (1.6 deg from its x-axis, 9 sigma) and HE 0435 (4.7 deg, 3.2 sigma). The Bullet Cluster has none (0.03) and passes the lensing check (z = 5.6 against the published Lenstool model), so this belongs to the nebular mosaics. Cause NOT identified: row-correlated detector noise (striping), PSF/drizzle anisotropy, or real nebular structure.
- **The deviations.** Only 3 of 309 twenty-arcsec cells differ by more than 20 deg from the global direction. They sit at image edges/corners in the darkest, most dust-poor background (local brightness 4-17 against a median 19), with fewer objects sharing the global direction (51-54% against 62%). Bright-star diffraction spikes are ruled out (0% of cells within 15 arcsec of the 60 brightest sources deviate). Working reading: where the emission is faint or coverage drops, the aligned component weakens and the field reverts to the local objects' own orientations.
- **To do:** (a) compare the deviation map with the exposure/weight map (WHT) of the mosaic; (b) get JWST per-exposure cal/rate frames and measure in the detector frame (stripe power, row/column anisotropy); a roll-angle test separates detector from sky; (c) repeat in F090W, F187N, F444W and MIRI on the same field; (d) build the PSF from real stars (23,000 "stars" are nebular knots, so the PSF model is polluted) or from a model PSF; (e) mask the nebula by a continuum threshold and re-measure only the background galaxies; (f) decide whether the orientation field is a useful dust/structure map in its own right.

## Redo all shear and polarization images as zoomable SVG  (IN PROGRESS)
Vector field over the WHOLE composite (unless only a spot is covered, as for the HST polarization), thin harpoon (one-sided barb) vectors, subdued contrasting field lines behind, wheel zoom and pan, vectors and lines scale with zoom. Done: Pillars shear, Crab polarization (`make_field_svg.py`). Still to do: Bullet Cluster, Crab shear, HE 0435; then wire these viewers into the gallery. The data are axial (orientation mod 180 deg): the harpoon head side is a drawing convention, not data.

## Polarization: Crab
- Position-angle zero point (ACS: V3 offset -38.15 deg, from two papers; a third paper uses -69.6 deg) is ASSUMED; confirm against the ACS Data Handbook. Instrumental polarization (~2%) not corrected; install acstools in `.venv` for its corrections (needs the user's OK).
- The ACS field is dominated by near-vertical orientations; the NICMOS cross-check agrees (9.8 deg rms after one fitted offset) but cannot fix the absolute angle. Check whether the vertical dominance is real before using it.

## Display
- Composites are at most ~2200 px; for deeper zoom regenerate the Pillars and Crab composites at higher resolution (`OUTMAX` in `scaffolds/make_scaffold.py`).

## Data cleanup  (ON HOLD until the overlay/shear follow-ups above are done; nothing deleted)
Candidates recorded 2026-11-20 (see `DATA_VERIFIED_2026-11-20.md`): Pillars HST (70 GB), Q2237 drizzled HST mosaics (36.7 GB), possibly the Bullet Planck SZ tarball (12.2 GB, extraction not yet verified). JWST all stays; radio all stays; anything uncertain stays.

## Waiting on the author
- The Gemini `.md` of Crab and pulsar download links.

## NRAO Crab nebula and pulsar downloads  (RECORDED, NOT DOWNLOADED; EVLA LINKS DEAD 2026-11-27)
**2026-11-27: every EVLA request link returns 404; re-request in the Archive Access Tool (author's login) and use `pending/nrao_downloads/crab_fetch/` on the 891 GB laptop.** Sgr A* added as dust target D5 (`already_evaluated/Dust/Dust_catalog.md`, survey `Sgr_A_star_survey_2026-11-27.md`); first download (JWST imaging, 39.5 GB) running into `Telescope Data/BulletCluster/Dust/Sagittarius_A_star/JWST/`.

Ten requests; the three megabyte-sized ones (AH919, AGBT19B_352, AGBT18B_338) and most of 11A-268 are on disk; six gigabyte-sized EVLA requests remain, 2,618.0 GB in total (no single drive can hold them at once; the 920.9 GB one is the author's "11B-341"); the Crab project 14B-341 itself is still to be requested by the author, then add it to the record; links (private, gitignored) and methods in `pending/nrao_downloads/`. Next step when you say go: list each request read-only to get files and sizes, then download one at a time.

## Galleries open over http, not file://  (2026-11-20)
Firefox stores no favicon for `file://` pages (checked in its favicons database: none for any local file; it stored the icon for the same page served from 127.0.0.1), so a file:// gallery tab shows the globe. Open the Scaffold Gallery with `scaffolds/serve_gallery.sh` (loopback only, port 8765). Every gallery page carries the author's favicon (embedded); the same launcher pattern is used for the Equation Space Gallery (SedenionSpectralRelativity, port 8766).
