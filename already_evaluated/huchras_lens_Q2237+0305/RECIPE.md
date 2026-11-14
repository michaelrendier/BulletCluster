# Huchra's Lens (Q2237+0305) — retrieval recipe
Script: `lensing_validation/download_validation_targets.py` + `run_huchra_downloads.sh` at git commit 08a8056 (BulletCluster). Target key `A5_q2237+0305`, ra 340.1258 dec 3.3578, radius 2′.
Data root: `/media/rendier/0123-4567/BulletCluster/huchras_lens/data/<stage>/`.
```
STAGES="jwst pol hst" ./run_huchra_downloads.sh      # one stage at a time; resumes from .part files
# or directly: python3 download_validation_targets.py --huchra hst --data-dir <dir> --tiers 1,2
```
Findings: stage jwst and stage pol found NO observations in MAST (2026-10-19). Stage hst: 3 697 per-exposure + drizzled files (tiers 1,2), 67.0 GB. The manifests in this folder list every filename, dataURI and size; a MAST product list can be replayed from `dataURI` without re-querying.

## Chandra ACIS-S (fetched 2026-10-19)
40 obsids (431, 1632, 6831–6840, 11534–11539, 12831, 12832, 13191, 13195, 13960, 13961,
14513–14518, 16316, 16317, 18804, 19638–19643, 22042), 280 primary files (evt2, bpix, fov,
asol1, eph1, images), 379 MB. Retrieve: `python3 lensing_validation/fetch_chandra_q2237.py`
(source cxc.cfa.harvard.edu/cdaftp/byobsid/{obsid%10}/{obsid}/primary/, resumable, Mozilla UA).
File lists: chandra_files.tsv, chandra_manifest.tsv. Run log completed with 0 errors.

## Re-fetch onto Telescope Data (2026-11-13 → 14)
After the 2026-11-04 loss of the Datasets drive the target was fetched again to `/media/rendier/Telescope Data/BulletCluster/EinsteinCrosses/Q2237+0305/{chandra,hst,xmm,run_state}/`.
- **Chandra:** 280 files, 316 MB, 0 errors (same obsids and method as above).
- **HST:** 3,697 files, 66.98 GB, from the MAST manifest `refetch_2026-11-14/hst_manifest.json` (each entry `{url, dest, size}`; url `https://mast.stsci.edu/api/v0.1/Download/file?uri=<dataURI>`). Run with `~/.claude/skills/telescope-download/telescope_download.py MANIFEST --state STATE --min-free-gb 20 --notify-secs 900` (Mozilla user agent; resumes from `.part` by HTTP Range). Completed 2026-11-14 01:13. Verified: 0 missing, 0 size mismatches (every entry with a known size), 60 randomly chosen files re-hashed and equal to the recorded sha256; the 38 entries with manifest size 0 are files of unknown size. Per-file state: `refetch_2026-11-14/hst_state.json.gz`; log: `hst.log`.
- **Interruption (kept):** on 2026-11-14 00:00 the (older, SATA) drive fell off the desk and was not unmounted. It re-attached as `sdc`, ext4 replayed its journal, the 3,632 files completed before the fall passed the size check and a re-hash of the 40 newest; the downloader was restarted with the same command and resumed the partial file. No file needed re-fetching. `fsck` was not run (drive mounted); SMART not available.
- **XMM-Newton (queued next, started 2026-11-14 01:22):** three public observations within 10′: 0110960101 (2002-05-28), 0781210201 (2016-11-26), 0823730101 (2018-05-19; 141.6 ks), found by an ESA XSA TAP query on `v_public_observations` (no login, no email). Products: `https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=<id>&level=ODF` and `level=PPS`; sizes are not reported before download. Manifest `xmm_manifest.json` in `run_state/`.

