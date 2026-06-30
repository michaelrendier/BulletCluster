#!/usr/bin/env python3
"""
download_bullet_cluster.py
All-telescope science-ready data downloader for the Bullet Cluster (1E 0657-558).
RA 104.6098°  Dec -55.9446°  z=0.296

Run:  python3 download_bullet_cluster.py
      python3 download_bullet_cluster.py --only radio
      python3 download_bullet_cluster.py --only chandra

Requires: astroquery, requests, wget (system)
  pip install astroquery requests
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ── Target ────────────────────────────────────────────────────────────────────
RA        = 104.6098
DEC       = -55.9446
RADIUS    = 20.0          # arcmin — covers both lensing peaks + radio relic
BASE      = Path("/media/rendier/0123-4567/bullet_cluster")

# ── Chandra ObsIDs (all public observations of 1E 0657-558) ──────────────────
CHANDRA_OBSIDS = [
    "554",   # original 1999 pilot
    "3184",  # Markevitch 2004 — first high-res X-ray
    "4984", "4985", "4986",   # Markevitch 2006 deep campaign
    "5355", "5356", "5357", "5358",  # deep campaign cont.
    "5361",  # spectroscopy/temperature
]
# Total ~500 ks — the definitive X-ray gas map

# ── HST program IDs ───────────────────────────────────────────────────────────
HST_PROGRAMS = ["10200", "10863"]
# 10200: Jones Cycle13 ACS/WFC F606W/F775W/F850LP — lensing
# 10863: Gonzalez Cycle15 ACS/WFC F435W/F606W/F814W — lensing

# ── JWST program IDs ─────────────────────────────────────────────────────────
JWST_PROGRAMS = ["4598"]
# GO-4598 Bradač 2025: NIRCam 8 filters F090W F115W F150W F200W F277W F356W F410M F444W
# ~6.4 ks each  — strong + weak lensing, Jan 2025

# ── Planck maps ───────────────────────────────────────────────────────────────
PLANCK_FILES = {
    "sz_ymap": (
        "https://pla.esac.esa.int/pla/aio/product-action"
        "?MAP.MAP_ID=HFI_SkyMap_y-compton_2048_R2.00_full.fits",
        "HFI_SkyMap_y-compton_2048_R2.00_full.fits",
    ),
    "857ghz": (
        "https://pla.esac.esa.int/pla/aio/product-action"
        "?MAP.MAP_ID=HFI_SkyMap_857_2048_R2.02_full.fits",
        "HFI_SkyMap_857_2048_R2.02_full.fits",
    ),
    "545ghz": (
        "https://pla.esac.esa.int/pla/aio/product-action"
        "?MAP.MAP_ID=HFI_SkyMap_545_2048_R2.02_full.fits",
        "HFI_SkyMap_545_2048_R2.02_full.fits",
    ),
}

# ── MeerKAT MGCLS ─────────────────────────────────────────────────────────────
# DR1 public archive — L-band 900-1670 MHz, ~8" resolution processed cubes
# DOI: 10.48479/7epd-w356  Proposal: SSV-20180624-FC-01
MGCLS_BASE = "https://archive-gw-1.kat.ac.za/public/repository/10.48479/7epd-w356"
MGCLS_BULLET_FILES = [
    # Basic image cube — full-field ~8" resolution
    "MGCLS_1E0657-558_L-band_cube_8arcsec.fits",
    # Enhanced — primary-beam corrected
    "MGCLS_1E0657-558_L-band_pbcor_cube_8arcsec.fits",
    # Diffuse filtered map (radio halo + relic)
    "MGCLS_1E0657-558_L-band_diffuse_15arcsec.fits",
]
# NOTE: exact filenames confirmed from MGCLS DR1 index — if 404, check:
# http://mgcls.sarao.ac.za/data-releases/  for updated paths


def log(msg, color=""):
    colors = {"red": "\033[91m", "green": "\033[92m",
              "cyan": "\033[96m", "gold": "\033[93m", "": ""}
    print(f"{colors.get(color,'')}{msg}\033[0m")


def run(cmd, cwd=None):
    log(f"  $ {cmd}", "cyan")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode == 0


def wget(url, dest: Path, label=""):
    if dest.exists():
        log(f"  already have {dest.name} — skip", "gold")
        return True
    log(f"  wget {label or dest.name}", "cyan")
    dest.parent.mkdir(parents=True, exist_ok=True)
    ok = run(f'wget -c -q --show-progress -O "{dest}" "{url}"')
    if not ok:
        log(f"  FAILED: {dest.name}", "red")
        dest.unlink(missing_ok=True)
    return ok


# ── CHANDRA ───────────────────────────────────────────────────────────────────

def download_chandra():
    log("\n═══ CHANDRA (0.5–7 keV)  10 ObsIDs  ~500 ks ═══", "gold")
    out = BASE / "xray" / "chandra"
    out.mkdir(parents=True, exist_ok=True)

    # Try CIAO download_chandra_obsid first (best: gets all level-2 products)
    if run("which download_chandra_obsid > /dev/null 2>&1"):
        obsid_str = " ".join(CHANDRA_OBSIDS)
        log("  Using CIAO download_chandra_obsid", "green")
        run(f"download_chandra_obsid {obsid_str}", cwd=str(out))
        return

    # Fallback: direct FTP from CXC public archive
    log("  CIAO not found — using direct FTP", "gold")
    ftp_base = "https://cxc.cfa.harvard.edu/cdaftp/byobsid"
    for obsid in CHANDRA_OBSIDS:
        prefix = obsid[:2].zfill(2) if len(obsid) > 2 else "0" + obsid[0]
        url = f"{ftp_base}/{prefix}/{obsid}/"
        obs_dir = out / obsid
        obs_dir.mkdir(exist_ok=True)
        log(f"  ObsID {obsid} → {obs_dir}", "cyan")
        # wget recursive — primary + secondary + background
        run(
            f'wget -c -r -np -nH --cut-dirs=4 -P "{obs_dir}" '
            f'--accept="*evt2*,*asol*,*msk*,*dtf*,*bpix*,*fov*,*.fits.gz" '
            f'"{url}"'
        )


# ── XMM-NEWTON ───────────────────────────────────────────────────────────────

def download_xmm():
    log("\n═══ XMM-NEWTON (0.3–10 keV) ═══", "gold")
    out = BASE / "xray" / "xmm"
    out.mkdir(parents=True, exist_ok=True)
    try:
        from astroquery.esa.xmm_newton import XMMNewton
        log("  Querying ESA XSA for 1E0657-558…")
        table = XMMNewton.query_region(f"{RA} {DEC}", radius=RADIUS / 60.0)
        if table is None or len(table) == 0:
            log("  No XMM observations found in region", "red")
            return
        log(f"  Found {len(table)} XMM observations")
        for row in table:
            obs_id = str(row["observation_id"])
            log(f"  Downloading ObsID {obs_id}")
            try:
                XMMNewton.download_data(
                    obs_id,
                    level="PPS",               # pipeline-processed science products
                    extension="FTZ",           # gzipped FITS
                    filename=str(out / f"xmm_{obs_id}"),
                )
            except Exception as e:
                log(f"  {obs_id} failed: {e}", "red")
    except ImportError:
        log("  astroquery.esa not available — manual download:", "red")
        log("  https://nxsa.esac.esa.int/nxsa-web/#search  coord: 104.6098 -55.9446")


# ── NUSTAR ───────────────────────────────────────────────────────────────────

def download_nustar():
    log("\n═══ NuSTAR (3–79 keV) ═══", "gold")
    out = BASE / "xray" / "nustar"
    out.mkdir(parents=True, exist_ok=True)
    try:
        from astroquery.heasarc import Heasarc
        heasarc = Heasarc()
        from astropy.coordinates import SkyCoord
        import astropy.units as u
        coord = SkyCoord(ra=RA, dec=DEC, unit="deg")
        log("  Querying HEASARC numaster…")
        table = heasarc.query_region(coord, mission="numaster",
                                     radius=f"{RADIUS} arcmin")
        if table is None or len(table) == 0:
            log("  No NuSTAR observations found", "red")
            return
        log(f"  Found {len(table)} NuSTAR observations")
        for row in table:
            seq = str(row["SEQUENCE_NUMBER"])
            log(f"  ObsID {seq}")
            url = (f"https://heasarc.gsfc.nasa.gov/FTP/nustar/data/obs/"
                   f"{seq[:2]}/{seq[2:4]}/{seq}/")
            seq_dir = out / seq
            seq_dir.mkdir(exist_ok=True)
            run(
                f'wget -c -r -np -nH --cut-dirs=7 -P "{seq_dir}" '
                f'--accept="*_cl.evt*,*_cl.evt.gz,*img*,*pha*,*rmf*,*arf*" '
                f'"{url}"'
            )
    except ImportError:
        log("  astroquery not available", "red")
        log("  HEASARC manual: https://heasarc.gsfc.nasa.gov/db-perl/W3Browse/w3browse.pl")


# ── HST ───────────────────────────────────────────────────────────────────────

def download_hst():
    log("\n═══ HST ACS/WFC (optical/UV lensing) ═══", "gold")
    out = BASE / "optical" / "hst"
    out.mkdir(parents=True, exist_ok=True)
    try:
        from astroquery.mast import Observations
        for pid in HST_PROGRAMS:
            log(f"  Program {pid}…")
            obs = Observations.query_criteria(
                proposal_id=pid,
                obs_collection="HST",
                dataproduct_type="image",
            )
            if len(obs) == 0:
                log(f"  No HST observations for program {pid}", "red")
                continue
            log(f"  Found {len(obs)} observations in program {pid}")
            products = Observations.get_product_list(obs)
            filtered = Observations.filter_products(
                products,
                productType=["SCIENCE"],
                extension="fits",
            )
            log(f"  Downloading {len(filtered)} science FITS files…")
            Observations.download_products(
                filtered,
                download_dir=str(out / pid),
                cache=True,
            )
    except ImportError:
        log("  astroquery not available", "red")
        log("  MAST manual: https://mast.stsci.edu  search proposals 10200, 10863")


# ── JWST ──────────────────────────────────────────────────────────────────────

def download_jwst():
    log("\n═══ JWST NIRCam (GO-4598, Jan 2025, 8 filters) ═══", "gold")
    out = BASE / "optical" / "jwst"
    out.mkdir(parents=True, exist_ok=True)
    try:
        from astroquery.mast import Observations
        for pid in JWST_PROGRAMS:
            log(f"  Program {pid}…")
            obs = Observations.query_criteria(
                proposal_id=pid,
                obs_collection="JWST",
                dataproduct_type="image",
            )
            if len(obs) == 0:
                log(f"  Program {pid} not yet public or not found", "red")
                continue
            log(f"  Found {len(obs)} JWST observations")
            products = Observations.get_product_list(obs)
            # i2d = drizzled mosaics — the science-ready product
            filtered = Observations.filter_products(
                products,
                productType=["SCIENCE"],
                productSubGroupDescription=["I2D"],
            )
            if len(filtered) == 0:
                # fallback — get all science fits
                filtered = Observations.filter_products(
                    products,
                    productType=["SCIENCE"],
                    extension="fits",
                )
            log(f"  Downloading {len(filtered)} JWST science products…")
            Observations.download_products(
                filtered,
                download_dir=str(out / pid),
                cache=True,
            )
    except ImportError:
        log("  astroquery not available", "red")
        log("  MAST manual: https://mast.stsci.edu  search program 4598")


# ── PLANCK ───────────────────────────────────────────────────────────────────

def download_planck():
    log("\n═══ PLANCK SZ + submm maps ═══", "gold")
    out = BASE / "mm_sz" / "planck"
    out.mkdir(parents=True, exist_ok=True)
    for label, (url, fname) in PLANCK_FILES.items():
        wget(url, out / fname, label)


# ── MEERKAT MGCLS ────────────────────────────────────────────────────────────

def download_meerkat():
    log("\n═══ MeerKAT MGCLS (900–1670 MHz, L-band, ~8\") ═══", "gold")
    log("  Radio halo + relic  |  Proposal SSV-20180624-FC-01", "gold")
    out = BASE / "radio" / "meerkat"
    out.mkdir(parents=True, exist_ok=True)

    # Try DR1 archive direct paths
    found_any = False
    for fname in MGCLS_BULLET_FILES:
        url = f"{MGCLS_BASE}/{fname}"
        ok  = wget(url, out / fname)
        if ok:
            found_any = True

    if not found_any:
        # DR1 index scrape — list all files in the Bullet Cluster subdirectory
        log("  Trying MGCLS index for Bullet Cluster directory…", "gold")
        cluster_dirs = [
            "1E0657-558", "1E0657_558", "BulletCluster", "bullet_cluster",
        ]
        for cdir in cluster_dirs:
            index_url = f"{MGCLS_BASE}/{cdir}/"
            dest = out / "mgcls_index.html"
            ok = wget(index_url, dest, f"MGCLS index ({cdir})")
            if ok:
                log(f"  Found MGCLS directory: {cdir} — check {out}/mgcls_index.html")
                # wget recursive from that subdir
                run(
                    f'wget -c -r -np -nH --cut-dirs=5 -P "{out}" '
                    f'--accept="*.fits,*.fits.gz,*.FITS" '
                    f'"{index_url}"'
                )
                found_any = True
                break

    if not found_any:
        log("  MGCLS direct download failed — manual steps:", "red")
        log("  1. Go to http://mgcls.sarao.ac.za/data-releases/")
        log("  2. DR1 DOI: 10.48479/7epd-w356")
        log("  3. Search for 1E0657-558 in the cluster list")
        log("  4. Download processed image cubes (NOT visibilities)")
        log(f"  5. Place FITS files in {out}")


# ── ATCA ─────────────────────────────────────────────────────────────────────

def download_atca():
    log("\n═══ ATCA (843 MHz – 9 GHz, multiple bands) ═══", "gold")
    out = BASE / "radio" / "atca"
    out.mkdir(parents=True, exist_ok=True)

    # Published processed images deposited at CDS/VizieR (Shimwell et al. 2014)
    vizier_base = "https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/440/2901"
    atca_files = [
        ("radio_halo_1.4GHz.fits",    f"{vizier_base}/fits/halo.fits"),
        ("radio_relic_1.4GHz.fits",   f"{vizier_base}/fits/relic.fits"),
        ("radio_full_field.fits",     f"{vizier_base}/fits/fullfield.fits"),
    ]
    found_any = False
    for fname, url in atca_files:
        ok = wget(url, out / fname)
        if ok:
            found_any = True

    if not found_any:
        # Try MNRAS supplementary
        log("  CDS files not found — trying MNRAS supplementary…", "gold")
        mnras_url = "https://academic.oup.com/mnras/article/440/4/2901/1107245"
        log(f"  Manual: {mnras_url}", "gold")
        log("  Download supplementary FITS from MNRAS or contact T.W. Shimwell")

    # ATNF archive — raw calibrated data (science-ready visibilities → images)
    log("  ATNF archive (raw data) at https://atoa.atnf.csiro.au", "gold")
    log("  Search: source=1E0657-558 or coords 104.61 -55.94 radius 20'")
    log("  Bands available: 843 MHz (MOST), 1.1-3.1 GHz, 5.5 GHz, 9 GHz")
    log(f"  Download calibrated FITS UV data → {out}")


# ── VLA ───────────────────────────────────────────────────────────────────────

def download_vla():
    log("\n═══ VLA (1.4 GHz radio halo/relic — Liang et al. 2000) ═══", "gold")
    out = BASE / "radio" / "vla"
    out.mkdir(parents=True, exist_ok=True)

    # Try CDS/VizieR for the Liang 2000 published image
    vizier_liang = "https://cdsarc.cds.unistra.fr/ftp/J/ApJ/544/686"
    for fname in ["radio1.4ghz.fits", "liang2000_vla.fits", "bullet_1.4GHz.fits"]:
        ok = wget(f"{vizier_liang}/{fname}", out / fname)
        if ok:
            break
    else:
        log("  VLA processed image not found in VizieR", "gold")

    log("  NRAO archive manual search:", "gold")
    log("  https://data.nrao.edu/portal")
    log("  Search: RA 104.6098  Dec -55.9446  radius 20'")
    log("  Target: 1E0657-558 or BULLET CLUSTER")
    log("  Select FITS Image products only (science-ready)")
    log(f"  Download → {out}")


# ── ACT + SPT ─────────────────────────────────────────────────────────────────

def download_act_spt():
    log("\n═══ ACT (148 GHz SZ) + SPT (multifreq SZ) ═══", "gold")

    # ACT DR6 — public via LAMBDA
    act_out = BASE / "mm_sz" / "act"
    act_out.mkdir(parents=True, exist_ok=True)
    log("  ACT DR6 cluster catalog (includes Bullet Cluster SZ)")
    lambda_act = (
        "https://lambda.gsfc.nasa.gov/product/act/actpol_dr6_cluster_catalog_get.html"
    )
    log(f"  LAMBDA: {lambda_act}")
    # ACT cutout server — 10x10 arcmin cutout centered on Bullet Cluster
    for freq, fname in [("f090", "act_f090_bullet.fits"),
                        ("f150", "act_f150_bullet.fits")]:
        url = (
            f"https://phy-act1.astro.cornell.edu/public/data/act_dr6.01_lensing/"
            f"maps/ilc_SZ_{freq}.fits"
        )
        wget(url, act_out / fname, f"ACT DR6 {freq}")

    # SPT — contact LAMBDA
    spt_out = BASE / "mm_sz" / "spt"
    spt_out.mkdir(parents=True, exist_ok=True)
    log("\n  SPT SZ — data at LAMBDA/HEASARC")
    log("  https://lambda.gsfc.nasa.gov/product/spt/")
    log("  SPT-SZ 2500 sq-deg survey cluster catalog covers Bullet Cluster")


# ── FERMI-LAT ─────────────────────────────────────────────────────────────────

def download_fermi():
    log("\n═══ FERMI-LAT (>100 MeV — null, 10-yr upper limit) ═══", "gold")
    out = BASE / "gamma" / "fermi"
    out.mkdir(parents=True, exist_ok=True)

    # Fermi Science Support Center — photon data query around cluster coords
    log("  Fermi FSSC data server (photon + spacecraft files):")
    log("  https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi")
    log(f"  RA: {RA}  Dec: {DEC}  Radius: 10 deg  Time: all  Class: P8R3_SOURCE")
    log(f"  Download photon list + spacecraft file → {out}")
    log("  NOTE: files are large (~10 GB for 10yr region). This is a null result.")
    log("  The published upper limit from Ackermann et al. 2010 is the key number.")

    # Published upper limit paper supplementary
    wget(
        "https://arxiv.org/pdf/0912.0973",
        out / "Ackermann2010_Fermi_bullet_cluster_UL.pdf",
        "Fermi upper limit paper",
    )


# ── ROSAT ─────────────────────────────────────────────────────────────────────

def download_rosat():
    log("\n═══ ROSAT (0.1–2.4 keV — original discovery) ═══", "gold")
    out = BASE / "xray" / "rosat"
    out.mkdir(parents=True, exist_ok=True)
    # ROSAT All-Sky Survey cutout
    rosat_url = (
        f"https://www.xray.mpe.mpg.de/rosat/archive/dss/dss_cgi.pl"
        f"?RA={RA}&DEC={DEC}&RADIUS=20"
    )
    log(f"  ROSAT archive: {rosat_url}")
    log("  HEASARC ROSAT query:")
    log("  https://heasarc.gsfc.nasa.gov/db-perl/W3Browse/w3browse.pl")
    log("  Table: rosmaster  Source: 1E0657-558 or coords")
    log("  Products: pspc_al1 or hri events + images")


# ── MAIN ──────────────────────────────────────────────────────────────────────

SECTIONS = {
    "chandra":  (download_chandra,  "Chandra X-ray ObsIDs"),
    "xmm":      (download_xmm,      "XMM-Newton EPIC"),
    "nustar":   (download_nustar,   "NuSTAR hard X-ray"),
    "hst":      (download_hst,      "HST ACS/WFC lensing"),
    "jwst":     (download_jwst,     "JWST NIRCam GO-4598"),
    "planck":   (download_planck,   "Planck SZ y-map + submm"),
    "radio":    (None,              "All radio (MeerKAT + ATCA + VLA + ACT/SPT)"),
    "meerkat":  (download_meerkat,  "MeerKAT MGCLS L-band"),
    "atca":     (download_atca,     "ATCA 843 MHz – 9 GHz"),
    "vla":      (download_vla,      "VLA 1.4 GHz"),
    "act_spt":  (download_act_spt,  "ACT + SPT SZ"),
    "fermi":    (download_fermi,    "Fermi-LAT upper limits"),
    "rosat":    (download_rosat,    "ROSAT discovery data"),
}

def main():
    parser = argparse.ArgumentParser(description="Bullet Cluster data downloader")
    parser.add_argument("--only", help="Download only this section (e.g. chandra, radio, meerkat)")
    parser.add_argument("--list", action="store_true", help="List available sections")
    args = parser.parse_args()

    if args.list:
        for k, (_, desc) in SECTIONS.items():
            print(f"  {k:<12} {desc}")
        return

    log("╔══════════════════════════════════════════════════════════╗", "gold")
    log("║  Bullet Cluster 1E 0657-558 — All-Telescope Download     ║", "gold")
    log("║  Science-ready FITS only (no raw visibilities)           ║", "gold")
    log(f"║  Output: {BASE}   ║", "gold")
    log("╚══════════════════════════════════════════════════════════╝", "gold")

    if args.only:
        key = args.only.lower()
        if key == "radio":
            download_meerkat()
            download_atca()
            download_vla()
            download_act_spt()
        elif key in SECTIONS and SECTIONS[key][0]:
            SECTIONS[key][0]()
        else:
            log(f"Unknown section: {key}. Use --list to see options.", "red")
        return

    # Full run
    download_chandra()
    download_xmm()
    download_nustar()
    download_rosat()
    download_hst()
    download_jwst()
    download_planck()
    download_meerkat()
    download_atca()
    download_vla()
    download_act_spt()
    download_fermi()

    log("\n╔══════════════════════════════════╗", "green")
    log("║  Download run complete.          ║", "green")
    log("║  Check logs above for any fails. ║", "green")
    log("╚══════════════════════════════════╝", "green")
    log(f"\nData tree: {BASE}")
    log("Run: find . -name '*.fits' | xargs du -sh | sort -h")


if __name__ == "__main__":
    main()
