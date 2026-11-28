#!/usr/bin/env python3
"""nrao_fetch.py -- set up Python and fetch NRAO request products (Crab nebula and pulsar polarization control set), one file at a time,
checkpointed, resumable after a crash, and tolerant of network loss.  Standard library only.

    python3 nrao_fetch.py --setup                 # A. install what is needed (apt), make a venv, check the python
    python3 nrao_fetch.py --plan                  # what would be fetched under the budget, and what is skipped
    python3 nrao_fetch.py --probe                 # which request links still answer (read-only; lists files and sizes)
    python3 nrao_fetch.py --run  --dest DIR       # B. fetch (use fetch_crab.sh to run it under a restart loop)
    python3 nrao_fetch.py --status --dest DIR     # what is done, partial, expired
    python3 nrao_fetch.py --add-link ID URL       # add or replace the direct URL of one request (a fresh NRAO email link)
    python3 nrao_fetch.py --add-link ID URL --project 14A-209 --size-gb 85.3   # a NEW request (not in the built-in table): name and size as NRAO reported

The request links carry a per-request key: they live in links.txt next to this script (one `REQUEST_ID  DIRECT_URL` per line, `#`
comments) and are never printed in full. This file contains no key. Rules kept: Mozilla user agent on every request, one download at a time,
no login (a login or paywall page stops that request and is reported, never repaired), no e-mail address ever sent.
Exit codes: 0 all selected requests done, 2 disk guard stopped the run, 3 every selected request expired or blocked, 4 another run holds the lock.
"""
import argparse
import fcntl
import hashlib
import http.client
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = os.environ.get("CLAUDE_UA") or "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
CHUNK = 8 * 1024 * 1024
TRIM = 16 * 1024 * 1024            # a resumed .part is cut back by this much: the tail may not have reached the disk before a crash
FSYNC_EVERY = 256 * 1024 * 1024

# (request id, project, instrument, stated size in GB, role)   sizes are the author's, 2026-11-18; role: 'fetch' | 'have' | 'skip'
REQUESTS = [
    ("303004365", "25A-385", "EVLA", 125.5, "fetch"),     # Crab pulsar, high-frequency dispersion measure and polarimetry (2025)
    ("302964371", "11A-268", "EVLA", 21.4, "fetch"),      # Crab nebula after the giant gamma-ray flare (19.29 GB reached disk before: re-fetch to settle the 2.1 GB gap)
    ("302954368", "12A-486", "EVLA", 192.4, "fetch"),     # radio counterparts of the gamma-ray flares
    ("302944689", "12B-380", "EVLA", 360.0, "fetch"),     # contemporaneous multispectral observations (basic measurement set, uncalibrated)
    ("302986674", "AH919", "EVLA", 0.179, "have"),        # on disk already
    ("303010600", "AGBT19B_352", "GBT", 0.0165, "have"),
    ("303031735", "AGBT18B_338", "GBT", 0.0313, "have"),
    ("302994447", "15B-252", "EVLA", 525.0, "skip"),      # over the 490 GB line: later
    ("302999511", "22B-192", "EVLA", 494.2, "skip"),      # over the 490 GB line: later
    ("302969789", "11B-341?", "EVLA", 920.9, "skip"),     # the author's label; larger than the disk
]
APT_PACKAGES = ["python3", "python3-venv", "python3-pip", "curl", "ca-certificates", "p7zip-full", "util-linux"]


class Expired(Exception):
    """The request directory answers 404 (the NRAO copy has been removed) or is not a listing."""


class Blocked(Exception):
    """A login or paywall page, or HTTP 401/403: a stop, never repaired."""


class DiskGuard(Exception):
    """Free space on the destination fell under the guard."""


# ---------------------------------------------------------------- A. setup
def setup(args):
    """Install the packages and create the virtual environment; report the python in use."""
    print(f"[setup] python {platform.python_version()} at {sys.executable}")
    if sys.version_info < (3, 8):
        print("[setup] this script needs python 3.8 or newer; install python3 from your distribution and run again")
        return 1
    apt = shutil.which("apt-get")
    if apt:
        missing = [p for p in APT_PACKAGES if subprocess.run(["dpkg", "-s", p], capture_output=True).returncode != 0]
        if missing:
            cmd = (["sudo"] if os.geteuid() != 0 else []) + [apt, "install", "-y"] + missing
            print("[setup] installing:", " ".join(missing))
            if subprocess.run((["sudo"] if os.geteuid() != 0 else []) + [apt, "update"]).returncode != 0:
                print("[setup] apt-get update failed; continuing")
            if subprocess.run(cmd).returncode != 0:
                print("[setup] package install failed (no sudo, or no network): install by hand:", " ".join(missing))
                return 1
        else:
            print("[setup] packages already present:", " ".join(APT_PACKAGES))
    else:
        print("[setup] no apt-get here; make sure python3, venv, curl, ca-certificates and 7z are installed")
    venv = os.path.join(HERE, ".venv")
    if not os.path.exists(os.path.join(venv, "bin", "python")):
        print("[setup] creating", venv)
        if subprocess.run([sys.executable, "-m", "venv", venv]).returncode != 0:
            print("[setup] venv failed (python3-venv missing?)")
            return 1
    py = os.path.join(venv, "bin", "python")
    print("[setup] venv python:", subprocess.run([py, "-c", "import sys;print(sys.version.split()[0])"], capture_output=True, text=True).stdout.strip())
    print("[setup] this script needs nothing beyond the standard library; the venv keeps it apart from the system python")
    free = shutil.disk_usage(HERE).free / 1e9
    print(f"[setup] free space here: {free:.0f} GB")
    print("[setup] swap:", open("/proc/swaps").read().strip().splitlines()[-1] if os.path.exists("/proc/swaps") else "unknown")
    print("[setup] done. Next: python3 nrao_fetch.py --plan ; --probe ; then ./fetch_crab.sh")
    return 0


# ---------------------------------------------------------------- links
def load_links(path):
    """Read links.txt (or the links_PRIVATE.md of the repository): {request id: direct URL}."""
    links = {}
    if not os.path.exists(path):
        return links
    text = open(path, encoding="utf-8").read()
    for blk in re.split(r"\n## Request ", text)[1:]:                  # links_PRIVATE.md layout
        m = re.search(r"direct \(files\): (\S+)", blk)
        if m:
            links[blk.split()[0]] = m.group(1)
    for line in text.splitlines():                                     # links.txt layout
        line = line.strip()
        if line and not line.startswith("#"):
            p = line.split()
            if len(p) >= 2 and p[0].isdigit() and p[1].startswith("http"):
                links[p[0]] = p[1]
    return links


def redact(url):
    """A URL with its key part hidden, for logs and screens."""
    u = urllib.parse.urlsplit(url)
    parts = [p if (i < 2 or len(p) < 12) else "<key>" for i, p in enumerate(u.path.split("/"))]
    return f"{u.scheme}://{u.netloc}{'/'.join(parts)}"


def read_link_lines(path):
    """links.txt as {request id: [url, project or None, size GB or None, role or None]}; lines may be `ID URL` or `ID URL PROJECT GB [ROLE]`."""
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            p = line.split()
            if line and not line.startswith("#") and len(p) >= 2 and p[0].isdigit() and p[1].startswith("http"):
                out[p[0]] = [p[1], p[2] if len(p) > 2 else None, float(p[3]) if len(p) > 3 else None, p[4] if len(p) > 4 else None]
    return out


def add_link(path, rid, url, project=None, gb=None, role=None):
    """Add or replace one request in links.txt. A request that is not in the built-in table needs a project name and a size in GB
    (the size is only used to plan the budget); it is fetched like the others."""
    rows = read_link_lines(path)
    old = rows.get(rid, [None, None, None, None])
    rows[rid] = [url, project or old[1], gb if gb is not None else old[2], role or old[3]]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# REQUEST_ID  DIRECT_URL  [PROJECT  SIZE_GB  [ROLE]]   (private: each URL carries a per-request key)\n")
        for k, v in sorted(rows.items()):
            fh.write("  ".join([k, v[0]] + ([v[1], str(v[2] if v[2] is not None else 0)] + ([v[3]] if v[3] else []) if v[1] else [])) + "\n")
    os.chmod(path, 0o600)


def register_extra_requests(path):
    """Requests named in links.txt but not in REQUESTS (new NRAO e-mails) join the table with role 'fetch'."""
    known = {r[0] for r in REQUESTS}
    for rid, (url, proj, gb, role) in read_link_lines(path).items():
        if rid not in known and proj:
            REQUESTS.append((rid, proj, "EVLA" if "dsoc" in url else "GBT" if "naasc" in url else "NRAO", float(gb or 0), role or "fetch"))


# ---------------------------------------------------------------- network
def host_of(url):
    return urllib.parse.urlsplit(url).hostname


def wait_for_network(host, log, patience=None):
    """Block until a TCP connection to host:443 works; sleeps 10 s, then up to 5 min between tries. Returns False if `patience` seconds pass."""
    delay, t0, warned = 10, time.time(), False
    while True:
        try:
            socket.create_connection((host, 443), timeout=8).close()
            if warned:
                log("network is back")
            return True
        except OSError:
            if not warned:
                log(f"network or {host} unreachable; waiting")
                warned = True
            if patience is not None and time.time() - t0 > patience:
                return False
            time.sleep(delay)
            delay = min(delay * 2, 300)


def open_url(url, method="GET", headers=None, timeout=60):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


NET_ERRORS = (urllib.error.URLError, socket.timeout, ConnectionError, http.client.HTTPException, OSError)


def fetch_text(url, log, tries=6):
    """GET a directory index, retrying through network loss and server errors; 404 raises Expired, 401/403 or a login page raises Blocked."""
    for attempt in range(tries):
        try:
            with open_url(url) as r:
                body = r.read(5_000_000).decode("utf-8", "replace")
            if re.search(r"Choose Account Service|Log In|login", body[:4000], re.I) and "SHA1SUMS" not in body and "Index of" not in body:
                raise Blocked(f"a login page answered at {redact(url)}")
            return body
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Expired(f"404 at {redact(url)}")
            if e.code in (401, 403):
                raise Blocked(f"HTTP {e.code} at {redact(url)}")
            log(f"HTTP {e.code} at {redact(url)}; retry {attempt + 1}")
        except NET_ERRORS as e:
            log(f"{type(e).__name__} listing {redact(url)}; retry {attempt + 1}")
            wait_for_network(host_of(url), log)
        time.sleep(min(10 * 2 ** attempt, 120))
    raise Expired(f"no usable answer from {redact(url)} after {tries} tries")


def crawl(url, log, depth=0):
    """Every file under a request directory: [(relative path, absolute URL)]."""
    if depth > 8:
        return []
    body = fetch_text(url, log)
    out = []
    for href in re.findall(r'href="([^"#?]+)"', body):
        if href.startswith("/") or href.startswith("..") or href.startswith("http") or href.lower().startswith("index.html"):
            continue
        child = urllib.parse.urljoin(url, href)
        if not child.startswith(url):
            continue
        rel = child[len(url):]
        if href.endswith("/"):
            out += [(rel + r, u) for r, u in crawl(child, log, depth + 1)]
        else:
            out.append((urllib.parse.unquote(rel), child))
    return out


def remote_size(url, log):
    """Content-Length of a file, via HEAD (retried)."""
    for attempt in range(6):
        try:
            with open_url(url, "HEAD") as r:
                n = r.headers.get("Content-Length")
                return int(n) if n else None
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                raise Expired(f"{e.code} for a file at {redact(url)}")
            if e.code in (401, 403):
                raise Blocked(f"HTTP {e.code} at {redact(url)}")
        except NET_ERRORS:
            wait_for_network(host_of(url), log)
        time.sleep(min(10 * 2 ** attempt, 120))
    return None


# ---------------------------------------------------------------- state
class State:
    """JSON state, written atomically (temp file, fsync, rename), so a crash leaves the last complete copy."""

    def __init__(self, path):
        self.path = path
        self.data = {"version": 1, "requests": {}}
        if os.path.exists(path):
            try:
                self.data = json.load(open(path, encoding="utf-8"))
            except (OSError, ValueError):
                shutil.copy(path, path + ".corrupt")
        self.data.setdefault("requests", {})

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)
        fd = os.open(os.path.dirname(os.path.abspath(self.path)) or ".", os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def req(self, rid):
        return self.data["requests"].setdefault(rid, {"status": "pending", "files": {}})


# ---------------------------------------------------------------- one file
def sha1_of(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(CHUNK), b""):
            h.update(blk)
    return h.hexdigest()


def fetch_file(url, dest, size, args, log, stop):
    """Download one file to dest through `dest.part`, resuming by HTTP Range, retrying through network loss. Returns True when complete."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    part = dest + ".part"
    fails, eof = 0, False
    while not stop["flag"]:
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if have and not stop.get("trimmed_" + part):
            have = max(0, have - TRIM)                                 # a crash may have lost the tail of the last write
            with open(part, "r+b") as fh:
                fh.truncate(have)
            stop["trimmed_" + part] = True
        if size is not None and have >= size:
            break
        free = shutil.disk_usage(os.path.dirname(dest)).free
        need = (size or 0) - have
        if free - need < args.min_free_gb * 1e9:
            raise DiskGuard(f"{free / 1e9:.1f} GB free, {need / 1e9:.1f} GB still needed, guard {args.min_free_gb} GB")
        try:
            hdr = {"Range": f"bytes={have}-"} if have else {}
            with open_url(url, headers=hdr, timeout=60) as r:
                if have and r.status != 206:
                    have = 0                                           # the server ignored Range: start the file again
                    open(part, "wb").close()
                t0, got, last_sync = time.time(), 0, have
                with open(part, "ab") as fh:
                    while not stop["flag"]:
                        blk = r.read(CHUNK)
                        if not blk:
                            eof = True
                            break
                        fh.write(blk)
                        got += len(blk)
                        if args.max_mbps:                              # polite rate limit
                            ahead = got / (args.max_mbps * 125000.0) - (time.time() - t0)
                            if ahead > 0:
                                time.sleep(ahead)
                        if fh.tell() - last_sync >= FSYNC_EVERY:
                            fh.flush()
                            os.fsync(fh.fileno())
                            last_sync = fh.tell()
                    fh.flush()
                    os.fsync(fh.fileno())
            fails = 0
        except urllib.error.HTTPError as e:
            if e.code == 416 and size is not None and os.path.getsize(part) >= size:
                break
            if e.code == 404:
                raise Expired(f"404 for a file at {redact(url)}")
            if e.code in (401, 403):
                raise Blocked(f"HTTP {e.code} at {redact(url)}")
            fails += 1
            log(f"HTTP {e.code} at {redact(url)}")
        except NET_ERRORS as e:
            fails += 1
            log(f"{type(e).__name__} while fetching {os.path.basename(dest)}; the partial file is kept")
            wait_for_network(host_of(url), log)
        if fails:
            time.sleep(min(15 * 2 ** min(fails, 5), 300))
        if eof and size is None:
            break
    if stop["flag"]:
        return False
    if size is not None and os.path.getsize(part) != size:
        log(f"size mismatch for {os.path.basename(dest)}: {os.path.getsize(part)} of {size}")
        return False
    os.replace(part, dest)
    fd = os.open(os.path.dirname(dest), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


# ---------------------------------------------------------------- B. run
def select(args):
    """The requests to fetch: role 'fetch' in order, then anything named with --also, until the budget is reached."""
    chosen, total, skipped = [], 0.0, []
    for rid, proj, inst, gb, role in REQUESTS:
        want = (role == "fetch") or rid in args.also or proj in args.also or (args.include_have and role == "have")
        if getattr(args, "only", None):
            want = rid in args.only or proj in args.only
        if not want or proj in args.skip or rid in args.skip:
            skipped.append((rid, proj, gb, role))
            continue
        if total + gb > args.budget_gb:
            skipped.append((rid, proj, gb, "over the budget"))
            continue
        chosen.append((rid, proj, inst, gb))
        total += gb
    return chosen, total, skipped


def plan(args):
    chosen, total, skipped = select(args)
    links = load_links(args.links)
    print(f"budget {args.budget_gb:.0f} GB; selected {total:.1f} GB in {len(chosen)} requests, in this order:")
    for rid, proj, inst, gb in chosen:
        print(f"  {rid}  {proj:<12} {inst:<5} {gb:>8.1f} GB   link {'present' if rid in links else 'MISSING'}")
    print("not fetched:")
    for rid, proj, gb, why in skipped:
        print(f"  {rid}  {proj:<12} {gb:>8.1f} GB   {why}")
    return 0


def probe(args):
    links, log = load_links(args.links), (lambda m: print("   ", m))
    chosen, _, _ = select(args)
    ids = [c[0] for c in chosen] if not args.all else [r[0] for r in REQUESTS]
    for rid, proj, inst, gb in [(r[0], r[1], r[2], r[3]) for r in REQUESTS if r[0] in ids]:
        if rid not in links:
            print(f"{rid} {proj}: no link in {os.path.basename(args.links)}")
            continue
        try:
            files = crawl(links[rid], log)
            names = [f for f, _ in files if not f.upper().endswith("SHA1SUMS")]
            tot = sum(remote_size(u, log) or 0 for f, u in files if f in names)
            print(f"{rid} {proj}: ANSWERS, {len(names)} file(s), {tot / 1e9:.1f} GB (stated {gb} GB)")
        except Expired as e:
            print(f"{rid} {proj}: EXPIRED ({e})")
        except Blocked as e:
            print(f"{rid} {proj}: BLOCKED ({e})")
    return 0


def status(args):
    st = State(os.path.join(args.dest, "nrao_fetch_state.json"))
    for rid, proj, inst, gb, role in REQUESTS:
        r = st.data["requests"].get(rid)
        if not r:
            continue
        files = r.get("files", {})
        done = sum(1 for f in files.values() if f.get("done"))
        got = sum(f["size"] for f in files.values() if f.get("done"))
        print(f"{rid} {proj:<12} {r['status']:<11} {done}/{len(files)} files, {got / 1e9:.1f} GB of {gb} GB")
    return 0


def run(args):
    os.makedirs(args.dest, exist_ok=True)
    lock = open(os.path.join(args.dest, ".nrao_fetch.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another nrao_fetch run holds the lock")
        return 4
    try:
        os.nice(args.nice)
    except OSError:
        pass
    if shutil.which("ionice"):
        subprocess.run(["ionice", "-c", str(args.ionice_class), "-p", str(os.getpid())], capture_output=True)
    logf = open(os.path.join(args.dest, "nrao_fetch.log"), "a", buffering=1)

    def log(m):
        line = time.strftime("%Y-%m-%d %H:%M:%S ") + m
        print(line, flush=True)
        logf.write(line + "\n")

    stop = {"flag": False}
    for sg in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sg, lambda *_: stop.__setitem__("flag", True))
    st, links = State(os.path.join(args.dest, "nrao_fetch_state.json")), load_links(args.links)
    chosen, total, _ = select(args)
    log(f"start: {len(chosen)} request(s), {total:.1f} GB selected, destination {args.dest}")
    usable, last_note = 0, time.time()
    for rid, proj, inst, gb in chosen:
        if stop["flag"]:
            break
        r = st.req(rid)
        if r["status"] == "done":
            usable += 1
            continue
        if rid not in links:
            log(f"{rid} {proj}: no link; skipped")
            r["status"] = "no-link"
            st.save()
            continue
        try:
            if not r["files"]:
                log(f"{rid} {proj}: listing")
                files = crawl(links[rid], log)
                sums = {}
                for rel, u in files:
                    if rel.upper().endswith("SHA1SUMS"):
                        try:
                            for ln in fetch_text(u, log).splitlines():
                                p = ln.split()
                                if len(p) == 2:
                                    sums[p[1].lstrip("*").split("/")[-1]] = p[0]
                        except (Expired, Blocked):
                            pass
                for rel, u in files:
                    if rel.upper().endswith("SHA1SUMS") or rel.endswith("fetch-all.sh"):
                        continue
                    r["files"][rel] = {"url": u, "size": remote_size(u, log), "sha1": sums.get(os.path.basename(rel)), "done": False}
                r["status"] = "downloading"
                st.save()
                log(f"{rid} {proj}: {len(r['files'])} file(s), {sum(f['size'] or 0 for f in r['files'].values()) / 1e9:.1f} GB")
            for rel, f in r["files"].items():
                if f["done"] or stop["flag"]:
                    continue
                dest = os.path.join(args.dest, proj, rel)
                if os.path.exists(dest) and f["size"] and os.path.getsize(dest) == f["size"]:
                    f["done"] = True
                    st.save()
                    continue
                log(f"{rid} {proj}: {rel} ({(f['size'] or 0) / 1e9:.2f} GB)")
                if not fetch_file(f["url"], dest, f["size"], args, log, stop):
                    break
                if f.get("sha1") and not args.no_verify:
                    log(f"verifying sha1 of {rel}")
                    if sha1_of(dest) != f["sha1"]:
                        log(f"SHA1 MISMATCH for {rel}: the file is kept as {dest}.bad and will be fetched again on the next run")
                        os.replace(dest, dest + ".bad")
                        continue
                f["done"] = True
                st.save()
                if time.time() - last_note > args.notify_secs:
                    log(f"[status] {proj}: {sum(1 for x in r['files'].values() if x['done'])}/{len(r['files'])} files, {shutil.disk_usage(args.dest).free / 1e9:.0f} GB free")
                    last_note = time.time()
            if all(x["done"] for x in r["files"].values()):
                r["status"] = "done"
                usable += 1
                log(f"{rid} {proj}: complete")
            st.save()
        except Expired as e:
            r["status"] = "expired"
            st.save()
            log(f"{rid} {proj}: EXPIRED, the NRAO copy is gone ({e}). Re-request it in the Archive Access Tool and add the new link with --add-link {rid} URL")
        except Blocked as e:
            r["status"] = "blocked"
            st.save()
            log(f"{rid} {proj}: BLOCKED ({e}); not repaired")
        except DiskGuard as e:
            st.save()
            log(f"DISK GUARD: {e}")
            return 2
    st.save()
    if stop["flag"]:
        log("stopped by signal; state saved")
        return 130
    if usable == 0 and chosen:
        log("nothing usable: every selected request expired, is blocked or has no link")
        return 3
    pend = [x for x in chosen if st.req(x[0])["status"] not in ("done",)]
    log("all selected requests done" if not pend else f"finished with {len(pend)} request(s) not done: " + ", ".join(p[1] for p in pend))
    return 0 if not pend else 3


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--add-link", nargs=2, metavar=("ID", "URL"))
    ap.add_argument("--project", default=None, help="with --add-link: project name of a request that is not in the built-in table")
    ap.add_argument("--size-gb", type=float, default=None, help="with --add-link: size in GB as NRAO reported it (for the budget)")
    ap.add_argument("--role", default=None, help="with --add-link: fetch (default), have or skip")
    ap.add_argument("--links", default=os.path.join(HERE, "links.txt"))
    ap.add_argument("--dest", default=os.path.expanduser("~/CrabNebula/data/nrao"))
    ap.add_argument("--budget-gb", type=float, default=700.0)
    ap.add_argument("--min-free-gb", type=float, default=20.0)
    ap.add_argument("--also", nargs="*", default=[], help="request ids or project names to add beyond the default set")
    ap.add_argument("--only", nargs="*", default=[], help="fetch only these request ids or project names (ignores the default set and the other roles)")
    ap.add_argument("--skip", nargs="*", default=[], help="request ids or project names to leave out")
    ap.add_argument("--include-have", action="store_true", help="also fetch the three small requests already on the main machine")
    ap.add_argument("--all", action="store_true", help="with --probe: probe every request, not only the selected ones")
    ap.add_argument("--max-mbps", type=float, default=0.0, help="rate limit in megabit/s (0 = none)")
    ap.add_argument("--nice", type=int, default=5)
    ap.add_argument("--ionice-class", type=int, default=2, help="2 = best effort, 3 = idle")
    ap.add_argument("--notify-secs", type=int, default=900)
    ap.add_argument("--no-verify", action="store_true", help="skip the sha1 check against SHA1SUMS")
    a = ap.parse_args(argv)
    if a.add_link:
        add_link(a.links, a.add_link[0], a.add_link[1], a.project, a.size_gb, a.role)
        print("link stored for", a.add_link[0], redact(a.add_link[1]), a.project or "")
        return 0
    register_extra_requests(a.links)
    for flag, fn in (("setup", setup), ("plan", plan), ("probe", probe), ("status", status), ("run", run)):
        if getattr(a, flag):
            return fn(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
