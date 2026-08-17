# What Data, From Which Telescope, And What Each Is For

**2026-08-17.** Written against the claim as Cody restates it:

> **Spacetime vacuum is a medium. The *shape* of that compressible fluid is what we call
> dark matter — not a *stuff* that alters curvature.**

That reframing changes the data priorities, because a compressible medium has specific
observables (pressure, sound speed, shocks, equation of state) that a collisionless-stuff
hypothesis does not care about. Section 3 is the consequence and it is the most useful part
of this document.

---

## 0. THE RESOLUTION-CEILING RULE — applied first, to our own results

**The Bruniquel Cave principle.** C14 has a ceiling near 47–50 kyr. The cave's stalagmite
result came back *at* that ceiling — which means the ceiling was what was measured, not the
age. Switching to U-Th dating of the calcite regrowth gave **176,000 years**: a questionable
result became a landmark one, purely by changing method rather than improving the old one.

**Rule: a result that lands at the instrument's limit is a measurement OF the limit. It
requires a different method, not a better version of the same one.**

Applied honestly to this repository, three results are limit-artifacts and one of them is
mine from today:

### ⚠ R2's empirical claim is resolution-limited — correcting it now

I reported that the Galactic Faraday foreground is **common-mode across the transect**, based on:

```
n_distinct_pixels = 1        map pixel 6.871'      DM separation 2.891'
RM = 18.274 +/- 19.669 rad/m^2
```

**That is the C14 error exactly.** The DM separation is *below* the map resolution, so I
could not have detected a gradient if one existed. And σ (19.669) **exceeds** the value
(18.274), so the foreground RM is not significantly different from zero at 1σ.

- **Wrong:** "the foreground is uniform across the transect."
- **Right:** "the foreground is **unresolved** at 6.87′. Uniformity is untested."

What survives: the *reasoning* that a common additive offset drags a ratio toward 1 (the
particle verdict). That is analytic and stands. What does not survive: the claim that the
foreground *is* common-mode here.
**Different method required:** a high-density RM grid — POSSUM/ASKAP, or targeted
polarimetry — not a re-read of Hutschenreuter.

### The other two

- **Planck SZ.** MILCA y-map has 1.72′ *pixels* and a **10′ beam**. It cannot resolve the
  2.89′ DM separation. Any statement about pressure structure in the Bullet from this map is a
  statement about the beam. **Different instrument required: SPT or ACT.**
- **MeerKAT radio null (N5).** Already correctly self-flagged: 15″ = 67 kpc/beam against ~1 kpc
  predicted structure — two orders too coarse. The null is about the beam, not the physics.

**And one from earlier today:** the magnification-bias count slope α = 0.870 was fit inside
the incompleteness regime (catalog median flux sits almost on the detection limit). Same
error class. A deeper external reference catalog is the different method.

---

## 1. Every telescope that has resolved the Bullet Cluster — status and purpose

| Telescope | Band | On disk | What it measures | What it is FOR here |
|---|---|---|---|---|
| **Chandra** | X-ray 0.5–7 keV | ✅ 576.6 ks, 1.01M counts | gas **density**, bow shock, cold front | shock Mach number; the ρ term; 3D orientation via shock geometry |
| **HST** (10200) | optical | ✅ 4 drz, **covers both halos** | background galaxy shear | **the κ map** — the only lensing route that covers DM_NW |
| **JWST** (4598) | NIR | ✅ 424 i2d, 2 tiles | deeper shear, stellar mass | resolving Einstein crosses. **Footprint excludes DM_NW** |
| **MeerKAT** (MGCLS) | radio L-band | ✅ Stokes **I only** | synchrotron halo, spectral index | turbulence P(k); relativistic electrons |
| **Planck** | mm / SZ | ✅ y-map + 545/857 | Compton-y = **pressure** | the P term — **but 10′ beam, unusable at cluster scale** |
| **SPT** | mm / SZ | ❌ **empty dir** | y at ~1′ | **the critical gap — see §3** |
| **ACT** | mm / SZ | ❌ **empty dir** | y at ~1.4′ | same; either SPT or ACT closes it |
| **XMM-Newton** | X-ray | ❌ not present | **temperature** map, better extended spectroscopy | sound speed `c_s = sqrt(gamma kT/mu m_p)`; the T in P = nkT |
| **ATCA** | radio | ❌ empty dir | radio incl. **polarization** | Stokes Q/U — a second route to Faraday besides SARAO |
| **VLA** | radio | ❌ empty dir | radio, polarimetry | Q/U; differential Faraday on lensed sources |
| **MOST** | radio 843 MHz | ❌ empty dir | low-freq halo | extends the spectral-index lever arm |
| **Magellan / VLT / Subaru** | optical ground | ❌ not present | wide-field shear | Clowe+2006 used Magellan + HST; wider area than HST alone |
| **Spitzer** | IR | ❌ not present | stellar mass | the Σ_stars term in the DM residual |
| **EHT** | mm VLBI | — later | nuclei only | Cody: deferred; not a cluster-scale instrument |

**Six telescope directories exist and are empty:** SPT, ACT, ALMA, ATCA, VLA, MOST. Those are
the acquisition list, and they are not equally urgent — see below.

---

## 2. Organised by what each observable is FOR

```
DENSITY      rho       Chandra X-ray SB              ON DISK
PRESSURE     P = nkT   SZ Compton-y                  ON DISK BUT UNRESOLVED (10' beam)
TEMPERATURE  T         X-ray spectroscopy            MISSING (XMM)
SOUND SPEED  c_s       from T                        MISSING (follows from XMM)
TOTAL MASS   kappa     HST/JWST shear                ON DISK (HST covers the halos)
STELLAR MASS Sigma_*   NIR photometry                partial (JWST); Spitzer would help
TURBULENCE   P(k)      radio halo, X-ray SB fluct.   ON DISK (beam-limited)
MAGNETIC/VORTICITY     Stokes Q/U -> RM              MISSING — the known blocker
```

The DM residual everyone actually wants:

```
Sigma_DM  =  kappa_total  -  Sigma_gas  -  Sigma_stars
             HST            Chandra       JWST/Spitzer
```

Two of three are on disk. This is computable **now** at HST resolution, and it is the
literature-comparable quantity (Clowe+2006 used exactly this logic).

---

## 3. What the restated claim changes — and the test it makes available

If dark matter is the **shape of a compressible medium** rather than collisionless stuff, the
diagnostic observable is not mass, it is **the equation of state**. And that gives a sharp
test the repo has never run, using physics specific to this cluster:

**Across a SHOCK, both density and pressure jump. Across a COLD FRONT, pressure is
continuous while density jumps.**

The Bullet has **both** discontinuities — the bow shock (Mach ~3) and the bullet subcluster's
cold front. So density and pressure peaks are *physically separated* in this system, and that
separation is measurable rather than assumed.

**The test:**

```
does kappa track PRESSURE, or DENSITY, or neither?

  stuff (CDM)                kappa tracks NEITHER — separate collisionless component
  shape of a compressible    kappa should track a FLUID quantity; pressure is the
    medium                     natural candidate, since pressure is what a compressible
                               medium's shape actually is
```

This is falsifiable, it is not degenerate with the mass-sheet transformation (it compares
*morphology*, not normalisation), and it does not require polarization, a variable source, or
Einstein crosses. It requires three maps at matched resolution:

```
kappa    HST 10200          ON DISK
rho      Chandra            ON DISK
P        SZ at ~1 arcmin    ** MISSING — SPT or ACT **
```

**So the highest-value single acquisition is resolved SZ.** Not MeerKAT Q/U. The Q/U blocks
the *old* RM-ratio test; resolved SZ enables a *better* test of the claim as now stated, with
two of three inputs already in hand.

Priority order, revised on that basis:

1. **SPT-SZ or ACT y-map** (~1′) — enables the P-vs-ρ-vs-κ test. Bullet is in the SPT
   footprint. **New top priority.**
2. **Rerun the pipeline on HST 10200** — zero acquisition; fixes the off-field cause of N1–N4.
3. **XMM temperature map** — completes P = nkT independently of SZ, and gives sound speed.
4. **MeerKAT/ATCA/VLA Stokes Q/U** — the RM-ratio test, which R2 shows also needs foreground
   subtraction at better than 6.87′.
5. **High-density RM grid (POSSUM/ASKAP)** — the different method R2's correction demands.

---

## 4. Rotation curves — and Andromeda as the testbed

Rotation curves test the DM **density profile**, which is a *shape* statement, so they bear
directly on the restated claim rather than tangentially.

**Gaia is genuinely useful here** — and this is the reverse of the Bullet case, where I
correctly said it was useless. At Milky Way distances parallax works, so Gaia gives the
Galactic circular-velocity curve directly (Eilers+2019 and later work find a *declining*
curve out to ~25 kpc, which is itself a constraint on halo shape). That is a real DM-halo
measurement from data designed for it.

**M31 as the working testbed is a good call**, for reasons that are specific rather than
convenient:

- **Close and resolved** — 785 kpc, so structure is resolvable in a way no other massive
  spiral is.
- **Resolved multiple ways** — HST PHAT (panchromatic stellar populations), HI rotation
  curves (WSRT/GBT), Spitzer/Herschel dust and gas, JWST now, plus Gaia proper motion for its
  3D velocity vector.
- **Not a nucleus problem** — as Cody notes, EHT-scale physics is deferred; M31 tests halo
  shape, which is the current question.
- **A known rotation curve** to check any method against before pointing it at a cluster.

That last point is the real argument: M31 is where a method can be *validated against a
known answer*, which is exactly what the Bullet cannot provide. Same role `Ptolemy2/working`
plays for code.

---

## 5. PTorrent — one downloader instead of N scripts

Current state: `download_bullet_cluster.py`, `jwst_resume_download.py`,
`optical/hst/resume_hst.py`, `optical/jwst/resume_jwst.py`,
`optical/jwst/download_mosaics.py`, `lensing_validation/download_validation_targets.py`,
`engine/ptorrent/sarao_download.py` — **seven** overlapping downloaders, each with its own
state file and its own resume logic. That is the same provenance failure as the orphan images,
in a different register.

Wanted: a single Linux console (curses) manager with
- one state store, byte-range resume, `netgate.py` pause-on-signal-loss already written
- per-archive adapters (MAST, Chandra CDA, SARAO GraphQL, ASKAP/CASDA, NED/IRSA)
- AWS S3 path for MAST where available (`enable_cloud_dataset`, `cloud_only=True`) — the real
  bulk-speed win, since these archives publish no torrents
- a queue view, throughput, and a visible reason when something is *paused* rather than failed

Not built. Scoped here so it is a task rather than an aspiration.

---

## 6. Summary — what is necessary, and for what

**Necessary and blocking nothing (do first, no acquisition):**
rerun weak lensing on **HST 10200**; compute Σ_DM = κ − Σ_gas − Σ_stars at HST resolution.

**Necessary for the restated claim (top acquisition):**
**resolved SZ from SPT or ACT.** Enables the κ-vs-P-vs-ρ morphology test, which is the
sharpest available test of "shape of a compressible medium" and needs no polarization.

**Necessary for the equation of state:** XMM temperature map.

**Necessary for the original RM-ratio prediction:** real Stokes Q/U (MeerKAT/SARAO, or ATCA,
or VLA) **plus** a foreground map finer than 6.87′.

**Necessary for method validation, not for the Bullet:** Gaia (Milky Way rotation curve) and
M31 multi-wavelength as the testbed.

**Not necessary / closed:** Gaia for Bullet distances; any JWST filter for polarization (no
polarimetric mode exists); ptychography from incoherent astronomical dithers.
