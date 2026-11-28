# Crab nebula and pulsar NRAO fetch: the second machine (Lenovo Yoga Ultra 7)

Copy this whole folder to the laptop (USB stick or `scp`). It needs nothing but Python 3 (standard library). **links.txt holds keyed URLs: keep it private.**

1. **Python and packages (A):** `python3 nrao_fetch.py --setup` (apt: python3, venv, pip, curl, ca-certificates, p7zip-full; makes `.venv`; asks for sudo once).
2. **See the plan:** `python3 nrao_fetch.py --plan` (700 GB budget: 25A-385, 11A-268, 12A-486, 12B-380 = 699.3 GB; 15B-252, 22B-192 and 11B-341 are skipped).
3. **See which links still answer (read-only):** `python3 nrao_fetch.py --probe`. **On 2026-11-27 every EVLA link answered 404** (the GBT links still work). If yours do, re-request the projects in the NRAO Archive Access Tool (you log in; the script never does), then `python3 nrao_fetch.py --add-link REQUEST_ID "DIRECT_URL"` for each new email.
4. **Fetch (B):** `DEST=/path/with/space ./fetch_crab.sh start` then `./fetch_crab.sh status`. One file at a time, 8 MB chunks, `.part` files with HTTP Range resume, sha1 checked against NRAO's SHA1SUMS, state written atomically, restart loop with network waits, a 20 GB free-space guard. `./fetch_crab.sh stop` saves and stops.
5. **After a reboot or crash:** run `./fetch_crab.sh start` again; it resumes. For automatic restart after a reboot: `./fetch_crab.sh install-service` and, once, `sudo loginctl enable-linger $USER`.
6. **Tests (no network needed):** `python3 test_nrao_fetch.py` (14 checks: drops, resume, crash trim, corruption, expiry, login page, disk guard, budget).

Files are not extracted by the script (extraction needs a second copy's worth of space). Extract later, one project at a time, with `tar`/`7z`.
Memory: the engine streams in 8 MB chunks and stays well under 100 MB resident; `fetch_crab.sh` caps it at 6 GB with `systemd-run` when available (`MEM_MAX`).
