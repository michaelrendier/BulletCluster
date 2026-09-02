# The Bullet Cluster as Two Shapes Passing Through
## Gravity is a Shape, Not a Stuff — GR and QM Read Through Each Other, In Code

*Companion / lead-in to: `FourthAgePapers/DM_GalacticCavity` (the galactic resonation chamber — the "Witch's Hat" paper)*
*Author: Cody Michael Allison*

---

## Abstract

**Gravity is a shape, not a stuff.** General relativity couples only to the
stress–energy tensor. In code: a `class GR` that consumes the output of a
`class QM` can receive it only through `GR` types — `GR.observe(qm) →
GR.StressEnergy`, the expectation value ⟨T_μν⟩. GR has no channel to a particle
*as a particle*; its phase, its which-path state, its identity are outside GR's
scope. Gravity cannot feel a particle — it registers energy, and what energy
leaves behind is a **shape**: the curvature of the region the energy occupied.
The reverse call is equally constrained — a `class QM` takes the metric as a
read-only parameter it propagates on but cannot edit. Each theory sees the other
only as an instance of one of its own classes; neither is a subtype of the
other. This paper uses that scope boundary as an instrument: reading GR through
QM's jurisdiction and QM through GR's is how the relationship between the two is
*located*, before any claim that they share a parent.

Applied to the Bullet Cluster (1E 0657-558): the lensing peaks are not a
substance that passed through the collision. They are the **shape** — two
gravitational wells, each carved by a cluster, crossing and re-forming the way
two surface ripples pass through one another. The baryonic gas, being
electromagnetic, stopped; the shape did not, because a shape has nothing to
scatter against.

**The cavity.** A galaxy carves a resonant cavity whose boundary is the stellar
disk — radius of order 100,000 light-years, half the ≈200,000-light-year stellar
diameter. The standing wave is anchored with a **node at the central
supermassive black hole** (r = 0) and propagates radially outward, so it spans
one radius, not the full diameter: its fundamental radial period is ≈ half the
galactic diameter ≈ the cavity radius ≈ 100,000 light-years. That lowest mode
oscillates on billion-year timescales; on the baseline available to observation
it reads as stationary — a fixed bowl, a fixed lens carved by the galaxy. Every
macroscopic collection of particles in the cavity — each star population a
`QM`-scope object — still follows the `GR`-scope shape: it rolls up the wall and
back down. That oscillation, integrated across the disk, is the observed
undulation of the galactic plane. The companion rotation-curve analysis (SPARC;
Lelli, McGaugh & Schombert 2016, 175 galaxies) tests the radial period against
data; this paper is its lead-in to the galactic resonation-chamber treatment,
held to GR and QM alone, in code, with no unifying theory asserted.

**Two rulers.** Scale is read on a continuous chart — the Smith chart, a
conformal gap-free ruler, natural to `GR()` — and on a discrete chart — an
Apollonian gasket, an integer curvature ladder, natural to `QM()`. They are
presented orthogonally, with matter and energy on the tilt between the two axes.
Pairing GR with the continuous chart and QM with the discrete one is a
**choice**; that the two rulers appear to share an axis is recorded as an
artifact of that choice and left for a later paper to chase.

---

## 1. Scope as jurisdiction — `class GR` reading `class QM`

*(to draft)* The forgetful projection `GR.observe(qm) → GR.StressEnergy`, its
non-empty kernel (relative phase, which-path superposition of the source, the
entanglement partition), and the read-only `GR.metric` parameter on the QM side.
The relationship between the two theories is found at the seam, not by asserting
a parent class. Cross-ref: `GenerationalLineage/wiki/The-Two-Charts-and-Jurisdiction.md`.

## 2. The Bullet Cluster: two wells crossing and re-forming

*(to draft)* Lensing peaks as shape, not substance; the gas stops because it is
electromagnetic, the shape does not because it has nothing to scatter. The
pre-registered RM-ratio test (`README.md`) is untouched and remains the
substance-vs-wave discriminator — still never run on observational data. Per
`Cleanup/`: a claim with no committed generating script is not a result.

## 3. The cavity: node at the SMBH, radial period ≈ half the galactic diameter

*(to draft)* Cavity boundary = stellar disk radius (~100,000 ly), not the virial
radius (`FourthAgePapers/DM_GalacticCavity/dark_matter_cavity.py` already flags
this). Node at r = 0, radial propagation, fundamental radial period ≈ the cavity
radius. Cite the SPARC companion analysis; do not import `d*` / `Ω_ZS` here —
this section stays GR + QM.

## 4. Two rulers: the Smith chart (continuous / GR) ⟂ the Apollonian gasket (discrete / QM)

*(to draft)* `GenerationalLineage/engine/toolsets/scale.py` — `charts(s)` reads a
scale ratio in both jurisdictions at once; `sedenion_locus_orthogonality()`
returns the `METHOD` verdict — the apparent shared axis is an artifact of two
charts both monotone in ln(s), with GR/QM attached by hand. Chased, not claimed.

## 5. Lead-in to the galactic resonation-chamber paper

*(to draft)* Hand-off to `FourthAgePapers/DM_GalacticCavity` — the "roll up the
wall and back down" oscillation as the disk warp; the Witch's Hat potential as
the resonation chamber for the star particles.

---

## Status

**Supposition / thesis layer.** Changes no data status in this repository. The
pre-registered RM-ratio prediction (`README.md`) is unaffected and remains never
run on observational data. Abstract seeded 2026-09-02; sections 1–5 are stubs.
