#!/usr/bin/env python3
"""build_bundle.py -- make the private transfer folder for the second machine: the engine, the runner, the tests, and links.txt with the keyed
NRAO URLs copied from ../links_PRIVATE.md (gitignored). The bundle is written OUTSIDE the repository (default ~/Desktop/SpaceClaude/BulletCluster/CrabTransfer)
and must not be committed or published: each URL carries a per-request key.   python3 build_bundle.py [DEST]"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
dest = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.expanduser("~/Desktop/SpaceClaude/BulletCluster/CrabTransfer")
os.makedirs(dest, exist_ok=True)
for f in ("nrao_fetch.py", "fetch_crab.sh", "test_nrao_fetch.py", "README_TRANSFER.md"):
    shutil.copy2(os.path.join(HERE, f), os.path.join(dest, f))
sys.path.insert(0, HERE)
import nrao_fetch as nf  # noqa: E402

links = nf.load_links(os.path.join(HERE, "..", "links_PRIVATE.md"))
with open(os.path.join(dest, "links.txt"), "w", encoding="utf-8") as fh:
    fh.write("# REQUEST_ID  DIRECT_URL   (PRIVATE: each URL carries a per-request key. Do not commit, do not post.)\n"
             "# EVLA links from 2026-11-18 returned 404 on 2026-11-27: re-request in the NRAO Archive Access Tool and replace the line\n"
             "# (python3 nrao_fetch.py --add-link ID URL).\n")
    names = {r[0]: r[1] for r in nf.REQUESTS}
    for rid in sorted(links):
        fh.write(f"# {names.get(rid, '?')}\n{rid}  {links[rid]}\n")
os.chmod(os.path.join(dest, "links.txt"), 0o600)
print("bundle written to", dest, "with", len(links), "links")
