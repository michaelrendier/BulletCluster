#!/usr/bin/env python3
"""Offline tests for the --huchra mode of download_validation_targets.py (2026-10-17).

Nothing here touches the network or MAST: astroquery is faked, robots_verdict is faked, and every file the mode writes
(state, manifests, logs, locks) is redirected to a temp directory so a test manifest can never be mistaken for a real one.
Run:  python3 test_huchra_mode.py
"""
import json, math, os, sys, tempfile, types, unittest
from pathlib import Path

import numpy as np
from astropy.table import Table

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import download_validation_targets as dv          # noqa: E402


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        c = dv.classify_tier
        for f in ("ib0r02u2q_flc.fits", "ib0r02u2q_flt.fits", "ib0r02u2q_raw.fits", "ib0r02u2q_spt.fits",
                  "ib0r02u2q_jit.fits", "ib0r02u2q_jif.fits", "ib0r02010_asn.fits", "jw0_cal.fits", "jw0_rate.fits",
                  "jw01_asn.json", "u2lg0401t_c0m.fits", "u2lg0401t_d0m.fits", "ib0r02u2q_flt_hlet.fits", "x_trl.fits"):
            self.assertEqual(c(f), 1, f)
        for f in ("hst_drz.fits", "x_drc.fits", "jw_i2d.fits", "jw_s2d.fits", "x_cat.ecsv", "jw_crf.fits"):
            self.assertEqual(c(f), 2, f)
        for f in ("jw_uncal.fits", "jw_rateints.fits", "jw_calints.fits", "jw_ramp.fits"):
            self.assertEqual(c(f), 3, f)
        for f in ("ib0r02u2q_flc.jpg", "x_thumb.png", "preview_1.jpg"):
            self.assertEqual(c(f), 9, f)

    def test_pol(self):
        self.assertTrue(dv.is_pol_obs({"filters": "POL0V;F606W", "instrument_name": "ACS/WFC"}))
        self.assertTrue(dv.is_pol_obs({"filters": "POLQ", "instrument_name": "WFPC2"}))
        self.assertTrue(dv.is_pol_obs({"filters": "POL120S", "instrument_name": "NICMOS/NIC2"}))
        self.assertFalse(dv.is_pol_obs({"filters": "F555W", "instrument_name": "WFC3/UVIS"}))


class TestGeometry(unittest.TestCase):
    RA, DEC = 340.125975, 3.3585083        # Q2237+0305, SIMBAD

    def test_earth_speed_and_orbit(self):
        g = dv.earth_geometry(55000.0, self.RA, self.DEC)
        self.assertTrue(29.0 < g["earth_speed_kms"] < 30.6, g["earth_speed_kms"])      # Earth's orbital speed
        self.assertTrue(0.982 < np.linalg.norm(g["earth_pos_au"]) < 1.018)              # 1 au to within the ellipse
        self.assertLess(g["parallax_baseline_au"], 1.02)

    def test_aberration_amplitude_over_a_year(self):
        vals = [dv.earth_geometry(55000.0 + d, self.RA, self.DEC)["aberration_arcsec"] for d in range(0, 366, 5)]
        self.assertTrue(19.5 < max(vals) < 20.7, max(vals))          # constant of aberration, 20.4955 arcsec
        self.assertLess(min(vals), 4.0)                              # target is near the ecliptic: ~0 at the turning points

    def test_light_time_scale(self):
        lt = [dv.earth_geometry(55000.0 + d, self.RA, self.DEC)["light_time_s"] for d in range(0, 366, 15)]
        self.assertTrue(480 < max(lt) < 510 and -510 < min(lt) < -480, (min(lt), max(lt)))   # +-1 au / c = +-499 s

    def test_observatory_offsets(self):
        self.assertAlmostEqual(dv.OBSERVATORY_OFFSET_AU["JWST"], 0.0100, delta=0.0005)
        self.assertAlmostEqual(dv.OBSERVATORY_OFFSET_AU["HST"], 4.6e-5, delta=0.3e-5)


class TestGuards(unittest.TestCase):
    def test_local_volume_rule(self):
        old = dv.LOCAL_DATA_ROOT
        try:
            dv.LOCAL_DATA_ROOT = Path("/tmp/claude-1000/never_here")        # system partition
            self.assertFalse(dv.local_volume_ok())
            dv.LOCAL_DATA_ROOT = Path.home() / "Projects" / "x_does_not_exist_yet" / "data"   # /home partition
            self.assertTrue(dv.local_volume_ok())
        finally:
            dv.LOCAL_DATA_ROOT = old

    def test_old_guard_untouched(self):
        self.assertIsNone(dv.LOCAL_DATA_ROOT)            # default behaviour unchanged for every other mode


class TestHeaderScan(unittest.TestCase):
    def test_real_local_file(self):
        cand = sorted((HERE / "data.premigration" / "A5_q2237+0305").glob("ic3u12050_drz.fits")) or \
               sorted((HERE / "data.premigration" / "A5_q2237+0305").glob("*.fits"))
        if not cand:
            self.skipTest("no local FITS to scan")
        out = dv.scan_headers(cand[0])
        self.assertNotIn("_error", out)
        self.assertIn("INSTRUME", out)
        print("   header keys recorded from", cand[0].name, "->", sorted(out)[:40])


def _fake_astroquery(obs_rows, prod_rows):
    class _Sess:  headers = {}
    class Observations:
        _session = _Sess()
        @staticmethod
        def query_region(coord, radius=None):
            return Table(rows=obs_rows[0], names=obs_rows[1])
        @staticmethod
        def get_product_list(obs):
            ids = {str(x) for x in obs["obsid"]}
            rows = [r for r in prod_rows[0] if str(r[0]) in ids]
            return Table(rows=rows, names=prod_rows[1]) if rows else Table(names=prod_rows[1])
    pkg = types.ModuleType("astroquery"); mast = types.ModuleType("astroquery.mast")
    mast.Observations = Observations; pkg.mast = mast
    sys.modules["astroquery"], sys.modules["astroquery.mast"] = pkg, mast


OBS_COLS = ["obsid", "obs_collection", "instrument_name", "filters", "proposal_id", "proposal_pi", "obs_id", "target_name",
            "dataproduct_type", "calib_level", "t_min", "t_max", "t_exptime", "s_ra", "s_dec"]
PROD_COLS = ["parent_obsid", "productFilename", "dataURI", "size", "productType", "productSubGroupDescription"]


def _obs(i, coll, inst, filt, mjd=55200.0):
    return (i, coll, inst, filt, "11791", "Someone", f"x{i}", "Q2237+0305", "image", 2, mjd, mjd + 0.01, 700.0, 340.126, 3.3586)


def _prod(i, name, size=1000, ptype="SCIENCE"):
    return (i, name, f"mast:HST/product/{name}", size, ptype, "X")


class TestStages(unittest.TestCase):
    def setUp(self):
        self.obs = ([_obs(1, "HST", "WFC3/UVIS", "F555W"), _obs(2, "HST", "ACS/WFC", "POL0V;F606W"),
                     _obs(3, "HST", "COS/NUV", "G230L"), _obs(4, "HLA", "WFC3/UVIS", "F555W")], OBS_COLS)
        self.prod = ([_prod(1, "a_flt.fits"), _prod(1, "a_drz.fits"), _prod(1, "a_flt.jpg"), _prod(1, "a_spt.fits"),
                      _prod(1, "a_uncal.fits"), _prod(2, "p_flc.fits"), _prod(3, "c_x1d.fits")], PROD_COLS)
        _fake_astroquery(self.obs, self.prod)

    def test_hst_stage_excludes_pol_cos_and_previews(self):
        m = dv.build_huchra_manifest("hst", {1, 2})
        names = {p["filename"] for p in m["products"]}
        self.assertEqual(names, {"a_flt.fits", "a_drz.fits", "a_spt.fits"})        # no jpg, no uncal (tier 3), no pol, no COS
        self.assertTrue(all("geometry" in o for o in m["observations"].values()))
        self.assertEqual([p["tier"] for p in m["products"]][:2], [1, 1])            # tier 1 first

    def test_pol_stage(self):
        m = dv.build_huchra_manifest("pol", {1, 2})
        self.assertEqual({p["filename"] for p in m["products"]}, {"p_flc.fits"})

    def test_jwst_stage_none_is_a_finding(self):
        m = dv.build_huchra_manifest("jwst", {1, 2})
        self.assertEqual(m["products"], [])
        self.assertEqual(len(m["findings"]), 1)
        self.assertIn("NO JWST OBSERVATIONS", m["findings"][0])

    def test_tier3_opt_in(self):
        m = dv.build_huchra_manifest("hst", {1, 2, 3})
        self.assertIn("a_uncal.fits", {p["filename"] for p in m["products"]})


class TestEndToEndDryRun(unittest.TestCase):
    def test_dry_run_flow_writes_only_to_temp(self):
        obs = ([_obs(1, "HST", "WFC3/UVIS", "F555W")], OBS_COLS)
        prod = ([_prod(1, "a_flt.fits", 168_000_000), _prod(1, "a_spt.fits", 100_000)], PROD_COLS)
        _fake_astroquery(obs, prod)
        with tempfile.TemporaryDirectory(dir=str(Path.home() / ".cache")) as td:       # /home partition, not /tmp
            td = Path(td)
            saved = {k: getattr(dv, k) for k in ("HERE", "GLOBAL_LOCK", "robots_verdict")}
            dv.HERE, dv.GLOBAL_LOCK = td, td / "global.pid"
            dv.robots_verdict = lambda host, paths, session=None: {
                "host": host, "state": "parsed", "crawl_delay": None, "allowed": {p: False for p in paths}}
            argv = sys.argv
            try:
                sys.argv = ["x", "--huchra", "hst", "--dry-run", "--data-dir", str(td / "data")]
                dv.main()
            finally:
                sys.argv = argv
                for k, v in saved.items():
                    setattr(dv, k, v)
                dv.LOCAL_DATA_ROOT = None
                dv.LOG_FILE = HERE / "validation_download.log"; dv.STATE_FILE = HERE / "validation_download_state.json"
                dv.PID_FILE = HERE / "validation_download.pid"; dv.DATA_DIR = HERE / "data"
            mf = json.load(open(td / "validation_manifest_huchra_hst.json"))
            self.assertEqual(len(mf["products"]), 2)
            self.assertFalse(all(mf["robots"]["allowed"].values()))          # verdict recorded in the manifest
            self.assertFalse((td / "global.pid").exists())                    # lock released
            self.assertFalse(any((td / "data").rglob("*.fits")) if (td / "data").exists() else False)   # dry run: nothing fetched

    def test_respect_robots_refuses(self):
        _fake_astroquery(([_obs(1, "HST", "WFC3/UVIS", "F555W")], OBS_COLS), ([], PROD_COLS))
        with tempfile.TemporaryDirectory(dir=str(Path.home() / ".cache")) as td:
            td = Path(td)
            saved = {k: getattr(dv, k) for k in ("HERE", "GLOBAL_LOCK", "robots_verdict")}
            dv.HERE, dv.GLOBAL_LOCK = td, td / "global.pid"
            dv.robots_verdict = lambda host, paths, session=None: {"host": host, "state": "parsed", "allowed": {p: False for p in paths}}
            argv = sys.argv
            try:
                sys.argv = ["x", "--huchra", "hst", "--dry-run", "--respect-robots", "--data-dir", str(td / "data")]
                with self.assertRaises(SystemExit) as cm:
                    dv.main()
                self.assertEqual(cm.exception.code, 4)
            finally:
                sys.argv = argv
                for k, v in saved.items():
                    setattr(dv, k, v)
                dv.LOCAL_DATA_ROOT = None
                dv.LOG_FILE = HERE / "validation_download.log"; dv.STATE_FILE = HERE / "validation_download_state.json"
                dv.PID_FILE = HERE / "validation_download.pid"; dv.DATA_DIR = HERE / "data"
            self.assertFalse((td / "validation_manifest_huchra_hst.json").exists())   # refused BEFORE any query


if __name__ == "__main__":
    unittest.main(verbosity=2)
