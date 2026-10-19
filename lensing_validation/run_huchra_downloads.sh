#!/usr/bin/env bash
# run_huchra_downloads.sh — Huchra's Lens (Q2237+0305) downloads to the SD card: stage jwst, then stage pol, ONE at a time.
# A restart / back-off / checkpoint wrapper around download_validation_targets.py (which keeps its own three-level checkpoint: manifest cache,
# per-file state, .part byte-range resume, PID lock, SIGTERM-safe).  This wrapper adds: a memory cap (systemd scope), low CPU/IO priority,
# waiting for the card and the network, a per-attempt time limit (a hung attempt is TERMed and resumed), exponential back-off, a free-space floor.
# Run detached:   setsid nohup ./run_huchra_downloads.sh >/dev/null 2>&1 < /dev/null & disown
# Status:         tail $ROOT/huchras_lens/run_state/wrapper.log ; python3 download_validation_targets.py --huchra jwst --status --data-dir ...
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MNT=/media/rendier/0123-4567
ROOT=$MNT/BulletCluster
DATA="$ROOT/huchras_lens/data"; STATE="$ROOT/huchras_lens/run_state"
MEM_MAX="${MEM_MAX:-2G}"; MEM_HIGH="${MEM_HIGH:-1500M}"; BUDGET="${BUDGET_GB:-100}"; MAX_TRIES="${MAX_TRIES:-25}"; ATTEMPT_LIMIT="${ATTEMPT_LIMIT:-7200}"
UA="${CLAUDE_UA:-Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0}"
mkdir -p "$DATA" "$STATE"
LOG="$STATE/wrapper.log"
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
exec 9>"$STATE/wrapper.lock"; flock -n 9 || { echo "wrapper already running"; exit 0; }
log "wrapper start pid $$ (mem max $MEM_MAX, budget ${BUDGET} GB, stages: jwst pol)"
for stage in ${STAGES:-jwst pol}; do
  [ -f "$STATE/$stage.done" ] && { log "stage $stage already done"; continue; }
  tries=0
  while [ "$tries" -lt "$MAX_TRIES" ]; do
    until mountpoint -q "$MNT"; do log "card not mounted; sleeping 120 s"; sleep 120; done
    free_gb=$(df --output=avail -BG "$MNT" | tail -1 | tr -dc 0-9)
    if [ "${free_gb:-0}" -lt 5 ]; then log "free space ${free_gb} GB below the 5 GB floor; stopping"; exit 3; fi
    until curl -sI -m 20 -A "$UA" https://mast.stsci.edu/ >/dev/null 2>&1; do log "network or MAST unreachable; sleeping 120 s"; sleep 120; done
    tries=$((tries + 1)); log "stage $stage attempt $tries"
    systemd-run --user --scope --quiet -p MemoryMax="$MEM_MAX" -p MemoryHigh="$MEM_HIGH" -p CPUQuota=70% -- \
      timeout -s TERM -k 60 "$ATTEMPT_LIMIT" nice -n 15 ionice -c3 \
      python3 "$HERE/download_validation_targets.py" --huchra "$stage" --data-dir "$DATA" --tiers 1,2 --budget-gb "$BUDGET" >> "$STATE/$stage.log" 2>&1
    rc=$?
    if [ "$rc" -eq 0 ]; then touch "$STATE/$stage.done"; log "stage $stage finished (rc 0)"; break; fi
    shift_n=$(( tries > 5 ? 5 : tries )); back=$(( 30 * (2 ** shift_n) )); [ "$back" -gt 900 ] && back=900
    log "stage $stage rc=$rc; backing off ${back} s"; sleep "$back"
  done
  [ -f "$STATE/$stage.done" ] || log "stage $stage gave up after $tries attempts (state kept; rerun resumes)"
done
log "wrapper finished"
