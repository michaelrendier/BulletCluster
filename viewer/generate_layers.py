#!/usr/bin/env python3
"""
generate_layers.py
Produces WCS-aligned PNG layers for the Bullet Cluster HTML viewer.
Run from the viewer/ directory, or anywhere — paths are absolute.

Output: viewer/layers/*.png  (800×800 px, RGBA)
"""

import os, sys, warnings, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from astropy.io import fits
from astropy.wcs import WCS as AWCS
from astropy import units as u
from astropy.coordinates import SkyCoord
warnings.filterwarnings('ignore')

# ── Common output grid ────────────────────────────────────────────────────────
RA0, DEC0 = 104.6098, -55.9446   # Bullet Cluster centre
SIZE       = 800                   # pixels
SCALE      = 1.0 / 3600           # 1 arcsec/pixel
OUT        = os.path.join(os.path.dirname(__file__), 'layers')
BASE       = '/media/rendier/0123-4567/bullet_cluster'
os.makedirs(OUT, exist_ok=True)

def make_target_wcs():
    w = AWCS(naxis=2)
    w.wcs.crpix = [SIZE/2 + 0.5, SIZE/2 + 0.5]
    w.wcs.cdelt = [-SCALE, SCALE]        # RA flipped
    w.wcs.crval = [RA0, DEC0]
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    return w

TARGET_WCS = make_target_wcs()

def wcs_footprint_deg():
    """Return (ra_min, ra_max, dec_min, dec_max) of the target grid."""
    half = SIZE * SCALE / 2
    return (RA0 - half / math.cos(math.radians(DEC0)),
            RA0 + half / math.cos(math.radians(DEC0)),
            DEC0 - half, DEC0 + half)

def save_rgba(arr, name, cmap='inferno', log=False, alpha_floor=0.0):
    """Normalise arr → RGBA PNG, black=transparent."""
    if arr is None or np.all(arr == 0):
        print(f"  {name}: no data — saving placeholder"); save_placeholder(name); return
    a = arr.astype(float)
    a[~np.isfinite(a)] = 0
    vmin, vmax = np.nanpercentile(a[a > 0], [0.5, 99.5]) if np.any(a > 0) else (0, 1)
    if vmax <= vmin: vmax = vmin + 1
    if log and vmin > 0:
        a = np.log10(np.clip(a, vmin, None))
        vmin, vmax = math.log10(vmin), math.log10(vmax)
    a = np.clip((a - vmin) / (vmax - vmin), 0, 1)

    cm = plt.cm.get_cmap(cmap) if isinstance(cmap, str) else cmap
    rgba = cm(a)                          # (H, W, 4)
    # Alpha = normalised intensity (background stays transparent)
    alpha = np.clip(a - alpha_floor, 0, 1) / (1 - alpha_floor + 1e-9)
    rgba[..., 3] = alpha

    from PIL import Image
    img = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA')
    out_path = os.path.join(OUT, name + '.png')
    img.save(out_path)
    print(f"  Saved {out_path}  ({img.size[0]}×{img.size[1]})")

def save_placeholder(name):
    from PIL import Image
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    img.save(os.path.join(OUT, name + '.png'))

def reproject_fits(fits_path, hdu=0):
    """Reproject a FITS image onto the target WCS. Returns 2D array or None."""
    try:
        from reproject import reproject_interp
        with fits.open(fits_path) as hdul:
            h = hdul[hdu]
            data = h.data.squeeze()
            header = h.header
        if data.ndim != 2:
            print(f"  {fits_path}: unexpected shape {data.shape}"); return None
        reproj, _ = reproject_interp((data, header), TARGET_WCS.to_header(),
                                      shape_out=(SIZE, SIZE))
        return reproj
    except Exception as e:
        print(f"  reproject failed {fits_path}: {e}"); return None


# ══════════════════════════════════════════════════════════════════════════════
#  1. CHANDRA X-RAY
# ══════════════════════════════════════════════════════════════════════════════
def layer_chandra():
    print("── Chandra X-ray ─────────────────────────────")
    from scipy.ndimage import gaussian_filter

    chdir = os.path.join(BASE, 'xray', 'chandra')
    img = np.zeros((SIZE, SIZE), dtype=float)
    total_events = 0

    for obsid in ['554','3184','4984','4985','4986','5355','5356','5357','5358','5361']:
        obsdir = os.path.join(chdir, obsid)
        if not os.path.isdir(obsdir): continue
        for fname in os.listdir(obsdir):
            if 'evt2' not in fname or not fname.endswith('.gz'): continue
            path = os.path.join(obsdir, fname)
            try:
                with fits.open(path) as h:
                    ev  = h['EVENTS']
                    hdr = ev.header
                    d   = ev.data
                    mask = (d['energy'] >= 500) & (d['energy'] <= 7000)
                    cols = list(ev.columns.names)
                    # Get column-WCS for x,y sky pixel coords (TAN projection)
                    xcol = cols.index('x') + 1
                    ycol = cols.index('y') + 1
                    crpx     = hdr.get(f'TCRPX{xcol}', 4096.5)
                    crpy     = hdr.get(f'TCRPX{ycol}', 4096.5)
                    crvl_ra  = hdr.get(f'TCRVL{xcol}', RA0)
                    crvl_dec = hdr.get(f'TCRVL{ycol}', DEC0)
                    cdlt_ra  = hdr.get(f'TCDLT{xcol}', -1.37e-4)  # deg/px
                    cdlt_dec = hdr.get(f'TCDLT{ycol}',  1.37e-4)
                    xp  = d['x'][mask].astype(float)
                    yp  = d['y'][mask].astype(float)
                    # TAN → RA/Dec (approx linear for small offsets)
                    ra  = crvl_ra  + (xp - crpx) * cdlt_ra
                    dec = crvl_dec + (yp - crpy) * cdlt_dec
                    # RA/Dec → target grid pixel
                    px = SIZE/2 - (ra  - RA0)  / SCALE
                    py = SIZE/2 + (dec - DEC0) / SCALE
                    ix = np.round(px).astype(int)
                    iy = np.round(py).astype(int)
                    valid = (ix >= 0) & (ix < SIZE) & (iy >= 0) & (iy < SIZE)
                    np.add.at(img, (iy[valid], ix[valid]), 1)
                    n = int(valid.sum())
                    total_events += n
                    print(f"  {obsid}: {n:,} events on grid")
            except Exception as e:
                print(f"  {obsid} error: {e}")

    print(f"  Total events on grid: {total_events:,}")
    if img.max() == 0:
        print("  Chandra: zero events on grid!")
    if img.max() == 0:
        print("  Chandra: no events mapped"); save_placeholder('xray_chandra'); return

    from scipy.ndimage import gaussian_filter
    img = gaussian_filter(img, sigma=1.0)
    print(f"  Chandra: max counts/pixel = {img.max():.1f}")

    hot = LinearSegmentedColormap.from_list('xray_hot', [
        (0,'#000000'), (0.2,'#440022'), (0.45,'#cc0044'),
        (0.7,'#ff8800'), (0.85,'#ffee44'), (1,'#ffffff')])
    save_rgba(img, 'xray_chandra', cmap=hot, log=True, alpha_floor=0.0)


# ══════════════════════════════════════════════════════════════════════════════
#  2. PLANCK — submm cutouts (gnomview via healpy)
# ══════════════════════════════════════════════════════════════════════════════
def planck_cutout(fits_path, out_name, cmap_colors, label):
    print(f"── Planck {label} ─────────────────────────────")
    if not os.path.exists(fits_path):
        print(f"  Missing: {fits_path}"); save_placeholder(out_name); return
    try:
        import healpy as hp
        m = hp.read_map(fits_path, verbose=False)
        # gnomview: gnomonic cutout centred on cluster
        fov_deg = SIZE * SCALE           # ~13.3 arcmin
        xsize = SIZE
        theta = np.radians(90 - DEC0)
        phi   = np.radians(RA0)
        img = hp.gnomview(m, rot=[RA0, DEC0, 0], xsize=xsize,
                          reso=SCALE * 60,   # arcmin/pixel
                          return_projected_map=True, no_plot=True)
        cm = LinearSegmentedColormap.from_list(label, cmap_colors)
        save_rgba(img, out_name, cmap=cm, log=False, alpha_floor=0.05)
    except Exception as e:
        print(f"  {label}: {e}"); save_placeholder(out_name)

def layer_planck():
    planck_cutout(
        os.path.join(BASE, 'mm_sz', 'planck', 'HFI_SkyMap_857_2048_R2.02_full.fits'),
        'submm_planck857',
        ['#000000','#1a0020','#5a0040','#cc0066','#ff6600','#ffdd00','#ffffff'],
        '857GHz')

    planck_cutout(
        os.path.join(BASE, 'mm_sz', 'planck', 'HFI_SkyMap_545_2048_R2.02_full.fits'),
        'submm_planck545',
        ['#000000','#000820','#002266','#0066cc','#44ddff','#ffffff'],
        '545GHz')

    # SZ y-map — check for extracted FITS
    for ymap_path in [
        os.path.join(BASE, 'mm_sz', 'planck', 'COM_CompMap_Compton-SZMap-milca_2048_R2.00.fits'),
        os.path.join(BASE, 'mm_sz', 'planck', 'COM_CompMap_SZ_milca_2048_R2.00.fits'),
    ]:
        if os.path.exists(ymap_path) and os.path.getsize(ymap_path) > 1e6:
            planck_cutout(ymap_path, 'sz_planck',
                ['#000000','#0d0020','#3d0080','#8800cc','#dd44ff','#ffffff'],
                'SZ-ymap')
            return
    print("  SZ y-map: still downloading — placeholder")
    save_placeholder('sz_planck')


# ══════════════════════════════════════════════════════════════════════════════
#  3. LENSING κ MAP — two-NFW model (Clowe+2006 parameters)
# ══════════════════════════════════════════════════════════════════════════════
def layer_lensing():
    print("── Lensing κ (NFW model, Clowe+2006) ──────────")
    from astropy.cosmology import FlatLambdaCDM
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    z_l, z_s = 0.296, 1.2
    D_l  = cosmo.angular_diameter_distance(z_l).to(u.Mpc).value
    D_s  = cosmo.angular_diameter_distance(z_s).to(u.Mpc).value
    D_ls = cosmo.angular_diameter_distance_z1z2(z_l, z_s).to(u.Mpc).value
    Sigma_cr = (1.66e15 / (D_l * D_ls / D_s))   # M_sun/Mpc²  (approx)

    # NFW convergence κ(R) = Σ(R)/Σ_cr
    def nfw_sigma(R_mpc, M200_msun, c=5.0):
        """Projected surface mass density at projected radius R (Mpc)."""
        rho_c = 1.878e11 * 0.7**2   # M_sun/Mpc³
        r200  = (M200_msun / (200 * 4/3 * np.pi * rho_c))**(1/3)
        rs    = r200 / c
        rho0  = M200_msun / (4 * np.pi * rs**3 * (np.log(1+c) - c/(1+c)))
        x     = R_mpc / rs
        x     = np.clip(x, 1e-4, None)
        # NFW surface density (Bartelmann 1996)
        def f(xi):
            out = np.zeros_like(xi)
            lt = xi < 1
            gt = xi > 1
            eq = np.abs(xi - 1) < 1e-4
            out[lt] = 1/np.sqrt(1-xi[lt]**2) * np.arctanh(np.sqrt(1-xi[lt]**2)) if np.any(lt) else 0
            out[gt] = 1/np.sqrt(xi[gt]**2-1) * np.arctan(np.sqrt(xi[gt]**2-1))
            out[eq] = 1.0
            return out
        ff = f(x)
        # NFW projected surface density (Bartelmann 1996 eq. 13), regularised at x→1
        with np.errstate(invalid='ignore', divide='ignore'):
            denom = x**2 - 1
            Sigma = 2 * rho0 * rs / np.where(np.abs(denom) > 0.01,
                                              denom, np.sign(denom + 1e-10) * 0.01) * (1 - ff)
        # Soft-core regularisation: clip inner 10 kpc to avoid singularity
        Sigma = np.where(R_mpc < 0.01, 2 * rho0 * rs * 0.5, Sigma)
        Sigma = np.nan_to_num(Sigma, nan=0.0, posinf=0.0, neginf=0.0)
        return Sigma

    # Build pixel coordinate arrays
    iy, ix = np.indices((SIZE, SIZE))
    ra_arr, dec_arr = TARGET_WCS.all_pix2world(ix.ravel(), iy.ravel(), 0)
    ra_arr  = ra_arr.reshape(SIZE, SIZE)
    dec_arr = dec_arr.reshape(SIZE, SIZE)
    coord   = SkyCoord(ra=ra_arr*u.deg, dec=dec_arr*u.deg, frame='icrs')

    # Two DM halos from Clowe+2006 Table 1 (approximate)
    halos = [
        dict(ra=104.6383, dec=-55.9252, M200=3.7e14, c=5.0),   # main NW
        dict(ra=104.5726, dec=-55.9563, M200=1.5e14, c=4.5),   # bullet SE
    ]

    kappa = np.zeros((SIZE, SIZE))
    for h in halos:
        centre = SkyCoord(ra=h['ra']*u.deg, dec=h['dec']*u.deg)
        sep_rad  = coord.separation(centre).to(u.rad).value
        R_mpc    = sep_rad * D_l
        Sigma    = nfw_sigma(R_mpc, h['M200'], h['c'])
        kappa   += Sigma / Sigma_cr

    print(f"  κ max = {kappa.max():.3f}")
    blues = LinearSegmentedColormap.from_list('kappa_blue', [
        (0,'#000000'), (0.15,'#000820'), (0.35,'#001666'),
        (0.6,'#0044cc'), (0.8,'#4488ff'), (1,'#aaccff')])
    save_rgba(kappa, 'lensing_kappa', cmap=blues, log=False, alpha_floor=0.1)


# ══════════════════════════════════════════════════════════════════════════════
#  4. RADIO — MeerKAT MGCLS diffuse catalogue as synthetic image
# ══════════════════════════════════════════════════════════════════════════════
def layer_radio():
    print("── Radio MeerKAT (diffuse catalogue) ──────────")
    cat_path = os.path.join(BASE, 'radio', 'meerkat', 'MGCLS_Table4_diffuse.fits')
    if not os.path.exists(cat_path) or os.path.getsize(cat_path) < 1000:
        print("  Missing MGCLS Table4"); save_placeholder('radio_meerkat'); return

    try:
        from scipy.ndimage import gaussian_filter
        with fits.open(cat_path) as h:
            cat = h[1].data
            print(f"  MGCLS diffuse: {len(cat)} sources, columns: {cat.dtype.names[:8]}")

        # Find RA/Dec columns — handle 'R.A.J2000 (deg)' style names
        racol  = next((c for c in cat.dtype.names if 'R' in c.upper() and 'A' in c.upper() and '.' in c), None) or \
                 next((c for c in cat.dtype.names if c.upper().startswith('RA')), None)
        deccol = next((c for c in cat.dtype.names if 'DEC' in c.upper()), None)
        fcol   = next((c for c in cat.dtype.names if 'FLUX' in c.upper() or 'PEAK' in c.upper() or 'LLS' in c.upper()), None)
        # Filter to Bullet Cluster rows only (ClusterName column)
        if 'ClusterName' in cat.dtype.names:
            mask_cl = np.array(['bullet' in str(r).lower() or '0657' in str(r) or '1e0657' in str(r).lower()
                                 for r in cat['ClusterName']])
            if mask_cl.sum() == 0:
                print(f"  Bullet Cluster not found in diffuse catalogue — using all {len(cat)} sources")
            else:
                cat = cat[mask_cl]
                print(f"  Filtered to {len(cat)} Bullet Cluster sources")
        if not racol or not deccol:
            print(f"  Cols not found in {cat.dtype.names}"); save_placeholder('radio_meerkat'); return

        img = np.zeros((SIZE, SIZE))
        ra_s  = cat[racol].astype(float)
        dec_s = cat[deccol].astype(float)
        flux  = cat[fcol].astype(float) if fcol else np.ones(len(cat))
        flux  = np.nan_to_num(flux, nan=1.0)
        flux  = np.clip(flux, 0, np.nanpercentile(flux, 99))

        px, py = TARGET_WCS.all_world2pix(ra_s, dec_s, 0)
        ix = np.round(px).astype(int)
        iy = np.round(py).astype(int)
        valid = (ix >= 0) & (ix < SIZE) & (iy >= 0) & (iy < SIZE)
        for i in np.where(valid)[0]:
            # Gaussian blob per source, sigma ∝ source size
            sz_col = next((c for c in cat.dtype.names if 'SIZE' in c.upper() or 'MAJ' in c.upper()), None)
            sigma  = (cat[sz_col][i] / (SCALE * 3600) / 2.35) if sz_col else 8.0
            sigma  = max(2.0, min(float(np.nan_to_num(sigma, nan=8.0)), 60.0))
            # Place Gaussian
            y0, x0 = iy[i], ix[i]
            Y, X = np.ogrid[max(0,y0-50):min(SIZE,y0+50), max(0,x0-50):min(SIZE,x0+50)]
            g = flux[i] * np.exp(-((X-x0)**2 + (Y-y0)**2) / (2*sigma**2))
            img[max(0,y0-50):min(SIZE,y0+50), max(0,x0-50):min(SIZE,x0+50)] += g

        # Add diffuse background glow centred on cluster (halo template)
        yy, xx = np.mgrid[0:SIZE, 0:SIZE]
        cx, cy = TARGET_WCS.all_world2pix([RA0], [DEC0], 0)
        r2 = (xx - cx[0])**2 + (yy - cy[0])**2
        halo_sigma = 120  # pixels ≈ 2' — typical halo size
        halo = 0.15 * np.exp(-r2 / (2 * halo_sigma**2))
        img += halo

        img = gaussian_filter(img, sigma=2.0)
        print(f"  Radio: max={img.max():.4f}")
        cyan = LinearSegmentedColormap.from_list('radio_cyan', [
            (0,'#000000'), (0.2,'#001a1a'), (0.45,'#005555'),
            (0.7,'#00cccc'), (0.88,'#44ffee'), (1,'#ffffff')])
        save_rgba(img, 'radio_meerkat', cmap=cyan, log=True, alpha_floor=0.0)
    except Exception as e:
        print(f"  Radio layer error: {e}"); save_placeholder('radio_meerkat')


# ══════════════════════════════════════════════════════════════════════════════
#  5. OPTICAL — HST drizzled
# ══════════════════════════════════════════════════════════════════════════════
def layer_optical_hst():
    print("── Optical HST ─────────────────────────────────")
    hst_root = os.path.join(BASE, 'optical', 'hst')
    fits_files = []
    for root, _, files in os.walk(hst_root):
        for f in files:
            if '_drz.fits' in f.lower() or 'drz.fits' in f.lower():
                fits_files.append(os.path.join(root, f))

    if not fits_files:
        print("  No HST DRZ files yet"); save_placeholder('optical_hst'); return

    # Stack all available DRZ files
    img = np.zeros((SIZE, SIZE))
    count = 0
    for fp in fits_files[:6]:  # limit to avoid huge RAM
        layer = reproject_fits(fp, hdu=1)   # SCI extension
        if layer is not None:
            layer = np.nan_to_num(layer)
            img += layer
            count += 1
    if count == 0:
        save_placeholder('optical_hst'); return
    img /= count
    print(f"  HST: {count} files stacked")
    gold = LinearSegmentedColormap.from_list('hst_gold', [
        (0,'#000000'), (0.15,'#100800'), (0.4,'#503010'),
        (0.65,'#c08030'), (0.85,'#ffe090'), (1,'#ffffff')])
    save_rgba(img, 'optical_hst', cmap=gold, log=True, alpha_floor=0.05)


# ══════════════════════════════════════════════════════════════════════════════
#  6. OPTICAL — JWST NIRCam
# ══════════════════════════════════════════════════════════════════════════════
def layer_optical_jwst():
    print("── Optical JWST NIRCam ──────────────────────────")
    jwst_root = os.path.join(BASE, 'optical', 'jwst')
    # Look for F200W mosaic (best sensitivity, representative)
    fits_files = []
    for root, _, files in os.walk(jwst_root):
        for f in files:
            if f.lower().endswith('_i2d.fits') and ('f200w' in f.lower() or 'f277w' in f.lower() or 'f150w' in f.lower()):
                fits_files.append(os.path.join(root, f))

    if not fits_files:
        print("  No JWST I2D files yet"); save_placeholder('optical_jwst'); return

    fp = fits_files[0]
    print(f"  Using {os.path.basename(fp)}")
    # JWST FITS: SCI extension
    for hdu_idx in [1, 0, 'SCI']:
        try:
            layer = reproject_fits(fp, hdu=hdu_idx)
            if layer is not None:
                layer = np.nan_to_num(layer)
                break
        except:
            layer = None

    if layer is None:
        save_placeholder('optical_jwst'); return

    silver = LinearSegmentedColormap.from_list('jwst_silver', [
        (0,'#000000'), (0.1,'#080810'), (0.3,'#202838'),
        (0.6,'#7090c0'), (0.85,'#d0e4ff'), (1,'#ffffff')])
    save_rgba(layer, 'optical_jwst', cmap=silver, log=True, alpha_floor=0.05)


# ══════════════════════════════════════════════════════════════════════════════
#  7. POLARIZATION VECTORS — placeholder with synthetic field model
# ══════════════════════════════════════════════════════════════════════════════
def layer_polarization():
    print("── Polarization E-vectors (synthetic model) ────")
    from PIL import Image, ImageDraw
    import math

    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Synthetic B-field model for Bullet Cluster:
    # - Merger axis NW→SE
    # - B-field mostly perpendicular to merger → E-vectors parallel to merger axis
    # - RM gradient along merger axis
    # - At DM band (between halos): curvature test site
    def model_evpa(ra, dec):
        """Return EVPA in radians (measured N through E)."""
        # Base field: parallel to merger axis (PA ≈ 135° NW→SE)
        merger_pa = 135 * math.pi / 180
        # Add curvature near each DM halo (cardioid-like)
        dra1 = (ra - 104.6383) * math.cos(math.radians(-55.9252))
        ddec1 = dec - (-55.9252)
        r1 = math.sqrt(dra1**2 + ddec1**2)
        dra2 = (ra - 104.5726) * math.cos(math.radians(-55.9563))
        ddec2 = dec - (-55.9563)
        r2 = math.sqrt(dra2**2 + ddec2**2)
        # Halo-induced rotation (wave model: smooth Faraday)
        angle1 = math.atan2(ddec1, dra1) * 0.3 / (r1 + 0.01) * 0.005
        angle2 = math.atan2(ddec2, dra2) * 0.3 / (r2 + 0.01) * 0.005
        return merger_pa + angle1 + angle2

    def model_polfrac(ra, dec):
        """Return polarised fraction 0–1."""
        dra  = (ra - RA0) * math.cos(math.radians(DEC0))
        ddec = dec - DEC0
        r    = math.sqrt(dra**2 + ddec**2)
        # High polarisation in relic, moderate in halo
        relic_ra, relic_dec = 104.44, -55.97
        dr   = (ra - relic_ra) * math.cos(math.radians(relic_dec))
        dd   = dec - relic_dec
        rr   = math.sqrt(dr**2 + dd**2)
        p_relic = 0.35 * math.exp(-rr / 0.03)
        p_halo  = 0.12 * math.exp(-r  / 0.05)
        return min(0.45, p_relic + p_halo)

    # Grid of vector positions (every ~30px = 30")
    step = 30
    for iy in range(step//2, SIZE, step):
        for ix in range(step//2, SIZE, step):
            ra, dec = TARGET_WCS.all_pix2world([ix], [iy], 0)
            ra, dec = float(ra[0]), float(dec[0])
            pf   = model_polfrac(ra, dec)
            if pf < 0.015: continue
            evpa = model_evpa(ra, dec)
            # Arrow length ∝ polarised fraction
            half_len = max(4, int(pf * 60))
            dx = half_len * math.cos(evpa)
            dy = half_len * math.sin(evpa)
            # Gold color, alpha ∝ pf
            alpha = min(255, int(pf / 0.45 * 230 + 25))
            draw.line([(ix - dx, iy - dy), (ix + dx, iy + dy)],
                      fill=(255, 215, 0, alpha), width=2)
            # Perpendicular tick at end (head of vector)
            hx =  dy * 0.3; hy = -dx * 0.3
            draw.line([(ix + dx - hx, iy + dy - hy), (ix + dx + hx, iy + dy + hy)],
                      fill=(255, 215, 0, alpha), width=1)

    out_path = os.path.join(OUT, 'polarization.png')
    img.save(out_path)
    print(f"  Saved {out_path} (synthetic model — replace with rmsynth3d output)")


# ══════════════════════════════════════════════════════════════════════════════
#  8. RM FARADAY DEPTH — synthetic model
# ══════════════════════════════════════════════════════════════════════════════
def layer_rm():
    print("── RM Faraday Depth (synthetic model) ──────────")
    iy, ix = np.indices((SIZE, SIZE))
    ra_arr, dec_arr = TARGET_WCS.all_pix2world(ix.ravel(), iy.ravel(), 0)
    ra_arr  = ra_arr.reshape(SIZE, SIZE)
    dec_arr = dec_arr.reshape(SIZE, SIZE)

    # Model RM: gradient along merger axis, peaks at DM halo positions
    # RM ~ B·n_e·dl integrated along line of sight
    # For wave DM: smooth gradient only from gas
    from scipy.ndimage import gaussian_filter

    rm = np.zeros((SIZE, SIZE))
    # Gas contribution — peaks at the X-ray gas centroids, not DM peaks
    for gas_ra, gas_dec, sign, amp in [
        (104.625, -55.930, +1, 120),   # NW gas
        (104.569, -55.961, -1,  80),   # SE gas
    ]:
        dr  = (ra_arr - gas_ra) * np.cos(np.radians(gas_dec))
        dd  = dec_arr - gas_dec
        r   = np.sqrt(dr**2 + dd**2)
        rm += sign * amp * np.exp(-r / 0.025)

    # Background gradient
    rm += 15 * (ra_arr - RA0) / (SIZE * SCALE / math.cos(math.radians(DEC0)))
    rm = gaussian_filter(rm, sigma=3)

    # Map to spectral colormap
    spectral = plt.cm.get_cmap('RdBu_r')
    rm_norm = (rm - rm.min()) / (rm.max() - rm.min() + 1e-9)

    from PIL import Image
    rgba = (spectral(rm_norm) * 255).astype(np.uint8)
    # Alpha: transparent where signal is low
    alpha = np.clip(np.abs(rm - rm.mean()) / (rm.std() + 1e-9), 0, 1)
    alpha = (np.clip(alpha, 0.1, 1) * 200).astype(np.uint8)
    rgba[..., 3] = alpha

    img = Image.fromarray(rgba, 'RGBA')
    out_path = os.path.join(OUT, 'rm_faraday.png')
    img.save(out_path)
    print(f"  Saved {out_path} (synthetic — replace with rmsynth3d output)")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', help='Only generate this layer (chandra|planck|lensing|radio|hst|jwst|pol|rm|all)')
    args = parser.parse_args()

    only = args.only or 'all'

    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow..."); os.system('pip3 install --break-system-packages Pillow')
        from PIL import Image

    tasks = {
        'chandra': layer_chandra,
        'planck':  layer_planck,
        'lensing': layer_lensing,
        'radio':   layer_radio,
        'hst':     layer_optical_hst,
        'jwst':    layer_optical_jwst,
        'pol':     layer_polarization,
        'rm':      layer_rm,
    }

    if only == 'all':
        for name, fn in tasks.items():
            try: fn()
            except Exception as e: print(f"  ERROR {name}: {e}")
    elif only in tasks:
        tasks[only]()
    else:
        print(f"Unknown layer: {only}. Choose from: {list(tasks.keys())}")

    print(f"\nDone. Open viewer/index.html in browser (or run: python3 -m http.server 8888)")
