# NRAO requests for the Crab nebula and pulsar polarization control set (recorded 2026-11-20)

The author placed these requests in the NRAO Archive Access Tool and received a completion email for each. **Nothing has been downloaded from them by Claude; the author said to record the links and methods only.** The links carry a per-request key, so they are NOT in this README: they are in `links_PRIVATE.md` (gitignored; the master copy is `~/Desktop/SpaceClaude/BulletCluster/nrao-downloads.txt`). This repository is public: never commit the keyed URLs.

Plan the requests came from: `already_evaluated/CrabNebula/VLA_REQUEST_v2_2026-11-17.md` (nebula time series: 12B-380, 12A-486, 11A-268, 14B-341, AH919; pulsar: 15B-252, 22B-192, 25A-385, AGBT19B_352, AGBT18B_338, plus extra EVLA blocks found by position). The emails give only request numbers, so the seven undownloaded EVLA requests cannot yet be matched to projects.

| request | type | project (sizes from the author, 2026-11-18) | size | emailed | status | note |
|---|---|---|---|---|---|---|
| 302944689 | EVLA | 12B-380 | 360.0 GB | Wed Nov 18, 5:57 AM | NOT DOWNLOADED | basic measurement set, uncalibrated (author) |
| 302954368 | EVLA | 12A-486 | 192.4 GB | Wed Nov 18, 12:14 AM | NOT DOWNLOADED |  |
| 302964371 | EVLA | 11A-268 | 21.4 GB | Tue Nov 17, 7:11 PM | ACQUIRED (19.29 GB on disk) | two tarballs in CrabNebula/data/nrao/11A-268/; 2.1 GB shorter than the stated 21.4 GB, unexplained (a third file? .rar versus .tar.gz overhead?); the request listing would settle it |
| 302969789 | EVLA | **11B-341**, as the author labelled it (identity not checked; NOT the Crab project 14B-341) | 920.9 GB | Wed Nov 18, 5:23 PM | NOT DOWNLOADED | larger than any drive's free space; the author's own label, kept as written |
| 302986674 | EVLA | AH919 | 179.1 MB | Wed Nov 18, 12:09 PM | ACQUIRED | the 179,118,080-byte tar on disk equals the stated 179.1 MB exactly |
| 302994447 | EVLA | 15B-252 | 525.0 GB | Wed Nov 18, 8:30 AM | NOT DOWNLOADED |  |
| 302999511 | EVLA | 22B-192 | 494.2 GB | Wed Nov 18, 11:50 AM | NOT DOWNLOADED |  |
| 303004365 | EVLA | 25A-385 | 125.5 GB | Tue Nov 17, 11:03 PM | NOT DOWNLOADED |  |
| 303010600 | GBT | AGBT19B_352 | 16.5 MB | Tue Nov 17, 6:46 PM | ACQUIRED | two tarballs, 16,506,880 bytes = 16.5 MB exactly |
| 303031735 | GBT | AGBT18B_338 | 31.3 MB | Tue Nov 17, 6:46 PM | ACQUIRED | 31,344,640 bytes = 31.3 MB exactly |

**How the requests were matched to projects (INFERRED, one anchor confirmed).** The emails give only request numbers, but the numbers rise in the order the author requested the projects (the plan's order, and the order the author quoted the sizes): 12B-380, 12A-486, 11A-268, then the 920.9 GB request (the author's label 11B-341; the plan's slot was 14B-341), AH919, 15B-252, 22B-192, 25A-385, then the two GBT. The anchor `302964371` = `11A-268` is certain (the on-disk file names end in that number), it falls third in that order as predicted, and the two GBT requests are the two highest numbers and the only ones on the `dl-naasc` host. The remaining matches follow from the order and are not independently confirmed: listing a request (file names start with the project code) confirms each. The author's sizes are from messages of 2026-11-17 18:02-18:42 local; the files arrive as `.rar` (extractable here with `7z`).

## 2026-11-27 (late): the EVLA links no longer answer
Probed read-only (Mozilla UA, HEAD and GET of each `direct` directory): **all eight EVLA request directories on `dl-dsoc.nrao.edu` return HTTP 404**, including 302964371 (11A-268), which was downloaded on 2026-11-17/18. Both GBT requests on `dl-naasc.nrao.edu` still answer 200 and list their files plus `SHA1SUMS`. The keyed request pages on `data.nrao.edu` now go to the NRAO login chooser (a login page is a stop; nothing was attempted). The likeliest cause is expiry of the EVLA request copies (emails of 17-18 Nov, nine to ten days earlier); the GBT copies of the same dates are still served. **To fetch the EVLA projects the author has to re-request them in the Archive Access Tool (his login) and send the new emails.** Plan for the 700 GB laptop: 25A-385 (125.5), 11A-268 (21.4), 12A-486 (192.4), 12B-380 (360.0) = 699.3 GB; skipped: 15B-252 (525.0), 22B-192 (494.2), the author's 11B-341 (920.9).

The tool for the second machine is in `crab_fetch/` (no keys in it): `nrao_fetch.py` (stdlib only: `--setup`, `--plan`, `--probe`, `--run`, `--status`, `--add-link`), `fetch_crab.sh` (restart loop, network wait, systemd-inhibit, memory cap, optional systemd user service), `test_nrao_fetch.py` (14 checks against a local mock server: connection drop mid-file, Range resume, a crash with a damaged `.part` tail, corruption caught by SHA1SUMS, expiry, login page, disk guard, budget), `build_bundle.py` (writes the private transfer folder with `links.txt` outside the repository, `~/Desktop/SpaceClaude/BulletCluster/CrabTransfer/`). It was also run against the two live GBT links: both fetched, SHA1 verified, sizes equal to the files already on disk (31,344,640 and 9,932,800 + 6,574,080 bytes).

## Open: the Crab project 14B-341 has NOT been requested (author, 2026-11-20)
The 920.9 GB request is the author's `11B-341`, not `14B-341` ("Exploring the exotic chemistry of the Crab nebula", EVLA, 2014-10-19 to 2014-11-12, 4 execution blocks, the one in the plan). The author will request 14B-341 from the archive; when its completion email arrives, add its request number, size and links here (links to `links_PRIVATE.md`). Plan: take the two 2014-11-12 blocks (9.1 and 23.5 cm) first; the 2.2 and 1.7 cm blocks are very large. Its size is unknown until requested, so it is NOT in the total below. What 11B-341 is has not been looked up (the author's project list of 2026-11-17 had no such project).

## What is left to download from NRAO
The three megabyte-sized requests (AH919, AGBT19B_352, AGBT18B_338) are already on disk. Everything else is gigabyte-sized:

| project | request | size |
|---|---|---|
| 12B-380 | 302944689 | 360.0 GB |
| 12A-486 | 302954368 | 192.4 GB |
| 11B-341 (author's label) | 302969789 | 920.9 GB |
| 15B-252 | 302994447 | 525.0 GB |
| 22B-192 | 302999511 | 494.2 GB |
| 25A-385 | 303004365 | 125.5 GB |
| **total still to download** | 6 requests | **2,618.0 GB (about 2.6 TB)** |

Plus the 2.1 GB of 11A-268 that is not accounted for (21.4 GB stated, 19.29 GB on disk). All eight EVLA projects together are 2,639.4 GB; 19.3 GB of that is already here.

**Storage.** `Telescope Data` has 345 GB free (about 452 GB if the cleanup candidates were removed); `SDCard` is 235 GB; the 750 GB drive the author was formatting is not mounted. So nothing fits at once: 14B-341 (920.9 GB) is larger than any single drive, and 15B-252 (525 GB) and 22B-192 (494 GB) exceed even the cleaned-up free space. The author's plan is download, evaluate and discard, project by project; 12A-486 (192.4 GB) and 25A-385 (125.5 GB) fit now, 12B-380 (360 GB) needs the cleanup first, and the three over 490 GB need an empty drive of at least 1 TB or a per-block split of the request (14B-341 has four blocks; the plan said take the two 2014-11-12 blocks first).

## Method for when the downloads are wanted
Standing rules (the author's, from the telescope-download skill): Mozilla user agent on every request (`$CLAUDE_UA`), ONE download at a time, the author's explicit go first, the author's email is never sent, failures are logged and not repaired, free-space guard on `Telescope Data` (stop at 20 GB spare, overflow to `/media/rendier/SDCard`), record each download under `already_evaluated/CrabNebula/`. Telescope Data's USB bridge has dropped under heavy load (2026-11-17, 2026-11-20): throttle (`ionice -c3 nice`), keep the `noatime` mount, one stream.

1. **List first (read-only, small).** Fetch the request's page or directory index (`<DIRECT>`) to get file names and sizes, and report the total. The names reveal the project (`<project>_sb...` / `<project>.sb....eb....`); sort into `CrabNebula/data/nrao/<project>/`. Flag anything over about 100 GB before queuing (Telescope Data has ~345 GB free; the cleanup list in `../../TODO.md` would add ~110 GB).
2. **Download** (files arrive as `.rar`; extract with `7z x`). NRAO's own commands, with the Mozilla user agent added:
   * `wget -r -l 10 --reject "index.html*" -np -nH --cut-dirs=3 --user-agent="$CLAUDE_UA" -c <DIRECT>`
   * Calibrated or basic measurement sets can exceed 100 GB and plain `wget` may fail; NRAO recommends `wget2 -r -l 10 --reject-regex="index.html*" --progress=bar -np -nH --cut-dirs=3 --user-agent="$CLAUDE_UA" <DIRECT>`.
   * Resumable alternative that fits the skill: turn the listing into a manifest of per-file URLs and run `telescope_download.py MANIFEST.json --state STATE.json --min-free-gb 20` (8 MB chunks, `.part` files, HTTP Range resume, sha256 recorded, a status line every 15 minutes through Monitor).
3. **Verify** each file (size against the listing; `gzip -t` / `tar -tf` for archives), record size and sha256, and write the record to `already_evaluated/CrabNebula/`.
4. **Hosts:** EVLA requests are served from `dl-dsoc.nrao.edu`; GBT requests from `dl-naasc.nrao.edu`.
5. **Expiry:** NRAO keeps request data for a limited time (confirm the period on the request page); the emails are dated 17-18 Nov 2026, so list the requests soon even if the downloads wait.
6. **Reduction later:** the EVLA products are Calibrated Measurement Sets (as in the 11A-268 and HE 0435 tarballs); imaging Stokes Q/U needs CASA (`BulletCluster/.venv` has `casatools` and `casatasks`).
