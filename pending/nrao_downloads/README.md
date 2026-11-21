# NRAO requests for the Crab nebula and pulsar polarization control set (recorded 2026-11-20)

The author placed these requests in the NRAO Archive Access Tool and received a completion email for each. **Nothing has been downloaded from them by Claude; the author said to record the links and methods only.** The links carry a per-request key, so they are NOT in this README: they are in `links_PRIVATE.md` (gitignored; the master copy is `~/Desktop/SpaceClaude/BulletCluster/nrao-downloads.txt`). This repository is public: never commit the keyed URLs.

Plan the requests came from: `already_evaluated/CrabNebula/VLA_REQUEST_v2_2026-11-17.md` (nebula time series: 12B-380, 12A-486, 11A-268, 14B-341, AH919; pulsar: 15B-252, 22B-192, 25A-385, AGBT19B_352, AGBT18B_338, plus extra EVLA blocks found by position). The emails give only request numbers, so the seven undownloaded EVLA requests cannot yet be matched to projects.

| request | type | host | emailed | status |
|---|---|---|---|---|
| 302944689 | EVLA | dl-dsoc.nrao.edu | Wed, Nov 18, 5:57 AM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 302954368 | EVLA | dl-dsoc.nrao.edu | Wed, Nov 18, 12:14 AM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 302964371 | EVLA | dl-dsoc.nrao.edu | Tue, Nov 17, 7:11 PM | ACQUIRED: the two 9.6 GB `11A-268` calibrated measurement-set tarballs (file names end in this request number) are in `Telescope Data/CrabNebula/data/nrao/11A-268/`. |
| 302969789 | EVLA | dl-dsoc.nrao.edu | Nov 18, 2026, 5:23 PM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 302986674 | EVLA | dl-dsoc.nrao.edu | Wed, Nov 18, 12:09 PM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 302994447 | EVLA | dl-dsoc.nrao.edu | Wed, Nov 18, 8:30 AM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 302999511 | EVLA | dl-dsoc.nrao.edu | Wed, Nov 18, 11:50 AM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 303004365 | EVLA | dl-dsoc.nrao.edu | Tue, Nov 17, 11:03 PM | NOT DOWNLOADED. Project and size unknown: the email names neither; open the request page (or list the direct URL, read-only) to see files and sizes. |
| 303010600 | GBT | dl-naasc.nrao.edu | Tue, Nov 17, 6:46 PM | ACQUIRED per the author ('the two small ones'): the other GBT request (request-to-project order not recorded). |
| 303031735 | GBT | dl-naasc.nrao.edu | Tue, Nov 17, 6:46 PM | ACQUIRED per the author ('the two small ones'): one of the two GBT requests; the `AGBT18B_338` and `AGBT19B_352` tarballs are in `Telescope Data/CrabNebula/data/nrao/`. |

## Method for when the downloads are wanted
Standing rules (the author's, from the telescope-download skill): Mozilla user agent on every request (`$CLAUDE_UA`), ONE download at a time, the author's explicit go first, the author's email is never sent, failures are logged and not repaired, free-space guard on `Telescope Data` (stop at 20 GB spare, overflow to `/media/rendier/SDCard`), record each download under `already_evaluated/CrabNebula/`. Telescope Data's USB bridge has dropped under heavy load (2026-11-17, 2026-11-20): throttle (`ionice -c3 nice`), keep the `noatime` mount, one stream.

1. **List first (read-only, small).** Fetch the request's page or directory index (`<DIRECT>`) to get file names and sizes, and report the total. The names reveal the project (`<project>_sb...` / `<project>.sb....eb....`); sort into `CrabNebula/data/nrao/<project>/`. Flag anything over about 100 GB before queuing (Telescope Data has ~345 GB free; the cleanup list in `../../TODO.md` would add ~110 GB).
2. **Download.** NRAO's own commands, with the Mozilla user agent added:
   * `wget -r -l 10 --reject "index.html*" -np -nH --cut-dirs=3 --user-agent="$CLAUDE_UA" -c <DIRECT>`
   * Calibrated or basic measurement sets can exceed 100 GB and plain `wget` may fail; NRAO recommends `wget2 -r -l 10 --reject-regex="index.html*" --progress=bar -np -nH --cut-dirs=3 --user-agent="$CLAUDE_UA" <DIRECT>`.
   * Resumable alternative that fits the skill: turn the listing into a manifest of per-file URLs and run `telescope_download.py MANIFEST.json --state STATE.json --min-free-gb 20` (8 MB chunks, `.part` files, HTTP Range resume, sha256 recorded, a status line every 15 minutes through Monitor).
3. **Verify** each file (size against the listing; `gzip -t` / `tar -tf` for archives), record size and sha256, and write the record to `already_evaluated/CrabNebula/`.
4. **Hosts:** EVLA requests are served from `dl-dsoc.nrao.edu`; GBT requests from `dl-naasc.nrao.edu`.
5. **Expiry:** NRAO keeps request data for a limited time (confirm the period on the request page); the emails are dated 17-18 Nov 2026, so list the requests soon even if the downloads wait.
6. **Reduction later:** the EVLA products are Calibrated Measurement Sets (as in the 11A-268 and HE 0435 tarballs); imaging Stokes Q/U needs CASA (`BulletCluster/.venv` has `casatools` and `casatasks`).
