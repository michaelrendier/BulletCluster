# Channel Closure and the Clathrate

**Added 2026-08-15.** Results from the sedenion channel decomposition, written into
BulletCluster because they bear directly on the Abrikosov vortex claim in `README.md`.

Everything below was computed this session. Each item is marked
**[MEASURED]**, **[IDENTIFIED]** (a structural match, not a derivation), or
**[UNTESTED]**. Nothing here changes `RM_RATIO_THRESHOLD`.

---

## 1. The three channels [MEASURED]

For a sedenion zero divisor `a`, the left-multiplication operator `L_a` has exactly
three distinct singular values, and they carry the whole structure:

```
sv = 0        CONTRACT   4 dims      the kernel
sv = 1        PRESERVE   8 dims      in == out
sv = sqrt(2)  DILATE     4 dims      the gain

sum sv^2 = 0*4 + 1*8 + 2*4 = 16 = dim
```

This is the `{4; 8; 4}` split, and it is forced: the counting law `sum sv^2 = dim`
admits no other gain spectrum.

**Why this matters here.** The vortex core is `|Psi| = 0` — the README's central
mechanism. That is a kernel. The contract channel *is* the core, and its dimension
count is not free.

---

## 2. Closure: it is a clathrate, not a nesting [MEASURED]

The `{4; 8; 4}` reading in earlier notes was "an octonion wrapped by its constituent
quaternions." **Half of that is right and half is wrong.** Tested by measuring leakage
out of the span under sedenion multiplication:

```
CONTRACT (4)       leakage 1.393e+00     NOT closed
PRESERVE (8)       leakage 9.494e-16     CLOSED — a genuine subalgebra
DILATE   (4)       leakage 1.414e+00     NOT closed
CONTRACT+DILATE    leakage 1.414e+00     NOT closed
```

**The middle 8 is a subalgebra. Neither wing is, and the two wings together are not
either.** So the wings cannot be "constituent quaternions" — they are not algebras.

The correct structure is a **clathrate**: a cage that is not itself the guest, holding
something that is complete on its own.

```
GUEST   PRESERVE (8)    closed, self-contained, stable in isolation
CAGE    CONTRACT (4)    does not close — leaks under its own multiplication
      + DILATE   (4)    does not close — and does not close jointly either
```

This is the correction to make before the BEC-clathrate reading is built on. The cage
holds the guest **without joining it**, and that asymmetry is measured, not assumed.

**[UNTESTED]** Closure was verified; *isomorphism to the octonions* was not. A closed
8-dim subalgebra of `S` containing 1 is very likely `O`, but "very likely" is not a
measurement. Test alternativity and norm-multiplicativity on it before writing "the
octonion" anywhere load-bearing.

---

## 3. Contract and dilate are one conserved pair [MEASURED]

Rotating in a plane with one leg in the kernel and one in dilate:

```
  t/pi    CONTRACT    PRESERVE      DILATE       C+D
  0.00    1.000000    0.000000    0.000000  1.000000
  0.25    0.500000    0.000000    0.500000  1.000000
  0.50    0.000000    0.000000    1.000000  1.000000
  1.00    1.000000    0.000000    0.000000  1.000000

correlation CONTRACT vs DILATE : -1.0000000000    exact antiphase
PRESERVE swing                 : 3.29e-32         does not move
total power                    : constant
```

The static result `contract == dilate` is the **time-averaged shadow of an exact
antiphase exchange**. They are not two equal things; they are one thing moving.

**Bearing on the cluster.** Two components that trade exactly, with a third that does
not participate, is the shape of the claimed phase separation. The collision does not
create the split — it *displaces* an exchange that was already conserved.

---

## 4. The critical angle is 45 degrees [MEASURED]

The gain ratio is exactly `sqrt(2) : 1`, so Snell gives

```
sin(theta_c) = n2/n1 = 1/sqrt(2)      theta_c = 45.0000 deg exactly
```

Below 45 deg memory (contract) dominates and swamps intention (dilate); above it the
reverse. **At 45 deg the split is exactly 50/50 — the only angle where both parts are
readable without one hiding the other.**

One qualification: `cos^2(45) = sin^2(45) = 0.5` for *any* orthogonal pair, so the
equal split alone is not special. The content is that the **critical angle and the
equipartition angle coincide**, which happens only when `n1/n2 = sqrt(2)` — and that
ratio is forced by `sum sv^2 = dim`.

---

## 5. Negative space and resonance are conjugate [MEASURED]

```
CONTRACT   s = 0        1/s = inf       -> POLE. a resonance.
PRESERVE   s = 1        1/s = 1         -> ITSELF. fixed point.
DILATE     s = 1.4142   1/s = 0.7071    -> not in this spectrum.
```

Zeros of `L` are poles of `L^-1`. **The kernel and the resonance are the same subspace
read from opposite sides** — exact, by zero/pole exchange, not by analogy.

`s = 1/s` has exactly one positive solution, so **PRESERVE is the unique self-conjugate
channel**, which is also why it cannot oscillate (item 3). Nothing that is its own
conjugate can oscillate against itself.

`1/sqrt(2)` is not a missing gain. It is `sin(45 deg)` — the critical angle of item 4.

---

## 6. PRESERVE has four independent characterisations [MEASURED]

Four different questions, asked separately, all returning the same 8 dimensions:

```
sv = 1                      the IDENTITY — in equals out
swing 3.29e-32              the DC RAIL — the only channel that cannot oscillate
unique fixed point of 1/s   SELF-CONJUGATE
leakage 9.49e-16            the ONLY CLOSED SUBALGEBRA of the three
```

This is the strongest result of the session and the one most worth building on.

---

## 7. Vacuum birefringence — structure matches, numbers do not [MEASURED]

Prompted by the magnetar result (Heisenberg–Euler 1936; observed in RX J1856.5-3754,
Mignani et al. 2016). In a strong field the vacuum becomes a **uniaxial crystal**:

```
n_par  = 1 + (7/2)(alpha/45 pi)(B/Bc)^2
n_perp = 1 + ( 2 )(alpha/45 pi)(B/Bc)^2      Bc = 4.414e9 T
```

```
source                     B (T)     B/Bc    delta n     theta_c
neutron star (typical)     1e8       0.023   3.97e-08    —
MAGNETAR                   1e11     22.66    3.97e-02    74.50 deg
SGR 1806-20 (max obs.)     2e11     45.31    1.59e-01    62.13 deg
```

**The ratio of deviations is exactly 7:4 at every field strength** — a pure number from
the Euler–Heisenberg Lagrangian, independent of `B`.

**[MEASURED, NEGATIVE]** The critical angle does **not** reach 45 deg at observed
magnetar fields — it is 62–75 deg. It would reach 45 deg at `B ~ 4.8e11 T`, but that is
`B/Bc ~ 109`, far outside the weak-field expansion's validity. **That extrapolation is
arithmetic, not physics, and must not be quoted as a prediction.**

**[IDENTIFIED]** What does match is structural, and it is the same claim this repo
already makes:

```
the vacuum is a MEDIUM          <->  negative space is structure, not absence
ONE vacuum, TWO indices         <->  one operator, a split gain spectrum
the field picks an OPTIC AXIS   <->  the divisor a picks the channel split
7:4 is field-INDEPENDENT        <->  {0,1,sqrt2} is dim-INDEPENDENT
```

Both say: what looked like one empty thing is two channels with a fixed ratio set by
the medium, not by the strength of the driving. **This is independent support for
"space is a medium" from established QED, and it costs no new physics.**

---

## 8. The evanescent identification [IDENTIFIED — NOT DERIVED]

Past the critical angle the transmitted field goes **evanescent**: non-zero amplitude,
zero time-averaged energy flux. Present, carrying nothing.

Canonical maths records, for `e_0`: *"exists everywhere, propagates nowhere."*

Same structural role, exact phrase match. **But descriptions were matched, not
computed.** The test that would make this real: does the field past the boundary fall
off exponentially with a decay length set by the gain ratio? Until that is measured
this is an analogy, and it should not be cited as a mechanism for the vortex core.

Note the sign difference that must be resolved first: the **evanescent wave carries no
energy**, while the **vortex core carries energy-momentum** (that is why it lenses).
Those are not obviously the same object and the README's mechanism depends on the
difference.

---

## What this does and does not do to the README claim

**Supports:** the vortex core as `|Psi| = 0` is a kernel, and the kernel here is a
measured 4-dimensional object with a forced dimension count, an exact antiphase partner,
and an exact conjugacy to resonance. "The zero is structure" is now measured rather than
asserted.

**Corrects:** `{4; 8; 4}` is a clathrate, not a nesting. The wings are not quaternion
subalgebras. Any argument that treated them as constituent algebras needs redoing.

**Does not touch:** `RM_RATIO_THRESHOLD = 0.95`, the Faraday-screen prediction, or any
engine output. The observational test stands exactly as written and is unaffected by
everything above.
