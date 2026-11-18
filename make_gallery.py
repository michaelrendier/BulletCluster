"""Build gallery.html: every scaffold, raw beside false colour, synced zoom/pan, blink and wipe.  stdlib only.  Run in this directory."""
import os, re, json, glob
items = []
def rawfile(t, stem):
    for c in (stem + "_raw.png", stem.split("_", 3)[-1] + "_raw.png"):
        if os.path.exists(f"{t}/raw/{c}"): return f"{t}/raw/{c}"
    m = glob.glob(f"{t}/raw/*{stem}*_raw.png")
    return m[0] if m else None
for t in sorted(d for d in os.listdir(".") if os.path.isdir(d)):
    fc = sorted(os.listdir(f"{t}/false_color")); seen = set()
    for f in fc:
        if f.endswith("_rgb_lupton.png"):                                  # composite: sky-subtracted + original
            base = f[:-4]; txt = open(f"{t}/false_color/{base}.txt").read() if os.path.exists(f"{t}/false_color/{base}.txt") else ""
            stems = []
            m = re.search(r"channels \(blue -> red\): (.*)", txt)
            if m: stems = [s.strip() for g in m.group(1).split("|") for s in g.split(",")]
            raws = [(re.sub(r"^.*?(miri|nircam)", r"\1", s), rawfile(t, s)) for s in stems]
            items.append({"target": t, "title": base.replace("_rgb_lupton", "").replace(t + "_", "") + " composite",
                          "false": [("sky-subtracted", f"{t}/false_color/{f}"), ("original algorithm (no sky subtraction)", f"{t}/false_color/{base}_nosky.png")],
                          "raw": [(a, b) for a, b in raws if b], "note": txt.strip()})
        elif f.endswith("_cube_thirds_rgb.png"):                           # IFU cube thirds vs collapsed
            stem = f[:-len("_cube_thirds_rgb.png")]; r = f"{t}/raw/{stem}_collapsed_raw.png"
            items.append({"target": t, "title": stem + " (IFU cube)", "false": [("cube thirds in wavelength -> RGB", f"{t}/false_color/{f}")],
                          "raw": [("collapsed cube", r)] if os.path.exists(r) else [], "note": ""})
        elif f.endswith("_inferno.png"):                                    # single filter
            m = re.search(r"(jw\d+-o\d+_t\d+_(?:miri|nircam)_[a-z0-9-]+)_inferno", f); r = rawfile(t, m.group(1)) if m else None
            items.append({"target": t, "title": (m.group(1) if m else f) + " (single filter)", "false": [("inferno", f"{t}/false_color/{f}")],
                          "raw": [("raw", r)] if r else [], "note": ""})
html = open("gallery_template.html").read().replace("/*DATA*/", json.dumps(items))
open("gallery.html", "w").write(html)
n = sum(len(i["raw"]) for i in items); print(len(items), "scaffold items,", sum(len(i["false"]) for i in items), "false-colour images,", n, "raw images paired")
