# already_evaluated — what has been fetched, and the exact method to fetch it again

Rule (Cody, 2026-10-19): once a target's scripts have run, its record lands here. If the data on the card is later deleted, everything needed to retrieve exactly the same files is in the target's folder. Nothing is downloaded twice. **One Einstein cross at a time.**

Each folder holds: the MAST manifests (every observation and product, with URI and size), the per-file state (`FILES.tsv` and the state JSON), the run logs, and `RECIPE.md` (exact commands). The scripts themselves live in `lensing_validation/` at the commit named in each recipe; files are NOT hashed here (68 GB), only named and sized.

| folder | target | status | files | size |
|---|---|---|---|---|
| `huchras_lens_Q2237+0305/` | Einstein Cross, 2′ radius | jwst: none exist; pol: none exist; hst: done | 3 697 | 67.0 GB |
| `bullet_cluster_scaffold/` | Bullet Cluster, 10′ radius, JWST level-3 mosaics only | done; kept by request | 77 | 20.3 GB |

Not yet evaluated (queue: Huchra's Lens only): radio (VLA 8.4 GHz, MERLIN 5 GHz), Chandra (30+), XMM (3).
