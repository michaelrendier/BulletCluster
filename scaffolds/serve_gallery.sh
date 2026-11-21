#!/bin/bash
# Open the Scaffold Gallery (and its report and viewers) through a local web server on 127.0.0.1.
# Why: Firefox shows a page's favicon only for http(s) pages; for file:// pages it stores none and shows the globe.
# Usage: ./serve_gallery.sh [page=gallery.html] [port=8765]       (the server listens on loopback only; stop it with: pkill -f "http.server 8765")
cd "$(dirname "$0")"; PAGE=${1:-gallery.html}; PORT=${2:-8765}; PY=../.venv/bin/python
curl -s -o /dev/null "http://127.0.0.1:$PORT/favicon.ico" || { nohup $PY -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 & sleep 1; }
xdg-open "http://127.0.0.1:$PORT/$PAGE" >/dev/null 2>&1
