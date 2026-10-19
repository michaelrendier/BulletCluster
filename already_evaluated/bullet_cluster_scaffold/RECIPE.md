# Bullet Cluster JWST scaffold — retrieval recipe
Script at commit 08a8056. Target key `E2_bullet_cluster_img`, radius 10′. Full JWST manifest: 3 934 products, 235 GB (not fetched). Fetched: the 77 level-3 files only.
```
SUBDIR=bullet_cluster STAGES=jwst BUDGET_GB=30 EXTRA_ARGS="--huchra-target E2_bullet_cluster_img --only ^jw[0-9]{5}-o[0-9]+_t[0-9]+_" ./run_huchra_downloads.sh
```
Note: this was fetched before the Huchra-only queue rule; kept by request. See SCAFFOLD_FIRST.md.
