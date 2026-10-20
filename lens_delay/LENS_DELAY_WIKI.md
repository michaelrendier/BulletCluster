# lens_delay.py: manual

Computes where the images of a lensed point source appear, how bright each is, and how many days apart they arrive.
It is the standard single-plane calculation behind the SN Refsdal reappearance predictions
(papers in `../pending/next_cross/MACS_J1149_Refsdal/papers/`). It is a toolset to compare against, not an engine.
Status: written 2026-10-20; the component self-test passes; it has not been run on any real target.

## The calculation in five lines
```
β = θ − α(θ)                        lens equation: image position θ, source position β
A = I − ∂α/∂θ ,  μ = 1/det A        magnification; det A>0,tr A>0 minimum · det A<0 saddle · det A>0,tr A<0 maximum
τ(θ) = ½|θ−β|² − ψ(θ)   (∇ψ = α)   Fermat potential, arcsec²
t = (D_Δt/c) τ ,  D_Δt = (1+z_l) D_l D_s / D_ls     arrival time
lag = t_i − t_first                 what you compare against
```
Angles are arcseconds (x east, y north, any origin you choose). Flat ΛCDM; `Cosmology(H0, Om)`, default 70, 0.3.
The lag scale is proportional to D_Δt, so it scales as 1/H0.

## What you must supply
| Need | Where it comes from |
|---|---|
| z_l, z_s | spectroscopy (Refsdal: lens cluster 0.54, host 1.49) |
| a mass model | fitted by you, or a published one (below) |
| the source position β | given, or back-mapped from the observed images |
| a search box (arcsec) | a box around the images |
| (optional) which image was seen first and when | to turn lags into calendar dates |

## Mass-model pieces (add any number)
| Class | Use | Parameters |
|---|---|---|
| `SIE(x0,y0,b,q,phi)` | one elliptical galaxy | b arcsec ≈ Einstein radius, q ≤1, phi deg CCW from +x |
| `Shear(g1,g2)` | environment of a galaxy lens | γ1, γ2 |
| `NFW(x0,y0,kappa_s,theta_s)` | spherical cluster halo | κ_s, θ_s arcsec |
| `DPIE(x0,y0,E0,a,s)` | cluster member or clump (circular PIEMD) | E0 = `sigma_to_E0(σ_km/s, zl, zs, cosmo)`, core a, cut s arcsec |
| `DeflectionMap(ax,ay,pix,x0,y0,z_ref)` | a published model given as maps | see below |

Not implemented: elliptical DPIE, multi-plane lensing, NFW ellipticity.

## Recipe 1: a galaxy-scale cross (four images around one galaxy)
```python
from lens_delay import *
cosmo = Cosmology()
quad = [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]            # measured image positions, arcsec
model, beta, rms = fit_sie_shear_to_quad(quad, centre=(xg,yg), cosmo=cosmo, zl=0.5, zs=2.0)
imgs = solve_images(model, beta, box=(-3,3,-3,3))   # all images, sorted by arrival time
for im in imgs: print(im)                           # x, y, μ, type, τ, delay in days
```
The lens centre is fixed on the observed galaxy so 7 unknowns meet 8 numbers. `rms` is the source-plane scatter: a large
value means the model does not explain the images.

## Recipe 2: a cluster, from a model you wrote down
```python
model = LensModel([NFW(0,0,0.15,20.0), DPIE(5,-2,sigma_to_E0(250,0.54,1.49,cosmo),0.1,10.0)], cosmo, 0.54, 1.49)
pts, beta, rms = backmap(model, observed_S1_to_S4)  # the predicted source = mean of back-mapped images
imgs = solve_images(model, beta, box=(-40,40,-40,40), n=800)
dates = predict_dates(imgs, ref_index=0, ref_date=datetime.date(2014,11,10))   # ref_index = the image seen first
```
This is the Refsdal procedure: back-map the four seen images, take the mean source, solve for every image, read off the
extra image's position and its lag.

## Recipe 3: a published deflection map
```python
m = load_fits_map("ax.fits", "ay.fits", pix=0.2, x0=-60, y0=-60, z_ref=9.0, flip_columns=True)
m.rescale_to(0.54, 1.49, cosmo)                      # α ∝ D_ls/D_s
model = LensModel([m], cosmo, 0.54, 1.49)
```
Arrays are [row=y, col=x]; the pixel grid must be in the same arcsec frame as your image positions, with x east. Published
maps usually have RA increasing leftwards, hence `flip_columns`. Check the file's pixel scale, units (arcsec vs pixels) and
reference redshift in its header before use. ψ is obtained by integrating α; the map component's potential has not been tested.

## Recipe 4: a JSON file
`python3 lens_delay.py run config.json`
```json
{"H0":70, "Om":0.3, "zl":0.54, "zs":1.49,
 "components":[{"type":"nfw","x0":0,"y0":0,"kappa_s":0.15,"theta_s":20},
               {"type":"dpie","x0":5,"y0":-2,"sigma":250,"a":0.1,"s":10}],
 "observed_images":[[1.0,2.0],[2.0,-1.0],[-1.5,0.5],[0.2,-2.2]],
 "box":[-40,40,-40,40], "n":800, "ref_image":0, "ref_date":"2014-11-10", "out":"result.json"}
```
Give either `"beta":[bx,by]` or `"observed_images"`. Component `type` is `sie`, `shear`, `nfw`, `dpie` or `map`
(`map` takes `ax, ay, pix, x0, y0, z_ref, flip_columns`).

## Reading the output
`Image(x, y, mu, kind, tau, delay)`: position, signed magnification (negative = reversed parity), minimum/saddle/maximum,
Fermat potential, lag behind the earliest image in days. `compare_models({name: imgs})` gives the min–max spread of the
delays across models: the honest uncertainty, since models of one cluster disagree.

## Checking it
`python3 lens_delay.py selftest` runs analytic checks: SIS images at β±θ_E with Δτ = 2θ_Eβ, ∇ψ = α for every component,
SIE→SIS as q→1, DPIE→SIS as a→0 and s→∞, and D_A(z=1). `LENS_DPRINT=1` prints `name = value` after the main assignments.

## Limits
Single lens plane. The lags depend on the mass model (mass-sheet degeneracy) and, in scale, on H0. A coarse `n` can miss
images near a singular centre. A good fit of the known images does not guarantee the predicted extra image: that is the
point of the Refsdal test.
