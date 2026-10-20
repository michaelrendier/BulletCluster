# NRAO archive holdings within 0.1° of Q2237+0305 (queried 2026-10-19)

Query: NRAO TAP `https://data-query.nrao.edu/tap/sync`, table `tap_schema.obscore`, cone r = 0.1° at RA 340.1258 Dec +3.3578, Mozilla user agent. 334 rows = 21 distinct execution blocks
(`nrao_holdings_2026-10-19.csv`). `access_estsize` is in kB (IVOA); sizes below are the archive's estimate for the whole execution block, not a measured download.

| program | array / config | band | epoch (MJD) | blocks | est. size per block | resolves the 4 images (1.8″ cross)? |
|---|---|---|---|---|---|---|
| 20B-080 | VLA A (+2 BnA→A) | 8–11.9 GHz | 59179–59275 (8 epochs, 389 s each, 2.3″ from target) | 8 | 39.7–42.9 GB (total 336 GB) | yes (~0.2″ beam) |
| 2021.1.00675.S | ALMA C43-5 | 288–300 GHz | 59798 | 1 | 9.04 GB | yes |
| AF293 | VLA A | 8.41–8.46 GHz | 49894 (1995) | 1 | 98.1 GB (archive estimate) | yes (this is the Falco 1996 data) |
| AG186 | VLA B | 1.46–1.51 GHz | 46173 | 1 | 23.4 GB | no (~4″ beam) |
| PERLEY | VLA D | 1.5–15 GHz | 45985 | 1 | 3.1 GB | no |
| BS270, BS275 | VLBA | 1.38–1.50 GHz | 58333–58522 | 3 | 2.4, 3.6, 5.0 TB | yes (mas) |
| AB825 | VLA C | 1.37 GHz | 50680–50683 | 3 | ~245 GB each, pointing 124″ off | no |
| AB1122, VLASS4.1 | VLA | 8.4 / 2–4 GHz | 53051, 60934, 60968 | 3 | 118 GB / ~565 GB each, pointings 184–326″ off | not pointed at the lens |

Whole holding ≈ 13.5 TB. Fits in 68 GB free: ALMA (9 GB) + one VLA 20B-080 A-config epoch (≈ 43 GB) = ≈ 52 GB.

**Download route:** the `access_url` of every row is the NRAO portal (`https://data.nrao.edu/portal/#/productViewer/<id>`). The portal's download form is a workflow that REQUIRES the user's email
(`emailNotification`, "User Email (required)") and mails a retrieval link. Not run: the user's email is not sent to an outside service without being told to.
