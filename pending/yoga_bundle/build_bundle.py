#!/usr/bin/env python3
"""build_bundle.py [DEST] -- assemble the private Yoga bundle OUTSIDE the repository (default ~/Desktop/SpaceClaude/BulletCluster/YogaBundle): these files plus links.txt
(keyed NRAO URLs copied from ../nrao_downloads/links_PRIVATE.md, gitignored). Do not commit or publish the result."""
import os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
dest = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.expanduser("~/Desktop/SpaceClaude/BulletCluster/YogaBundle")
os.makedirs(dest, exist_ok=True)
for f in ("CLAUDE.md", "JOBS.md", "nrao_fetch.py", "fetch_crab.sh", "test_nrao_fetch.py", "telescope_download.py", "prepare_job.py", "run_job.sh",
          "build_euclid_manifest.py", "build_mast_manifest.py"):
    shutil.copy2(os.path.join(HERE, f), os.path.join(dest, f))
shutil.copytree(os.path.join(HERE, "jobs"), os.path.join(dest, "jobs"), dirs_exist_ok=True)
sys.path.insert(0, HERE)
import nrao_fetch as nf  # noqa: E402
links = nf.load_links(os.path.join(HERE, "..", "nrao_downloads", "links_PRIVATE.md"))
with open(os.path.join(dest, "links.txt"), "w", encoding="utf-8") as fh:
    fh.write("# REQUEST_ID  DIRECT_URL   (PRIVATE: keyed URLs. Do not print, copy or commit.)\n# The EVLA links answered 404 on 2026-11-27; the GBT ones worked.\n")
    for rid in sorted(links):
        fh.write(f"{rid}  {links[rid]}\n")
os.chmod(os.path.join(dest, "links.txt"), 0o600)
for f in ("run_job.sh", "fetch_crab.sh", "nrao_fetch.py", "prepare_job.py", "telescope_download.py", "build_euclid_manifest.py", "build_mast_manifest.py", "test_nrao_fetch.py"):
    os.chmod(os.path.join(dest, f), 0o755)
print("bundle written to", dest, "with", len(links), "links")
