# JWST scaffolds: raw | false colour

`gallery.html` is the interactive viewer (open it in a browser; it loads the images beside it). Raw and false-colour images side by side with linked zoom and pan, blink, and a filter selector; every scaffold from nine JWST targets (not the Bullet Cluster, whose scaffold is `../JWST_Bullet_Cluster_background.png`).

- `make_scaffold.py` builds the images from JWST level-3 mosaics (algorithm in its header); `make_gallery.py` + `gallery_template.html` build the viewer.
- `INDEX.md` lists every target and group. Per-image recipes are the `.txt` files in each `false_color/` folder.
- Public page: https://michaelrendier.github.io/BulletCluster/scaffolds/gallery.html
