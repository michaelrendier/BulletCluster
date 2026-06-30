// ═══════════════════════════════════════════════════════════════════════════
//  Bullet Cluster (1E 0657-558) — Parametric 3D Model
//  Ainulindale / PtolemyHolcus σ-face experiment
//
//  COORDINATE SYSTEM (matches FITS WCS and Three.js companion):
//    x  = East    (RA decreasing → East positive)
//    y  = North   (Dec increasing → North positive)
//    z  = toward observer  (LOS positive = away from source, toward us)
//
//  UNITS:  1 unit = 100 kpc   (at z_redshift=0.296, 1 arcmin ≈ 206 kpc)
//          1 arcmin ≈ 2.06 units
//
//  SOURCES:
//    Positions:  Clowe+2006 (DM peaks), Markevitch+2002 (gas peaks)
//    3D geometry: Springel & Farrar 2007 (8° from plane of sky)
//    All positions relative to X-ray centroid: RA=104.6098°, Dec=-55.9446°
//
//  RENDER:  openscad bullet_cluster.scad
//  EXPORT:  File → Export → Export as STL / Export as PNG
// ═══════════════════════════════════════════════════════════════════════════

$fn = 48;

// ── Default view (OpenSCAD camera: translation, rotation, distance) ───────
$vpt = [0.5, -0.2, 0];
$vpr = [65, 0, 220];
$vpd = 22;

// ── Physical constants ────────────────────────────────────────────────────
ARCMIN_TO_UNIT = 2.06;          // 1 arcmin = 2.06 × 100 kpc units

// ── Positions (arcmin → units, [x=East, y=North, z=LOS_toward_observer]) ─
// Plane-of-sky offsets from centroid (Clowe+2006, Markevitch+2002)
// LOS offsets: Springel & Farrar 2007 — merger 8° from plane of sky
// Projected NW↔SE separation ≈ 2.89 arcmin → z_offset ≈ tan(8°)×2.89/2 = 0.20 arcmin = 0.42 units

DM_NW  = [ -1.97,  2.40, -0.42 ];   // Clowe+2006 — NW dark matter peak (far side)
DM_SE  = [  2.57, -1.45, +0.42 ];   // Clowe+2006 — SE dark matter peak / bullet (near side)
GAS_NW = [ -1.05,  1.80,  0.00 ];   // Markevitch+2002 — NW gas peak
GAS_SE = [  2.82, -2.03, +0.20 ];   // Markevitch+2002 — SE gas peak (bullet, shocked)
CENTROID = [ 0, 0, 0 ];             // X-ray / RA-Dec centroid

// ── Radii (100 kpc units) ─────────────────────────────────────────────────
DM_R_NW  = 1.8;     // NFW projected r_s NW halo  (~180 kpc effective radius shown)
DM_R_SE  = 1.2;     // Bullet sub-cluster DM halo (smaller)
GAS_R_NW = [1.4, 1.0, 0.7];   // NW gas: elongated N-S
GAS_R_SE = [0.6, 0.4, 0.3];   // SE gas: compact bullet, dense

// ── Modules ───────────────────────────────────────────────────────────────

// Dark matter halo — wireframe sphere (ZD/wave: does not interact with EM)
// Colour convention: blue = wave, no Faraday screen expected
module dm_halo(pos, r) {
    translate(pos) {
        // Outer shell only — hollow to show wave/transparent nature
        difference() {
            sphere(r=r);
            sphere(r=r * 0.92);
        }
    }
}

// Gas blob — solid ellipsoid (particle plasma = pigment, Faraday-active)
// Colour convention: hot pink/red = X-ray emitting ICM
module gas_blob(pos, radii) {
    translate(pos)
        scale(radii)
            sphere(r=1);
}

// Bow shock — paraboloid shell in front of the bullet (SE gas)
// The bullet punches through the main cluster gas → Mach shock cone
// Opening direction: toward NW (where the bullet came from)
module bow_shock() {
    // Approximate paraboloid as a thin cone section
    translate(GAS_SE)
        rotate([0, 0, 135])               // PA=135° → opens toward NW
        rotate([90, 0, 0])                // tip points along merger axis
        difference() {
            cylinder(h=1.4, r1=0, r2=1.2, center=false);
            cylinder(h=1.4, r1=0, r2=1.0, center=false);
        }
}

// Merger axis — line connecting the two DM peaks (PA=135°)
// Encodes the 3D trajectory including LOS component
module merger_axis() {
    hull() {
        translate(DM_NW) sphere(r=0.08);
        translate(DM_SE) sphere(r=0.08);
    }
}

// RM transect line — the measurement path for Faraday rotation
// Runs from NW to SE along merger axis, sampling RM(DM)/RM(gas)
module rm_transect() {
    hull() {
        translate(DM_NW + [0,0,0.05]) sphere(r=0.06);
        translate(DM_SE + [0,0,0.05]) sphere(r=0.06);
    }
}

// LOS direction indicator — arrow pointing toward observer (+z)
// This is the integration direction for Faraday rotation
module los_arrow() {
    translate([0, 0, 0]) {
        cylinder(h=2.5, r=0.06, center=false);
        translate([0, 0, 2.5])
            cylinder(h=0.5, r1=0.2, r2=0, center=false);
    }
    // Label base
    translate([0.3, 0, 0])
        linear_extrude(0.1)
            text("LOS +z", size=0.3, font="Liberation Mono");
}

// Compass rose in the sky plane (z=0)
module compass() {
    // East arrow
    color("cyan") {
        hull() {
            translate([-3.5, 0, -3]) sphere(r=0.06);
            translate([-2.0, 0, -3]) sphere(r=0.06);
        }
        translate([-1.8, 0, -3])
            rotate([0, 90, 0])
                cylinder(h=0.4, r1=0.15, r2=0, center=false);
    }
    // North arrow
    color("lime") {
        hull() {
            translate([-3.5, 0, -3]) sphere(r=0.06);
            translate([-3.5, 1.5, -3]) sphere(r=0.06);
        }
        translate([-3.5, 1.7, -3])
            rotate([-90, 0, 0])
                cylinder(h=0.4, r1=0.15, r2=0, center=false);
    }
}

// Scale bar — 1 arcmin = 2.06 units ≈ 206 kpc
module scale_bar() {
    translate([-3.5, -3.5, -3]) {
        hull() {
            sphere(r=0.05);
            translate([ARCMIN_TO_UNIT, 0, 0]) sphere(r=0.05);
        }
    }
}

// Grid — RA/Dec plane (z=0), showing the plane of the sky
module sky_plane_grid() {
    for (i = [-4:1:4]) {
        hull() {
            translate([i, -4, 0]) sphere(r=0.02);
            translate([i,  4, 0]) sphere(r=0.02);
        }
        hull() {
            translate([-4, i, 0]) sphere(r=0.02);
            translate([ 4, i, 0]) sphere(r=0.02);
        }
    }
}

// Faraday integration column — shows what we integrate through along LOS
// at the DM SE position. The KEY: we integrate through ALL gas along this
// sightline, not just gas co-located with DM in 3D (note 10 projection gap)
module los_column_at_dm_se() {
    translate([DM_SE[0], DM_SE[1], -2])
        cylinder(h=4, r=0.15, center=false);
}


// ═══════════════════════════════════════════════════════════════════════════
//  SCENE ASSEMBLY
// ═══════════════════════════════════════════════════════════════════════════

// Sky plane grid (RA/Dec = z=0 plane)
color([0.15, 0.25, 0.35, 0.3]) sky_plane_grid();

// Dark matter halos — blue wireframe shells (wave/ZD — transparent to EM)
color([0.2, 0.5, 1.0, 0.35]) dm_halo(DM_NW, DM_R_NW);
color([0.2, 0.5, 1.0, 0.35]) dm_halo(DM_SE, DM_R_SE);

// Gas blobs — solid hot colors (plasma = pigment = Faraday-active)
color([1.0, 0.2, 0.5, 0.80]) gas_blob(GAS_NW, GAS_R_NW);
color([1.0, 0.5, 0.1, 0.90]) gas_blob(GAS_SE, GAS_R_SE);

// Bow shock — yellow-gold shell
color([1.0, 0.85, 0.1, 0.45]) bow_shock();

// Merger axis — grey tube
color([0.5, 0.5, 0.6, 0.7]) merger_axis();

// RM transect — cyan line (slightly above sky plane for visibility)
color([0.0, 1.0, 1.0, 0.8]) rm_transect();

// LOS integration column at DM SE position — shows projection gap (note 10)
color([1.0, 1.0, 0.0, 0.15]) los_column_at_dm_se();

// LOS direction arrow (from centroid, toward observer)
color([0.8, 0.8, 1.0, 0.9]) los_arrow();

// Compass rose
compass();

// Scale bar
color([0.8, 0.8, 0.8, 0.9]) scale_bar();

// Centroid marker
color([1.0, 1.0, 1.0, 0.9]) translate(CENTROID) sphere(r=0.12);
