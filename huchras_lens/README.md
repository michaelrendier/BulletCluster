# huchras_lens — OUTPUT directory (Huchra's Lens, Q2237+0305)

**Created 2026-10-17.** This is where results land. The INPUT side (the dataset to travel, how to travel it, what file
types exist, how each is read where it sits) is designed in `PTorrent/in_situ/huchras_lens/`.

**Design constraint (Cody, 2026-10-17):** the in situ method evaluates data where it lives (MAST and the other archives) without
staging it. This directory holds *results and records*. The one exception is `data/`: the experiment's real download, made by
`../lensing_validation/download_validation_targets.py --huchra …` while the in situ method is still being engineered (Cody's
instruction: do the experiment on this smaller dataset first). `data/` is on `/home`, is git-ignored, and is never an output.

| path | holds |
|---|---|
| `DRAFT_PAPER.md` | the cataloguing of the whole experiment; mirrored to `FourthAgePapers/HuchrasLens/DRAFT_PAPER.md` |
| `catalog/` | archive censuses taken 2026-10-17 (counts, ObsIDs, product-type inventory, filter lists). `hst_exposures_PARTIAL_…tsv` is a **partial** list (2 239 of 4 720 target-named rows) and must be re-queried with paging before use as a manifest |
| `probe_log/` | measured feasibility probes (range reads, cutout evaluation) with their honest reading |
| `data/` | the experiment's archive download (git-ignored): `jwst/`, `pol/`, `hst/` per stage; created by the downloader, not by hand |
| `peval/` | `.peval` evaluation outputs (empty: nothing evaluated yet) |
| `figures/` | figures made from `peval/` (empty) |

Neighbouring, pre-existing: `../lensing_validation/` (group-A targets; `A5_q2237+0305/` holds **35 GB of drizzled** HST mosaics,
the wrong product class for ptychography) and its `EINSTEIN_CROSS_DATA_CATALOG.md`.
