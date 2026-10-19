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
