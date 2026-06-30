"""
constants.py — Bullet Cluster engine fixed values.
No free parameters. Numbers from literature, cited.
"""

# ── Base directory ────────────────────────────────────────────────────────────
BASE = '/media/rendier/0123-4567/bullet_cluster'

# ── Cluster ───────────────────────────────────────────────────────────────────
RA0       = 104.6098   # deg  centroid (X-ray)
DEC0      = -55.9446   # deg
Z_L       = 0.296      # lens redshift
Z_S       = 1.2        # source redshift (canonical weak-lensing background)

# ── DM halo positions — Clowe et al. 2006 ApJL 648 L109, Table 1 ─────────────
DM_NW = dict(ra=104.6383, dec=-55.9252, label='DM NW (main)')
DM_SE = dict(ra=104.5726, dec=-55.9563, label='DM SE (bullet)')

# ── X-ray gas peak positions — Markevitch et al. 2002 ApJ 567 L27 ─────────────
GAS_NW = dict(ra=104.625,  dec=-55.930, label='Gas NW')
GAS_SE = dict(ra=104.569,  dec=-55.961, label='Gas SE')

# ── Bow shock position — Markevitch et al. 2002 ──────────────────────────────
BOW_SHOCK = dict(ra=104.558, dec=-55.958, label='Bow shock')

# ── Radio relic — Shimwell et al. 2014 MNRAS 440 2901 ───────────────────────
RADIO_RELIC = dict(ra=104.44, dec=-55.97, label='Radio relic')

# ── Merger axis: NW→SE position angle (degrees E of N) ───────────────────────
MERGER_PA_DEG = 135.0

# ── Physical scale — FlatLCDM H0=70 Om0=0.3 ─────────────────────────────────
# At z=0.296: 1 arcmin = 0.265 Mpc  (Ned Wright's cosmology calculator)
ARCMIN_PER_MPC = 1.0 / 0.265     # arcmin/Mpc at z_l
MPC_PER_ARCMIN = 0.265           # Mpc/arcmin

# ── NFW halo parameters — Clowe+2006 Table 1 (approximate) ──────────────────
NFW_NW = dict(M200_msun=3.7e14, c=5.0, ra=DM_NW['ra'], dec=DM_NW['dec'])
NFW_SE = dict(M200_msun=1.5e14, c=4.5, ra=DM_SE['ra'], dec=DM_SE['dec'])

# ── Faraday / RM synthesis parameters ────────────────────────────────────────
# MeerKAT MGCLS L-band: 900–1670 MHz, ~800 channels
FREQ_MIN_HZ  = 900e6
FREQ_MAX_HZ  = 1670e6
N_FREQ_CHAN  = 800        # approximate
LAMBDA2_MIN  = (3e8 / FREQ_MAX_HZ) ** 2   # m²
LAMBDA2_MAX  = (3e8 / FREQ_MIN_HZ) ** 2   # m²
DELTA_LAMBDA2 = (LAMBDA2_MAX - LAMBDA2_MIN) / N_FREQ_CHAN

# RM resolution: δφ ≈ 2√3 / (λ²_max − λ²_min)   [rad/m²]
import math
RM_RESOLUTION_RADM2 = 2 * math.sqrt(3) / (LAMBDA2_MAX - LAMBDA2_MIN)

# Max detectable RM scale: ||φ||_max ≈ √3 / δλ²  [rad/m²]
RM_MAX_SCALE_RADM2  = math.sqrt(3) / DELTA_LAMBDA2

# ── σ-face values (from Ainulindale) ─────────────────────────────────────────
SIGMA_HALF  = 0.5          # causality / ZD boundary
D_STAR      = 0.2460       # canonical d* constant
OMEGA_ZS    = 0.5671432904097838

# ── Diagnostic thresholds (falsifiable, set BEFORE seeing data) ──────────────
# ΔRM_THRESHOLD: Faraday excess at DM peak vs interpolated gas field
# If |ΔRM_DM| > ΔRM_THRESHOLD → Faraday screen → particle DM
# If |ΔRM_DM| < ΔRM_THRESHOLD → no screen → wave/interference DM
# Value: 5 rad/m² = ~5σ of typical ICM RM fluctuations at this resolution
RM_THRESHOLD_RADM2 = 5.0   # kept for ΔRM reference in notebooks

# RM ratio diagnostic: |RM(DM)| / |RM(nearest_gas_peak)| ≥ threshold → screen
# Wave model: DM is on falling edge of gas peak → ratio < 1
# Particle model: DM screen raises RM to match/exceed gas peak → ratio ≥ 1
RM_RATIO_THRESHOLD  = 0.95

# Polarized fraction threshold at DM band center
# If p_frac(DM_center) > POL_FRAC_BRIGHT_THRESHOLD → bright band = slingshot
# If p_frac(DM_center) < POL_FRAC_DARK_THRESHOLD  → dark band = graviton
POL_FRAC_BRIGHT_THRESHOLD = 0.20   # 20% polarised fraction
POL_FRAC_DARK_THRESHOLD   = 0.05   # 5%
