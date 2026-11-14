# already_evaluated — what has been fetched, and the exact method to fetch it again

Rule (Cody, 2026-10-19): once a target's scripts have run, its record lands here. If the data on the card is later deleted, everything needed to retrieve exactly the same files is in the target's folder. Nothing is downloaded twice. **One Einstein cross at a time.**

Each folder holds: the MAST manifests (every observation and product, with URI and size), the per-file state (`FILES.tsv` and the state JSON), the run logs, and `RECIPE.md` (exact commands). The scripts themselves live in `lensing_validation/` at the commit named in each recipe; files are NOT hashed here (68 GB), only named and sized.

| folder | target | status | files | size |
|---|---|---|---|---|
| `huchras_lens_Q2237+0305/` | Einstein Cross, 2′ radius | jwst: none exist; pol: none exist; hst: done — **data deleted 2026-11-04 (no radio resolution)**; **re-fetched to Telescope Data 2026-11-14 (HST 66.98 GB verified; Chandra 316 MB); XMM started**; records kept | 3 697 | 0 GB on disk |
| `bullet_cluster_scaffold/` | Bullet Cluster, 10′ radius, JWST level-3 mosaics only | **verified 2026-11-04** (23 `i2d` valid); now at `Telescope Data/BulletCluster/BCData/JWST_scaffold_level3/` | 77 | 20.3 GB |

Band accounting (metadata only, 2026-10-19): `huchras_lens_Q2237+0305/BAND_ACCOUNTING.md`.

Not yet evaluated (queue: Huchra's Lens only): radio (VLA 8.4 GHz, MERLIN 5 GHz; NRAO needs an email: ask first). Chandra and HST re-fetched 2026-11-14; XMM (3 observations) in progress.


**2026-11-04:** the `/media/rendier/Datasets` drive was stolen; data was centralised on `Telescope Data/BulletCluster/` (see `../DATA_INVENTORY.md`). The HE 0435-1223 holdings are `Telescope Data/BulletCluster/EinsteinCrosses/HE_0435-1223/` (JWST level-3, HST, ALMA, VLA 12B-030 full-polarization 40 GB — verified size and gzip).
