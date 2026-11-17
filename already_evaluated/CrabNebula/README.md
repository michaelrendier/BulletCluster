# Crab Nebula (M1, Taurus A): retrieval record, started 2026-11-16

Purpose (author, 2026-11-16): a supernova-remnant polarization control for the Witch's Hat family: real polarization, one JWST image as the background scaffold, polarization over time. The Crab's polarization is intrinsic synchrotron, so it is a control for polarization measurement, not for scattering.

Data root: `/media/rendier/Telescope Data/CrabNebula/` (manifest, state, download.log, `data/`).
Survey (read-only, MAST + NRAO TAP, 2026-11-16): JWST program 1714 (NIRCam F150W2+F162M and F480M, Oct 2022; MIRI imaging and IFU, Feb–Mar 2023; no JWST polarimetry); HST polarizers WFPC2 F547M-POLQ 1996-01-26 (6129), NICMOS POL0L/120L/240L 1997-12-15 (7238), ACS/WFC F606W-POL0V/60V/120V 2003-08-08/09 (9787); VLA full-pol blocks 2010–2026 (`VLA_REQUEST_2026-11-16.md`).

Downloaded on 2026-11-16 (43 files, 1.94 GB, `manifest.json`): JWST NIRCam F480M level-3 `i2d` (scaffold, 1.32 GB); ACS flc ×6 and HAP drc ×3 (polarizers); WFPC2 c0f/c0m/c1f/c3t ×6 exposures; NICMOS cal/ima/raw ×3.
Not downloaded: NIRCam F150W2+F162M `i2d` (8.9 GB), MIRI, Chandra, IXPE, Euclid (no polarimeter), VLA (requires the NRAO portal; the author supplies links; the author's email is never sent by the assistant).
Re-fetch: `run_download.sh manifest.json state.json "/media/rendier/Telescope Data" download.log` from the telescope-download skill; MAST file URLs `https://mast.stsci.edu/api/v0.1/Download/file?uri=<dataURI>`.

## Result (2026-11-17 00:04)
43 of 43 files downloaded, 1.94 GB, in about 13 minutes of transfer; sizes match the manifest for all 43; every file opens with astropy; headers confirm the target and instrument: NIRCam F480M 2022-10-31 (`Crab Nebula`); ACS F606W with POL0V/POL60V/POL120V 2003-08-08/09 (`CRAB-POL`); NICMOS POL0L/POL120L/POL240L 1997-12-15 (`CRAB-FK10`); WFPC2 1996-01-26 (`CRAB-PULSAR`, filter given as wheel position 24 in the header; the archive lists it as F547M-POLQ). The WFPC2 `c3t` table files have no image header and were checked by size only.

## Download 2 and a drive fault (2026-11-17 01:32)
Second manifest (`manifest2.json`, 18 JWST level-3 mosaics: MIRI in 7 filters across 5 pointings, and NIRCam F150W2+F162M, 10.5 GB) — 17 of 18 complete and re-hashed against the recorded sha256 (60 of 60 Crab files verified, 0 bad). The NIRCam F150W2+F162M mosaic stopped at 2.66 GB of 8.92 GB: the kernel logged `critical target error, dev sda, WRITE` and ext4 `I/O error 5 writing to inode 30408780` (the .part file) on `/dev/sda` (the Telescope Data drive, JMicron JMS578 USB-SATA bridge), and the downloader returned Errno 121 twice before the downloader was stopped by hand. No repair was attempted. The queued Planck SMICA download (`/media/rendier/Telescope Data/Planck/manifest.json`) was cancelled before it started. Resume the mosaic with the same command once the drive is checked.
