# Retracted Claims — recorded here, excised from the live files

**2026-08-17.** This is the permanent record. Each item is preserved with its original
wording and the reason it fails, so nothing is lost — and then **removed** from `README.md`
and the viewer, rather than annotated in place.

## Why removal rather than annotation

The 2026-08-14 addendum in `CLAUDE_PRIMER.md` diagnosed most of this correctly. It then said:

> *"Addenda, not corrections. **Every prior result stands as written**; these sit beneath
> them."*

That policy is the actual fault, and it cost real time. A refuted claim left in a file is
still read as a claim — by a human skimming, and by any automated reader that ingests the
directory. "Noted as wrong" is not the same as "not present." Anything still in the file is
still in context.

So: recorded once, here. Removed there.

---

## RT1 — The eight "Already Confirmed (from existing data)" items

Original, `README.md`:

```
✓ Coherence peaks at DM band center          (band_coherence.png)
✓ Polarization angle aligned to merger axis  (band_coherence.png)
✓ Vortex winding in shear field at DM peaks  (bullet_polarization_field.png)
✓ Interference fringes in Δκ model           (lcdrm_polarization_map.png)
✓ ZD transit surface at interaction saddle   (dm_laplacian_topo.png)
✓ Abrikosov attractor/repeller in ∇²κ        (dm_laplacian_topo.png)
✓ N-Shape geometry in X-ray shock fronts     (The_Bullet_Cluster-defined.png)
✓ Holcus hash: all key concepts → γ₀,γ₁,γ₂  (holcus_sigma_result.txt)
```

Failures, item by item:

1–2. **Contradicted by their own figure.** Read directly off `band_coherence.png`: coherence
at band centre (d = 0) is **R ≈ 0.38**, while the maxima are **outside** the band —
≈0.63 at +275 kpc, ≈0.62 at +165, ≈0.55 at +245. The centre is mid-range, not a peak. Every
value lies in 0.05–0.63 on a scale where 1 = coherent and 0 = stochastic noise, and most
points fall **below** the 0.5 reference line. The angle panel swings −55° to +37° with no
stable alignment and no error bars, on bins of 9–35 sources.

3, 5, 6. **Derived from a map measured to be noise.** R4/R5: κ E/B = 1.023 and ψ E/B = 0.724
(B larger than E), with 89% of ψ's power in three wavenumbers. "Vortex winding," a "ZD
transit surface," and "∇²κ attractor/repeller" are structures read out of smoothed shape
noise and a `∇⁻²` artifact.

4. **A model, not data.** `lcdrm_polarization_map.png`'s own source column reads
"Model comparison." Interference fringes between two models are a property of the models.

7. **Read off the hand-drawn image.** `The_Bullet_Cluster-defined.png` is a hand-annotated
constraint band. It is correctly excluded from all code (R8), which also means it is not a
measurement.

8. **Retained, but reclassified — not evidence about the cluster.** The Holcus hash result
is arithmetically real and reproducible (`artifacts/holcus_sigma_result.txt`), but it is a
statement about a hash function applied to English phrases. It contains no Bullet Cluster
observational content. Kept as an artifact; removed from any "confirmed from existing data"
list.

Additionally: four of these five figures **have no generating code anywhere in the
repository** (see RT2), so they cannot be reproduced or audited even in principle.

---

## RT2 — "Visualizations (generated from real data)"

That heading is false for six of the eight files under it. Verified by grep — no `.py` in
the repo writes them:

```
ORPHAN   band_coherence.png
ORPHAN   bullet_polarization.png
ORPHAN   bullet_polarization_field.png
ORPHAN   lcdrm_polarization_map.png
ORPHAN   dm_topography.png
ORPHAN   dm_laplacian_topo.png
has code tif_channels.png
has code Ptychography_DM_Pockets_LIO_Polarization.png
```

An image with no generating code has unverifiable provenance. It cannot be regenerated when
the data improves, and it cannot be checked against the nulls. The files are kept on disk as
history; their description as results is removed.

---

## RT3 — Everything labelled "polarization" from JWST or the viewer

**There is no polarization data of the Bullet Cluster in this repository.** Established
three independent ways:

- **JWST has no polarimetric mode** — not in NIRCam, NIRISS, NIRSpec or MIRI. The data
  inventory already said so: *"Intensity only — JWST has no polarimetric mode."* So anything
  called "polarization" from F277W/F444W is galaxy **shear** (ellipticity position angle),
  relabelled.
- **Real MeerKAT is Stokes I only** — verified on the files: `NAXIS4 = 1` on the STOKES axis
  of both `Bullet.APSCal.1pln.fits.gz` and
  `Bullet_aFix_pol_I_Farcsec_5pln_cor.fits.gz`. No Q, no U.
- **The viewer layers say so in their own source.** `viewer/generate_layers.py`:
  line 427 `"POLARIZATION VECTORS — placeholder with synthetic field model"`;
  line 437 `"Synthetic B-field model for Bullet Cluster"`;
  line 496 `"(synthetic model — replace with rmsynth3d output)"`;
  line 500 `"RM FARADAY DEPTH — synthetic model"`;
  line 543 `"(synthetic — replace with rmsynth3d output)"`.

`viewer/layers/polarization*.png` and `viewer/layers/rm_faraday.png` are renderings of a
hand-written B-field model. They are not measurements and must not be displayed beside real
layers without that label.

The one genuine polarization measurement in the repo is R2 — and it is the **Galactic
foreground the cluster is seen through**, explicitly *not* polarization of the cluster.

---

## RT4 — "Engine verified: wave = 0.861, particle = 0.967"

This is **correct as written and must stop being quoted as a result.** It is a harness
verification: `engine/modules/synthetic.py` generates Stokes Q/U cubes for two DM models and
**injects ΔRM at the DM peaks**, then the engine recovers the injected answer.

The primer already stated the consequence exactly:

> *"Any polarization-gradient shape agreeing with DM_NW/DM_SE is circular **by construction
> of the test harness** — which is correct practice for a harness, and only a problem if its
> output is read as a finding."*

It was read as a finding. `artifacts/SYNTHETIC_diagnostic_summary.json` is retained under a
name that cannot be mistaken for data.

Building the harness was right. Reporting its output in a results table was not.

---

## RT5 — The "thermal gradient" / slingshot imagery

The middle panel of the slingshot map is ψ. R5 measures ψ to be integrated noise with 89% of
its power in three wavenumbers, and the `1/k²` operator produces that gradient from **any**
input, including pure noise. The gradient is the operator's signature, not the Fermat
potential emerging from data.

The design note for a density-accumulation render (Buddhabrot-style, `(x,y,t)` buffer) is
sound and is **not** retracted — it is a good instrument that has not been built. It is a
plan, and it belongs in the TODO, not in results.

---

## What survives

`REAL_RESULTS.md` — R1 through R9. One data product, one methodological finding, one
measurement, five nulls, one passed negative control, two infrastructure fixes.

The Abrikosov hypothesis is neither confirmed nor refuted by anything in this repository.
Its central prediction has never been run on observational data.
