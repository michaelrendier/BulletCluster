"""
Ripple simulation: superpose 2D circular waves from each cluster galaxy,
test whether the interference pattern reproduces the observed DM band.

Each galaxy → wave source with:
  amplitude  ∝ sqrt(F444W flux)   (halo mass proxy)
  wavelength = 2 × half-light radius (physical scale of the halo)
  damping    = 5 × wavelength      (NFW truncation proxy)

Wave function (2D Huygens/Bessel):
  ψ_i(r) = A_i × J_0(2π r / λ_i) × exp(-r / d_i)

Superposed field:  Ψ(x,y) = Σ_i ψ_i(|pos - pos_i|)
Intensity pattern: I(x,y) = Ψ²   (scalar field, no phase offset)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from scipy.special import j0
from PIL import Image
import os

# ── constants ────────────────────────────────────────────────────────────────
PIXSCL   = 0.06027451212851639   # arcsec / JWST pixel
RA0      = 104.6098              # cluster X-ray centroid
DEC0     = -55.9446
MERGER_PA_DEG = 135.0            # NW→SE position angle
V_MERGER_KMS  = 3000.0           # km/s relative velocity
SEP_KPC       = 720.0            # current projected separation (kpc)
Z_CLUST       = 0.296
KPC_PER_ARCMIN = 262.0           # at z=0.296 (flat ΛCDM)

# output grid in arcsec, centred on (RA0, DEC0)
GRID_ARCSEC_W = 400              # half-width
GRID_ARCSEC_H = 260              # half-height
GRID_RES      = 1.5              # arcsec / output pixel

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'viewer', 'layers')

# ── load catalog ──────────────────────────────────────────────────────────────
def load_catalog():
    d = np.load('/tmp/bullet_cluster_catalog.npz')
    ra   = d['ra']
    dec  = d['dec']
    flux = d['flux_f444']
    a_px = d['a_px']
    # sky → arcsec offset from centroid (tangent plane)
    cos_d = np.cos(np.radians(DEC0))
    xi  = -(ra  - RA0)  * cos_d * 3600   # arcsec, East=positive → flip RA
    eta = (dec - DEC0) * 3600            # arcsec, North=positive
    # amplitude: sqrt(flux), clamp NaN/negatives
    amp = np.where(np.isfinite(flux) & (flux > 0), np.sqrt(flux), 0.1)

    # NFW scale radius from flux (mass proxy):
    #   M_halo ∝ F^1.5  (abundance matching, Behroozi+2013)
    #   r_200  ∝ M_halo^(1/3) ∝ F^0.5
    #   r_s    = r_200 / c  (c≈7 concentration)
    # Normalise: brightest galaxy (F≈427) → r_s = 45 arcsec (~230 kpc at z=0.296)
    F_ref = 427.0
    r_s_ref_arcsec = 45.0
    flux_safe = np.where(np.isfinite(flux) & (flux > 0), flux, 0.01)
    r_s = r_s_ref_arcsec * (flux_safe / F_ref) ** 0.5
    r_s = np.clip(r_s, 1.5, 80.0)   # arcsec: 1.5 (dwarf) .. 80 (BCG)

    # wave wavelength = r_s (one half-cycle across the halo)
    lam  = r_s
    # damping scale = 3 × r_s
    damp = r_s * 3.0
    return xi, eta, amp, lam, damp

# ── build output grid ─────────────────────────────────────────────────────────
def make_grid():
    xs = np.arange(-GRID_ARCSEC_W, GRID_ARCSEC_W + GRID_RES, GRID_RES)
    ys = np.arange(-GRID_ARCSEC_H, GRID_ARCSEC_H + GRID_RES, GRID_RES)
    gx, gy = np.meshgrid(xs, ys)
    return gx, gy

# ── ripple superposition ──────────────────────────────────────────────────────
def compute_field(gx, gy, xi, eta, amp, lam, damp, chunk=200):
    """
    Ψ(x,y) = Σ_i A_i × J0(2π r_i / λ_i) × exp(-r_i / d_i)
    Computed in chunks to avoid huge memory allocation.
    """
    field = np.zeros(gx.shape, dtype='f8')
    n = len(xi)
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        # shape: (chunk, Ny, Nx)
        dx = gx[None, :, :] - xi[start:end, None, None]
        dy = gy[None, :, :] - eta[start:end, None, None]
        r  = np.sqrt(dx*dx + dy*dy)
        A  = amp[start:end, None, None]
        L  = lam[start:end, None, None]
        D  = damp[start:end, None, None]
        contrib = A * j0(2*np.pi * r / L) * np.exp(-r / D)
        field += contrib.sum(axis=0)
        if start % 400 == 0:
            print(f"  {start}/{n} galaxies processed...")
    return field

# ── time-rollback: shift galaxy positions to collision epoch ──────────────────
def rollback_positions(xi, eta, amp, lam, damp):
    """
    Shift each galaxy back along the merger axis by Δt × v_merger.
    Two groups: galaxies left of centre → move NW (+xi,+eta in PA=135° sense),
    galaxies right of centre → move SE (-xi,-eta).
    Time since core passage ~240 Myr; 3000 km/s × 240 Myr ≈ 700 kpc ≈ 2.7 arcmin.
    """
    DT_ARCSEC = 2.7 * 60  # ~160 arcsec shift each side
    pa_rad = np.radians(MERGER_PA_DEG)
    # unit vector NW→SE in (xi, eta) = (-sin PA, -cos PA) for E-of-N convention
    ux = -np.sin(pa_rad)   # arcsec xi component
    uy = -np.cos(pa_rad)   # arcsec eta component
    # project galaxy positions onto merger axis
    proj = xi * ux + eta * uy
    # galaxies on NW side (proj < 0) → push further NW, SE side → push further SE
    # i.e., roll back = push away from centre along merger axis
    shift = np.where(proj < 0, -DT_ARCSEC, DT_ARCSEC)
    xi_rb  = xi  + shift * ux
    eta_rb = eta + shift * uy
    return xi_rb, eta_rb, amp, lam, damp

# ── render ────────────────────────────────────────────────────────────────────
def render(field, gx, gy, title, outpath, bg_path=None):
    fig, axes = plt.subplots(1, 2 if bg_path else 1,
                             figsize=(18 if bg_path else 10, 7),
                             facecolor='k')
    if bg_path is None:
        axes = [axes]

    intensity = field**2
    intensity /= intensity.max()

    extent = [gx.min(), gx.max(), gy.min(), gy.max()]

    ax = axes[0]
    im = ax.imshow(intensity, origin='lower', extent=extent,
                   cmap='inferno', norm=PowerNorm(gamma=0.5),
                   aspect='equal', interpolation='bilinear')
    ax.set_title(title, color='w', fontsize=11)
    ax.set_xlabel('Δξ (arcsec, E→W)', color='w')
    ax.set_ylabel('Δη (arcsec, S→N)', color='w')
    ax.tick_params(colors='w')
    for spine in ax.spines.values(): spine.set_edgecolor('w')
    plt.colorbar(im, ax=ax, label='Normalised |Ψ|²', shrink=0.8)

    # DM peak positions (Clowe+2006) in arcsec from centroid
    cos_d = np.cos(np.radians(DEC0))
    dm_nw_xi  = -(104.6383 - RA0) * cos_d * 3600
    dm_nw_eta =  (-55.9252 - DEC0) * 3600
    dm_se_xi  = -(104.5726 - RA0) * cos_d * 3600
    dm_se_eta =  (-55.9563 - DEC0) * 3600
    for axi in axes:
        axi.plot(dm_nw_xi, dm_nw_eta, '+', color='cyan', ms=14, mew=2, label='DM NW (Clowe+06)')
        axi.plot(dm_se_xi, dm_se_eta, 'x', color='cyan', ms=14, mew=2, label='DM SE (Clowe+06)')
        axi.legend(fontsize=8, facecolor='k', labelcolor='w')

    if bg_path:
        bg = np.array(Image.open(bg_path).convert('RGB'))
        bh, bw = bg.shape[:2]
        # TIF is the public composite (HST+Chandra), covers ~7.5×5.4 arcmin
        # (estimated from standard Bullet Cluster release dimensions)
        bg_w_arcsec = 450   # arcsec
        bg_h_arcsec = 324   # arcsec
        bg_extent = [-bg_w_arcsec/2, bg_w_arcsec/2, -bg_h_arcsec/2, bg_h_arcsec/2]
        axes[1].imshow(bg, origin='upper', extent=bg_extent, aspect='equal')
        axes[1].imshow(intensity, origin='lower', extent=extent,
                       cmap='hot', alpha=0.55, norm=PowerNorm(gamma=0.4),
                       aspect='equal', interpolation='bilinear')
        axes[1].set_xlim(gx.min(), gx.max())
        axes[1].set_ylim(gy.min(), gy.max())
        axes[1].set_title('Ripple overlay on optical', color='w', fontsize=11)
        axes[1].set_xlabel('Δξ (arcsec)', color='w')
        axes[1].tick_params(colors='w')

    plt.tight_layout()
    fig.savefig(outpath, dpi=150, bbox_inches='tight', facecolor='k')
    plt.close(fig)
    print(f"Saved → {outpath}")

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print("Loading catalog...")
    xi, eta, amp, lam, damp = load_catalog()
    print(f"  {len(xi)} cluster galaxies")

    print("Building output grid...")
    gx, gy = make_grid()
    print(f"  Grid: {gx.shape[1]} × {gx.shape[0]} px at {GRID_RES} arcsec/px")

    # ── run 1: current epoch ───────────────────────────────────────────────
    print("\nComputing current-epoch ripple field...")
    field_now = compute_field(gx, gy, xi, eta, amp, lam, damp)
    render(field_now, gx, gy,
           'Galaxy wave superposition — current epoch (z=0.296)',
           '/tmp/ripple_current.png',
           bg_path='/media/rendier/0123-4567/bullet_cluster/The_Bullet_Cluster.tif')

    # ── run 2: rolled back to collision epoch ──────────────────────────────
    print("\nRolling back to collision epoch (~240 Myr ago)...")
    xi_rb, eta_rb, amp_rb, lam_rb, damp_rb = rollback_positions(xi, eta, amp, lam, damp)
    print("Computing collision-epoch ripple field...")
    field_rb = compute_field(gx, gy, xi_rb, eta_rb, amp_rb, lam_rb, damp_rb)
    render(field_rb, gx, gy,
           'Galaxy wave superposition — collision epoch (rolled back ~240 Myr)',
           '/tmp/ripple_rollback.png',
           bg_path='/media/rendier/0123-4567/bullet_cluster/The_Bullet_Cluster.tif')

    # ── difference: what moved ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7), facecolor='k')
    diff = (field_rb**2 - field_now**2)
    diff /= np.abs(diff).max()
    extent = [gx.min(), gx.max(), gy.min(), gy.max()]
    ax.imshow(diff, origin='lower', extent=extent,
              cmap='RdBu_r', vmin=-1, vmax=1,
              aspect='equal', interpolation='bilinear')
    ax.set_title('Δ|Ψ|² (rollback − current): positive=brighter at collision', color='w')
    ax.set_xlabel('Δξ (arcsec)', color='w'); ax.tick_params(colors='w')
    fig.savefig('/tmp/ripple_diff.png', dpi=150, bbox_inches='tight', facecolor='k')
    plt.close(fig)
    print("Saved → /tmp/ripple_diff.png")

    # copy to viewer layers
    import shutil
    shutil.copy('/tmp/ripple_current.png', os.path.join(OUT_DIR, 'ripple_current.png'))
    shutil.copy('/tmp/ripple_rollback.png', os.path.join(OUT_DIR, 'ripple_rollback.png'))
    print("\nDone. Check /tmp/ripple_current.png and /tmp/ripple_rollback.png")

if __name__ == '__main__':
    main()
