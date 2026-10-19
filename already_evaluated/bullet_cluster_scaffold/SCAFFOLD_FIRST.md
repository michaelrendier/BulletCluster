# Bullet Cluster (1E 0657-558) — JWST: build the scaffold FIRST

Note from Cody, 2026-10-18:
Use JWST's complete resolution of ALL cameras to build a scaffold "background" first and foremost.
Everything else (per-exposure frames, HST, spectra) is laid onto that scaffold afterwards.

What "scaffold pass" downloads (target E2_bullet_cluster_img, 10 arcmin radius, MAST, 2026-10-18):
  - the level-3 combined mosaics (`jwPPPPP-oNNN_tNNN_<camera>_<filter>_i2d.fits`) for EVERY filter of
    EVERY imaging camera: NIRCam (all filters) and NIRISS imaging. 23 mosaics, ~17.6 GB, plus their
    `_segm.fits` and `_cat.ecsv` companions.
  - Regex used: ^jw\d{5}-o\d+_t\d+_     (programs 4598 and 6882)

Held for later passes (not in this pass; sizes from the manifest):
  - NIRCam per-visit i2d + crf tier-2 frames ......... ~118 GB   (does not fit with the 88 GB free)
  - NIRCam tier-1 per-exposure (_cal/_rate) .......... ~99 GB
  - NIRISS imaging + WFSS, NIRSpec MSA ............... ~19 GB combined
  Full JWST manifest = 3,934 products, 235 GB.  Free space on the card is the limit, not MAST.

Where things are:
  data/jwst/ ................ downloaded files
  run_state/ ................ wrapper.log, jwst.log, jwst.done
  manifest .................. BulletCluster/lensing_validation/validation_manifest_E2_bullet_cluster_img_jwst.json
Resume: re-run the wrapper (see lensing_validation/run_huchra_downloads.sh header). Partial files resume by byte range.
