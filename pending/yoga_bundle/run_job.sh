#!/usr/bin/env bash
# run_job.sh JOB_NAME  -- download one job from jobs/JOB_NAME/manifest.json into $DATA_ROOT (default ~/TelescopeData), one file at a time, resumable.
# Restarts the downloader after a crash, waits out a network loss, holds a systemd sleep inhibitor, keeps 20 GB free.
# Environment: DATA_ROOT  MAX_MBPS (0 = no cap)  MEM_MB (downloader address-space cap, default 8192)  MIN_FREE_GB (20)
#   ./run_job.sh euclid_DESJ0408_5354          foreground      ./run_job.sh euclid_DESJ0408_5354 start    background (nohup)      ./run_job.sh NAME status
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; JOB="${1:?job name (a folder in jobs/)}"; MODE="${2:-run}"
DATA_ROOT="${DATA_ROOT:-$HOME/TelescopeData}"; MAX_MBPS="${MAX_MBPS:-0}"; MEM_MB="${MEM_MB:-8192}"; MIN_FREE_GB="${MIN_FREE_GB:-20}"
JD="$HERE/jobs/$JOB"; [ -f "$JD/manifest.json" ] || { echo "no $JD/manifest.json"; exit 1; }
PY="$HERE/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
LOG="$JD/download.log"; STATE="$JD/state.json"; PID="$JD/run.pid"; mkdir -p "$DATA_ROOT"
case "$MODE" in
  status) "$PY" - "$STATE" "$JD/manifest.resolved.json" <<'PYS'
import json,sys,os
st=json.load(open(sys.argv[1])) if os.path.exists(sys.argv[1]) else {}
m=json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else []
done=sum(1 for i in m if os.path.exists(i["dest"]) and i.get("size") and os.path.getsize(i["dest"])==i["size"])
print(f"{done}/{len(m)} files complete, {sum(i.get('size') or 0 for i in m if os.path.exists(i['dest']))/1e9:.1f} GB on disk of {sum(i.get('size') or 0 for i in m)/1e9:.1f} GB")
PYS
    [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null && echo "running (pid $(cat "$PID"))" || echo "not running"; tail -n 4 "$LOG" 2>/dev/null; exit 0 ;;
  stop) [ -f "$PID" ] && kill -TERM "$(cat "$PID")" && echo "stop requested"; exit 0 ;;
  start) nohup "$0" "$JOB" run >/dev/null 2>&1 & echo "started; $0 $JOB status"; exit 0 ;;
esac
exec 9>"$JD/.lock"; flock -n 9 || { echo "already running"; exit 4; }
echo $$ > "$PID"; trap 'rm -f "$PID"; exit 130' INT TERM
"$PY" "$HERE/prepare_job.py" "$JD" "$DATA_ROOT" | tee -a "$LOG"
fails=0
while :; do
  if command -v systemd-inhibit >/dev/null; then pre=(systemd-inhibit --what=sleep:idle:handle-lid-switch --who=telescope-job --why="download"); else pre=(); fi
  "${pre[@]}" nice -n 5 "$PY" "$HERE/telescope_download.py" "$JD/manifest.resolved.json" --state "$STATE" --min-free-gb "$MIN_FREE_GB" --max-mem-mb "$MEM_MB" --max-mbps "$MAX_MBPS" --retries 20 --trust-server-size >>"$LOG" 2>&1
  rc=$?
  case "$rc" in
    0) echo "$(date '+%F %T') job $JOB complete" | tee -a "$LOG"; break ;;
    2) echo "$(date '+%F %T') free-space guard stopped the job" | tee -a "$LOG"; break ;;
    130|143) echo "$(date '+%F %T') stopped" | tee -a "$LOG"; break ;;
    *) fails=$((fails+1)); w=$(( fails<6 ? 60*fails : 300 )); echo "$(date '+%F %T') downloader exited $rc; restarting in ${w}s (a size mismatch, a crash or the network)" | tee -a "$LOG"; sleep "$w" ;;
  esac
done
rm -f "$PID"
