#!/usr/bin/env python3
"""lens_delay.py: image positions, magnifications and time lags for a gravitationally lensed point source.

An outside toolset for comparing other mechanisms against the standard lensing calculation behind the
SN Refsdal reappearance prediction (papers in BulletCluster/pending/next_cross/MACS_J1149_Refsdal/papers).
It is NOT an engine: plain functions and small classes, numpy (+ scipy for the fit, astropy only to read FITS).

Angles are in arcseconds on the sky, x = east offset, y = north offset, from any origin you choose.
Distances in Mpc, times in days.  Flat ΛCDM only.

The calculation (single lens plane):
    lens equation        β = θ − α(θ)
    Jacobian             A = I − ∂α/∂θ ;  μ = 1/det A
    Fermat potential     τ(θ) = ½|θ − β|² − ψ(θ)          (arcsec²),  ∇ψ = α
    arrival time         t(θ) = (D_Δt / c) τ(θ),  D_Δt = (1+z_l) D_l D_s / D_ls
    time lag             t_i − t_first
Image type: det A>0 & tr A>0 minimum; det A<0 saddle; det A>0 & tr A<0 maximum.

Usage:  see LENS_DELAY_WIKI.md.   python3 lens_delay.py selftest | run CONFIG.json
dPrint feed: LENS_DPRINT=1 prints `name = new value` after the main assignments.
"""
import json, math, os, sys, datetime
import numpy as np

ARCSEC = math.pi / 648000.0
C_KMS = 299792.458
MPC_M = 3.0856775814913673e22
DP = os.environ.get("LENS_DPRINT") == "1"


def dp(name, value):
    if DP:
        print(f"[dp] {name} = {value!r}", flush=True)


# ───────────────────────────── cosmology (flat ΛCDM) ─────────────────────────────

class Cosmology:
    def __init__(self, H0=70.0, Om=0.3):
        self.H0, self.Om, self.OL = H0, Om, 1.0 - Om
        dp("cosmology", (H0, Om))

    def comoving(self, z, n=4001):
        """Comoving distance in Mpc, Simpson rule."""
        if z <= 0:
            return 0.0
        zz = np.linspace(0.0, z, n)
        f = 1.0 / np.sqrt(self.Om * (1 + zz) ** 3 + self.OL)
        h = zz[1] - zz[0]
        s = f[0] + f[-1] + 4 * f[1:-1:2].sum() + 2 * f[2:-1:2].sum()
        return (C_KMS / self.H0) * s * h / 3.0

    def D_A(self, z1, z2=None):
        """Angular-diameter distance (Mpc): observer→z1, or between z1<z2 when z2 is given."""
        if z2 is None:
            return self.comoving(z1) / (1 + z1)
        return (self.comoving(z2) - self.comoving(z1)) / (1 + z2)

    def time_delay_distance(self, zl, zs):
        d = (1 + zl) * self.D_A(zl) * self.D_A(zs) / self.D_A(zl, zs)
        dp("D_dt_Mpc", d)
        return d

    def days_per_arcsec2(self, zl, zs):
        """T such that t = T·τ, with τ in arcsec²: T = D_Δt/c × (1 arcsec in rad)²."""
        T = self.time_delay_distance(zl, zs) * MPC_M / (C_KMS * 1e3) / 86400.0 * ARCSEC ** 2
        dp("T_days_per_arcsec2", T)
        return T

    def ratio_Dls_Ds(self, zl, zs):
        return self.D_A(zl, zs) / self.D_A(zs)


# ───────────────────────────── lens components ─────────────────────────────
# Each has alpha(x,y)->(ax,ay), psi(x,y), dalpha(x,y)->(axx,axy,ayx,ayy).  Angles in arcsec.

class Component:
    fd = 1e-4

    def dalpha(self, x, y):
        h = self.fd
        axp, ayp = self.alpha(x + h, y); axm, aym = self.alpha(x - h, y)
        bxp, byp = self.alpha(x, y + h); bxm, bym = self.alpha(x, y - h)
        return ((axp - axm) / (2 * h), (bxp - bxm) / (2 * h), (ayp - aym) / (2 * h), (byp - bym) / (2 * h))


class SIE(Component):
    """Singular isothermal ellipsoid (Kormann et al. 1994; Keeton 2001 eqs.), core 0.
    b: Einstein-radius scale (arcsec), q: axis ratio ≤1, phi: major-axis angle from +x (deg, CCW).
    κ = ½ b / sqrt(x'² + y'²/q²) in the frame aligned with the major axis x'. q=1 is the SIS."""

    def __init__(self, x0, y0, b, q=1.0, phi=0.0):
        self.x0, self.y0, self.b, self.q, self.phi = x0, y0, b, min(q, 1.0), math.radians(phi)

    def _aligned(self, x, y):
        c, s = math.cos(self.phi), math.sin(self.phi)
        dx, dy = x - self.x0, y - self.y0
        return c * dx + s * dy, -s * dx + c * dy, c, s

    def alpha(self, x, y):
        xa, ya, c, s = self._aligned(np.asarray(x, float), np.asarray(y, float))
        q, b = self.q, self.b
        e = math.sqrt(max(1.0 - q * q, 0.0))
        r = np.sqrt(xa ** 2 + ya ** 2) + 1e-300
        if e < 1e-8:
            ax, ay = b * xa / r, b * ya / r
        else:
            w = np.sqrt(q * q * xa ** 2 + ya ** 2) + 1e-300
            ax = b * q / e * np.arctan(e * xa / w)
            ay = b * q / e * np.arctanh(e * ya / w)
        return c * ax - s * ay, s * ax + c * ay

    def psi(self, x, y):
        xa, ya, c, s = self._aligned(np.asarray(x, float), np.asarray(y, float))
        ax, ay = self.alpha(x, y)
        axa, aya = c * ax + s * ay, -s * ax + c * ay        # deflection in aligned frame
        return xa * axa + ya * aya                           # ψ is homogeneous of degree 1


class Shear(Component):
    """External shear γ1, γ2: ψ = ½[γ1(x²−y²) + 2γ2 xy] about (x0,y0); α = (γ1 x + γ2 y, γ2 x − γ1 y)."""

    def __init__(self, g1, g2, x0=0.0, y0=0.0):
        self.g1, self.g2, self.x0, self.y0 = g1, g2, x0, y0

    def alpha(self, x, y):
        dx, dy = np.asarray(x, float) - self.x0, np.asarray(y, float) - self.y0
        return self.g1 * dx + self.g2 * dy, self.g2 * dx - self.g1 * dy

    def psi(self, x, y):
        dx, dy = np.asarray(x, float) - self.x0, np.asarray(y, float) - self.y0
        return 0.5 * (self.g1 * (dx ** 2 - dy ** 2) + 2 * self.g2 * dx * dy)


class NFW(Component):
    """Spherical NFW (Bartelmann 1996; Wright & Brainerd 2000). κ_s: characteristic convergence, theta_s (arcsec).
    α(θ) = 4 κ_s θ_s g(x)/x ; ψ = 2 κ_s θ_s² [ln²(x/2) − arccosh²(1/x)] (x<1), [ln²(x/2) + arccos²(1/x)] (x>1); x = θ/θ_s."""

    def __init__(self, x0, y0, kappa_s, theta_s):
        self.x0, self.y0, self.ks, self.ts = x0, y0, kappa_s, theta_s

    @staticmethod
    def _g(x):
        x = np.asarray(x, float)
        out = np.empty_like(x)
        lo, hi, eq = x < 1 - 1e-9, x > 1 + 1e-9, np.abs(x - 1) <= 1e-9
        out[lo] = np.log(x[lo] / 2) + np.arccosh(1 / x[lo]) / np.sqrt(1 - x[lo] ** 2)
        out[hi] = np.log(x[hi] / 2) + np.arccos(1 / x[hi]) / np.sqrt(x[hi] ** 2 - 1)
        out[eq] = np.log(0.5) + 1.0
        return out

    def alpha(self, x, y):
        dx, dy = np.asarray(x, float) - self.x0, np.asarray(y, float) - self.y0
        r = np.sqrt(dx ** 2 + dy ** 2) + 1e-300
        xx = r / self.ts
        a = 4 * self.ks * self.ts * self._g(xx) / xx
        return a * dx / r, a * dy / r

    def psi(self, x, y):
        dx, dy = np.asarray(x, float) - self.x0, np.asarray(y, float) - self.y0
        xx = np.sqrt(dx ** 2 + dy ** 2) / self.ts + 1e-300
        out = np.empty_like(xx)
        lo, hi = xx < 1, xx >= 1
        out[lo] = np.log(xx[lo] / 2) ** 2 - np.arccosh(1 / xx[lo]) ** 2
        out[hi] = np.log(xx[hi] / 2) ** 2 + np.arccos(1 / xx[hi]) ** 2
        return 2 * self.ks * self.ts ** 2 * out


class DPIE(Component):
    """Circular dual pseudo-isothermal (Elíasdóttir et al. 2007 with zero ellipticity; the 'PIEMD' of Lenstool).
    κ(θ) = A [1/√(a²+θ²) − 1/√(s²+θ²)], A = (E0/2) s/(s−a), E0 = 4π(σ/c)² D_ls/D_s in arcsec
    (use sigma_to_E0). a: core radius, s: cut radius (arcsec). a→0, s→∞ is the SIS of Einstein radius E0.
    α = (2A/θ)[√(a²+θ²) − a − √(s²+θ²) + s]; ψ = 2A[F_a − F_s], F_u = √(u²+θ²) − u ln(u+√(u²+θ²)) − u(1 − ln 2u).
    Ellipticity is not implemented (use SIE for elliptical single galaxies)."""

    def __init__(self, x0, y0, E0, a, s):
        self.x0, self.y0, self.E0, self.a, self.s = x0, y0, E0, a, s
        self.A = 0.5 * E0 * s / (s - a)

    def alpha(self, x, y):
        dx, dy = np.asarray(x, float) - self.x0, np.asarray(y, float) - self.y0
        r = np.sqrt(dx ** 2 + dy ** 2) + 1e-300
        a, s = self.a, self.s
        mag = 2 * self.A / r * (np.sqrt(a * a + r * r) - a - np.sqrt(s * s + r * r) + s)
        return mag * dx / r, mag * dy / r

    def psi(self, x, y):
        r2 = (np.asarray(x, float) - self.x0) ** 2 + (np.asarray(y, float) - self.y0) ** 2

        def F(u):
            w = np.sqrt(u * u + r2)
            return w - u * np.log(u + w) - u * (1 - math.log(2 * u))
        return 2 * self.A * (F(self.a) - F(self.s))


def sigma_to_E0(sigma_kms, zl, zs, cosmo):
    """E0 = 4π (σ/c)² D_ls/D_s, converted to arcsec."""
    E0 = 4 * math.pi * (sigma_kms / C_KMS) ** 2 * cosmo.ratio_Dls_Ds(zl, zs) / ARCSEC
    dp("E0_arcsec", E0)
    return E0


class DeflectionMap(Component):
    """A published model as arrays: ax, ay (arcsec) on a regular grid, valid for source redshift z_ref.
    ax, ay are [row=y, col=x] arrays; pixel (i,j) sits at (x0 + j·pix, y0 + i·pix) in arcsec, x east, y north.
    FITS maps usually have RA increasing to the left: flip columns (and the sign convention) yourself so x is east.
    psi is built by integrating α (curl-free) along the bottom row then up each column, zero at pixel (0,0).
    Rescale to another source redshift with rescale_to (α ∝ D_ls/D_s)."""

    def __init__(self, ax, ay, pix, x0, y0, z_ref=None):
        self.ax, self.ay = np.asarray(ax, float), np.asarray(ay, float)
        self.pix, self.x0, self.y0, self.z_ref = pix, x0, y0, z_ref
        self.scale = 1.0
        self._psi = None
        self._grads = None

    def rescale_to(self, zl, zs, cosmo):
        if self.z_ref is None:
            raise ValueError("DeflectionMap.z_ref is needed to rescale")
        self.scale = cosmo.ratio_Dls_Ds(zl, zs) / cosmo.ratio_Dls_Ds(zl, self.z_ref)
        dp("map_scale", self.scale)

    def _interp(self, arr, x, y):
        from scipy.ndimage import map_coordinates
        col = (np.asarray(x, float) - self.x0) / self.pix
        row = (np.asarray(y, float) - self.y0) / self.pix
        return map_coordinates(arr, [np.atleast_1d(row), np.atleast_1d(col)], order=1, mode="nearest").reshape(np.shape(x))

    def alpha(self, x, y):
        return self.scale * self._interp(self.ax, x, y), self.scale * self._interp(self.ay, x, y)

    def _build_psi(self):
        p = self.pix
        row0 = np.concatenate([[0.0], np.cumsum(0.5 * (self.ax[0, 1:] + self.ax[0, :-1]) * p)])
        up = np.cumsum(0.5 * (self.ay[1:, :] + self.ay[:-1, :]) * p, axis=0)
        psi = np.vstack([np.zeros(self.ax.shape[1]), up]) + row0[None, :]
        self._psi = psi

    def psi(self, x, y):
        if self._psi is None:
            self._build_psi()
        return self.scale * self._interp(self._psi, x, y)

    def dalpha(self, x, y):
        if self._grads is None:
            axy, axx = np.gradient(self.ax, self.pix)      # np.gradient gives (d/drow, d/dcol)
            ayy, ayx = np.gradient(self.ay, self.pix)
            self._grads = (axx, axy, ayx, ayy)
        s = self.scale
        return tuple(s * self._interp(g, x, y) for g in self._grads)


def load_fits_map(path_ax, path_ay, pix, x0, y0, z_ref=None, flip_columns=False):
    """Read two FITS images (needs astropy). flip_columns=True mirrors x when the file has RA increasing leftwards."""
    from astropy.io import fits
    ax, ay = fits.getdata(path_ax).astype(float), fits.getdata(path_ay).astype(float)
    if flip_columns:
        ax, ay = -ax[:, ::-1], ay[:, ::-1]
    return DeflectionMap(ax, ay, pix, x0, y0, z_ref)


# ───────────────────────────── lens model ─────────────────────────────

class LensModel:
    def __init__(self, components, cosmo, zl, zs):
        self.components, self.cosmo, self.zl, self.zs = list(components), cosmo, zl, zs
        self.T = cosmo.days_per_arcsec2(zl, zs)

    def alpha(self, x, y):
        ax = ay = 0.0
        for c in self.components:
            a, b = c.alpha(x, y); ax = ax + a; ay = ay + b
        return ax, ay

    def psi(self, x, y):
        return sum(c.psi(x, y) for c in self.components)

    def jacobian(self, x, y):
        """A = I − ∂α/∂θ as (Axx, Axy, Ayx, Ayy)."""
        d = [0.0, 0.0, 0.0, 0.0]
        for c in self.components:
            for i, v in enumerate(c.dalpha(x, y)):
                d[i] = d[i] + v
        return 1.0 - d[0], -d[1], -d[2], 1.0 - d[3]

    def source_of(self, x, y):
        ax, ay = self.alpha(x, y)
        return np.asarray(x) - ax, np.asarray(y) - ay

    def fermat(self, x, y, bx, by):
        return 0.5 * ((np.asarray(x) - bx) ** 2 + (np.asarray(y) - by) ** 2) - self.psi(x, y)


# ───────────────────────────── solving ─────────────────────────────

class Image:
    def __init__(self, x, y, mu, kind, tau, t, delay=0.0):
        self.x, self.y, self.mu, self.kind, self.tau, self.t, self.delay = x, y, mu, kind, tau, t, delay

    def __repr__(self):
        return (f"Image(x={self.x:.4f}, y={self.y:.4f}, mu={self.mu:.3f}, {self.kind}, "
                f"tau={self.tau:.5f}, delay={self.delay:.2f} d)")

    def as_dict(self):
        return {k: getattr(self, k) for k in ("x", "y", "mu", "kind", "tau", "t", "delay")}


def _classify(Axx, Axy, Ayx, Ayy):
    det, tr = Axx * Ayy - Axy * Ayx, Axx + Ayy
    return ("minimum" if tr > 0 else "maximum") if det > 0 else "saddle", det


def solve_images(model, beta, box, n=500, tol=1e-9, merge=1e-3):
    """All images of a point source at beta=(bx,by).  box=(xmin,xmax,ymin,ymax) arcsec to search; n×n start grid.
    Starts Newton's method from every local minimum of |β(θ)−β| on the grid.  A coarse grid can miss images
    near a singular centre; raise n or narrow box.  Images are returned sorted by arrival time, delays relative to the first."""
    bx, by = beta
    xs, ys = np.linspace(box[0], box[1], n), np.linspace(box[2], box[3], n)
    X, Y = np.meshgrid(xs, ys)
    sx, sy = model.source_of(X, Y)
    R = (sx - bx) ** 2 + (sy - by) ** 2
    pad = np.pad(R, 1, constant_values=np.inf)
    core = pad[1:-1, 1:-1]
    mask = np.ones_like(core, bool)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di or dj:
                mask &= core <= pad[1 + di:n + 1 + di, 1 + dj:n + 1 + dj]
    cell = max(xs[1] - xs[0], ys[1] - ys[0])
    found = []
    for i, j in zip(*np.nonzero(mask)):
        x, y = float(X[i, j]), float(Y[i, j])
        for _ in range(60):
            sx0, sy0 = model.source_of(x, y)
            rx, ry = float(sx0 - bx), float(sy0 - by)
            Axx, Axy, Ayx, Ayy = (float(v) for v in model.jacobian(x, y))
            det = Axx * Ayy - Axy * Ayx
            if abs(det) < 1e-14:
                break
            dx, dy = (Ayy * rx - Axy * ry) / det, (-Ayx * rx + Axx * ry) / det
            step = math.hypot(dx, dy)
            if step > 5 * cell:
                dx, dy = dx * 5 * cell / step, dy * 5 * cell / step
            x, y = x - dx, y - dy
            if math.hypot(dx, dy) < tol:
                break
        sx0, sy0 = model.source_of(x, y)
        if math.hypot(float(sx0 - bx), float(sy0 - by)) < 1e-6 and box[0] <= x <= box[1] and box[2] <= y <= box[3]:
            if all(math.hypot(x - f[0], y - f[1]) > merge for f in found):
                found.append((x, y))
    out = []
    for x, y in found:
        J = tuple(float(v) for v in model.jacobian(x, y))
        kind, det = _classify(*J)
        tau = float(model.fermat(x, y, bx, by))
        out.append(Image(x, y, 1.0 / det, kind, tau, model.T * tau))
    out.sort(key=lambda im: im.t)
    for im in out:
        im.delay = im.t - out[0].t
    dp("n_images", len(out))
    return out


def backmap(model, positions):
    """Source-plane position of each observed image, their mean (the predicted source) and the scatter (rms, arcsec).
    This is the 'weighted-mean source position' step of the Refsdal predictions (unweighted here)."""
    pts = np.array([[float(v) for v in model.source_of(x, y)] for x, y in positions])
    mean = pts.mean(axis=0)
    rms = float(np.sqrt(((pts - mean) ** 2).sum(axis=1).mean()))
    dp("backmap_mean_rms", (mean.tolist(), rms))
    return pts, mean, rms


def delays_at(model, positions, beta):
    """Fermat potential, arrival time and delay (days, relative to the earliest) at given positions (observed images)."""
    taus = np.array([float(model.fermat(x, y, *beta)) for x, y in positions])
    t = model.T * taus
    return taus, t, t - t.min()


def predict_dates(images, ref_index, ref_date):
    """Calendar date of each image given that images[ref_index] was seen on ref_date (datetime.date)."""
    base = images[ref_index].t
    return [ref_date + datetime.timedelta(days=im.t - base) for im in images]


def compare_models(results):
    """results: {name: [Image,...]} → per-image-rank spread of delays (days): {rank: (min, max)}."""
    ranks = {}
    for imgs in results.values():
        for k, im in enumerate(imgs):
            lo, hi = ranks.get(k, (im.delay, im.delay))
            ranks[k] = (min(lo, im.delay), max(hi, im.delay))
    return ranks


# ───────────────────────────── fitting a galaxy-scale quad ─────────────────────────────

def fit_sie_shear_to_quad(positions, centre, cosmo, zl, zs, start=None):
    """Fit SIE + shear to measured image positions with the lens centre fixed at `centre` (the observed galaxy).
    Parameters: b, q, phi(deg), γ1, γ2, and the source (bx,by) → 7 unknowns against 8 numbers for 4 images.
    Minimises the source-plane scatter of the back-mapped images.  Needs scipy.  Returns (LensModel, beta, rms)."""
    from scipy.optimize import least_squares
    pos = np.asarray(positions, float)
    cx, cy = centre
    r0 = float(np.mean(np.hypot(pos[:, 0] - cx, pos[:, 1] - cy)))
    p0 = start or [r0, 0.8, 0.0, 0.0, 0.0]

    def build(p):
        return LensModel([SIE(cx, cy, p[0], min(max(p[1], 0.2), 1.0), p[2]), Shear(p[3], p[4], cx, cy)], cosmo, zl, zs)

    def resid(p):
        m = build(p)
        sx, sy = m.source_of(pos[:, 0], pos[:, 1])
        return np.concatenate([sx - sx.mean(), sy - sy.mean()])

    sol = least_squares(resid, p0)
    m = build(sol.x)
    _, mean, rms = backmap(m, pos.tolist())
    dp("fit_params", sol.x.tolist())
    return m, tuple(mean), rms


# ───────────────────────────── config runner and self-test ─────────────────────────────

def _component(d, cosmo, zl, zs):
    t = d["type"].lower()
    if t == "sie":
        return SIE(d["x0"], d["y0"], d["b"], d.get("q", 1.0), d.get("phi", 0.0))
    if t == "shear":
        return Shear(d["g1"], d["g2"], d.get("x0", 0.0), d.get("y0", 0.0))
    if t == "nfw":
        return NFW(d["x0"], d["y0"], d["kappa_s"], d["theta_s"])
    if t == "dpie":
        E0 = d["E0"] if "E0" in d else sigma_to_E0(d["sigma"], zl, zs, cosmo)
        return DPIE(d["x0"], d["y0"], E0, d["a"], d["s"])
    if t == "map":
        m = load_fits_map(d["ax"], d["ay"], d["pix"], d["x0"], d["y0"], d.get("z_ref"), d.get("flip_columns", False))
        if d.get("z_ref"):
            m.rescale_to(zl, zs, cosmo)
        return m
    raise ValueError(f"unknown component type {d['type']!r}")


def run_config(path):
    cfg = json.load(open(path))
    cosmo = Cosmology(cfg.get("H0", 70.0), cfg.get("Om", 0.3))
    zl, zs = cfg["zl"], cfg["zs"]
    model = LensModel([_component(c, cosmo, zl, zs) for c in cfg["components"]], cosmo, zl, zs)
    obs = cfg.get("observed_images")
    if "beta" in cfg:
        beta = tuple(cfg["beta"])
    elif obs:
        _, mean, rms = backmap(model, obs)
        beta = tuple(mean)
        print(f"source from back-mapping {len(obs)} images: β = ({beta[0]:.5f}, {beta[1]:.5f}) arcsec, rms {rms:.5f}")
    else:
        raise ValueError("config needs 'beta' or 'observed_images'")
    imgs = solve_images(model, beta, tuple(cfg["box"]), cfg.get("n", 500))
    for im in imgs:
        print(im)
    if cfg.get("ref_image") is not None and cfg.get("ref_date"):
        d0 = datetime.date.fromisoformat(cfg["ref_date"])
        for im, d in zip(imgs, predict_dates(imgs, cfg["ref_image"], d0)):
            print(f"  ({im.x:.3f},{im.y:.3f}) {im.kind:8s} → {d}")
    if cfg.get("out"):
        json.dump({"beta": beta, "T_days_per_arcsec2": model.T, "images": [i.as_dict() for i in imgs]},
                  open(cfg["out"], "w"), indent=1)


def selftest():
    """Analytic and consistency checks of the components (no data needed). Returns a list of (name, ok, detail)."""
    res = []
    cosmo = Cosmology()
    # SIS: images at β±θE, Δτ = 2 θE β
    m = LensModel([SIE(0, 0, 1.0, 1.0, 0)], cosmo, 0.5, 1.5)
    imgs = solve_images(m, (0.3, 0.0), (-3, 3, -3, 3), 300)
    xs = sorted(round(i.x, 4) for i in imgs)
    d_tau = abs(imgs[0].tau - imgs[-1].tau)
    res.append(("SIS images at β±θE, Δτ=2θEβ", xs == [-0.7, 1.3] and abs(d_tau - 0.6) < 1e-6, (xs, d_tau)))
    # q→1 SIE equals SIS deflection
    a1, a2 = SIE(0, 0, 1.0, 0.9999999, 0).alpha(0.7, 0.4), SIE(0, 0, 1.0, 1.0, 0).alpha(0.7, 0.4)
    res.append(("SIE(q→1)=SIS", abs(a1[0] - a2[0]) < 1e-6 and abs(a1[1] - a2[1]) < 1e-6, (a1, a2)))
    # ∇ψ = α for each analytic component
    for name, c in (("SIE", SIE(0.1, -0.2, 1.1, 0.7, 30)), ("NFW", NFW(0, 0, 0.2, 5.0)),
                    ("DPIE", DPIE(0, 0, 2.0, 0.3, 20.0)), ("Shear", Shear(0.05, -0.03))):
        h, ok = 1e-5, True
        for (x, y) in ((1.3, 0.4), (-2.0, 1.1), (6.0, -4.0)):
            gx = (c.psi(x + h, y) - c.psi(x - h, y)) / (2 * h)
            gy = (c.psi(x, y + h) - c.psi(x, y - h)) / (2 * h)
            ax, ay = c.alpha(x, y)
            ok &= abs(gx - ax) < 1e-5 and abs(gy - ay) < 1e-5
        res.append((f"∇ψ=α ({name})", bool(ok), None))
    # DPIE → SIS limit
    d = DPIE(0, 0, 1.0, 1e-6, 1e6).alpha(1.0, 0.0)[0]
    res.append(("DPIE→SIS (a→0, s→∞)", abs(d - 1.0) < 1e-4, d))
    # cosmology sanity: D_A(z=1) for H0=70, Ωm=0.3 ≈ 1651 Mpc
    da = cosmo.D_A(1.0)
    res.append(("D_A(z=1)≈1651 Mpc", abs(da - 1651) < 5, da))
    for r in res:
        print(("PASS " if r[1] else "FAIL ") + r[0] + (f"   {r[2]}" if r[2] is not None else ""))
    return res


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        ok = all(r[1] for r in selftest())
        sys.exit(0 if ok else 1)
    if len(sys.argv) >= 3 and sys.argv[1] == "run":
        run_config(sys.argv[2])
    else:
        print(__doc__)
