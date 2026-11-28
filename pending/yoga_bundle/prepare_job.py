#!/usr/bin/env python3
"""prepare_job.py JOB_DIR DATA_ROOT -- turn jobs/<name>/manifest.json (relative `dest` paths) into manifest.resolved.json with absolute paths under DATA_ROOT.
Stdlib only. The manifest format is the one telescope_download.py reads: a list of {"url", "dest", "size"?, "sha256"?}."""
import json, os, sys
job, root = sys.argv[1], os.path.abspath(os.path.expanduser(sys.argv[2]))
items = json.load(open(os.path.join(job, "manifest.json")))
for it in items:
    it["dest"] = os.path.join(root, it["dest"])
json.dump(items, open(os.path.join(job, "manifest.resolved.json"), "w"), indent=1)
print(f"{len(items)} files, {sum(i.get('size') or 0 for i in items) / 1e9:.1f} GB -> {os.path.join(job, 'manifest.resolved.json')}")
