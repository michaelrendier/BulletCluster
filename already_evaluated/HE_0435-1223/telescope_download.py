#!/usr/bin/env python3
"""Resumable, memory-safe, one-at-a-time downloader with a 15-minute status line.

Standard library only (no astroquery/requests, so it runs under any python3).

    python3 telescope_download.py MANIFEST.json --state STATE.json [--min-free-gb 5] [--notify-secs 900]

MANIFEST.json is a list of {"url": ..., "dest": ..., "size": <bytes, optional>, "sha256": <optional>}.
STATE.json is written after every chunk batch; re-running the same command resumes.
Status lines go to stdout (watch with the Monitor tool) and to STATE.json.status.
Set TELESCOPE_DPRINT=1 for the dPrint feed (name = new value after each assignment).
"""
import argparse, hashlib, json, os, shutil, sys, threading, time, urllib.request, urllib.error

UA = os.environ.get("CLAUDE_UA") or ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CHUNK = 8 * 1024 * 1024          # never hold more than one chunk in memory
SLEEP_GAP = 60                   # seconds between chunks that means the machine slept
DP = os.environ.get("TELESCOPE_DPRINT") == "1"


def dp(name, value):
    if DP:
        print(f"[dp] {name} = {value!r}", flush=True)


class Reconnect(Exception):
    pass


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
    dp("have", have)
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
        if total and shutil.disk_usage(os.path.dirname(os.path.abspath(dest))).free < (total - have) + min_free:
            raise OSError(f"free-space guard: need {(total-have)/1e9:.2f} GB + {min_free/1e9:.1f} GB spare")
        last = time.monotonic()
        with open(part, "ab" if have else "wb") as f:
            while True:
                b = resp.read(CHUNK)
                if not b:
                    break
                now = time.monotonic()
                if now - last > SLEEP_GAP:
                    raise Reconnect(f"gap {now-last:.0f}s between chunks (sleep/suspend)")
                last = now
                f.write(b); f.flush()
                with prog.lock:
                    prog.bytes_done += len(b)
                have += len(b); dp("have", have)
        resp.close()
    if item.get("size") and have != item["size"]:
        raise OSError(f"size mismatch {have} != {item['size']}")
    digest = sha256_of(part); dp("sha256", digest)
    if item.get("sha256") and digest != item["sha256"]:
        raise OSError(f"sha256 mismatch {digest} != {item['sha256']}")
    os.replace(part, dest)
    return {"bytes": have, "sha256": digest}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest"); ap.add_argument("--state", required=True)
    ap.add_argument("--min-free-gb", type=float, default=5.0)
    ap.add_argument("--notify-secs", type=int, default=900)
    ap.add_argument("--retries", type=int, default=8)
    a = ap.parse_args()
    items = json.load(open(a.manifest))
    state = json.load(open(a.state)) if os.path.exists(a.state) else {}
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
        for attempt in range(a.retries):
            try:
                state[item["dest"]] = fetch_one(item, prog, int(a.min_free_gb * 1e9))
                json.dump(state, open(a.state, "w"), indent=1)
                prog.files_done += 1
                break
            except Reconnect as e:
                print(f"[reconnect] {item['dest']}: {e}", flush=True)
            except OSError as e:
                if "free-space guard" in str(e) or "mismatch" in str(e):
                    print(f"[stop] {item['dest']}: {e}", flush=True); sys.exit(2)
                wait = min(2 ** attempt * 5, 300)
                print(f"[retry {attempt+1}/{a.retries}] {item['dest']}: {e}; wait {wait}s", flush=True)
                time.sleep(wait)
        else:
            print(f"[fail] {item['dest']} after {a.retries} attempts (logged, not repaired)", flush=True)
    print(prog.line() + " DONE", flush=True)


if __name__ == "__main__":
    main()
