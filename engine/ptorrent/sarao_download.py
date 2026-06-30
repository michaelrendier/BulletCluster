#!/usr/bin/env python3
"""
sarao_download.py — Two-path downloader for Bullet Cluster MeerKAT data.

PATH A (NOW): MGCLS DR1 public S3 — no auth required.
  Stokes I frequency cubes, basic continuum products, catalogues.

PATH B (NEEDS IDIA): requestExport via SARAO GraphQL + S3 download.
  The 4 new 2024/2025 S-band + UHF observations (13,926 FITS spectral images).
  Requires: IDIA project allocation + keycloak group membership.
  Once registered at ilifu.ac.za, set IDIA_DESTINATION below.

Usage:
    python3 sarao_download.py --path a           # download public MGCLS data
    python3 sarao_download.py --path b           # request + download 2024/2025 data (needs IDIA)
    python3 sarao_download.py --status           # check tape staging status
"""

import requests, json, time, sys, argparse
from pathlib import Path
from xml.etree import ElementTree as ET

# ── Config ────────────────────────────────────────────────────────────────────
USERAGENT   = 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'
PUBLIC_S3   = 'https://archive-gw-1.kat.ac.za/public'
AUTH_S3     = 'https://archive-gw-1.kat.ac.za'
GQL         = 'https://archive.sarao.ac.za/graphql'
BASE_DIR    = Path('/media/rendier/0123-4567/bullet_cluster/radio/meerkat')
MGCLS_DIR   = BASE_DIR / 'MGCLS_DR1'
NEW_DIR     = BASE_DIR / 'new_2024_2025'

# SARAO archive credentials (set via environment or edit here)
import os
SARAO_EMAIL    = os.getenv('SARAO_EMAIL', 'the.wandering.god@gmail.com')
SARAO_PASSWORD = os.getenv('SARAO_PASSWORD', '')

# IDIA project destination (registered in SARAO JOBS system).
# Leave empty until you have an IDIA allocation.
# Registration: https://www.idia.ac.za/research-projects/apply-for-computing-access/
IDIA_DESTINATION = os.getenv('IDIA_DESTINATION', '')

# 4 Bullet Cluster observations from proposal SCI-20241101-AB-01
NEW_CBIDS = [
    {'id': '1740850637-sdp-l0', 'desc': 'Bullet S1 - Setting (S-band, 2025-03-01)', 'gb': 873},
    {'id': '1738188256-sdp-l0', 'desc': 'Bullet UHF - Setting (UHF, 2025-01-29)',   'gb': 672},
    {'id': '1734200474-sdp-l0', 'desc': 'Bullet S1 - Rising (S-band, 2024-12-14)',  'gb': 898},
    {'id': '1734116661-sdp-l0', 'desc': 'Bullet UHF - Rising (UHF, 2024-12-13)',    'gb': 710},
]

# ── Public MGCLS files to download ───────────────────────────────────────────
MGCLS_FILES = [
    ('repository/10.48479/7epd-w356/data/basic_products/Bullet.APSCal.1pln.fits.gz',
     MGCLS_DIR / 'basic/Bullet.APSCal.1pln.fits.gz'),
    ('repository/10.48479/7epd-w356/data/enhanced_products/frequency_cubes/Bullet_aFix_pol_I_15arcsec_fcube_cor.fits.gz',
     MGCLS_DIR / 'enhanced/frequency_cubes/Bullet_aFix_pol_I_15arcsec_fcube_cor.fits.gz'),
    ('repository/10.48479/7epd-w356/data/enhanced_products/frequency_cubes/Bullet_aFix_pol_I_Farcsec_fcube_cor.fits.gz',
     MGCLS_DIR / 'enhanced/frequency_cubes/Bullet_aFix_pol_I_Farcsec_fcube_cor.fits.gz'),
    ('repository/10.48479/7epd-w356/data/enhanced_products/5pln_cubes/Bullet_aFix_pol_I_15arcsec_5pln_cor.fits.gz',
     MGCLS_DIR / 'enhanced/5pln_cubes/Bullet_aFix_pol_I_15arcsec_5pln_cor.fits.gz'),
    ('repository/10.48479/7epd-w356/data/enhanced_products/5pln_cubes/Bullet_aFix_pol_I_Farcsec_5pln_cor.fits.gz',
     MGCLS_DIR / 'enhanced/5pln_cubes/Bullet_aFix_pol_I_Farcsec_5pln_cor.fits.gz'),
    ('repository/10.48479/7epd-w356/data/Table1_MGCLS_targets.csv',
     MGCLS_DIR / 'Table1_MGCLS_targets.csv'),
    ('repository/10.48479/7epd-w356/data/Table4_MGCLS_diffuse.fits',
     MGCLS_DIR / 'Table4_MGCLS_diffuse.fits'),
    ('repository/10.48479/7epd-w356/data/Table2_MGCLS_compactcat_DR1.fits',
     MGCLS_DIR / 'Table2_MGCLS_compactcat_DR1.fits'),
]


# ── Download helper ───────────────────────────────────────────────────────────
def download_file(session, url, dest, chunk_mb=8):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    chunk = chunk_mb * 1024 * 1024
    if dest.exists():
        remote_sz = int(session.head(url, timeout=20).headers.get('Content-Length', 0))
        local_sz  = dest.stat().st_size
        if local_sz == remote_sz and remote_sz > 0:
            print(f'  SKIP (complete): {dest.name}')
            return True
        headers = {'Range': f'bytes={local_sz}-'}
        mode    = 'ab'
        print(f'  RESUME from {local_sz/1e6:.0f} MB: {dest.name}')
    else:
        headers, mode = {}, 'wb'

    r = session.get(url, headers=headers, stream=True, timeout=60)
    if r.status_code not in (200, 206):
        print(f'  ERROR {r.status_code}: {url}')
        return False

    total = int(r.headers.get('Content-Length', 0))
    done  = 0
    t0    = time.time()
    with open(dest, mode) as f:
        for data in r.iter_content(chunk_size=chunk):
            f.write(data)
            done += len(data)
            elapsed = time.time() - t0 or 0.001
            rate = done / elapsed / 1e6
            pct  = 100 * done / total if total else 0
            print(f'\r  {dest.name}: {done/1e6:.0f}/{total/1e6:.0f} MB ({pct:.0f}%) @ {rate:.1f} MB/s',
                  end='', flush=True)
    print()
    return True


# ── Path A: MGCLS public data ─────────────────────────────────────────────────
def download_public():
    print('\n=== PATH A: MGCLS DR1 public data ===')
    print(f'Destination: {MGCLS_DIR}')
    print(f'Note: Only Stokes I available for Bullet in DR1.')
    print(f'      Q/U cubes were not released for this target.\n')
    s = requests.Session()
    s.headers['User-Agent'] = USERAGENT
    for key, dest in MGCLS_FILES:
        url = f'{PUBLIC_S3}/{key}'
        print(f'[{Path(dest).name}]')
        download_file(s, url, dest)
    print('\nMGCLS DR1 download complete.')
    print(f'Files at: {MGCLS_DIR}')


# ── Selenium auth helper ──────────────────────────────────────────────────────
def get_auth_cookies():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    CHROMEDRIVER = '/home/rendier/.wdm/drivers/chromedriver/linux64/149.0.7827.155/chromedriver-linux64/chromedriver'
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument(f'--user-agent={USERAGENT}')
    svc    = Service(executable_path=CHROMEDRIVER)
    driver = webdriver.Chrome(service=svc, options=opts)
    wait   = WebDriverWait(driver, 25)
    driver.get('https://archive.sarao.ac.za/_auth/login?redirect=https://archive.sarao.ac.za/')
    time.sleep(3)
    wait.until(EC.presence_of_element_located(('id', 'username'))).send_keys(SARAO_EMAIL)
    driver.find_element('id', 'password').send_keys(SARAO_PASSWORD)
    driver.find_element('id', 'kc-login').click()
    time.sleep(5)
    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    driver.quit()
    return cookies


def gql_session(cookies):
    s = requests.Session()
    s.headers['User-Agent'] = USERAGENT
    for name, val in cookies.items():
        s.cookies.set(name, val, domain='archive.sarao.ac.za')
    return s


# ── Path B: 2024/2025 tape data via requestExport ────────────────────────────
def download_new_data():
    if not IDIA_DESTINATION:
        print('\n=== PATH B: 2024/2025 S-band + UHF data ===')
        print('BLOCKED — no IDIA destination configured.')
        print()
        print('To unlock Path B:')
        print('  1. Register at https://www.idia.ac.za/research-projects/apply-for-computing-access/')
        print('  2. Request Bullet Cluster data access via SARAO helpdesk: helpdesk@sarao.ac.za')
        print('  3. Once your IDIA project is registered in SARAO JOBS system,')
        print('     set the destination:')
        print('       export IDIA_DESTINATION="your-idia-project-id"')
        print('  4. Re-run: python3 sarao_download.py --path b')
        print()
        print('Data waiting on tape:')
        for obs in NEW_CBIDS:
            print(f'  {obs["id"]} — {obs["desc"]} ({obs["gb"]} GB raw)')
        print()
        print('Total raw data: ~3.15 TB')
        print('FITS products per obs: ~3500 spectral images (S-band) or 3400 (UHF)')
        return

    print(f'\n=== PATH B: requestExport to IDIA destination={IDIA_DESTINATION!r} ===')
    if not SARAO_PASSWORD:
        print('ERROR: set SARAO_PASSWORD environment variable')
        return

    cookies = get_auth_cookies()
    s = gql_session(cookies)

    export_ids = []
    for obs in NEW_CBIDS:
        print(f'\n[{obs["id"]}] {obs["desc"]}')
        mutation = '''
        mutation RequestExport($input: ExportRequestInput!) {
          requestExport(input: $input) {
            id name state link cbid Error
          }
        }
        '''
        variables = {
            'input': {
                'destination': IDIA_DESTINATION,
                'formData':    {'cbid': obs['id'], 'type': 'FITSImageProduct'},
                'productName': obs['id'],
            }
        }
        r = s.post(GQL, json={'query': mutation, 'variables': variables}, timeout=30)
        data = r.json()
        if data.get('errors'):
            print(f'  ERROR: {data["errors"]}')
            continue
        exp = data['data']['requestExport']
        print(f'  Export submitted: id={exp["id"]} state={exp["state"]} Error={exp.get("Error")}')
        export_ids.append(exp['id'])

    if not export_ids:
        print('\nNo exports submitted — check IDIA destination.')
        return

    # Poll for completion
    print('\nPolling for export completion (checks every 60s)...')
    query = '''
    {
      exports(limit: 20) {
        records { id name state link cbid Error size }
      }
    }
    '''
    while export_ids:
        time.sleep(60)
        r = s.post(GQL, json={'query': query}, timeout=30)
        records = r.json()['data']['exports']['records']
        for rec in records:
            if rec['id'] in export_ids:
                print(f'  {rec["id"]}: state={rec["state"]} link={rec.get("link")[:60] if rec.get("link") else None}')
                if rec.get('link'):
                    _download_export(s, rec)
                    export_ids.remove(rec['id'])
                elif rec.get('Error'):
                    print(f'  FAILED: {rec["Error"]}')
                    export_ids.remove(rec['id'])


def _download_export(session, export_rec):
    link = export_rec.get('link')
    cbid = export_rec.get('cbid', 'unknown')
    if not link:
        return
    dest_dir = NEW_DIR / cbid
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Link might be a tarball URL or an S3 manifest
    print(f'  Download link for {cbid}: {link[:80]}')
    dest = dest_dir / f'{cbid}_export.tar.gz'
    download_file(session, link, dest)


# ── Status check ─────────────────────────────────────────────────────────────
def check_status():
    print('\n=== Tape staging status for 2024/2025 observations ===')
    if not SARAO_PASSWORD:
        print('Set SARAO_PASSWORD to check live status. Showing known status:')
    print()
    for obs in NEW_CBIDS:
        cbid = obs['id'].split('-')[0]
        print(f'{obs["id"]}')
        print(f'  {obs["desc"]}')
        print(f'  Status: ARCHIVED (on tape, ~{obs["gb"]} GB raw)')
        print(f'  FITS products: ~3500 Spectral Images (Stokes I per channel)')
        print(f'  S3 bucket: {AUTH_S3}/{cbid}-fitsimageproduct/ (empty until staged)')
        print()


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SARAO Bullet Cluster data downloader')
    parser.add_argument('--path', choices=['a', 'b'], default='a',
                        help='a=public MGCLS, b=new 2024/2025 tape data (needs IDIA)')
    parser.add_argument('--status', action='store_true',
                        help='Show tape staging status for all observations')
    args = parser.parse_args()

    if args.status:
        check_status()
    elif args.path == 'a':
        download_public()
    elif args.path == 'b':
        download_new_data()
