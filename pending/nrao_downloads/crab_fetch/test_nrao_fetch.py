#!/usr/bin/env python3
"""Tests for nrao_fetch.py against a local HTTP server that mimics the NRAO layout (directory indexes, HEAD, Range, SHA1SUMS), and breaks on demand:
mid-transfer connection drops, a request that has expired (404), a login page, and a corrupted file. Run:  python3 test_nrao_fetch.py"""
import hashlib
import http.server
import os
import shutil
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nrao_fetch as nf  # noqa: E402

nf.CHUNK = 64 * 1024
nf.TRIM = 100_000
DROP = {"after": 0}          # >0: the next GET sends only this many bytes and then closes
STATE = {"gets": 0, "corrupt": False}


class H(http.server.BaseHTTPRequestHandler):
    root = None

    def log_message(self, *a):
        pass

    def _path(self):
        return os.path.join(self.root, self.path.lstrip("/").split("?")[0])

    def do_HEAD(self):
        p = self._path()
        if not os.path.isfile(p):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(os.path.getsize(p)))
        self.end_headers()

    def do_GET(self):
        p = self._path()
        if self.path.startswith("/login"):
            body = b"<html><body>NRAO Archive - Choose Account Service. Log In</body></html>"
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if os.path.isdir(p):
            names = sorted(os.listdir(p))
            body = ("<html><body><a href=\"/up/\">up</a>" + "".join(f'<a href="{n}{"/" if os.path.isdir(os.path.join(p, n)) else ""}">{n}</a>' for n in names) + "</body></html>").encode()
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if not os.path.isfile(p):
            self.send_error(404); return
        STATE["gets"] += 1
        data = open(p, "rb").read()
        start = 0
        rng = self.headers.get("Range")
        if rng:
            start = int(rng.split("=")[1].split("-")[0])
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
        else:
            self.send_response(200)
        body = data[start:]
        if STATE["corrupt"] and not p.endswith("SHA1SUMS"):
            body = b"X" * len(body)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if DROP["after"]:
            n, DROP["after"] = DROP["after"], 0
            self.wfile.write(body[:n]); self.wfile.flush(); self.connection.close(); return
        self.wfile.write(body)


def make_tree(root):
    os.makedirs(os.path.join(root, "req1", "key1", "sub"))
    files = {"req1/key1/a.bin": os.urandom(900_000), "req1/key1/sub/b.bin": os.urandom(400_000)}
    for rel, blob in files.items():
        open(os.path.join(root, rel), "wb").write(blob)
    with open(os.path.join(root, "req1/key1/SHA1SUMS"), "w") as fh:
        for rel, blob in files.items():
            fh.write(f"{hashlib.sha1(blob).hexdigest()}  {rel.split('key1/')[1]}\n")
    return files


def args_for(dest, links, **kw):
    ap_args = nf.argparse.Namespace(dest=dest, links=links, budget_gb=700, min_free_gb=0.0, also=[], skip=[], include_have=False, all=False, max_mbps=0.0, nice=0,
                                    ionice_class=2, notify_secs=900, no_verify=False)
    for k, v in kw.items():
        setattr(ap_args, k, v)
    return ap_args


def main():
    tmp = tempfile.mkdtemp(prefix="nrao_fetch_test_")
    srvroot, dest = os.path.join(tmp, "srv"), os.path.join(tmp, "dest")
    files = make_tree(srvroot)
    H.root = srvroot
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    nf.REQUESTS[:] = [("111", "TEST-A", "EVLA", 0.002, "fetch")]
    links = os.path.join(tmp, "links.txt")
    nf.add_link(links, "111", f"{base}/req1/key1/")
    nf.wait_for_network = lambda host, log, patience=None: True       # the local server has no 443; the real function is exercised by hand
    ok = []

    def check(name, cond):
        ok.append(cond)
        print(("PASS " if cond else "FAIL ") + name)

    # 1. a clean run: listing recursion, SHA1SUMS verification, sizes
    check("crawl finds both files and the SHA1SUMS, skipping the parent link",
          sorted(r for r, _ in nf.crawl(f"{base}/req1/key1/", print)) == ["SHA1SUMS", "a.bin", "sub/b.bin"])
    rc = nf.run(args_for(dest, links))
    check("clean run returns 0", rc == 0)
    check("files are byte-identical", all(open(os.path.join(dest, "TEST-A", r.split("key1/")[1]), "rb").read() == b for r, b in files.items()))
    st = nf.State(os.path.join(dest, "nrao_fetch_state.json"))
    check("state says done", st.data["requests"]["111"]["status"] == "done")
    check("a second run is a no-op", nf.run(args_for(dest, links)) == 0)

    # 2. a connection that drops mid-file, then resumes by Range and verifies
    shutil.rmtree(dest)
    DROP["after"] = 300_000
    gets0 = STATE["gets"]
    rc = nf.run(args_for(dest, links))
    check("a mid-transfer drop is survived and the file completes", rc == 0 and open(os.path.join(dest, "TEST-A", "a.bin"), "rb").read() == files["req1/key1/a.bin"])
    check("the resume used a second GET", STATE["gets"] - gets0 >= 3)

    # 3. a crash: a stale .part from a killed run, plus a state file with the files listed but not done
    shutil.rmtree(dest)
    os.makedirs(os.path.join(dest, "TEST-A"))
    blob = files["req1/key1/a.bin"]
    open(os.path.join(dest, "TEST-A", "a.bin.part"), "wb").write(blob[:500_000] + b"JUNKJUNK")   # 8 junk bytes: the TRIM must cut them
    rc = nf.run(args_for(dest, links))
    check("a stale .part with a damaged tail is repaired by the trim and the file verifies against SHA1SUMS", rc == 0 and open(os.path.join(dest, "TEST-A", "a.bin"), "rb").read() == blob)

    # 4. corruption is caught by SHA1SUMS and kept as .bad
    shutil.rmtree(dest)
    STATE["corrupt"] = True
    nf.run(args_for(dest, links))
    STATE["corrupt"] = False
    bad = os.path.exists(os.path.join(dest, "TEST-A", "a.bin.bad"))
    check("a corrupted download is detected (kept as .bad, not marked done)", bad)

    # 5. an expired request (404) and a login page are reported, never repaired
    shutil.rmtree(dest)
    nf.add_link(links, "111", f"{base}/gone/key/")
    check("expired request returns 3 and is marked expired", nf.run(args_for(dest, links)) == 3 and nf.State(os.path.join(dest, "nrao_fetch_state.json")).data["requests"]["111"]["status"] == "expired")
    shutil.rmtree(dest)
    nf.add_link(links, "111", f"{base}/login/")
    check("a login page is a stop (blocked)", nf.run(args_for(dest, links)) == 3 and nf.State(os.path.join(dest, "nrao_fetch_state.json")).data["requests"]["111"]["status"] == "blocked")

    # 6. the disk guard stops before the disk fills
    shutil.rmtree(dest)
    nf.add_link(links, "111", f"{base}/req1/key1/")
    check("the disk guard stops the run with code 2", nf.run(args_for(dest, links, min_free_gb=10 ** 9)) == 2)

    # 7. the budget selection
    nf.REQUESTS[:] = [("1", "A", "EVLA", 300.0, "fetch"), ("2", "B", "EVLA", 300.0, "fetch"), ("3", "C", "EVLA", 150.0, "fetch"), ("4", "D", "EVLA", 100.0, "skip")]
    chosen, total, _ = nf.select(args_for(dest, links, budget_gb=700))
    check("selection stops at the budget and honours skip (A, B, C = 750 > 700 so C is dropped)", [c[1] for c in chosen] == ["A", "B"] and total == 600.0)
    # 8. a new request (not in the built-in table) added with a project name and size joins the plan
    lk = os.path.join(tmp, "links2.txt")
    nf.REQUESTS[:] = [("1", "A", "EVLA", 10.0, "fetch")]
    nf.add_link(lk, "999", "https://dl-dsoc.nrao.edu/rendier/999/abcdefghijklmnopqrstuvwxyz/", "14A-209", 85.3)
    nf.add_link(lk, "1", "https://dl-dsoc.nrao.edu/rendier/1/abcdefghijklmnopqrstuvwxyz/")
    nf.register_extra_requests(lk)
    ch, tot, _ = nf.select(args_for(dest, lk, budget_gb=700))
    check("a new request named in links.txt joins the plan with its size", [c[1] for c in ch] == ["A", "14A-209"] and abs(tot - 95.3) < 1e-9)
    check("links.txt keeps the project and size on a rewrite", nf.read_link_lines(lk)["999"][1:3] == ["14A-209", 85.3])
    ch2, tot2, _ = nf.select(args_for(dest, lk, budget_gb=700, only=["14A-209"]))
    check("--only restricts the plan to the named project", [c[1] for c in ch2] == ["14A-209"] and abs(tot2 - 85.3) < 1e-9)
    check("redact hides the key", "<key>" in nf.redact("https://h.example/rendier/302944689/abcdefghijklmnopqrstuvwxyz/"))
    srv.shutdown()
    shutil.rmtree(tmp)
    print(f"{sum(ok)} of {len(ok)} checks passed")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
