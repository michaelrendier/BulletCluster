#!/bin/bash
# sequential, low-priority; one mosaic at a time (the Telescope Data bridge has dropped under load before)
cd "$(dirname "$0")"
PY=../../.venv/bin/python
run() { ionice -c3 nice $PY shear_measure.py "$1" "$2" "$3" "/tmp/claude-1000/-home-rendier-Projects-ThePlace/913a7f31-70a3-4996-99ab-97326909a85f/scratchpad" "$4"; }
run "/media/rendier/Telescope Data/BulletCluster/EinsteinCrosses/HE_0435-1223/legacy_2026-08/jw01198-o007_t005_nircam_clear-f150w_i2d.fits" HE0435_F150W HE_0435-1223 20
run "/media/rendier/Telescope Data/BulletCluster/Dust/Pillars_of_Creation/JWST_2739/jw02739-o001_t001_nircam_clear-f200w/jw02739-o001_t001_nircam_clear-f200w_i2d.fits" Pillars_F200W Pillars_of_Creation 20
run "/media/rendier/Telescope Data/CrabNebula/data/jwst_nircam_scaffold/jw01714-o006_t005_nircam_f150w2-f162m_i2d.fits" Crab_F150W2_F162M CrabNebula 20
