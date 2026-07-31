#!/usr/bin/env python3
"""
make_data_inventory.py — plain-text inventory of every telescope dataset in the
programme: what is planned, what is on disk, one line of description each.

Writes to /storage/emulated/0/Documents/TELESCOPE_DATA_INVENTORY.txt (and a copy
next to this script, since the Documents path is Android-side and may not be
mounted everywhere this repo runs).

Two sources, deliberately kept separate:

  PLANNED   -- read from download_validation_targets.py's own TARGETS and
               DIRECT_PRODUCTS lists, so the inventory cannot drift out of sync
               with the downloader. Change a target there, re-run this, done.

  ON DISK   -- read by actually walking the filesystem and stat-ing files. Not
               from the state file. The state file records what the downloader
               BELIEVES it fetched; the filesystem records what is actually
               there. When those disagree, the filesystem is right and the
               disagreement is exactly what an inventory is for.

Existing Bullet Cluster holdings (Chandra, Planck y-map, MeerKAT, JWST 4598,
HST 10200) predate the downloader and are enumerated separately in
LEGACY_HOLDINGS below.

Usage:
    python3 make_data_inventory.py
    python3 make_data_inventory.py --out /some/other/path.txt
"""

import argparse
import importlib.util
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA_DIR = HERE / "data"

DEFAULT_OUT = Path("/storage/emulated/0/Documents/TELESCOPE_DATA_INVENTORY.txt")
LOCAL_COPY = HERE / "TELESCOPE_DATA_INVENTORY.txt"

# ── Pre-existing holdings, not managed by download_validation_targets.py ──────
# (path relative to the BulletCluster repo root, telescope, one-line description)
LEGACY_HOLDINGS = [
    ("xray/chandra/merged_xray.fits", "Chandra X-ray",
     "Merged ACIS event map -- the shocked baryonic gas, the bow shock, and the "
     "X-ray centroid that defines RA0/DEC0."),
    ("mm_sz/planck/COM_CompMap_YSZ_R2.01/milca_ymaps.fits", "Planck (mm/SZ)",
     "MILCA Compton-y map -- thermal Sunyaev-Zel'dovich signal, an independent "
     "tracer of the hot gas that does not depend on X-ray emissivity."),
    ("radio/meerkat/MGCLS_DR1", "MeerKAT (radio)",
     "MGCLS DR1 total-intensity cubes, 15 arcsec and full resolution. STOKES I "
     "ONLY -- no Q/U for this cluster, which is what blocks the RM-ratio test."),
    ("radio/meerkat/synthetic", "MeerKAT (synthetic)",
     "Synthetic Stokes Q/U cubes, wave and particle models. What the engine was "
     "verified on (0.861 vs 0.967). NOT observational data."),
    ("optical/jwst/4598", "JWST NIRCam",
     "Programme 4598 imaging mosaics, 8 filters F090W-F444W. Intensity only -- "
     "JWST has no polarimetric mode. Source of all background-galaxy shear."),
    ("optical/hst/10200", "HST",
     "Programme 10200 imaging. Partial: j90702020_drz.fits stalled mid-download."),
    ("gamma", "gamma-ray", "Gamma-ray data for the field."),
    ("The_Bullet_Cluster.tif", "composite",
     "Published composite image (optical + X-ray + lensing), used for the "
     "RGB channel separation in tif_channels.png."),
]

TELESCOPE_BY_GROUP = {
    "A": "HST / JWST", "B": "HST / JWST", "C": "HST / JWST",
    "D": "Planck / all-sky surveys", "E": "HST / JWST",
}

GROUP_TITLES = {
    "A": "GROUP A -- EINSTEIN CROSSES (quad-image lenses)",
    "B": "GROUP B -- STRIPPED NUCLEI, UCDs, DM-POOR DWARFS",
    "C": "GROUP C -- NON-LENSING POLARIZATION (the negative control)",
    "D": "GROUP D -- ALL-SKY POLARIZATION & FARADAY (direct URL, not MAST)",
    "E": "GROUP E -- THE BULLET CLUSTER ITSELF",
}

GROUP_PURPOSE = {
    "A": "Break the mass-sheet degeneracy. Image positions give alpha with absolute\n"
         "normalisation; time delays give the Fermat potential difference, which IS\n"
         "L_(I|O) - L. Validates the machinery, NOT the dark-matter hypothesis.",
    "B": "Test the vortex coherence length. Wave DM cannot compress below xi, so it\n"
         "predicts UCDs are DM-free; CDM predicts a surviving central cusp. This is\n"
         "the right mass scale for a wave test -- the cluster scale is not.",
    "C": "Demonstrate what is NOT the prediction. Real polarized fields with known\n"
         "non-lensing origins, pushed through the identical eb_decompose(). Lensing\n"
         "shear is curl-free (E-only); dust and synchrotron carry real B-mode.",
    "D": "Measured galactic dust polarization and the Galactic Faraday screen. Both\n"
         "are all-sky, so both already cover the Bullet Cluster line of sight.",
    "E": "Settle by query rather than assumption what polarimetry of the Bullet\n"
         "Cluster exists, and look for archival coverage of DM_NW.",
}


def load_downloader():
    spec = importlib.util.spec_from_file_location(
        "dvt", HERE / "download_validation_targets.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dvt"] = mod
    spec.loader.exec_module(mod)
    return mod


def human(n):
    n = float(n or 0)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024


def scan_dir(path):
    """(file count, total bytes, list of (name, bytes)) for everything under path."""
    if not path.exists():
        return 0, 0, []
    if path.is_file():
        return 1, path.stat().st_size, [(path.name, path.stat().st_size)]
    files = []
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file() and not p.name.endswith(".part"):
                s = p.stat().st_size
                files.append((p.name, s))
                total += s
        except OSError:
            continue
    return len(files), total, sorted(files)


def wrap(text, width, indent):
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return f"\n{indent}".join(out)


def build(dvt):
    W = 84
    L = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L.append("=" * W)
    L.append("TELESCOPE DATA INVENTORY".center(W))
    L.append("BulletCluster / L_(I|O) validation programme".center(W))
    L.append(f"generated {now}".center(W))
    L.append("=" * W)
    L.append("")
    L.append("STATUS KEY:   [ON DISK] downloaded and present    [PARTIAL] some files present")
    L.append("              [PLANNED] queued, not yet fetched   [POINTER] no download needed")
    L.append("")
    try:
        du = shutil.disk_usage(HERE)
        L.append(f"Volume: {human(du.free)} free of {human(du.total)} "
                 f"({100*du.used/du.total:.0f}% used)")
    except OSError:
        pass
    L.append("")

    # ── Legacy holdings ──────────────────────────────────────────────────────
    L.append("=" * W)
    L.append("PRE-EXISTING BULLET CLUSTER HOLDINGS")
    L.append("(acquired before the validation programme; not managed by the downloader)")
    L.append("=" * W)
    legacy_total = 0
    for rel, scope, desc in LEGACY_HOLDINGS:
        p = REPO / rel
        n, size, _ = scan_dir(p)
        legacy_total += size
        status = "[ON DISK]" if n else "[MISSING]"
        L.append("")
        L.append(f"  {status}  {scope}")
        L.append(f"      path : {rel}")
        L.append(f"      files: {n}   size: {human(size)}")
        L.append(f"      desc : {wrap(desc, W - 14, ' ' * 13)}")
    L.append("")
    L.append(f"  Pre-existing subtotal: {human(legacy_total)}")
    L.append("")

    # ── Programme groups ─────────────────────────────────────────────────────
    planned_total = disk_total = 0
    by_group = {}
    for t in dvt.TARGETS:
        by_group.setdefault(t["group"], []).append(("mast", t))
    for d in dvt.DIRECT_PRODUCTS:
        by_group.setdefault(d["group"], []).append(("direct", d))

    for g in sorted(by_group):
        L.append("=" * W)
        L.append(GROUP_TITLES.get(g, f"GROUP {g}"))
        L.append(f"telescope/archive: {TELESCOPE_BY_GROUP.get(g, '-')}")
        L.append("-" * W)
        for line in GROUP_PURPOSE.get(g, "").split("\n"):
            L.append(f"  {line}")
        L.append("=" * W)

        for kind, item in sorted(by_group[g], key=lambda x: x[1]["key"]):
            key = item["key"]
            tdir = DATA_DIR / key
            n, size, files = scan_dir(tdir)
            disk_total += size

            if kind == "direct":
                if not item["urls"]:
                    status = "[POINTER]"
                else:
                    status = "[ON DISK]" if n else "[PLANNED]"
                what = item["filename"]
                extra = f"products: {what}"
            else:
                status = "[ON DISK]" if n else "[PLANNED]"
                mode = item.get("mode", "img")
                extra = (f"resolve : {item['resolve']}    "
                         f"mode: {'polarimetry only' if mode == 'pol' else 'imaging'}")

            L.append("")
            L.append(f"  {status}  {key}")
            L.append(f"      {extra}")
            if kind == "mast":
                L.append(f"      search  : RA {item['ra']:.4f}  Dec {item['dec']:+.4f}  "
                         f"r = {item['radius_arcmin']:.1f} arcmin")
            L.append(f"      on disk : {n} files, {human(size)}")
            L.append(f"      desc    : {wrap(item['note'], W - 17, ' ' * 16)}")
            if files:
                for fn, fs in files[:6]:
                    L.append(f"                - {fn}  ({human(fs)})")
                if len(files) > 6:
                    L.append(f"                - ... and {len(files)-6} more")
        L.append("")

    # ── Totals ───────────────────────────────────────────────────────────────
    L.append("=" * W)
    L.append("TOTALS")
    L.append("=" * W)
    L.append(f"  Pre-existing holdings      : {human(legacy_total)}")
    L.append(f"  Validation programme       : {human(disk_total)} on disk")
    L.append(f"  Combined                   : {human(legacy_total + disk_total)}")
    L.append("")
    L.append("  Regenerate:  python3 lensing_validation/make_data_inventory.py")
    L.append("  Live status: python3 lensing_validation/download_validation_targets.py --status")
    L.append("=" * W)
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    text = build(load_downloader())

    written = []
    for dest in (args.out, LOCAL_COPY):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
            written.append(dest)
        except OSError as e:
            print(f"could not write {dest}: {e}", file=sys.stderr)

    for w in written:
        print(f"wrote {w}  ({w.stat().st_size/1024:.1f} KB)")
    if not written:
        sys.exit(1)


if __name__ == "__main__":
    main()
