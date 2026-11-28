#!/usr/bin/env bash
# fetch_crab.sh -- run nrao_fetch.py under a restart loop so it survives a crash of the script, a dropped network and (with `install-service`)
# a reboot of the machine. One download at a time; checkpoints and resume are in nrao_fetch.py (.part files + Range + atomic state).
#
#   ./fetch_crab.sh                start (foreground); safe to run again after any interruption
#   ./fetch_crab.sh start          start in the background (nohup); log in $DEST/fetch_crab.log
#   ./fetch_crab.sh status         what is done, partial, expired; free space; is it running
#   ./fetch_crab.sh stop           ask it to stop (state is saved first)
#   ./fetch_crab.sh install-service   a systemd user service that restarts after a reboot (needs: loginctl enable-linger $USER, once, with sudo)
# Environment: EXTRA_ARGS (e.g. "--only 14A-209 18A-416")  DEST (default ~/CrabNebula/data/nrao)  BUDGET_GB (700)  MIN_FREE_GB (20)  MAX_MBPS (0 = none)  NICE (5)  MEM_MAX (6G, needs systemd-run)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${DEST:-$HOME/CrabNebula/data/nrao}"
BUDGET_GB="${BUDGET_GB:-700}"; MIN_FREE_GB="${MIN_FREE_GB:-20}"; MAX_MBPS="${MAX_MBPS:-0}"; NICE="${NICE:-5}"; MEM_MAX="${MEM_MAX:-6G}"
PY="$HERE/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
mkdir -p "$DEST"; LOG="$DEST/fetch_crab.log"; PIDFILE="$DEST/fetch_crab.pid"
ENGINE=("$PY" "$HERE/nrao_fetch.py" --run --dest "$DEST" --budget-gb "$BUDGET_GB" --min-free-gb "$MIN_FREE_GB" --max-mbps "$MAX_MBPS" --nice "$NICE" ${EXTRA_ARGS:-})
note() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG"; }

case "${1:-run}" in
  status)
    "$PY" "$HERE/nrao_fetch.py" --status --dest "$DEST"; df -h "$DEST" | tail -1
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then echo "running (pid $(cat "$PIDFILE"))"; else echo "not running"; fi
    tail -n 5 "$LOG" 2>/dev/null; exit 0 ;;
  stop)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then kill -TERM "$(cat "$PIDFILE")"; echo "stop requested; it saves its state and exits"; else echo "not running"; fi; exit 0 ;;
  start)
    nohup "$0" run >/dev/null 2>&1 & echo "started in the background; $0 status to look"; exit 0 ;;
  install-service)
    unit="$HOME/.config/systemd/user/nrao-fetch.service"; mkdir -p "$(dirname "$unit")"
    cat > "$unit" <<UNIT
[Unit]
Description=NRAO Crab fetch (resumable)
After=network-online.target
[Service]
Environment=DEST=$DEST BUDGET_GB=$BUDGET_GB MIN_FREE_GB=$MIN_FREE_GB MAX_MBPS=$MAX_MBPS NICE=$NICE
ExecStart=$HERE/fetch_crab.sh run
Restart=on-failure
RestartSec=60
[Install]
WantedBy=default.target
UNIT
    systemctl --user daemon-reload && systemctl --user enable --now nrao-fetch.service
    echo "installed. For it to run after a reboot without logging in: sudo loginctl enable-linger $USER"; exit 0 ;;
esac

exec 9>"$DEST/.fetch_crab.lock"; flock -n 9 || { echo "another fetch_crab.sh is already running"; exit 4; }
echo $$ > "$PIDFILE"; trap 'rm -f "$PIDFILE"; [ -n "${CHILD:-}" ] && kill -TERM "$CHILD" 2>/dev/null; exit 130' INT TERM
wrap=()
command -v ionice >/dev/null && wrap+=(ionice -c2 -n4)
command -v systemd-inhibit >/dev/null && wrap=(systemd-inhibit --what=sleep:idle:handle-lid-switch --who=nrao-fetch --why="download in progress" "${wrap[@]}")
if command -v systemd-run >/dev/null && systemd-run --user --scope -p MemoryMax="$MEM_MAX" true 2>/dev/null; then wrap=(systemd-run --user --scope -q -p MemoryMax="$MEM_MAX" -p MemorySwapMax=0 "${wrap[@]}"); fi
fails=0
while :; do
  until curl -s -o /dev/null --max-time 10 -A "Mozilla/5.0" https://dl-dsoc.nrao.edu/ ; do note "network down; waiting 30 s"; sleep 30; done
  note "starting engine (restart count $fails)"
  "${wrap[@]}" "${ENGINE[@]}" >>"$LOG" 2>&1 & CHILD=$!
  wait "$CHILD"; rc=$?; CHILD=""
  case "$rc" in
    0)   note "all selected requests are done"; break ;;
    2)   note "disk guard stopped the run: free space is below ${MIN_FREE_GB} GB. Make room and run again."; break ;;
    3)   note "nothing usable is left: the remaining requests are expired or blocked. See the log; re-request in the NRAO Archive Access Tool, then: python3 nrao_fetch.py --add-link ID URL"; break ;;
    4)   note "another engine holds the lock"; break ;;
    130) note "stopped"; break ;;
    *)   fails=$((fails+1)); wait_s=$(( fails < 6 ? 30 * fails : 180 )); note "engine exited with $rc (crash, OOM or kill); restarting in ${wait_s} s"; sleep "$wait_s" ;;
  esac
done
rm -f "$PIDFILE"
