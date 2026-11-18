#!/usr/bin/env bash
# After installing casatools in BulletCluster/.venv: the pip wheel bundles OpenSSL-3.2-era libssl/libldap/liblber that do not load against
# this system's OpenSSL 3.0.13, so the bundled copies are set aside (renamed, reversible) and the system ones are used.  Measures data: ~/.casa/config.py.
set -e; L="$(dirname "$0")/.venv/lib/python3.12/site-packages/casatools/__casac__/lib"
for f in libssl.so.3 libldap.so.2 liblber.so.2; do [ -f "$L/$f" ] && mv "$L/$f" "$L/$f.bundled_unused"; done
"$(dirname "$0")/.venv/bin/python" -c "import casatools, casatasks; print('casatools', casatools.version())"
