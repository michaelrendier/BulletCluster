# Euclid — Q2237+0305 (Huchra's Lens): PENDING, wanted the day it is released

Cody, 2026-10-19: "i want that data as soon as it comes out next month."

- DR1-Foundation: November 2026 (exact date not yet announced), ~1 900 deg²: raw + calibrated images, catalogues, spectra. https://www.cosmos.esa.int/web/euclid/dr1-timeline
- Archive: ESA Euclid science archive via `astroquery.esa.euclid` (default environment PDR). The archive was reachable 2026-10-19.
- Checked 2026-10-19: public MER catalogue (`catalogue.mer_catalogue`), 5′ cone at RA 340.1258 Dec +3.3578: **0 rows**. Q1 (63 deg²) does not cover the field. Position: ecliptic latitude +10.9°, galactic latitude −46.1°; whether the wide survey reaches |β| ≈ 11° is NOT confirmed.
- The script `check_footprint.py` runs that cone search; the second query in it uses a table name that does not exist (the error is in the output) — fix it from the astroquery.esa.euclid docs before use.
- When DR1 is out: (1) re-run the cone search; (2) if covered, fetch VIS (0.1″/px) + NISP Y/J/H + slitless spectra for the field, one cross at a time; (3) log the manifest in `already_evaluated/huchras_lens_Q2237+0305/`.
- Rule: only Huchra's Lens on the queue; target folder goes under /media/rendier/0123-4567/BulletCluster/huchras_lens/.
