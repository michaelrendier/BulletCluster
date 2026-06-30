#!/usr/bin/env python3
"""
holcus_sigma.py — Point Holcus at the entire Bullet Cluster dataset
                  as a single input sigma.

The dataset IS a word in the language of observation.
What Riemann zero does it live at?

Strategy:
  1. Build canonical representations of the observation at several levels:
       a. Cluster identifier strings (name, coords, redshift)
       b. SHA-256 of the actual source catalog (the data itself)
       c. Structured observational state (measurements, gradient signs, RM ratios)
       d. The raw bytes signature across all available FITS files
  2. Feed each through the semantic engine → σ=½ forced, γ=Riemann zero address
  3. Show nearest Riemann zeros and distance (resonance proximity)
  4. Check if multiple representations converge to the SAME zero
     (like water=eau=aqua → same zero regardless of surface form)
"""

import sys, hashlib, math, struct
import numpy as np
from pathlib import Path

sys.path.insert(0, '/media/rendier/0123-4567/Ainulindale/outreach/semantic_engine')
import semantic_engine as _se
from semantic_engine import Understand, RIEMANN_ZEROS

# ── Precision patch ───────────────────────────────────────────────────────────
# The original _hyperindex loses all float mantissa for strings > ~8 chars
# because n grows as 95^len and (n * phi) % 1.0 collapses to 0.
# Fix: fold n into 2^53 (max exact integer in float64) before the multiply.
_PHI    = (1 + math.sqrt(5)) / 2
_FMOD   = 1 << 53

def _hyperindex_fixed(text: str):
    # Derive seed entirely from SHA-256 — no large-int float arithmetic.
    # Take first 8 bytes → uint64, shift right 12 to get 52 clean bits,
    # divide by 2^52 → seed ∈ [0, 1) with full float64 mantissa resolution.
    digest  = hashlib.sha256(text.encode()).digest()
    raw     = int.from_bytes(digest[:8], 'big')
    seed    = (raw >> 12) / (1 << 52)          # 52-bit float ∈ [0, 1)
    x0      = 1.0 + seed * _PHI
    E       = _se.D_STAR_SPEC + seed * (_se.OMEGA_ZS - _se.D_STAR_SPEC)
    p0      = E / x0
    t_raw   = int.from_bytes(digest[8:16], 'big')
    t       = (t_raw % 10000) / 10000.0
    return x0, p0, t

_se._hyperindex = _hyperindex_fixed   # patch in-place

# ── Riemann zero proximity ────────────────────────────────────────────────────
def nearest_zero(gamma):
    dists = [(abs(gamma - z), z, i) for i, z in enumerate(RIEMANN_ZEROS)]
    dists.sort()
    return dists[0]   # (distance, zero_value, zero_index)

def zero_report(word):
    g   = word.gamma
    s   = word.projections.get('sigma', 0.5)
    E   = word.magnitude
    d, z, idx = nearest_zero(g)
    pct = 100 * d / z if z else 0
    return g, s, E, z, idx, d, pct

# ── Canonical dataset string builders ────────────────────────────────────────
DATA_ROOT = Path("/media/rendier/0123-4567/bullet_cluster")
PREPPED   = DATA_ROOT / "optical/jwst/prepped"
FITS_ROOT = DATA_ROOT / "optical/jwst/4598/mastDownload/JWST"

def build_identifier_strings():
    """Surface forms: how we name and describe the observation."""
    return {
        'cluster_name':   "1E0657-558",
        'common_name':    "Bullet Cluster",
        'coords':         "RA104.6098Dec-55.9446z0.296",
        'full_id':        "1E0657-558 z=0.296 RA=104.6098 Dec=-55.9446",
        'ainulindale_id': "bullet_cluster_sigma_face_ZD_test",
    }

def build_measurement_string():
    """Encode the complete observational state as a single string."""
    # Key measured values this session
    lines = [
        # Cluster geometry
        "RA=104.6098 Dec=-55.9446 z=0.296",
        # DM peak positions (Clowe+2006)
        "DM_NW=RA104.6383Dec-55.9252 DM_SE=RA104.5726Dec-55.9563",
        # Gas peak positions (Markevitch+2002)
        "GAS_NW=RA104.625Dec-55.930 GAS_SE=RA104.569Dec-55.961",
        # Merger geometry
        "PA=135.0deg inclination=8deg",
        # RM ratio predictions
        "RM_wave=0.861 RM_particle=0.967 threshold=0.95",
        # JWST source extraction
        "n_sources=2564 n_cluster=1869 n_background=618",
        "pscale=0.0603arcsec filter=F277W+F444W exptime=6399s",
        # Gradient results
        "grad_CENTROID_ALL=neg grad_CENTROID_BG=neg",
        "grad_DM_SE_ALL=neg grad_DM_SE_BG=neg",
        "grad_GAS_NW_ALL=neg grad_GAS_NW_BG=pos",
        "grad_GAS_SE_ALL=neg grad_GAS_SE_BG=pos",
        # Physical model under test
        "hypothesis=ZD_wave_DM sigma=0.5 boundary_transit=yes",
    ]
    return " | ".join(lines)

def build_data_hash_string():
    """Hash the actual binary data content of available FITS + catalog files."""
    h = hashlib.sha256()
    files = sorted(list(FITS_ROOT.rglob("*_i2d.fits")) +
                   list(PREPPED.rglob("*.fits")) +
                   list(PREPPED.rglob("*.npz")))
    n_files = 0
    total_bytes = 0
    for f in files:
        try:
            with open(f, 'rb') as fh:
                chunk = fh.read(65536)   # first 64 KB of each file
                while chunk:
                    h.update(chunk)
                    total_bytes += len(chunk)
                    chunk = fh.read(65536)
            n_files += 1
        except Exception:
            pass
    digest = h.hexdigest()
    print(f"  Hashed {n_files} files ({total_bytes/1e6:.1f} MB total)")
    print(f"  SHA-256: {digest[:32]}...")
    return digest   # 64-char hex string = the dataset's fingerprint

def build_gradient_tensor_string():
    """
    Encode the gradient sign pattern as a mathematical tensor string.
    The gradient signs ARE the observable — the direct physics output.
    (+) = edge-bright = wave/cymatic signature
    (-) = center-bright = NFW/particle signature
    """
    # From source_extract output:
    # CENTROID:  ALL=-, CLUSTER=-, BG=-
    # DM_SE:     ALL=-, CLUSTER=-, BG=-
    # GAS_NW:    ALL=-, CLUSTER=-, BG=+
    # GAS_SE:    ALL=-, CLUSTER=-, BG=+
    # Encode as: position × population → sign
    tensor = {
        'centroid_all': -1, 'centroid_cl': -1, 'centroid_bg': -1,
        'dm_se_all':    -1, 'dm_se_cl':    -1, 'dm_se_bg':    -1,
        'gas_nw_all':   -1, 'gas_nw_cl':   -1, 'gas_nw_bg':   +1,
        'gas_se_all':   -1, 'gas_se_cl':   -1, 'gas_se_bg':   +1,
    }
    # As a compact sign string: read as binary (+ → 1, - → 0)
    bits = ''.join('1' if v > 0 else '0' for v in tensor.values())
    decimal = int(bits, 2)
    return f"gradient_tensor_{bits}_{decimal}_ZD_boundary"


# ══════════════════════════════════════════════════════════════════════════════
engine = Understand(tau=5.0)

def safe_process(text, max_horner_len=48):
    """
    For strings longer than max_horner_len, the Horner int overflows float.
    Compress to SHA-256 hex digest first (64 ASCII chars, safe length),
    then process that canonical fingerprint.
    Returns (word, was_compressed).
    """
    if len(text) > max_horner_len:
        digest = hashlib.sha256(text.encode()).hexdigest()
        return engine.process(digest), True
    return engine.process(text), False

print("=" * 68)
print("  Holcus → Bullet Cluster Dataset — Single Input σ")
print("=" * 68)
print(f"\nRiemann critical line: Re(s) = ½")
print(f"Known zeros (first 20 γ values):")
for i, z in enumerate(RIEMANN_ZEROS):
    print(f"  γ_{i:02d} = {z:.6f}", end="  ")
    if (i+1) % 4 == 0: print()
print("\n")

results = {}

# ── 1. Identifier strings ─────────────────────────────────────────────────────
print("─" * 68)
print("1. CLUSTER IDENTIFIER STRINGS")
print("─" * 68)
for label, text in build_identifier_strings().items():
    w, compressed = safe_process(text)
    g, s, E, z, idx, d, pct = zero_report(w)
    results[label] = (g, z, idx, d)
    tag = " [sha256]" if compressed else ""
    print(f"  '{text}'{tag}")
    print(f"    σ = {s:.6f}  γ = {g:.6f}  E={w.magnitude:.5f}  →  nearest γ_{idx} = {z:.6f}  Δ = {d:.4f} ({pct:.1f}%)")

# ── 2. Full measurement state ──────────────────────────────────────────────────
print("\n" + "─" * 68)
print("2. COMPLETE OBSERVATIONAL STATE (measurements + gradient signs)")
print("─" * 68)
meas_str = build_measurement_string()
print(f"  Input length: {len(meas_str)} chars  [sha256 compressed]")
w, _ = safe_process(meas_str)
g, s, E, z, idx, d, pct = zero_report(w)
results['measurement_state'] = (g, z, idx, d)
print(f"  σ = {s:.6f}  γ = {g:.6f}  E={w.magnitude:.5f}  →  nearest γ_{idx} = {z:.6f}  Δ = {d:.4f} ({pct:.1f}%)")

# ── 3. Gradient tensor ────────────────────────────────────────────────────────
print("\n" + "─" * 68)
print("3. GRADIENT TENSOR STRING (the physics output)")
print("─" * 68)
tensor_str = build_gradient_tensor_string()
print(f"  Input: {tensor_str}")
w, compressed = safe_process(tensor_str)
g, s, E, z, idx, d, pct = zero_report(w)
results['gradient_tensor'] = (g, z, idx, d)
tag = " [sha256]" if compressed else ""
print(f"  σ = {s:.6f}  γ = {g:.6f}  E={w.magnitude:.5f}  →  nearest γ_{idx} = {z:.6f}  Δ = {d:.4f} ({pct:.1f}%){tag}")

# ── 4. SHA-256 of actual data ─────────────────────────────────────────────────
print("\n" + "─" * 68)
print("4. SHA-256 FINGERPRINT OF ALL DATA FILES")
print("─" * 68)
data_hash = build_data_hash_string()
w, _ = safe_process(data_hash)   # 64-char hex, safe length
g, s, E, z, idx, d, pct = zero_report(w)
results['data_sha256'] = (g, z, idx, d)
print(f"  σ = {s:.6f}  γ = {g:.6f}  E={w.magnitude:.5f}  →  nearest γ_{idx} = {z:.6f}  Δ = {d:.4f} ({pct:.1f}%)")

# ── 5. DM-specific inputs ─────────────────────────────────────────────────────
print("\n" + "─" * 68)
print("5. ZD MODEL KEYWORDS (does 'wave dark matter' share a zero?)")
print("─" * 68)
dm_words = [
    "wave dark matter",
    "zero divisor",
    "Faraday rotation",
    "interference dark matter",
    "gravitational standing wave",
    "sedenion boundary transit",
]
for text in dm_words:
    w, compressed = safe_process(text)
    g, s, E, z, idx, d, pct = zero_report(w)
    results[text] = (g, z, idx, d)
    tag = " [sha256]" if compressed else ""
    print(f"  '{text}'{tag}")
    print(f"    σ = {s:.6f}  γ = {g:.6f}  E={w.magnitude:.5f}  →  γ_{idx} = {z:.6f}  Δ = {d:.4f}")

# ── Summary: zero convergence check ───────────────────────────────────────────
print("\n" + "=" * 68)
print("ZERO CONVERGENCE SUMMARY")
print("=" * 68)
print("Do multiple representations of the same observation land at the same zero?")
print("(Like water=eau=aqua → γ_1 = 21.022)")
print()

from collections import Counter
zero_votes = Counter(idx for (g, z, idx, d) in results.values())
gamma_votes = Counter(z for (g, z, idx, d) in results.values())

print(f"  Zero index distribution: {dict(zero_votes)}")
print(f"  Most common zero: γ_{zero_votes.most_common(1)[0][0]} = {RIEMANN_ZEROS[zero_votes.most_common(1)[0][0]]:.6f}")
print()
print(f"  {'Input':<35} {'γ':>10}  {'nearest zero':>14}  {'Δ':>8}")
print(f"  {'-'*35} {'-'*10}  {'-'*14}  {'-'*8}")
for label, (g, z, idx, d) in results.items():
    print(f"  {label[:35]:<35} {g:>10.4f}  γ_{idx}={z:.4f}    {d:>8.4f}")

# ── Save result ───────────────────────────────────────────────────────────────
out = DATA_ROOT / "holcus_sigma_result.txt"
with open(out, 'w') as f:
    f.write("Bullet Cluster — Holcus Single-Input σ Result\n")
    f.write(f"Critical line: Re(s) = ½  (σ forced by Noether balance)\n\n")
    for label, (g, z, idx, d) in results.items():
        f.write(f"{label}: γ={g:.6f}  nearest=γ_{idx}({z:.6f})  Δ={d:.6f}\n")
print(f"\nResult saved: {out}")
