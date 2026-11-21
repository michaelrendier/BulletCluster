#!/bin/bash
# sequential, low priority; each step re-checks the drive.  2026-11-20
cd "$(dirname "$0")"; PY=../.venv/bin/python
S=/tmp/claude-1000/-home-rendier-Projects-ThePlace/913a7f31-70a3-4996-99ab-97326909a85f/scratchpad
D="/media/rendier/Telescope Data"
ionice -c3 nice $PY regen_sidecars.py $S CrabNebula "$D/CrabNebula/data"
sleep 20
ionice -c3 nice $PY regen_sidecars.py $S HE_0435-1223 "$D/BulletCluster/EinsteinCrosses/HE_0435-1223"
sleep 20
ionice -c3 nice $PY regen_sidecars.py $S Pillars_of_Creation "$D/BulletCluster/Dust/Pillars_of_Creation"
sleep 20
ionice -c3 nice $PY bullet_scaffold.py
echo ALL_DONE
