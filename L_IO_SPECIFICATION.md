# L_(I|O) — Formal Specification

*Written 2026-08-14. Each apparatus, its prerequisites, and its regime of validity.*

> The purpose of this document is to state what L_(I|O) **is**, what each step
> **requires**, and where each step **stops being valid** — so that a result is
> never read out of a step whose preconditions were not met. Every null recorded
> in this repo on 2026-08-14 was a step run outside its regime.

---

## 0. The identification

**L_(I|O) is the Fermat potential.** Not analogously — the same expression.

```
gravitational lensing arrival time:

    t(theta)  ∝  [ ½|theta − beta|²  −  psi(theta) ]      ← the FERMAT POTENTIAL
                    \____________/      \________/
                     clean path L         the bend

    L_(I|O)   =          L           −    psi_Fermat
```

with

| symbol | meaning |
|---|---|
| `theta` | image position — where you see it |
| `beta` | source position — where it actually is |
| `psi` | lensing potential (the aberration function) |
| `alpha = grad psi` | deflection angle |
| `kappa = ½ grad² psi` | convergence (projected surface density / Sigma_crit) |

The lens equation is `beta = theta − alpha(theta)`, and images form where
`grad_theta t = 0` — the **stationary points**, not the minima.

### Consequences that follow immediately

- An Einstein cross is **L_(I|O)'s stationary set, made visible.**
- **Time delays are the values of L_(I|O)** at those points.
- Image parities (minimum / saddle / maximum) are the catastrophe
  classification. Morse: `n_min − n_saddle + n_max = 1`, so a "4-image" cross is
  really **5**, one heavily demagnified near the centre.
- **The photon does not seek less-dense space.** Saddle and maximum images
  traverse the *compressed* region and arrive later (geometric + Shapiro delay).
  The minimum image is the one that skirts it.

---

## 1. It is an aberration expansion — the same one as eyeglasses

```
OPTICS  (wavefront W)          LENSING  (potential psi)
──────────────────────────────────────────────────────────────
defocus      Z(2,0)            convergence  kappa    TRACE of the Hessian
astigmatism  Z(2,±2)           shear        gamma    TRACE-FREE Hessian
coma         Z(3,±1)           FLEXION      F, G     THIRD derivatives
```

The entire tensor content is one symmetric 2×2 matrix of second derivatives:

```
A_ij   = delta_ij − d_i d_j psi                 the lensing Jacobian
kappa  = ½(psi_11 + psi_22)                     trace
gamma1 = ½(psi_11 − psi_22)     gamma2 = psi_12  trace-free
```

**Split a Hessian into trace plus trace-free part.** That is the same operation
as decomposing a stress tensor into isotropic pressure + deviatoric shear. No
transformation laws, no Christoffel symbols, no covariant derivatives are
required to *use* this. GR is needed to *derive* `alpha = 2∫grad⊥Phi dl / c²`;
it is not needed to apply it.

**Adaptive optics is the inverse operation.** Measure the aberration, apply its
conjugate. In lensing that is **de-lensing** — recover `beta` from the bent path.
AO gets a laser guide star as its reference; lensing has no reference unless a
multiply-imaged source supplies one.

⚠ **Conjugation is not cancellation.** ANC emits `−p(t)` and destroys energy.
AO emits `e^(−i·phi)` and *redirects* it — same photons, reorganised into a
focus. The Monad's purpose (wide beam → point) is conjugation.

---

## 2. The pipeline, step by step, with prerequisites

| # | step | requires | regime | status here |
|---|---|---|---|---|
| 1 | shear `gamma` from galaxy shapes | background galaxies, 2nd shape moments | weak | **done** (noisy) |
| 2 | Kaiser–Squires → `kappa` | step 1; `kappa << 1` | weak | **done** — E/B = 1.023 |
| 3 | `psi = grad⁻²(2 kappa)` | step 2 | weak | **done** — integrated noise |
| 3b | **FLEXION `F`, `G`** | **3rd shape moments** | weak | **NOT COMPUTED — no data** |
| 4 | `alpha = grad psi` | step 3 | weak | **done** |
| 5 | Fermat `phi = ½\|theta−beta\|² − psi` | **a source position `beta`** | either | **unavailable** |
| 6 | arrival time `t ∝ phi` | step 5 | either | **unavailable** |
| 7 | images at `grad phi = 0` | identified multiple images | strong | **unavailable** |
| 8 | magnification `mu = 1/det A` | `kappa ~ 1` | **strong** | **unavailable** |
| 9 | critical curves at `det A = 0` | `kappa ~ 1` | **strong** | **unavailable** |

**Steps 1–4 are weak lensing. Steps 5–9 are strong lensing.** The current
implementation stops at step 4.

### ⚠ Regime boundaries that must be checked before reading a result

**Caustics require `kappa ~ 1`.**
```
det A = (1 − kappa)² − gamma²
```
Measured here: `kappa_rms = 0.072`, so `det A ≈ 1` everywhere and `1 − kappa`
never approaches zero. **There are no caustics in a weak-lensing map, by
construction.** Not faint — absent from this kind of data.

**`psi` amplifies noise catastrophically.**
```
psi_k = −2 kappa_k / k²
```
The `1/k²` is a brutal low-pass. Noise in `kappa` is roughly flat in `k`, so
`psi` is dominated by the lowest wavenumbers **whatever the input**. Measured:
89% of `psi_E`'s power sits in the 3 lowest wavenumbers (`kappa`: 13%).
**A smooth large-scale gradient in `psi` is guaranteed by the operator and is
not evidence of signal.**

**`kappa`, `psi` and `alpha` are the same field, differently filtered.**
```
kappa_k      alpha_k = −2i kappa_k / k      psi_k = −2 kappa_k / k²
```
`alpha` and `psi` contain **no information absent from `kappa`.** "Did the
gradient show the mass or the path?" is not a well-posed question — the path is
a deterministic functional of the mass.

---

## 3. Mandatory nulls

No result from this pipeline is reportable without its null.

| test | null | why |
|---|---|---|
| any `kappa` structure | **B-mode** (shear rotated 45°) | lensing produces E-mode ONLY; B is systematics + noise |
| any map–map correlation | **circular shift** of one map | both fields are autocorrelated; textbook p-values are meaningless |
| any spectral feature | **power-law fit + residual scatter** | turbulence is a power law; interference is a *peak* |
| a hand-drawn region | **check no code reads it** | verified by grep for `The_Bullet_Cluster-defined.png` — nothing does |

**Read the z-score, never the raw r.**

---

## 4. Measured state, 2026-08-14

```
kappa   E/B amplitude ratio          1.023      -> NOISE DOMINATED
psi     E/B rms ratio                0.724      -> B-mode LARGER than E
psi     peak-to-peak E/B             0.972      -> indistinguishable
psi     power in 3 lowest k          0.893 (B: 0.945)
emission vs kappa/psi/alpha          all |z| < 2, E and B agree
```

**Cause, single and shared:** the reference mosaic is one tile
(`jw04598-o001_t001`), a 5.66′ × 2.51′ strip. **`DM_NW` — the main cluster's mass
peak — falls outside the field** (px y = 84.8 against ny = 78). `DM_SE` sits 12 px
from the bottom edge. Too little area, too few background galaxies.

Four symptoms, one disease. Not four independent failures.

### Pre-registered thresholds for the re-run

When the full 292-observation mosaic completes, rerun unchanged. A real
reconstruction must show:

- `psi_E / psi_B` **well above 1** (currently 0.724)
- `kappa` E/B **well above 1** (currently 1.023)
- and only then are steps 5–9 worth attempting

---

## 5. What each intended use actually needs

| you want | you need | have it? |
|---|---|---|
| the mass map | steps 1–2 | yes, noisy |
| the aberration map | steps 3–4 — **this is `psi`/`alpha`, NOT the RGB composite** | yes, noise |
| focusing / coma structure | **step 3b, flexion** — 3rd shape moments | **no — `source_extract.py` keeps only E1/E2** |
| caustics, focal points | steps 8–9, `kappa ~ 1` | no — needs strong lensing |
| "through what space did the photon travel" | steps 5–7, a source position | no — needs multiple images |
| time delays / path-integral differences | steps 5–6 | no — needs a multiply-imaged **variable** source |

**The Einstein crosses are not an enhancement.** They are the only route to
steps 5–9, because they supply the `beta` that 5–7 require and the `kappa ~ 1`
that 8–9 require — and the source becomes its own reference, removing the
observer's choice of where to look.

---

## 6. Ptychography — what the word does and does not mean here

**Real ptychography maps the aberration.** Iterative reconstruction (ePIE and
descendants) solves simultaneously for the *object* and the **probe** — and probe
retrieval yields the illuminating wavefront, i.e. the aberration function. This
is routinely used to characterise X-ray optics.

**`ptychography_polarization.py` does not do this.** It is an RGB composite of
F444W/F356W/F277W: three intensity images, no coherent probe, no overlapping
scan, no phase retrieval, **no phase at all.** It maps *emission* — where the
galaxies are. Interference is a phase phenomenon and astronomical sources are
mutually incoherent, so no interference pattern can appear in it.

**But weak lensing is already structurally ptychographic.** Every background
galaxy samples the lens potential at a different position: many overlapping
probes, one aberration function, solved jointly. The difference is truncation —

```
real ptychography   full diffraction pattern   ->  complete complex field
weak lensing        2nd shape moments only     ->  kappa + gamma
+ FLEXION           3rd shape moments          ->  coma
```

Weak lensing is a **truncated ptychography**. Adding flexion extends the
reconstruction by one Zernike order using data already present in the images —
and unlike caustics, **flexion works in the weak regime**, so it does not have to
wait for `kappa ~ 1`.

---

## References in this repo

- `optical/jwst/l_io_lensing.py` — steps 1–4
- `ValaQuenta/modules/l_io_photon_path/maths.py` — `bounded_lensing_pipeline`
- `xray/kappa_EB_test.py` — the E/B null
- `xray/lio_vs_ptychography.py` — the psi-is-integrated-noise test
- `xray/kappa_vs_xray_vs_nfw.py` — the shape test
- `Ainulindale/wiki/82_l_io_photon_path.md`, `wiki/85_the_apex_path.md`
- `Ainulindale/wiki/74_lagrangians_are_catastrophe_theory.md` — image parities
