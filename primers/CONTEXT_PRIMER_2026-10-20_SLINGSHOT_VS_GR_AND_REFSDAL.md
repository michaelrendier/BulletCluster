# CONTEXT PRIMER 2026-10-20: the slingshot mechanism, SN Refsdal, and what to run next
Repo: BulletCluster. Written for a cold session. Pull by block; every number is reproducible from the files named.

## 1. The mechanism (Cody's words are his; the repos' words are quoted)
- **Slingshot / "L_(I|O) is the actual path of the photon":** a photon does not follow a clean (straight or purely geodesic) path past a mass. Lensing extends the path, and, in Cody's UFT reading, can return frequency lost to expansion.
- **What exists in writing:**
  - S-A, `FourthAgePapers_scalar-context-propagation/UmbrellaNoether/mode3_code/COSMOLOGY_REVISION_light_slingshot.md`: f_exit/f_enter = (1 + 2GM/(r c²))^α, α a free "trajectory parameter" 0..1; Δm = −2.5 log10(f_exit/f_enter).
  - S-B, Ainulindale wiki 51 (`ContextPlease/claude/hist_wiki/Ainulindale/wiki/51_dynamic_geodesic.md`): L_(I|O) = L_standard + ∫ J_red · d(J_blue)/dt dλ; the slingshot term L_sling ~ v·∂g/∂t.
- **Where the UFT comes from, and what it is NOT (Cody, 2026-10-20, recorded as his position):** the Unified Field Theory was carved out of 0_RB (canonical chain J_red + J_blue = 0_RB; J_red and J_blue are the two octonions). It is **not GR and not QM**: it is not a modification of GR, not a quantisation, not an effective field theory on a metric. Its objects are the J_red / J_blue pair inside 0_RB. Machinery that needs J_red and J_blue is where its origin and its difference from GR and QM show; a GR or QM reading of its terms is a category error. Counterpart facts: σ_RB, the Oblique Gear and the Maxwell identification are in memory `project_oblique_gear`.
- **Gap:** no numerical definition of J_red, J_blue or the L_sling integral for a lens exists in the repos that can be evaluated. Until it does, S-B has no number to test.

## 2. Why the Refsdal delay does not discriminate
- SN Refsdal (MACS J1149, z_l 0.54, z_s 1.49): four images S1–S4 round a cluster galaxy (2014); the fifth, SX, was predicted blind by several lens models and appeared 2015-12-11 at 11h49m36.02s +22°23′48.1″ (Kelly et al. 2016, arXiv:1512.04654).
- The predicted delay is GR: geometric path difference + Shapiro delay, i.e. the Fermat potential τ(θ) = ½|θ−β|² − ψ(θ), t = (D_Δt/c) τ. GR already says a lensed path is longer than straight. So the success confirms GR lensing plus the cluster mass models.
- By S-B's own form (∝ ∂g/∂t) the slingshot term is zero for a static lens, so it adds nothing to the Refsdal delay. The result cannot separate S-B from GR.
- Kelly+ 2016: SX colour F125W−F160W = 0.2 ± 0.3 mag, consistent with S1–S4; "consistent with the blind predictions of a fraction of the models"; most models predict shorter delays.

## 3. The tests (persistent scratchpad: `ContextPlease/claude/scratchpad/2026-10-20_slingshot_tests/`, `slingshot_tests.py` → `RESULTS.md`)
| Test | Result |
|---|---|
| T1 delay scale 4GM/c³ | stellar BH 2e-4 s; Sgr A* 85 s; M87* 1.5 d; TON 618 15 d; cluster core 1e14 Msun 62 yr. Days of delay need ≳1e9 Msun; stellar-mass lenses are unresolved. |
| T2 static Schwarzschild null geodesic (RK4) | Deflection matches weak-field GR (b=100M: 4.122e-2 vs 4.118e-2; b=1000M: 4.0118e-3 exact). E conserved to 1e-14. Blueshift in = redshift out: net 1.000000000 for any static lens. |
| T3 S-A formula | Its own example (−0.2 mag at 10 r_s) needs α ≈ 1.94, outside its stated 0–1 (max −0.103). α is never derived. |
| T4 S2 at Sgr A* | GR pericentre redshift 204 km/s; GRAVITY f = 0.90 ± 0.175 (quoted from memory, VERIFY) gives α = 0.10 ± 0.17, |α| ≲ 0.43 if S-A is applied literally (my reading). |
| T5 cluster ∂g/∂t | Rees–Sciama-type shift ≈ 2.5e-7 per crossing, ≈ 3e-7 mag; SX colour precision is 0.3 mag. |
| T6 | Refsdal confirms GR; slingshot untested. |

## 4. NEXT (Cody 2026-10-20): run the tests with GR as well
GR is established, so every slingshot test needs the GR column beside it, computed by the same code path:
- `BulletCluster/lens_delay/lens_delay.py` is the GR single-plane calculation (SIE, shear, NFW, circular PIEMD, deflection maps; lens equation, μ, Fermat time delays; selftest 8/8 passes). Manual: `LENS_DELAY_WIKI.md`. **Written, never run on a real target.** The map reader's potential, the quad fit and the JSON runner are untested.
- Plan: (a) run published Refsdal models through it and compare with Kelly's observed SX; (b) put the S-A / S-B prediction (once S-B has a number) in the same table as the GR number; (c) pre-register thresholds before the run (see `BulletCluster/Cleanup/RETRACTED.md`: nulls through the identical pipeline).
- Reference-papers: `BulletCluster/pending/next_cross/MACS_J1149_Refsdal/papers/` (gitignored, local; copy in `ContextPlease/claude/references/refsdal_predictions/`, also ignored): Sharon & Johnson 1411.6933, Oguri 1411.6443, Diego 1504.05953, Jauzac 1509.08914, Grillo 1511.04093, Treu 1510.05750, Kelly 1512.04654. A `refsdal_maths.py` (per-paper maths) was discussed and NOT written; the audit of what each paper prints vs cites comes first.

## 5. Telescope state (all of it is paused)
- Huchra's Lens Q2237+0305: dropped (no JWST). Its data deleted; the catalogue in `already_evaluated/huchras_lens_Q2237+0305/` kept.
- New cross NOT chosen. `pending/next_cross/candidates.html` shows the four with all four JWST cameras: SMACS 0723, MACS J1149 (Refsdal), Abell 2744, MACS J0416.
- Polarization: no polarizer-filter data (HST or JWST) for any of them; JWST has no imaging polarimeter. Radio full-polarization (VLA RR/RL/LR/LL) exists for Abell 2744, MACS J0416, J0717, J1149, Abell 370 and Abell S1063; SMACS 0723 has none (dec −73°, ALMA XX/YY only). Resolution vs the ~5″ cross is unchecked. NRAO downloads need Cody's email: never sent without his explicit say-so.
- JWST on the cross (10″): programs 1176, 1199, 1208, 1262, 2883, 3362, 4552, 5890, 6882, 91 observations, all level 3. Cody said the 63 GB of JWST level-3 combined mosaics was acceptable for the chosen cross, but required polarization to exist first; **no download has been started**. The card has ≈132 GB free.
- Skill `telescope-download` (survey_field.py + telescope_download.py) is in `ContextPlease/claude/skills/` and `~/.claude/skills/`.

## 6. Standing rules for this repo
Mozilla UA on every request; one cross and one download at a time; no new Bullet Cluster downloads; never send his email; maths in Unicode glyphs; failures are data (log, don't repair); discuss before building when told; no suggestions beyond the stated scope.
