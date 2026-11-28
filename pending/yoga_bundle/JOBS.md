# Job queue (run in this order, one at a time)

| # | job folder | what | files | size | where it lands under DATA_ROOT |
|---|---|---|---|---|---|
| 1 | `euclid_DESJ0408_5354` | Euclid DR1-Foundation, quad lens DES J0408-5354 (RA 62.09132, Dec -53.90026): VIS and NISP Y/J/H tile mosaics, DECam G/R/I/Z mosaics, noise and auxiliary maps (PSF catalog), VIS and NISP stacked frames with PSF files. Public IRSA archive, released 12 Nov 2026. | 80 | about 83 GB | `EuclidDR1/euclid_DESJ0408_5354/` |
| 2 | `jwst_9637_DESJ0408_5354` | JWST program 9637 on the same lens: per-exposure calibrated frames (`*_cal.fits`, 9.4 GB), level-3 mosaics (`*_i2d.fits`, 11.2 GB). Public MAST. | 164 | about 21 GB | `JWST/jwst_9637_DESJ0408_5354/` |
| 3 | NRAO Crab (only if `python3 nrao_fetch.py --probe` shows live links; see CLAUDE.md step 3) | EVLA projects 25A-385, 12A-486, 12B-380 (11A-268 optional) | | up to about 680 GB | `CrabNebula/nrao/` |

More jobs may be added later by the owner as new folders in `jobs/` (create them with `build_euclid_manifest.py` or `build_mast_manifest.py`).
