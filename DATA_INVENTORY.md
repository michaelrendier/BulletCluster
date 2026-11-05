# Bullet Cluster — telescope data inventory (verified 2026-11-04)

**Rule for this file:** nothing here is taken from a "completed" note. Every FITS file under the data root was opened (all HDUs) and its length checked
against the length its headers imply; JWST and HST were also compared with the MAST product list. Machine-readable result:
`ContextPlease/claude/scratchpad/2026-11-04_bullet_inventory/validate_BCData.csv`. Chandra, MeerKAT and Planck were checked for structure only (no archive sizes were available).

**Data root** (one setting, `bc_paths.py`, env `BC_DATA_ROOT`): `/media/rendier/Telescope Data/BulletCluster/BCData/`
The `/media/rendier/Datasets` drive (which the old `optical/*`, `xray/chandra`, `radio/meerkat`, `mm_sz/planck` symlinks pointed at) was **stolen 2026-11-04**; those symlinks are dead.
The SD card (`/media/rendier/0123-4567`) still holds the old copies and is not touched.

## On disk and verified
| data | files | verified | notes |
|---|---|---|---|
| JWST level-3 mosaics, programs 4598 + 6882 (`JWST_scaffold_level3/data/jwst/`) | 23 `i2d` (14 NIRCam 4598 = 13.7 GB, 3 NIRISS 4598; 4 NIRCam + 2 NIRISS 6882) + `segm`, `cat` | valid, sizes match the MAST list | the complete science mosaic set |
| JWST 4598 `JWST/4598/mastDownload/` | 36 valid files | partial download; **6 truncated/partial files deleted 2026-11-04** | the old `jwst_download_state.json` said 495 files complete; ~450 were on the stolen drive. Per-exposure frames are not needed for the paper (shear uses the mosaics). |
| HST program 10200 (`HST/10200/`) | 4 ACS `drz` (F606W ×2 pointings, F814W, F435W), 219 MB each | valid | `j90702020`, once noted as stalled, is complete |
| HST 10863, 11591, 10200 combined, 11099 (`HST/…`) | 12 files, 2.83 GB | **download started 2026-11-04**, manifest `HST/_manifest_2026-11-04.json` | see `HST/_download_2026-11-04.log` |
| Chandra (`Chandra/`) | 10 ObsIDs: 554, 3184, 4984–4986, 5355–5358, 5361 (evt2, asol, bpix, fov, image) | valid | the ObsIDs in `download_bullet_cluster.py`; the CDA was not queried for others |
| MeerKAT MGCLS DR1 (`MeerKAT/MGCLS_DR1/`) + two catalogues | Stokes I only | valid | `MeerKAT/synthetic/` (1.2 GB) is **simulated, not data** |
| Planck (`Planck/`) | MILCA y-map, 545 and 857 GHz maps | valid | |

## Not on disk
* **Real radio polarization (Stokes Q/U).** Blocking the paper's prediction. Leads, from a read-only survey (2026-11-04):
  * **MeerKAT MGCLS** observed 115 clusters in full polarization (−80° < Dec < 0°); the DR1 public products here are Stokes I; the visibilities are in SARAO's archive (the tape request the author is sending).
  * **ASKAP/POSSUM** (CASDA obs ASKAP-51927, 0.8–1.09 GHz) has Stokes I, Q, U, V cubes (≈ 200 GB each) and a small **polarisation component catalogue (0.03 GB)** for this field; **RACS** full-polarization visibilities (XX/XY/YX/YY) for the field are 0.3–0.64 GB each (RACS-mid 1.37 GHz ASKAP-67997; RACS-low ASKAP-57052; RACS-high ASKAP-36265).
    **CASDA data links return HTTP 401 (login required) — a locked door, recorded, not opened.**
  * **ATCA** (Shimwell et al. 2015; a 5.5/9 GHz full-polarization relic study) — archive location not confirmed.
* **A citable lensing-mass map as the control.** Clowe et al. 2006 (arXiv:astro-ph/0611496) states "a partial data release" at `http://flamingos.astro.ufl.edu/1e0657/` (that host does not answer now; Wayback snapshots exist, e.g. `web.archive.org/web/20100626064023/http://flamingos.astro.ufl.edu/1e0657/index.html`, but the Archive blocked this machine as bot traffic — opened by hand in a browser). Bradač et al. 2006 (arXiv:astro-ph/0608408) is the strong+weak map. The released Σ map is described as 185 × 185 pixels at 8.5 kpc/pixel (arXiv:1110.3893) and κ at 15.4 kpc/pixel (arXiv:0908.0040): sources disagree, so check the release itself.
* **Derived inputs the engine expects but are absent:** `Chandra/merged_xray.fits`, `Lensing/kappa_model.fits`, `Planck/sz_ymap_cutout.fits`, `MeerKAT/MGCLS_1E0657-558_{Q,U}_cube.fits`. (A Chandra 0.5–7 keV map is built in the repo by `xray/make_chandra_map.py`.)

## Lost with the stolen drive
About 450 of the 495 JWST 4598 per-exposure files (NIRCam cal/crf/rate/i2d; NIRSpec; NIRISS). Anything else that the dead symlinks pointed at beyond the SD copies cannot be enumerated.

## Scripts
All Bullet Cluster scripts now take their data location from `bc_paths.py` (`$BC_DATA_ROOT`). Not changed (Huchra's Lens is out of scope): `lensing_validation/run_huchra_downloads.sh`, `fetch_chandra_q2237.py`.
