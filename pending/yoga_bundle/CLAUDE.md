# Primer for Claude Code on the Lenovo Yoga (read this first, then act without asking)

You are Claude Code on a laptop (Linux, 16 GB RAM + 8 GB swap, about 891 GB free disk) whose owner is away overnight. You have NO other context. Your job is to **download public telescope data safely and keep it downloading**, nothing else. You may use all of the machine's RAM and swap. Do not ask questions; if something blocks a job, write the problem to `STATUS.md` in this folder and go on to the next job.

## Why this data exists (one paragraph)
The owner is building his own weak-gravitational-lensing and ptychography pipeline to map dark matter around strong-lens systems and galaxy clusters, with polarization data only as a control for dust. Weak lensing needs deep, high-resolution, dithered images with per-exposure calibrated frames, point-spread-function (PSF) information, several filters for source selection, and wide fields around the target. So the first targets are the Euclid DR1 and JWST data on the quad lens **DES J0408-5354**, then the NRAO Crab nebula and pulsar radio data (controls) when fresh links exist. You do not evaluate or analyse the data; you fetch it, verify it and report.

## Rules (do not relax)
1. Every outbound request carries a Mozilla user agent (the scripts do this). Public sources only. If a page asks you to log in, that is a **stop**: record it, never try to log in, never invent credentials.
2. Never send or write the owner's e-mail address or any account name to any server.
3. **One download at a time.** Never run two download jobs at once.
4. Never delete downloaded data. Never "repair" a drive, never format, never run `fsck`, never change partitions. If a disk or the network misbehaves, log it and wait.
5. Keep 20 GB free (the scripts enforce it). Do not extract archives (`.tar`, `.rar`, `.gz`): it needs extra disk. Leave them as downloaded.
6. Do not commit, push or publish anything. `links.txt` holds private keyed URLs: never print it in full, never copy it anywhere.
7. Failures are data: log them in `STATUS.md` with the exact message, do not hide them.

## What is in this folder
| file | what it is |
|---|---|
| `CLAUDE.md` | this primer |
| `run_job.sh JOB [start\|status\|stop]` | runs one job from `jobs/JOB/manifest.json` with `telescope_download.py` (8 MB chunks, `.part` files, HTTP Range resume, sha256, atomic state, restart loop, sleep inhibitor, free-space guard) |
| `prepare_job.py` | called by `run_job.sh`: puts `DATA_ROOT` in front of the relative paths in a manifest |
| `telescope_download.py` | the downloader (standard library only) |
| `build_euclid_manifest.py` | writes a Euclid DR1 manifest for a sky position from the IRSA archive tables (read-only) |
| `build_mast_manifest.py` | writes a JWST/HST manifest from MAST (needs `astroquery`, installed by step 1 below) |
| `nrao_fetch.py`, `fetch_crab.sh`, `links.txt`, `test_nrao_fetch.py` | the NRAO Crab nebula and pulsar fetcher (`links.txt` is private; the 2026-11-18 EVLA links returned 404, see below) |
| `jobs/` | one folder per job with its `manifest.json` |
| `JOBS.md` | the queue, in order |

## Step 1: set up (once)
```
python3 nrao_fetch.py --setup            # apt packages (asks for sudo once), makes .venv; if sudo is not possible, note it and continue
.venv/bin/pip install astroquery astropy requests   # only needed for build_mast_manifest.py
python3 test_nrao_fetch.py               # 16 checks against a local mock server; all must PASS before any real download
```
Choose the data root (default `~/TelescopeData`; it must have at least 150 GB free for the first two jobs): `export DATA_ROOT=/path/with/space`. Check with `df -h "$DATA_ROOT"`.

## Step 2: run the jobs in the order of `JOBS.md`, one at a time
```
./run_job.sh euclid_DESJ0408_5354 start       # about 83 GB, public IRSA archive
./run_job.sh euclid_DESJ0408_5354 status
```
Look at `status` every 20 to 30 minutes (sleep in a loop with `sleep 1500` between checks, or use a background monitor). When it prints `job ... complete`, check that the file count equals the manifest count and start the next job. The runner restarts the downloader after a crash and waits out a network loss, so a "downloader exited" line is normal; investigate only if the same file fails five times in a row (write it to `STATUS.md`, then go on).
A `[size-fix]` line is normal: archive size listings are sometimes stale and the server size is used.

## Step 3: the NRAO Crab fetch (only if fresh links exist)
`links.txt` has the request ids of the NRAO Crab nebula and pulsar projects. On 2026-11-27 every EVLA link returned HTTP 404 (expired); the two GBT links worked. Run `python3 nrao_fetch.py --probe` (read-only). If the EVLA requests answer, run `DEST=$DATA_ROOT/CrabNebula/nrao ./fetch_crab.sh start`. If they all say EXPIRED, do nothing: the owner will re-request them and add fresh links with `python3 nrao_fetch.py --add-link REQUEST_ID "URL"`. Do not log in to NRAO.

### New NRAO requests (the owner is requesting Galactic Center projects)
When the owner pastes a new NRAO request e-mail or link, extract the request number, the project code, the size NRAO reports, and the `direct` download URL (host `dl-dsoc.nrao.edu` for EVLA/VLA, `dl-naasc.nrao.edu` for GBT), then run
`python3 nrao_fetch.py --add-link REQUEST_ID "DIRECT_URL" --project PROJECT_CODE --size-gb SIZE` (never print the URL back in full), then `python3 nrao_fetch.py --probe` and, if it answers, `EXTRA_ARGS="--only PROJECT_CODE" ./fetch_crab.sh start` (`--only` restricts the run to that project, so the expired Crab requests in the built-in table do not use up the budget; `BUDGET_GB` defaults to 700). These requests expire after about a week, so start promptly. Everything fetched lands under `$DEST/<project>/`.

## Reporting
Keep `STATUS.md` up to date (one line per event: time, job, what happened, bytes on disk). When all jobs are done or blocked, write a short summary at the top of `STATUS.md` (files, GB, any failures) and stop. Do not start anything not listed in `JOBS.md`.

## If something goes wrong
- No network: the scripts wait and resume. Do nothing.
- "free-space guard stopped": the disk is full. Report, do not delete anything.
- Many `size mismatch`/`sha256 mismatch` lines for one file: report the file, move on.
- The machine rebooted: just run `./run_job.sh JOB start` again; partial files resume.
