#!/usr/bin/env python3
"""
download_validation_targets.py — Checkpointed MAST bulk download for the
L_(I|O) external-validation programme.

WHY THIS EXISTS
---------------
The Bullet Cluster L_(I|O) reconstruction (optical/jwst/l_io_lensing.py) is
currently unfalsifiable in absolute terms: psi is mass-sheet degenerate, its
additive constant is fixed by our own kappa_hat[0,0]=0 convention, and the
recovered |alpha| (mean 0.41", max 1.08" -- see prepped/l_io/l_io_deficit.json)
sits an order of magnitude below the cluster's known strong-lensing
deflections. Nothing about the engine has ever been checked against a system
where psi is independently known.

This script fetches the two datasets that fix that:

  GROUP A -- Einstein Crosses (quad-image lenses).
    Image positions measure alpha at four points with ABSOLUTE normalisation,
    breaking the mass-sheet degeneracy. Measured time delays give the Fermat
    potential difference directly:  dt ~ D[ (theta-beta)^2/2 - psi(theta) ].
    The bracketed quantity IS L_(I|O) - L. These are the only direct
    observational handle on psi differences that exists.

    NOTE, stated up front so it does not get overclaimed later: these validate
    the psi -> alpha -> beta MACHINERY. They do not test the Abrikosov / wave
    dark-matter hypothesis. Different question, different object.

    Second caveat: a quad lens is the STRONG regime (kappa ~ 1). Kaiser-Squires
    is a linear inversion valid for kappa << 1. Do NOT feed these to
    bounded_lensing_pipeline() and expect meaning -- run the psi->alpha->beta
    chain FORWARD on a published lens model instead.

  GROUP B -- stripped nuclei / ultra-compact dwarfs, plus the two DM-poor
    dwarfs. Under the standard soliton core-halo relation the wave signature
    scales as M_halo^(-1/3): more massive halos have SMALLER cores. At
    10^15 Msun the predicted core is far below anything JWST resolves, so the
    Bullet Cluster is the WRONG mass scale for a wave test. The signature
    lives at dwarf/UCD masses. That is what Group B is for.

    The discriminant: globulars cap near 10^6 Msun with M/L ~ 1-3 (pure stars).
    UCDs run 10^7-10^8 Msun with dynamical M/L roughly double what stellar
    populations predict. A vortex has a coherence length xi and cannot be
    compressed below it -- so a vortex picture predicts UCDs are DM-FREE and
    their excess M/L must be entirely black hole or IMF. CDM predicts a
    stripped nucleus retains its innermost cusp, i.e. small but nonzero DM.

    Convert GAP = 7.07e-4 to a physical length and COMMIT TO IT BEFORE
    LOOKING AT ANY OF THIS DATA. Otherwise the test is a post-hoc fit and
    worth nothing.

DESIGN
------
Checkpointed at three levels, so a kill -9, a power loss, or an LTE dropout
mid-file all resume correctly:

  1. MANIFEST CACHE  -- the MAST query result is cached to disk. Re-runs do not
                        re-query (use --requery to force). Survives MAST being
                        down.
  2. STATE FILE      -- per-product status, written atomically (tmp + os.replace)
                        after every single file. Never a torn state file.
  3. .part FILES     -- byte-range HTTP resume. A file interrupted at 80% picks
                        up at 80%, not 0%.

Downloads use plain requests + Range headers rather than
Observations.download_products(), which has no byte-level resume. astroquery is
used ONLY for the metadata query. Same choice jwst_resume_download.py made.

USAGE
-----
    # dry run first -- see what it would fetch and how big
    python3 download_validation_targets.py --dry-run

    # background + disown (the intended mode)
    nohup python3 download_validation_targets.py >> validation_download.log 2>&1 &
    disown
    tail -f validation_download.log

    # check on it later, from anywhere, without touching the running process
    python3 download_validation_targets.py --status

    # retry whatever failed
    python3 download_validation_targets.py --retry-failed

Safe to re-run at any time. Safe to Ctrl-C or SIGTERM -- state is flushed after
every file and the current .part is kept. A second concurrent instance refuses
to start (PID lock).

Requirements: astroquery, requests  (astropy comes in with astroquery)
"""

import argparse
import json
import os
import re
import shutil
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ── Layout ────────────────────────────────────────────────────────────────────
# Everything is relative to this file. No hardcoded /mnt/sdcard, /media/rendier,
# or /storage/emulated/0 -- those three appear in different scripts in this repo
# and none of them currently resolve.
HERE          = Path(__file__).resolve().parent
# 2026-08-19: data/ is now a SYMLINK to
#   /media/rendier/Datasets/ThePlace/BulletCluster/lensing_validation/data
# so the bulk sits on the 469 GB Datasets volume, not /home. Every free-space
# check therefore measures DATA_DIR, never HERE -- those are different volumes
# now and reading HERE would let the floor pass while the real target fills.
DATA_DIR      = HERE / "data"
STATE_FILE    = HERE / "validation_download_state.json"
MANIFEST_FILE = HERE / "validation_manifest.json"
LOG_FILE      = HERE / "validation_download.log"
PID_FILE      = HERE / "validation_download.pid"

# The state, the log and the script itself must survive the data volume going
# away -- otherwise the outage takes down the very thing that would recover
# from it. Nothing here may live on the removable drive.
if str(HERE).startswith("/media/"):
    raise SystemExit(
        f"refusing to run from {HERE}: state, log and script must live off the "
        f"data volume so they survive it being unplugged")

# ── Tunables ──────────────────────────────────────────────────────────────────
CHUNK_BYTES        = 4 * 1024 * 1024   # 4 MB -- unlimited LTE, go wide
HTTP_TIMEOUT       = (30, 300)         # (connect, read) seconds
MAX_ATTEMPTS       = 4                 # per file, per run
BACKOFF_BASE       = 15                # seconds; doubles each attempt
PROGRESS_EVERY     = 30                # seconds between progress lines in a log
SIZE_TOLERANCE     = 0.01              # 1% -- MAST catalog sizes are approximate
MANIFEST_MAX_AGE_D = 14                # re-query if cache older than this
DEFAULT_BUDGET_GB  = 120               # stop before filling the card
MIN_FREE_GB        = 12                # never dip below this much free space

MAST_DOWNLOAD_URL = "https://mast.stsci.edu/api/v0.1/Download/file?uri="
USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
              "Gecko/20100101 Firefox/120.0")   # same UA convention as SARAO access

# High-level drizzled science products only. These are what the lensing
# pipeline actually consumes; _cal/_rate/_uncal/*ints are 10-50x the volume for
# no gain here. --all-products widens this.
DEFAULT_SUFFIXES = ("_i2d.fits", "_drz.fits", "_drc.fits")
ALL_SUFFIXES     = DEFAULT_SUFFIXES + ("_cal.fits", "_flc.fits", "_flt.fits",
                                       "_s2d.fits", "_x1d.fits")
# Never worth pulling on a phone-tethered link.
EXCLUDE_PATTERNS = ("_uncal.", "_rateints.", "_calints.", "_ramp.", "_trapsfilled.",
                    "_segm.", "_pool.", "_asn.json", "thumb", "preview")

# ── Targets ───────────────────────────────────────────────────────────────────
# Coordinates below are FALLBACKS ONLY. The script resolves each target by name
# through MAST's resolver first and logs the resolved position, precisely so a
# coordinate typo here cannot silently point the query at empty sky. Compare the
# logged resolved position against the fallback before trusting a run.
TARGETS = [
    # ---- GROUP A: Einstein Crosses / quad lenses -----------------------------
    dict(key="A1_sn_refsdal_macs1149", resolve="MACS J1149.5+2223",
         ra=177.3987, dec=+22.3986, radius_arcmin=3.0, priority=1,
         group="A", note="SN Refsdal. Four images around a cluster elliptical. "
                         "The reappearance SX was PREDICTED from lens models and "
                         "then observed -- prediction-then-verification of exactly "
                         "our quantity. Cluster scale. The benchmark."),
    dict(key="A2_sdss_j1004+4112", resolve="SDSS J1004+4112",
         ra=151.1450, dec=+41.2108, radius_arcmin=2.5, priority=1,
         group="A", note="Cluster-lensed quad quasar, ~15 arcsec separation, "
                         "measured delays including the very long one. Bridges "
                         "galaxy scale to Bullet-Cluster scale."),
    dict(key="A3_rxj1131-1231", resolve="RX J1131-1231",
         ra=172.9650, dec=-12.5325, radius_arcmin=2.0, priority=1,
         group="A", note="Galaxy scale, long delays, best-characterised Fermat "
                         "potential. z_lens ~ 0.295, essentially identical to the "
                         "Bullet Cluster's 0.296 -- distance factors are shared."),
    dict(key="A4_he0435-1223", resolve="HE 0435-1223",
         ra=69.5621, dec=-12.2873, radius_arcmin=2.0, priority=2,
         group="A", note="Independent galaxy-scale system. Exists to test that "
                         "A3 was not a fluke."),
    dict(key="A5_q2237+0305", resolve="Q2237+0305",
         ra=340.1262, dec=+3.3586, radius_arcmin=2.0, priority=2,
         group="A", note="Huchra's Lens, the original Einstein Cross. Delays are "
                         "hours, so useless for dt -- but the cleanest pure-geometry "
                         "alpha test: four images through a near-face-on bulge with "
                         "minimal external shear."),

    # ---- GROUP B: stripped nuclei / UCDs / DM-poor dwarfs --------------------
    dict(key="B1_m60_ucd1", resolve="M60-UCD1",
         ra=190.9000, dec=+11.5197, radius_arcmin=2.0, priority=1,
         group="B", note="THE 'too big to be a globular cluster' object. ~2e8 Msun "
                         "inside ~24 pc, hosts an SMBH that is ~15% of its total "
                         "mass. If IMBH/SMBH explains the excess M/L here, the "
                         "residual-DM reading loses its best case."),
    dict(key="B2_omega_centauri", resolve="NGC 5139",
         ra=201.6970, dec=-47.4795, radius_arcmin=6.0, priority=2,
         group="B", note="Stripped nucleus of an accreted progenitor. ~20 yr of HST "
                         "proper motions attributed its core excess mass to an "
                         "~8200 Msun IMBH, NOT dark matter. Include it precisely "
                         "because it cuts against us."),
    dict(key="B3_m54_ngc6715", resolve="NGC 6715",
         ra=283.7639, dec=-30.4799, radius_arcmin=5.0, priority=2,
         group="B", note="The nucleus of the Sagittarius dwarf, still embedded in "
                         "its host. The cleanest 'satellite galactic core' -- "
                         "stripping is caught in progress rather than inferred."),
    dict(key="B4_ngc1052-df2", resolve="NGC 1052-DF2",
         ra=40.4450, dec=-8.4025, radius_arcmin=3.0, priority=2,
         group="B", note="Galaxy apparently lacking dark matter. Awkward under CDM; "
                         "natural if a vortex is either pinned somewhere or is not."),
    dict(key="B5_ngc1052-df4", resolve="NGC 1052-DF4",
         ra=39.8129, dec=-8.1161, radius_arcmin=3.0, priority=3,
         group="B", note="Second DM-poor dwarf in the same group. Confirms DF2 is "
                         "not a one-off measurement failure."),

    # ---- GROUP C: the NEGATIVE CASE -- real polarization that is NOT lensing --
    #
    # Two distinct sub-modes, because they falsify two different things.
    #
    #   mode="pol" -- REAL MEASURED POLARIMETRY (HST POL filters).
    #     Feed genuine Stokes (Q,U) through the SAME eb_decompose() used on the
    #     Bullet Cluster shear. Both are spin-2 fields, so the function applies
    #     unchanged -- no new math, no new code path, nothing to accuse us of
    #     tuning. These fields are strongly polarized by mechanisms that are
    #     definitively NOT gravitational lensing (synchrotron; dust scattering;
    #     grain alignment). Lensing shear is curl-free to first order: E-mode
    #     only, B ~ 0. That is a theorem, not a fit. Dust and synchrotron carry
    #     substantial B-mode power. So B/E is the discriminant, and Group C is
    #     what supplies the measured non-lensing B/E to compare against.
    #
    #   mode="img" -- STRUCTURED INTENSITY IMAGING, no polarimetry.
    #     This is the harsher test, and the one worth caring about most. Run
    #     source_extract.py -> pixel_vector_field.py over a field where the
    #     "sources" are dust filaments, pillar edges and young stars rather than
    #     lensed background galaxies. There is NO lensing signal in the Horsehead.
    #     If our shape-measurement chain still emits a coherent, B-suppressed
    #     E-mode field there, then the chain MANUFACTURES the signal and the
    #     Bullet Cluster result is an artifact of our own pipeline. That result
    #     would kill the project, which is exactly why it must be run.
    #
    # On the Brian May precedent cited in dust_confound_test.py's docstring:
    # accurate in spirit, loose in fact. That thesis ("A Survey of Radial
    # Velocities in the Zodiacal Dust Cloud", Imperial College, 2007) measured
    # Doppler shifts of the MgI 5183 line, not polarization. Zodiacal light IS
    # scattered sunlight and IS polarized, and it IS a taken-seriously diffuse
    # foreground -- the precedent stands -- but the thesis is spectroscopy.
    # Worth correcting in that docstring before anyone else does.
    dict(key="C1_crab_nebula", resolve="M1", mode="pol",
         ra=83.6331, dec=+22.0145, radius_arcmin=6.0, priority=1,
         group="C", note="THE reference non-lensing polarized field. Synchrotron, "
                         "polarization degree up to tens of percent, mapped with ACS "
                         "POLV filters. Large, bright, high-S/N, and its polarization "
                         "origin is not in dispute. If eb_decompose() cannot tell the "
                         "Crab from a lensing field, the statistic is worthless."),
    dict(key="C2_egg_nebula_crl2688", resolve="CRL 2688", mode="pol",
         ra=315.0000, dec=+36.6947, radius_arcmin=3.0, priority=1,
         group="C", note="Textbook centrosymmetric SCATTERING polarization (NICMOS "
                         "polarimetry). The pattern is known a priori, so it doubles "
                         "as a correctness check on our Q/U angle conventions -- if "
                         "we do not recover a centrosymmetric field here, our sign "
                         "or angle convention is wrong and every other result is too."),
    dict(key="C3_ngc1068", resolve="NGC 1068", mode="pol",
         ra=40.6696, dec=-0.0133, radius_arcmin=3.0, priority=2,
         group="C", note="AGN scattering cone, ACS polarimetry. A third independent "
                         "polarization MECHANISM, so Group C is not one physical "
                         "process argued three ways."),
    dict(key="C4_ngc7023_iris", resolve="NGC 7023", mode="pol",
         ra=315.3958, dec=+68.1633, radius_arcmin=8.0, priority=3,
         group="C", note="Reflection nebula -- dust scattering over a wide field. "
                         "Closest analogue to diffuse galactic dust that still has "
                         "resolved HST-scale polarimetry."),
    dict(key="C5_pillars_m16", resolve="M16", mode="img",
         ra=274.7000, dec=-13.8070, radius_arcmin=8.0, priority=2,
         group="C", note="Pillars of Creation. JWST/HST INTENSITY only -- no "
                         "polarimetry exists (JWST has no polarimetric mode at all). "
                         "Its job is the mode='img' null test: maximally structured, "
                         "filamentary, zero lensing. Any coherent E-mode our pipeline "
                         "reports here is pipeline, not sky."),
    dict(key="C6_horsehead_b33", resolve="Barnard 33", mode="img",
         ra=85.2458, dec=-2.4586, radius_arcmin=6.0, priority=2,
         group="C", note="Horsehead. Same mode='img' null test as C5, different dust "
                         "morphology and a sharp illuminated ridge -- an edge is the "
                         "single most likely thing to fool a shape estimator into "
                         "reporting coherent alignment."),

    # ---- GROUP E: polarization ON THE BULLET CLUSTER ITSELF ------------------
    #
    # CLAUDE_PRIMER.md lists real MeerKAT Stokes Q/U as the CRITICAL blocker on
    # the RM-ratio result, with both documented routes stalled (IDIA groups
    # empty -> requestExport blocked; PI email unsent). This group does not
    # unblock MeerKAT. It gets the things that are actually fetchable today and
    # that the RM test needs ANYWAY -- because even when Q/U lands, the measured
    # RM is not the cluster's RM until the Galactic foreground is subtracted.
    #
    # Read that again, because it is a live hole in the current design: the
    # engine's diagnostic is RM(DM)/RM(gas), and both terms sit behind the same
    # Milky Way Faraday screen toward (l,b) ~ (266, -21). The foreground is
    # smooth on the ~10 arcmin scale of the transect, so it largely cancels in
    # a RATIO -- but "largely" is doing real work in that sentence and has never
    # been quantified here. D4 quantifies it. If the Galactic RM gradient across
    # the transect is comparable to the DM-vs-gas difference being measured,
    # the 0.95 threshold is not measuring the cluster at all.
    #
    # This is also the honest form of what was asked for: the Bullet Cluster
    # polarization data that EXISTS, versus the data that is wanted.
    dict(key="E1_bullet_cluster_pol", resolve="1E 0657-558", mode="pol",
         ra=104.6098, dec=-55.9446, radius_arcmin=10.0, priority=1,
         group="E", note="Direct MAST query for ANY HST/JWST polarimetric observation "
                         "of the Bullet Cluster field. Expected result: nothing -- JWST "
                         "has no polarimeter and HST POL programmes on this field are "
                         "unlikely. Included because 'we checked and it is not there' "
                         "is data, and 'we assumed it is not there' is not. Costs one "
                         "query."),
    dict(key="E2_bullet_cluster_img", resolve="1E 0657-558", mode="img",
         ra=104.6098, dec=-55.9446, radius_arcmin=10.0, priority=2,
         group="E", note="Full HST/JWST imaging inventory over a 10 arcmin radius -- "
                         "wider than the 4.2 arcmin used by jwst_resume_download.py. "
                         "dust_confound_report.json records that only DM_SE falls "
                         "inside the current F444W tile; the whole wave-vs-particle "
                         "contrast needs BOTH peaks. This looks for archival coverage "
                         "of DM_NW that the narrower search missed."),
]

# ── Group D: direct-URL products (not in MAST) ────────────────────────────────
# Diffuse galactic dust polarization is a Planck product, served by IRSA, not
# MAST. Same resumable downloader, same state file, different URL source.
#
# This is the most important single file in the whole programme. Planck 353 GHz
# is THE reference dust-polarization dataset: full-sky Stokes I/Q/U, and the
# measured dust B-mode power is a substantial fraction of its E-mode power --
# unlike lensing shear, which is E-only by construction. That contrast is the
# quantitative backbone of the negative case, and it comes from published
# survey data rather than from a model we wrote.
#
# The repo already has Planck HEALPix infrastructure (mm_sz/planck/,
# milca_ymaps.fits, 577 MB), so nothing new is needed to read these.
#
# URLs are HEAD-checked before download (--verify-urls runs the check alone).
# IRSA reorganises paths between releases, so a 404 here is expected
# maintenance, not a crash: it is logged with the URL so it can be fixed by
# hand, and the run continues.
DIRECT_PRODUCTS = [
    dict(key="D1_planck_353_iqu", group="D", priority=1,
         filename="HFI_SkyMap_353-psb_2048_R3.01_full.fits",
         urls=["https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/"
               "maps/HFI_SkyMap_353-psb_2048_R3.01_full.fits",
               "https://pla.esac.esa.int/pla/aio/product-action?"
               "MAP.MAP_ID=HFI_SkyMap_353-psb_2048_R3.01_full.fits"],
         note="Planck 353 GHz Stokes I/Q/U, nside 2048. The dust polarization "
              "workhorse. Gives measured galactic-dust E and B power directly."),
    dict(key="D2_planck_dustpol_commander", group="D", priority=1,
         filename="COM_CompMap_DustPol-commander_1024_R2.00.fits",
         urls=["https://irsa.ipac.caltech.edu/data/Planck/release_2/all-sky-maps/"
               "maps/component-maps/foregrounds/"
               "COM_CompMap_DustPol-commander_1024_R2.00.fits"],
         note="Commander-separated thermal dust polarization component. Dust Q/U "
              "with the CMB and synchrotron already removed -- the cleanest "
              "dust-only comparison field."),
    dict(key="D3_planck_217_iqu", group="D", priority=3,
         filename="HFI_SkyMap_217_2048_R3.01_full.fits",
         urls=["https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/"
               "maps/HFI_SkyMap_217_2048_R3.01_full.fits"],
         note="Second frequency. Dust polarization is strongly frequency dependent; "
              "lensing shear is achromatic. A frequency lever arm no shear "
              "systematic can imitate."),

    # -- Bullet Cluster specific. See GROUP E note above for why these matter. --
    dict(key="D4_galactic_faraday_sky", group="D", priority=1,
         filename="faraday2020v2.fits",
         urls=["https://wwwmpa.mpa-garching.mpg.de/ift/data/faraday2020/faraday2020v2.fits"],
         note="Galactic Faraday rotation sky (Hutschenreuter et al. 2022), all-sky "
              "RM with uncertainties. THE foreground subtraction the RM-ratio test "
              "needs. Sample it along the NW->SE merger transect at MERGER_PA_DEG "
              "and compare the Galactic RM gradient against the DM-vs-gas difference "
              "the 0.95 threshold is meant to detect. If they are comparable, the "
              "threshold is measuring the Milky Way. This can and should be run "
              "BEFORE MeerKAT Q/U ever arrives -- it needs no cluster data at all. "
              "URL verified 2026-07-29, 25.2 MB."),
    dict(key="D6_faraday_components", group="D", priority=2,
         filename="components2020v2.fits",
         urls=["https://wwwmpa.mpa-garching.mpg.de/ift/data/faraday2020/"
               "components2020v2.fits"],
         note="Companion to D4: the separated Galactic Faraday sky components plus "
              "the per-pixel uncertainty. The uncertainty map is the part that "
              "matters -- it converts 'the foreground gradient is small' from an "
              "assertion into an error bar on the RM ratio. Verified, 50.3 MB."),
    dict(key="D5_planck_353_covers_bullet", group="D", priority=2,
         filename="_NOTE_planck353_covers_bullet.txt",
         urls=[],
         note="NOT A DOWNLOAD -- a pointer. D1 is all-sky, so it already contains "
              "the Bullet Cluster line of sight at (l,b) ~ (266, -21). Cut a patch "
              "at RA0/DEC0 to get the measured galactic dust polarization foreground "
              "toward the target, at ~5 arcmin resolution. That is real, published, "
              "already-in-hand Bullet Cluster polarization data -- just not of the "
              "cluster. It bounds how much of any polarization signal in that "
              "direction is Milky Way dust."),
]

# HST polarimetric filter names across ACS / WFPC2 / NICMOS all contain 'POL'.
# Substring match is deliberate -- robust to the several naming conventions
# (POL0V, POL60V, POL120V, POL0UV, POLQ, POLQN33, POL0S, POL120L, ...).
POL_TOKEN = "POL"

# ── Logging ───────────────────────────────────────────────────────────────────
_IS_TTY = sys.stdout.isatty()


def _stdout_is_logfile():
    """True when stdout has been redirected into LOG_FILE itself, e.g. the
    documented `nohup ... >> validation_download.log`. Without this check every
    line gets written twice -- once by print(), once by the file append."""
    try:
        so = os.fstat(sys.stdout.fileno())
        lf = LOG_FILE.stat()
        return (so.st_dev, so.st_ino) == (lf.st_dev, lf.st_ino)
    except (OSError, ValueError):
        return False


_ECHO_TO_FILE = not _stdout_is_logfile()


def log(msg=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}" if msg else ""
    print(line, flush=True)
    if not _ECHO_TO_FILE:
        return
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass   # a full or unmounted card must not kill the run


def human(nbytes):
    n = float(nbytes or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n:.0f} B"
        n /= 1024


# ── Graceful shutdown ─────────────────────────────────────────────────────────
class Shutdown:
    """SIGINT/SIGTERM set a flag. The current chunk finishes, state is flushed,
    the .part file is kept, and we exit 0. Nothing is ever left torn."""

    def __init__(self):
        self.requested = False
        signal.signal(signal.SIGINT, self._handle)
        signal.signal(signal.SIGTERM, self._handle)

    def _handle(self, signum, frame):
        if self.requested:            # second signal -- user means it
            log("Second signal received, exiting immediately.")
            sys.exit(130)
        self.requested = True
        name = signal.Signals(signum).name
        log(f"{name} received -- finishing current chunk, then saving and exiting.")


SHUTDOWN = Shutdown()


# ── Single-instance PID lock ──────────────────────────────────────────────────
# flock() is unreliable on the exFAT/FUSE mount this card uses, so this is a
# PID file with a liveness probe instead -- filesystem-agnostic.
def _pid_alive(pid):
    """True only if `pid` is alive AND is actually this script.

    A bare os.kill(pid, 0) is not enough here. When the proot container is
    torn down the PID file survives on the card but the process does not, and
    the next boot hands out low PIDs again -- so the recorded PID is very
    likely alive as something entirely unrelated, and a liveness-only check
    would refuse to start forever. Match the command line too.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True               # exists, owned by someone else
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "replace")
    except OSError:
        return True               # no procfs to check against -- assume alive
    return Path(__file__).name in cmdline


def acquire_lock():
    if PID_FILE.exists():
        try:
            old = int(PID_FILE.read_text().split()[0])
        except (ValueError, IndexError, OSError):
            old = None
        if old and old != os.getpid() and _pid_alive(old):
            log(f"Another instance is already running (pid {old}). Refusing to start.")
            log(f"If that is wrong, remove {PID_FILE} and re-run.")
            sys.exit(3)
        log(f"Clearing stale lock from dead pid {old}.")
    PID_FILE.write_text(f"{os.getpid()} {datetime.now(timezone.utc).isoformat()}\n")


def release_lock():
    try:
        if PID_FILE.exists() and PID_FILE.read_text().split()[0] == str(os.getpid()):
            PID_FILE.unlink()
    except (OSError, IndexError):
        pass


# ── State (atomic) ────────────────────────────────────────────────────────────
def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            backup = STATE_FILE.with_suffix(".corrupt.json")
            log(f"State file unreadable ({e}); moving it to {backup.name} and starting fresh.")
            try:
                STATE_FILE.replace(backup)
            except OSError:
                pass
    return {"version": 1,
            "started": datetime.now(timezone.utc).isoformat(),
            "files": {}}


def save_state(state):
    """tmp + os.replace == atomic on POSIX. A power cut can lose the last write
    but can never leave a half-written state file."""
    state["updated"] = datetime.now(timezone.utc).isoformat()
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE_FILE)


# ── MAST query, cached ────────────────────────────────────────────────────────
def _resolve_and_query(target, suffixes):
    """Return list of product dicts for one target. Name resolution first,
    coordinate fallback second."""
    from astroquery.mast import Observations
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    radius = target["radius_arcmin"] * u.arcmin
    obs = None
    how = None

    try:
        obs = Observations.query_object(target["resolve"], radius=radius)
        how = f"name '{target['resolve']}'"
    except Exception as e:
        log(f"    name resolution failed ({e}); falling back to coordinates")

    if obs is None or len(obs) == 0:
        coord = SkyCoord(ra=target["ra"], dec=target["dec"], unit="deg")
        obs = Observations.query_region(coord, radius=radius)
        how = f"fallback coords {target['ra']:.4f} {target['dec']:+.4f}"

    log(f"    resolved via {how}: {len(obs)} observations in {target['radius_arcmin']}'")

    if len(obs) == 0:
        return []

    mode = target.get("mode", "img")

    # Imaging from the two collections we can actually use.
    keep = []
    n_pol_seen = 0
    for i, row in enumerate(obs):
        if str(row["obs_collection"]) not in ("JWST", "HST"):
            continue
        if str(row["dataproduct_type"]) != "image":
            continue
        if str(row["calib_level"]) not in ("3", "4"):
            continue
        filters = str(row.get("filters", "") or "").upper()
        is_pol = POL_TOKEN in filters
        n_pol_seen += is_pol
        # mode="pol": ONLY polarimetric observations. Taking the intensity
        # imaging too would quietly turn the negative control into another
        # shape-measurement dataset, which is not what it is for.
        if mode == "pol" and not is_pol:
            continue
        keep.append(i)

    if mode == "pol":
        log(f"    {n_pol_seen} polarimetric observations found "
            f"(filters containing '{POL_TOKEN}')")
        if n_pol_seen == 0:
            # A real, reportable result -- not an error. Record it.
            log(f"    NO POLARIMETRY IN ARCHIVE for {target['key']}. "
                f"That is a finding, log it rather than assume it.")

    if not keep:
        log("    nothing matched after filtering")
        return []
    obs = obs[keep]
    log(f"    {len(obs)} observations kept (mode={mode})")

    products = Observations.get_product_list(obs)
    log(f"    {len(products)} products listed")

    out = []
    seen = set()
    for row in products:
        fname = str(row["productFilename"])
        if fname in seen:
            continue
        if str(row["productType"]) != "SCIENCE":
            continue
        if not fname.endswith(suffixes):
            continue
        if any(p in fname.lower() for p in EXCLUDE_PATTERNS):
            continue
        seen.add(fname)
        try:
            size = int(row["size"] or 0)
        except (TypeError, ValueError):
            size = 0
        out.append({
            "filename":   fname,
            "uri":        str(row["dataURI"]),
            "size":       size,
            "target":     target["key"],
            "group":      target["group"],
            "priority":   target["priority"],
            "mode":       mode,
            "collection": str(row.get("obs_collection", "")) or "",
        })

    log(f"    -> {len(out)} science products kept, {human(sum(p['size'] for p in out))}")
    return out


def save_manifest(manifest):
    """Atomic, same tmp+os.replace discipline as save_state(). Called after
    every target so a kill mid-query never loses the targets already done."""
    tmp = MANIFEST_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, MANIFEST_FILE)


def wanted_target_keys(only=None):
    return [t["key"] for t in TARGETS if not only or t["key"] in only]


def build_manifest(suffixes, only=None, prior=None):
    """Query MAST target-by-target, checkpointing after each one.

    A full sweep is ~15 minutes of network round-trips. Writing the manifest
    only at the end meant a proot teardown at minute 14 threw away all of it
    and the next run started from zero. Now each target's products are
    flushed to disk as soon as they are known, and `targets_done` records
    which targets are already covered so a restart resumes mid-sweep.
    """
    if prior is not None:
        manifest = prior
        manifest.setdefault("products", [])
        manifest.setdefault("targets_done", [])
        manifest.setdefault("suffixes", list(suffixes))
    else:
        manifest = {"built": datetime.now(timezone.utc).isoformat(),
                    "suffixes": list(suffixes),
                    "targets_done": [],
                    "products": []}
    done = set(manifest["targets_done"])

    todo = [t for t in TARGETS if (not only or t["key"] in only) and t["key"] not in done]
    if done:
        log(f"Resuming manifest build: {len(done)} target(s) already queried, "
            f"{len(todo)} to go.")
    else:
        log("Querying MAST for all validation targets. This takes a few minutes.")

    for t in todo:
        if SHUTDOWN.requested:
            log("Shutdown requested mid-query -- partial manifest saved, "
                "the next run resumes from here.")
            break
        log(f"  [{t['group']}] {t['key']}  ({t['resolve']})")
        try:
            manifest["products"].extend(_resolve_and_query(t, suffixes))
        except Exception as e:
            log(f"    QUERY FAILED: {e}  -- target skipped, re-run with --requery to retry")
            # Not marked done: a failed query is retried on the next run,
            # whereas a successful one never is.
            continue
        manifest["targets_done"].append(t["key"])
        manifest["updated"] = datetime.now(timezone.utc).isoformat()
        save_manifest(manifest)

    save_manifest(manifest)
    log(f"Manifest: {len(manifest['products'])} products, "
        f"{human(sum(p['size'] for p in manifest['products']))} total "
        f"({len(manifest['targets_done'])}/{len(wanted_target_keys(only))} targets queried)")
    return manifest


def load_manifest(suffixes, requery=False, only=None):
    if not requery and MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE) as f:
                m = json.load(f)
            built = datetime.fromisoformat(m["built"])
            age_d = (datetime.now(timezone.utc) - built).days
            if age_d <= MANIFEST_MAX_AGE_D and set(m.get("suffixes", [])) == set(suffixes):
                # Manifests written before checkpointing existed have no
                # targets_done key; they were only ever written complete, so
                # treat a missing key as "all of them".
                if "targets_done" not in m:
                    log(f"Using cached manifest ({len(m['products'])} products, "
                        f"{age_d} d old). --requery to refresh.")
                    return m
                missing = [k for k in wanted_target_keys(only)
                           if k not in set(m["targets_done"])]
                if not missing:
                    log(f"Using cached manifest ({len(m['products'])} products, "
                        f"{age_d} d old). --requery to refresh.")
                    return m
                log(f"Cached manifest is incomplete ({len(m['targets_done'])} targets "
                    f"queried, {len(missing)} missing) -- resuming the query.")
                return build_manifest(suffixes, only=only, prior=m)
            log(f"Cached manifest is {age_d} d old or built for different product "
                f"suffixes -- rebuilding.")
        except Exception as e:
            log(f"Manifest cache unreadable ({e}) -- rebuilding.")
    return build_manifest(suffixes, only=only)


# ── Download ──────────────────────────────────────────────────────────────────
def size_ok(actual, expected):
    if expected <= 0:
        return actual > 0
    return abs(actual - expected) / expected < SIZE_TOLERANCE


def free_gb(path):
    try:
        return shutil.disk_usage(path).free / 1e9
    except OSError:
        return float("inf")


# ── Removable-volume and network safety ───────────────────────────────────────
# 2026-08-19: the Datasets drive dropped off the bus mid-run and came back as a
# DIFFERENT device node -- /dev/sdc1 -> /dev/sdd1, same UUID, ext4 journal
# recovery on remount. The mount PATH was unchanged, so the run survived by
# luck. Three things had to change for that to be by design instead of luck:
#
#   1. NEVER mkdir into the mount point. With the volume absent, the mount
#      point is an ordinary empty directory on / and mkdir -p cheerfully
#      creates the whole tree there, after which the run downloads 140 GB onto
#      the root filesystem and reports success. Every mkdir on the data side is
#      now gated on volume_ok().
#   2. Location loss is a WAIT, not a failure. A missing volume must not burn a
#      retry attempt and must not mark a file failed -- the run parks until the
#      drive is back and then resumes.
#   3. The in-flight .part is DISCARDED after a volume loss. Resume trusts the
#      byte count on disk, and an unclean disconnect plus journal recovery can
#      leave a correctly-sized tail full of zeros. One re-fetched file is much
#      cheaper than one silently corrupt FITS.
#
# Same shape for the network: total connectivity loss is a wait, not four fast
# failures that mark good files bad.
#
# The script MUST live off the volume so it can keep running and keep logging
# while the volume is gone. Asserted at import.
VOLUME_UUID      = "356095de-3a44-409a-aa7d-34db75a3d635"
VOLUME_ROOT      = Path("/media/rendier/Datasets")
VOLUME_SENTINEL  = VOLUME_ROOT / ".datasets_volume_id"
VOLUME_POLL_S    = 15          # first poll interval; doubles
VOLUME_POLL_MAX  = 300         # ...up to 5 minutes between polls
NET_PROBE_URL    = "https://mast.stsci.edu/"


class VolumeGone(OSError):
    """The data volume is not mounted. Recoverable: park and wait."""


def _mounted_device(mountpoint):
    """Device currently mounted at `mountpoint`, per /proc/mounts, or None."""
    want = str(mountpoint).replace(" ", "\\040")
    dev = None
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) > 1 and parts[1] == want:
                    dev = parts[0]          # last wins: later mounts shadow
    except OSError:
        return None
    return dev


def _uuid_of(dev):
    """UUID of a device node, resolved through /dev/disk/by-uuid."""
    if not dev:
        return None
    try:
        target = os.path.realpath(dev)
        for link in Path("/dev/disk/by-uuid").iterdir():
            if os.path.realpath(link) == target:
                return link.name
    except OSError:
        return None
    return None


def volume_ok():
    """True only if the REAL Datasets volume is mounted at VOLUME_ROOT.

    Three independent checks, because each one alone has a hole:
      ismount       catches "not mounted", but not "a different disk"
      uuid          catches a different disk, and survives sdc1 -> sdd1
      sentinel+dev  catches a stale tree left on / by an earlier mkdir
                    accident, which is the failure this whole block exists for
    """
    try:
        if not os.path.ismount(VOLUME_ROOT):
            return False
        if _uuid_of(_mounted_device(VOLUME_ROOT)) != VOLUME_UUID:
            return False
        return os.stat(VOLUME_SENTINEL).st_dev == os.stat(VOLUME_ROOT).st_dev
    except OSError:
        return False


def wait_for_volume(why=""):
    """Park until the volume returns. False only if asked to shut down."""
    if volume_ok():
        return True
    log(f"VOLUME LOST{' -- ' + why if why else ''}")
    log(f"   {VOLUME_ROOT} is not the Datasets volume ({VOLUME_UUID}).")
    log("   Parking. Nothing is marked failed; no attempt is consumed.")
    wait = waited = 0
    wait = VOLUME_POLL_S
    while not SHUTDOWN.requested:
        time.sleep(wait)
        waited += wait
        if volume_ok():
            log(f"   volume back after {waited}s ({waited/60:.1f} min). Resuming.")
            return True
        log(f"   still waiting for the volume ({waited}s)")
        wait = min(wait * 2, VOLUME_POLL_MAX)
    return False


def network_ok(session):
    try:
        session.head(NET_PROBE_URL, timeout=(10, 20), allow_redirects=True)
        return True
    except Exception:
        return False


def wait_for_network(session, why=""):
    """Park until MAST is reachable again. False only on shutdown."""
    log(f"NETWORK LOST{' -- ' + why if why else ''}")
    log("   Parking. Nothing is marked failed; no attempt is consumed.")
    wait = VOLUME_POLL_S
    waited = 0
    while not SHUTDOWN.requested:
        time.sleep(wait)
        waited += wait
        if network_ok(session):
            log(f"   network back after {waited}s ({waited/60:.1f} min). Resuming.")
            return True
        log(f"   still waiting for the network ({waited}s)")
        wait = min(wait * 2, VOLUME_POLL_MAX)
    return False


def safe_mkdir(path):
    """mkdir -p, but only ever onto the mounted volume."""
    if not volume_ok():
        raise VolumeGone(f"refusing to create {path}: volume not mounted")
    path.mkdir(parents=True, exist_ok=True)


def download_one(session, product, dest):
    """Byte-range-resumable single-file download.
    Returns (ok: bool, bytes_on_disk: int)."""
    safe_mkdir(dest.parent)
    part = dest.with_name(dest.name + ".part")
    expected = product["size"]

    if dest.exists() and size_ok(dest.stat().st_size, expected):
        return True, dest.stat().st_size

    # Group D products carry an absolute URL; MAST products carry a mast: URI.
    url = product.get("url") or (MAST_DOWNLOAD_URL + product["uri"])

    # Manual counter, not range(): a volume or network outage must NOT consume
    # an attempt. Only a genuine per-file failure does.
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        if SHUTDOWN.requested:
            return False, part.stat().st_size if part.exists() else 0

        # The volume must be present before we so much as stat the .part.
        if not volume_ok():
            if not wait_for_volume(f"before {dest.name}"):
                return False, 0
            # An unclean disconnect can leave a .part that is the right SIZE
            # and the wrong BYTES -- ext4 recovery zero-fills the tail. Resume
            # trusts the size, so the only safe move is to drop it and refetch.
            try:
                if part.exists():
                    n = part.stat().st_size
                    part.unlink()
                    log(f"      discarded {human(n)} .part written across the "
                        f"outage -- refetching {dest.name} from 0")
            except OSError:
                pass
            continue

        attempt += 1
        resume_at = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": USER_AGENT}
        if resume_at:
            headers["Range"] = f"bytes={resume_at}-"

        try:
            r = session.get(url, headers=headers, stream=True, timeout=HTTP_TIMEOUT)

            # 416 == we already have the whole thing.
            if r.status_code == 416 and part.exists():
                part.replace(dest)
                return True, dest.stat().st_size

            r.raise_for_status()

            # Critical: if we ASKED for a range and the server sent 200 instead
            # of 206, it ignored us and is streaming from byte 0. Appending
            # would silently corrupt the file. Start over.
            mode = "ab"
            if resume_at and r.status_code == 200:
                log(f"      server ignored Range (HTTP 200) -- restarting from 0")
                resume_at, mode = 0, "wb"
            elif not resume_at:
                mode = "wb"

            content_len = int(r.headers.get("content-length", 0) or 0)
            total = content_len + resume_at if content_len else expected
            if resume_at:
                log(f"      resuming at {human(resume_at)} / {human(total)}")

            got = resume_at
            last_report = time.time()
            with open(part, mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK_BYTES):
                    if not chunk:
                        continue
                    f.write(chunk)
                    got += len(chunk)
                    now = time.time()
                    if _IS_TTY:
                        pct = 100 * got / total if total else 0
                        print(f"\r      {human(got)} / {human(total)} ({pct:.1f}%)",
                              end="", flush=True)
                    elif now - last_report >= PROGRESS_EVERY:
                        # nohup'd: newline-delimited, never \r spam into the log
                        pct = 100 * got / total if total else 0
                        log(f"      {human(got)} / {human(total)} ({pct:.1f}%)")
                        last_report = now
                    if SHUTDOWN.requested:
                        f.flush()
                        os.fsync(f.fileno())
                        if _IS_TTY:
                            print()
                        log(f"      stopped at {human(got)} -- .part kept, will resume")
                        return False, got
                f.flush()
                os.fsync(f.fileno())
            if _IS_TTY:
                print()

            if not size_ok(got, expected):
                log(f"      size mismatch: got {human(got)}, expected {human(expected)}")
                # Keep the .part. Either MAST's catalog size is stale (common)
                # or the transfer was short. Accept if we got >=99% of expected,
                # otherwise retry the remainder.
                if expected > 0 and got < expected * 0.99:
                    raise IOError("short read")

            part.replace(dest)
            return True, got

        except KeyboardInterrupt:
            raise
        except Exception as e:
            if SHUTDOWN.requested:
                return False, part.stat().st_size if part.exists() else 0

            # Classify BEFORE counting. Location loss and network loss are
            # conditions of the world, not verdicts on this file, so they hand
            # the attempt back rather than spending it.
            if not volume_ok():
                attempt -= 1
                if not wait_for_volume(f"during {dest.name}: {e}"):
                    return False, 0
                continue
            if not network_ok(session):
                attempt -= 1
                if not wait_for_network(session, f"during {dest.name}: {e}"):
                    return False, part.stat().st_size if part.exists() else 0
                continue

            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            if attempt < MAX_ATTEMPTS:
                log(f"      attempt {attempt}/{MAX_ATTEMPTS} failed: {e} "
                    f"-- retrying in {wait}s")
                time.sleep(wait)
            else:
                log(f"      attempt {attempt}/{MAX_ATTEMPTS} failed: {e} -- giving up this run")

    return False, part.stat().st_size if part.exists() else 0


# ── Group D: direct-URL products ──────────────────────────────────────────────
def resolve_direct_products(session, only=None):
    """HEAD-check each candidate URL and return usable product dicts.

    A dead URL is logged with the URL itself and skipped -- IRSA and MPA
    reorganise paths between releases, and that must not take down a 60 GB
    download run that is otherwise fine."""
    out = []
    for d in DIRECT_PRODUCTS:
        if only and d["key"] not in only:
            continue
        if not d["urls"]:
            log(f"  {d['key']}: pointer only, nothing to download")
            log(f"      {d['note']}")
            continue

        chosen, size = None, 0
        for url in d["urls"]:
            try:
                r = session.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
                if r.status_code < 400:
                    chosen = url
                    size = int(r.headers.get("content-length", 0) or 0)
                    break
                log(f"  {d['key']}: HTTP {r.status_code} for {url}")
            except Exception as e:
                log(f"  {d['key']}: HEAD failed for {url}: {e}")

        if not chosen:
            log(f"  {d['key']}: NO WORKING URL -- fix the entry in DIRECT_PRODUCTS. Skipped.")
            continue

        log(f"  {d['key']}: OK  {human(size) if size else 'size unknown'}  {chosen}")
        out.append({
            "filename": d["filename"], "url": chosen, "uri": "",
            "size": size, "target": d["key"], "group": d["group"],
            "priority": d["priority"], "mode": "direct", "collection": "DIRECT",
        })
    return out


# ── Reporting ─────────────────────────────────────────────────────────────────
def print_status(state, manifest):
    files = state.get("files", {})
    by_target = {}
    for p in manifest["products"]:
        rec = files.get(p["filename"], {})
        st = rec.get("status", "pending")
        d = by_target.setdefault(p["target"], {"done": 0, "failed": 0, "pending": 0,
                                               "bytes_done": 0, "bytes_total": 0})
        d["bytes_total"] += p["size"]
        if st == "done":
            d["done"] += 1
            d["bytes_done"] += rec.get("bytes", p["size"])
        elif st == "failed":
            d["failed"] += 1
        else:
            d["pending"] += 1

    all_keys = ([(t["key"], t["group"]) for t in TARGETS]
                + [(d["key"], d["group"]) for d in DIRECT_PRODUCTS])

    log("")
    log(f"{'target':30s} {'done':>6s} {'fail':>5s} {'pend':>5s}   {'downloaded / total':>22s}")
    log("-" * 78)
    last_group = None
    for key, group in all_keys:
        if group != last_group:
            log(f"-- group {group} " + "-" * 62)
            last_group = group
        d = by_target.get(key)
        if not d:
            log(f"{key:30s} {'-':>6s} {'-':>5s} {'-':>5s}   {'(not in manifest)':>22s}")
            continue
        log(f"{key:30s} {d['done']:6d} {d['failed']:5d} {d['pending']:5d}   "
            f"{human(d['bytes_done']):>10s} / {human(d['bytes_total']):>9s}")
    log("-" * 78)
    tot_done = sum(d["bytes_done"] for d in by_target.values())
    tot_all = sum(d["bytes_total"] for d in by_target.values())
    n_done = sum(d["done"] for d in by_target.values())
    n_all = len(manifest["products"])
    log(f"{'TOTAL':30s} {n_done:6d} "
        f"{sum(d['failed'] for d in by_target.values()):5d} "
        f"{sum(d['pending'] for d in by_target.values()):5d}   "
        f"{human(tot_done):>10s} / {human(tot_all):>9s}")
    log(f"Free space on volume: {free_gb(DATA_DIR):.1f} GB")
    if n_all:
        log(f"Progress: {100*n_done/n_all:.1f}% of files, "
            f"{100*tot_done/tot_all if tot_all else 0:.1f}% of bytes")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Checkpointed MAST download for the L_(I|O) validation programme.")
    ap.add_argument("--dry-run", action="store_true",
                    help="query and report what would be fetched; download nothing")
    ap.add_argument("--status", action="store_true",
                    help="print progress from the state file and exit (does not "
                         "disturb a running instance)")
    ap.add_argument("--requery", action="store_true",
                    help="force a fresh MAST query, ignoring the manifest cache")
    ap.add_argument("--retry-failed", action="store_true",
                    help="clear failed marks so this run retries them")
    ap.add_argument("--all-products", action="store_true",
                    help="also fetch _cal/_flc/_flt/_s2d/_x1d, not just drizzled "
                         "mosaics (much larger)")
    ap.add_argument("--target", action="append", default=None, metavar="KEY",
                    help="restrict to one target key; repeatable. "
                         f"Choices: {', '.join(t['key'] for t in TARGETS)}")
    ap.add_argument("--group", action="append", default=None,
                    choices=["A", "B", "C", "D", "E"],
                    help="restrict to a group; repeatable. "
                         "A=Einstein Crosses, B=UCDs/DM-poor dwarfs, "
                         "C=non-lensing polarization negative control, "
                         "D=Planck/all-sky direct-URL products, "
                         "E=Bullet Cluster itself")
    ap.add_argument("--verify-urls", action="store_true",
                    help="HEAD-check every group-D URL and exit; downloads nothing. "
                         "Run this first -- external archives move their paths.")
    ap.add_argument("--no-direct", action="store_true",
                    help="skip group D (direct-URL) products entirely")
    ap.add_argument("--budget-gb", type=float, default=DEFAULT_BUDGET_GB,
                    help=f"stop after this many GB this run (default {DEFAULT_BUDGET_GB})")
    args = ap.parse_args()

    suffixes = ALL_SUFFIXES if args.all_products else DEFAULT_SUFFIXES
    only = set(args.target) if args.target else None
    groups = set(args.group) if args.group else None
    if only:
        valid = {t["key"] for t in TARGETS} | {d["key"] for d in DIRECT_PRODUCTS}
        bad = only - valid
        if bad:
            print(f"Unknown target key(s): {', '.join(sorted(bad))}", file=sys.stderr)
            print(f"Valid: {', '.join(sorted(valid))}", file=sys.stderr)
            sys.exit(2)

    # --verify-urls is read-only and needs no lock or MAST query.
    if args.verify_urls:
        log("HEAD-checking all group-D direct URLs...")
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        found = resolve_direct_products(s, only=only)
        log("")
        log(f"{len(found)}/{len([d for d in DIRECT_PRODUCTS if d['urls']])} "
            f"direct URLs reachable, {human(sum(p['size'] for p in found))} total")
        return

    # --status is read-only: no lock, no query, safe while a download runs.
    if args.status:
        if not MANIFEST_FILE.exists():
            print("No manifest yet -- nothing has been queried.", file=sys.stderr)
            sys.exit(1)
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
        print_status(load_state(), manifest)
        return

    acquire_lock()
    try:
        # free_gb() returns inf on OSError, so a missing DATA_DIR would silently
        # disable the free-space floor. Make sure it exists before any check --
        # but ONLY on the real volume. The unguarded mkdir this replaces would,
        # with the drive absent, have built the tree on / and filled the root
        # filesystem while reporting success.
        if not wait_for_volume("at startup"):
            log("Shutdown while waiting for the volume.")
            return
        safe_mkdir(DATA_DIR)
        log("=" * 76)
        log("L_(I|O) validation download")
        log(f"pid {os.getpid()}  |  data -> {DATA_DIR}")
        log(f"products: {'ALL levels' if args.all_products else 'drizzled mosaics only'} "
            f"{suffixes}")
        log(f"budget this run: {args.budget_gb:.0f} GB  |  free now: {free_gb(DATA_DIR):.1f} GB")
        log("=" * 76)

        # Group D is direct-URL only. If that is all that was asked for, skip the
        # MAST query entirely -- it needs astroquery, takes minutes, and would
        # contribute nothing.
        direct_only = (groups == {"D"}) or (
            only is not None and all(any(d["key"] == k for d in DIRECT_PRODUCTS)
                                     for k in only))
        if direct_only:
            log("Direct-URL products only -- skipping the MAST query.")
            manifest = {"built": datetime.now(timezone.utc).isoformat(),
                        "suffixes": list(suffixes), "products": []}
        else:
            manifest = load_manifest(suffixes, requery=args.requery, only=only)
        state = load_state()
        files = state.setdefault("files", {})

        if args.retry_failed:
            n = 0
            for rec in files.values():
                if rec.get("status") == "failed":
                    rec["status"] = "pending"
                    n += 1
            save_state(state)
            log(f"Cleared {n} failed marks.")

        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        products = list(manifest["products"])

        # Group D is resolved live (HEAD-checked) rather than cached, because
        # external archive URLs go stale independently of the MAST manifest.
        want_direct = (not args.no_direct
                       and (groups is None or "D" in groups)
                       and (only is None or any(d["key"] in only for d in DIRECT_PRODUCTS)))
        if want_direct:
            log("")
            log("Resolving group-D direct-URL products...")
            products += resolve_direct_products(session, only=only)

        if only:
            products = [p for p in products if p["target"] in only]
        if groups:
            products = [p for p in products if p["group"] in groups]

        # Priority first, then small files first inside a priority -- gets the
        # most targets to a usable state soonest if the run is cut short.
        products.sort(key=lambda p: (p["priority"], p["group"], p["size"]))

        todo = [p for p in products
                if files.get(p["filename"], {}).get("status") != "done"]

        log("")
        log(f"{len(products)} products in scope | {len(products)-len(todo)} already done "
            f"| {len(todo)} to fetch ({human(sum(p['size'] for p in todo))})")

        if args.dry_run:
            log("")
            log("DRY RUN -- nothing will be downloaded.")
            notes = {t["key"]: (t["group"], t["note"]) for t in TARGETS}
            notes.update({d["key"]: (d["group"], d["note"]) for d in DIRECT_PRODUCTS})
            cur = None
            for p in todo:
                if p["target"] != cur:
                    cur = p["target"]
                    grp, note = notes.get(cur, (p["group"], ""))
                    log("")
                    log(f"  [{grp}] {cur}")
                    if note:
                        log(f"      {note}")
                log(f"      {p['collection']:6s} {p['filename']:58s} {human(p['size']):>10s}")
            print_status(state, {"products": products})
            return

        budget_bytes = args.budget_gb * 1e9
        spent = 0
        n_ok = n_fail = 0

        for i, p in enumerate(todo, 1):
            if SHUTDOWN.requested:
                log("Shutdown requested -- stopping cleanly.")
                break

            if spent >= budget_bytes:
                log(f"Run budget of {args.budget_gb:.0f} GB reached. "
                    f"Re-run to continue (state is saved).")
                break

            # Volume first: free_gb() on a vanished mount reads / , not sdd1,
            # and would happily report hundreds of GB free on the wrong disk.
            if not volume_ok() and not wait_for_volume(f"before [{i}/{len(todo)}]"):
                log("Shutdown while waiting for the volume -- stopping cleanly.")
                break

            avail = free_gb(DATA_DIR)
            if avail < MIN_FREE_GB:
                log(f"Only {avail:.1f} GB free (floor is {MIN_FREE_GB} GB). Stopping.")
                break
            if p["size"] and avail * 1e9 - p["size"] < MIN_FREE_GB * 1e9:
                log(f"Skipping {p['filename']} ({human(p['size'])}) -- would breach "
                    f"the {MIN_FREE_GB} GB free-space floor.")
                continue

            dest = DATA_DIR / p["target"] / p["filename"]
            log(f"[{i}/{len(todo)}] {p['target']} :: {p['filename']}  ({human(p['size'])})")

            ok, nbytes = download_one(session, p, dest)

            files[p["filename"]] = {
                "status":  "done" if ok else "failed",
                "target":  p["target"],
                "bytes":   nbytes,
                "size":    p["size"],
                "path":    str(dest.relative_to(HERE)),
                "updated": datetime.now(timezone.utc).isoformat(),
            }
            save_state(state)      # checkpoint after EVERY file

            if ok:
                n_ok += 1
                spent += nbytes
                log(f"      OK  {human(nbytes)}  "
                    f"(run total {human(spent)} / {args.budget_gb:.0f} GB budget)")
            else:
                n_fail += 1

        log("")
        log("=" * 76)
        log(f"This run: {n_ok} downloaded, {n_fail} failed, {human(spent)} transferred")
        if n_fail:
            log("Re-run with --retry-failed to retry them.")
        print_status(state, {"products": products})
        log("=" * 76)

    finally:
        release_lock()


if __name__ == "__main__":
    main()
