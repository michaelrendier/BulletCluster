# JWST scaffolds (every JWST data set on disk except the Bullet Cluster), 2026-11-17

Made by `make_scaffold.py` (algorithm in its header: level-3 mosaics reprojected to one north-up grid, chromatic assignment blue→red by wavelength, white balance, Lupton et al. 2004 asinh stretch). `raw/` = one filter alone on its own pixel grid (asinh grey, row 0 at the bottom of the sky as stored, up to 1600 px); `false_color/` = composites (`_rgb_lupton.png` sky-subtracted; `_rgb_lupton_nosky.png` the original BulletCluster algorithm without sky subtraction; `.txt` lists which filters feed blue, green and red), single-filter `_inferno.png`, and per-IFU-cube images (`_cube_thirds_rgb.png`: thirds of the wavelength axis as B, G, R; `raw/..._collapsed_raw.png`: median over wavelength).
Group = one pointing (obs id) and one instrument; groups are not combined across pointings or instruments. Mirror: `~/Desktop/SpaceClaude/BulletCluster/scaffolds/`.

| target | data | raw images | composites | single-filter | IFU cubes |
|---|---|---|---|---|---|
| CrabNebula | JWST GO 1714: MIRI 5 pointings + NIRCam F480M (F150W2+F162M mosaic now complete, 2026-11-17) | 18 | 5 | 1 | 0 |
| HE_0435-1223 | Einstein cross: NIRCam + MIRI + NIRSpec | 10 | 2 | 0 | 2 |
| NGC0300 | JWST SPARC IFU control | 4 | 2 | 0 | 0 |
| NGC0891 | JWST SPARC IFU control | 70 | 6 | 1 | 47 |
| NGC3521 | JWST SPARC IFU control | 63 | 8 | 0 | 32 |
| NGC4051 | JWST SPARC IFU control | 31 | 2 | 0 | 25 |
| NGC7331 | JWST SPARC IFU control | 44 | 2 | 0 | 38 |
| Pillars_of_Creation | JWST GO 2739 NIRCam + MIRI | 9 | 2 | 0 | 0 |
| UGC07524 | JWST SPARC IFU control | 29 | 1 | 0 | 26 |

Not rendered: the Bullet Cluster (scaffold already made, `BulletCluster/`). The Crab F150W2+F162M NIRCam mosaic was 2.66 of 8.92 GB when the Telescope Data drive reported write errors; it is not in the Crab composite.
