#!/usr/bin/env bash
# env.sh — activate the BulletCluster analysis environment.
#
#   source env.sh          # activate
#   ./env.sh check         # verify the stack imports
#
# WHY A VENV (2026-08-14):
#   The system Python has numpy 2.4.6 in ~/.local shadowing numpy 1.26.4 from
#   apt, and every apt-built C extension is still linked against 1.x. Six
#   packages were unimportable: bottleneck, numcodecs, zarr, reproject, aplpy,
#   pandas -- plus scikit-learn and NLTK. pip refuses to fix it in place
#   (PEP 668, externally managed). Five optional accelerators were removed from
#   the system; the rest live here instead.
#
#   Telescope data work runs in THIS venv. Do not use the system python for it.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HERE/.venv"

if [ "$1" = "check" ]; then
    "$VENV/bin/python" - <<'PY'
mods = ['numpy','scipy','matplotlib','astropy','astroquery',
        'pandas','sklearn','reproject','photutils','regions','numcodecs']
bad = 0
for m in mods:
    try:
        mod = __import__(m)
        print(f"  OK    {m:<12} {getattr(mod,'__version__','?')}")
    except Exception as ex:
        bad += 1
        print(f"  FAIL  {m:<12} {type(ex).__name__}: {str(ex)[:60]}")
print("\nall good" if not bad else f"\n{bad} broken")
PY
    exit 0
fi

if [ ! -d "$VENV" ]; then
    echo "no venv at $VENV — create with:"
    echo "  python3 -m venv .venv && .venv/bin/python -m pip install \\"
    echo "    numpy scipy matplotlib astropy astroquery pandas \\"
    echo "    scikit-learn reproject photutils regions numcodecs"
    return 1 2>/dev/null || exit 1
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
echo "BulletCluster env active — $(python -c 'import sys;print(sys.version.split()[0])') @ $VENV"
