# Huchra's Lens (Q2237+0305) — retrieval recipe
Script: `lensing_validation/download_validation_targets.py` + `run_huchra_downloads.sh` at git commit 08a8056 (BulletCluster). Target key `A5_q2237+0305`, ra 340.1258 dec 3.3578, radius 2′.
Data root: `/media/rendier/0123-4567/BulletCluster/huchras_lens/data/<stage>/`.
```
STAGES="jwst pol hst" ./run_huchra_downloads.sh      # one stage at a time; resumes from .part files
# or directly: python3 download_validation_targets.py --huchra hst --data-dir <dir> --tiers 1,2
```
Findings: stage jwst and stage pol found NO observations in MAST (2026-10-19). Stage hst: 3 697 per-exposure + drizzled files (tiers 1,2), 67.0 GB. The manifests in this folder list every filename, dataURI and size; a MAST product list can be replayed from `dataURI` without re-querying.
