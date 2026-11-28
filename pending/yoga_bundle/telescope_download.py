#!/usr/bin/env python3
"""Resumable, memory-safe, one-at-a-time downloader with a 15-minute status line.

Standard library only (no astroquery/requests, so it runs under any python3).

    python3 telescope_download.py MANIFEST.json --state STATE.json [--min-free-gb 5] [--notify-secs 900]
        [--require-mount "/media/rendier/Telescope Data"] [--max-mem-mb 1536] [--pause-file PATH]

Fault tolerance (added 2026-11-14, after a USB-controller crash, three OOM kills and lid-close suspends):
  * STATE.json is written atomically (temp file, fsync, rename): a reset in mid-write can no longer corrupt it.
  * Every finished file is fsync'd (and its directory) before it is renamed into place and recorded.
  * After a crash the last TAIL_REWIND bytes of a .part are discarded and re-fetched (they may be unflushed or garbage).
  * --require-mount: if the target drive is not mounted the run WAITS (never writes into an unmounted mount point,
    which would fill the internal disk with a ghost directory).
  * Network down or stalled: waits for connectivity with back-off (does not use up the retries), then resumes by Range.
  * SIGINT / SIGTERM: flush, fsync, save state, exit 130 / 143. SIGSTOP/SIGCONT also work; so does the pause file:
    `touch PAUSEFILE` pauses between chunks, `rm PAUSEFILE` resumes (default PAUSEFILE = STATE.json.PAUSE).
  * Memory: one 8 MB chunk at a time; RLIMIT_AS is capped (--max-mem-mb); nice 10 and idle I/O priority.
  * Sleep: run under `run_download.sh`, which holds a systemd sleep/idle inhibitor while the download runs.

MANIFEST.json is a list of {"url": ..., "dest": ..., "size": <bytes, optional>, "sha256": <optional>}.
STATE.json is written after every chunk batch; re-running the same command resumes.
Status lines go to stdout (watch with the Monitor tool) and to STATE.json.status.
Set TELESCOPE_DPRINT=1 for the dPrint feed (name = new value after each assignment).
"""
import argparse, hashlib, http.client, json, os, resource, shutil, signal, socket, subprocess, sys, threading, time, urllib.parse, urllib.request, urllib.error

UA = os.environ.get("CLAUDE_UA") or ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CHUNK = 8 * 1024 * 1024          # never hold more than one chunk in memory
TRUST_SIZE = False               # --trust-server-size: a manifest size that disagrees with the server's Content-Length is replaced (and logged), not fatal
MAX_BPS = 0                      # --max-mbps: polite rate limit in bytes/second (0 = none)
SLEEP_GAP = 60                   # seconds between chunks that means the machine slept
TAIL_REWIND = 16 * 1024 * 1024   # bytes of a .part to discard and re-fetch after an interrupted run
STOP = threading.Event()         # set by SIGINT / SIGTERM
OPTS = {"require_mount": None, "pause_file": None}
DP = os.environ.get("TELESCOPE_DPRINT") == "1"


def dp(name, value):
    if DP:
        print(f"[dp] {name} = {value!r}", flush=True)


class Reconnect(Exception):
    pass


class Stopped(Exception):
    pass


def atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(os.path.dirname(os.path.abspath(path)))


def fsync_dir(d):
    try:
        fd = os.open(d, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    except OSError:
        pass


def mounted_ok():
    m = OPTS["require_mount"]
    return m is None or os.path.ismount(m)


def wait_gate(why=""):
    """Block while the drive is missing or the pause file exists; raise Stopped on SIGINT/SIGTERM."""
    shown = 0
    while True:
        if STOP.is_set(): raise Stopped()
        pf = OPTS["pause_file"]
        if not mounted_ok():
            if time.time() - shown > 60: print(f"[wait] {OPTS['require_mount']} is not mounted; waiting {why}", flush=True); shown = time.time()
        elif pf and os.path.exists(pf):
            if time.time() - shown > 60: print(f"[paused] {pf} exists; remove it to resume", flush=True); shown = time.time()
        else:
            return
        time.sleep(5)


def network_up(url):
    u = urllib.parse.urlparse(url); port = u.port or (443 if u.scheme == "https" else 80)
    try:
        socket.create_connection((u.hostname, port), timeout=10).close(); return True
    except OSError:
        return False


def wait_network(url):
    delay = 5
    while not network_up(url):
        if STOP.is_set(): raise Stopped()
        print(f"[net-wait] no route to {urllib.parse.urlparse(url).hostname}; retrying in {delay}s (retries not used)", flush=True)
        time.sleep(delay); delay = min(delay * 2, 300)


class Progress:
    def __init__(self, total_files, total_bytes):
        self.files_done = 0; self.total_files = total_files
        self.bytes_done = 0; self.total_bytes = total_bytes
        self.current = ""; self.t0 = time.time(); self.lock = threading.Lock()

    def line(self):
        with self.lock:
            el = max(time.time() - self.t0, 1e-9)
            rate = self.bytes_done / el
            left = (self.total_bytes - self.bytes_done) / rate if rate > 0 and self.total_bytes else float("nan")
            return (f"[status] {time.strftime('%Y-%m-%d %H:%M:%S')} files {self.files_done}/{self.total_files} "
                    f"{self.bytes_done/1e9:.2f}/{self.total_bytes/1e9:.2f} GB rate {rate/1e6:.1f} MB/s "
                    f"eta {left/60:.0f} min now {self.current}")


def notifier(prog, every, status_path):
    def run():
        while True:
            time.sleep(every)
            s = prog.line(); print(s, flush=True)
            try:
                with open(status_path, "w") as f: f.write(s + "\n")
            except OSError:
                pass
    threading.Thread(target=run, daemon=True).start()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest()


def fetch_one(item, prog, min_free):
    url, dest = item["url"], item["dest"]
    part = dest + ".part"
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    have = os.path.getsize(part) if os.path.exists(part) else 0
    if have > TAIL_REWIND:                       # discard the tail that a crash may have left unflushed
        have -= TAIL_REWIND
        with open(part, "r+b") as f: f.truncate(have)
    elif have:
        have = 0
        os.remove(part)
    dp("have", have)
    wait_gate("before starting " + os.path.basename(dest))
    req = urllib.request.Request(url, headers={"User-Agent": UA, **({"Range": f"bytes={have}-"} if have else {})})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code == 416:                       # part already holds the whole file
            resp = None
        else:
            raise
    if resp is not None:
        if have and resp.status == 200:         # server ignored Range: start over
            have = 0; dp("have", have)
        total = have + int(resp.headers.get("Content-Length", 0))
        if TRUST_SIZE and total and item.get("size") and total != item["size"]:
            print(f"[size-fix] {os.path.basename(dest)}: manifest {item['size']} -> served {total}", flush=True); item["size"] = total
        if total and shutil.disk_usage(os.path.dirname(os.path.abspath(dest))).free < (total - have) + min_free:
            raise OSError(f"free-space guard: need {(total-have)/1e9:.2f} GB + {min_free/1e9:.1f} GB spare")
        last = time.monotonic(); t_file, got_file = time.monotonic(), 0
        with open(part, "ab" if have else "wb") as f:
            while True:
                wait_gate("mid-file")
                b = resp.read(CHUNK)
                if not b:
                    break
                now = time.monotonic()
                if now - last > SLEEP_GAP:
                    raise Reconnect(f"gap {now-last:.0f}s between chunks (sleep/suspend)")
                last = now
                f.write(b); f.flush(); os.fsync(f.fileno())
                with prog.lock:
                    prog.bytes_done += len(b)
                have += len(b); dp("have", have)
                got_file += len(b)
                if MAX_BPS:                      # polite: keep the average rate under the cap
                    ahead = got_file / MAX_BPS - (time.monotonic() - t_file)
                    if ahead > 0:
                        time.sleep(ahead); last = time.monotonic()
        resp.close()
        if total and have < total:                # connection dropped mid-file: retryable, not corruption
            raise ConnectionError(f"short read {have}/{total} bytes (connection closed early)")
    if item.get("size") and have < item["size"]:
        raise ConnectionError(f"short read {have}/{item['size']} bytes")
    if item.get("size") and have != item["size"]:
        raise OSError(f"size mismatch {have} != {item['size']}")
    with open(part, "rb") as f: os.fsync(f.fileno())
    digest = sha256_of(part); dp("sha256", digest)
    if item.get("sha256") and digest != item["sha256"]:
        raise OSError(f"sha256 mismatch {digest} != {item['sha256']}")
    os.replace(part, dest)
    fsync_dir(os.path.dirname(os.path.abspath(dest)))
    return {"bytes": have, "sha256": digest}


def main():
    global MAX_BPS, TRUST_SIZE
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest"); ap.add_argument("--state", required=True)
    ap.add_argument("--min-free-gb", type=float, default=5.0)
    ap.add_argument("--notify-secs", type=int, default=900)
    ap.add_argument("--retries", type=int, default=8)
    ap.add_argument("--require-mount", default=None, help="wait (never write) while this path is not a mount point")
    ap.add_argument("--max-mem-mb", type=int, default=1536, help="cap on address space (RLIMIT_AS); 0 = no cap")
    ap.add_argument("--trust-server-size", action="store_true", help="use the server Content-Length when it differs from the manifest size (MAST product lists are often stale)")
    ap.add_argument("--max-mbps", type=float, default=0.0, help="rate limit in megabit/s (0 = none); use on a machine in use")
    ap.add_argument("--pause-file", default=None, help="while this file exists the run pauses (default STATE.json.PAUSE)")
    a = ap.parse_args()
    MAX_BPS = int(a.max_mbps * 125000); TRUST_SIZE = a.trust_server_size
    OPTS["require_mount"] = a.require_mount; OPTS["pause_file"] = a.pause_file or (a.state + ".PAUSE")
    if a.max_mem_mb:
        try: resource.setrlimit(resource.RLIMIT_AS, (a.max_mem_mb * 1024 * 1024, resource.RLIM_INFINITY))
        except (ValueError, OSError) as e: print(f"[warn] could not cap memory: {e}", flush=True)
    try:
        os.nice(10); subprocess.run(["ionice", "-c3", "-p", str(os.getpid())], check=False, capture_output=True)
    except OSError:
        pass
    for sg in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sg, lambda n, f: STOP.set())
    items = json.load(open(a.manifest))
    try:
        state = json.load(open(a.state)) if os.path.exists(a.state) else {}
    except json.JSONDecodeError:                  # a half-written state from an older version: rebuild from the files on disk
        print("[warn] state file unreadable; rebuilding from the files on disk (finished files are re-hashed, not re-fetched)", flush=True)
        state = {}
    for i in items:                                  # adopt finished files that the state does not list (rebuilt state)
        if i["dest"] not in state and i.get("size") and os.path.exists(i["dest"]) and os.path.getsize(i["dest"]) == i["size"]:
            state[i["dest"]] = {"bytes": i["size"], "sha256": sha256_of(i["dest"])}
    total_bytes = sum(i.get("size", 0) for i in items)
    prog = Progress(len(items), total_bytes)
    for i in items:                                  # count finished files so resume reports honestly
        d = state.get(i["dest"])
        if d and os.path.exists(i["dest"]) and os.path.getsize(i["dest"]) == d["bytes"]:
            prog.files_done += 1; prog.bytes_done += d["bytes"]
    notifier(prog, a.notify_secs, a.state + ".status")
    print(prog.line(), flush=True)
    for item in items:
        d = state.get(item["dest"])
        if d and os.path.exists(item["dest"]) and os.path.getsize(item["dest"]) == d["bytes"]:
            continue
        prog.current = os.path.basename(item["dest"]); dp("current", prog.current)
        attempt = 0
        while attempt < a.retries:
            try:
                state[item["dest"]] = fetch_one(item, prog, int(a.min_free_gb * 1e9))
                atomic_write_json(a.state, state)
                prog.files_done += 1
                break
            except Stopped:
                atomic_write_json(a.state, state)
                print("[stopped] signal received; part files and state saved; rerun the same command to resume", flush=True)
                sys.exit(130)
            except Reconnect as e:
                print(f"[reconnect] {item['dest']}: {e}", flush=True)
            except (OSError, http.client.HTTPException) as e:
                if "free-space guard" in str(e) or "mismatch" in str(e):
                    print(f"[stop] {item['dest']}: {e}", flush=True); sys.exit(2)
                if not network_up(item["url"]):          # network hang or outage: wait, do not use up a retry
                    try: wait_network(item["url"])
                    except Stopped:
                        atomic_write_json(a.state, state); print("[stopped] while waiting for the network", flush=True); sys.exit(130)
                    continue
                wait = min(2 ** attempt * 5, 300)
                print(f"[retry {attempt+1}/{a.retries}] {item['dest']}: {e}; wait {wait}s", flush=True)
                attempt += 1
                time.sleep(wait)
        if attempt >= a.retries:
            print(f"[fail] {item['dest']} after {a.retries} attempts (logged, not repaired)", flush=True)
    print(prog.line() + " DONE", flush=True)


if __name__ == "__main__":
    main()
