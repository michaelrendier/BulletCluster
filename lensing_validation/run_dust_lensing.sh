#!/usr/bin/env bash
# Chained: dust (group D, 4.5 GB) first, then the lensing quads EXCLUDING A1.
# Sequential because the script holds a PID lock against concurrent instances.
cd "$(dirname "$0")"
echo "=== [$(date -Is)] START group D — Planck dust polarization (4.5 GB) ==="
python3 download_validation_targets.py --group D
echo "=== [$(date -Is)] START group A quads (A1 EXCLUDED — 910 GB, needs Cody's call) ==="
python3 download_validation_targets.py \
    --target A2_sdss_j1004+4112 --target A3_rxj1131-1231 \
    --target A4_he0435-1223     --target A5_q2237+0305 \
    --budget-gb 120
echo "=== [$(date -Is)] RUNNER DONE ==="
