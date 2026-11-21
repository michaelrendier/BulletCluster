"""contact.py: the author's contact bar (header) and footer, shared by every gallery and index page.
Email, Facebook and ORCID as the author gave them (2026-11-21). Idempotent injector: python3 contact.py FILE.html [...]"""
import re, sys
EMAIL = "the.wandering.god@gmail.com"; FB = "https://facebook.com/rendier"; ORCID = "0009-0007-7239-6760"; NAME = "Michael Rendier"; FULL = "Cody Michael Allison (Michael Rendier)"
MARK = "<!--ct-->"
CSS = """<style id="ct-css">.ct-bar,.ct-foot{font:13px/1.5 system-ui,sans-serif;color:#c9d1ff;background:#151a33;padding:6px 16px;display:flex;gap:6px 18px;flex-wrap:wrap;align-items:center;justify-content:center}
.ct-foot{margin-top:28px;padding:14px 16px;border-top:1px solid #2a3257;flex-direction:column;gap:4px;text-align:center}.ct-bar a,.ct-foot a{color:#9fb3ff;text-decoration:none}.ct-bar a:hover,.ct-foot a:hover{text-decoration:underline}
.ct-bar b{color:#e6e9f5;font-weight:600}.ct-orcid{display:inline-block;width:14px;height:14px;border-radius:50%;background:#a6ce39;color:#fff;font:700 9px/14px sans-serif;text-align:center;margin-right:4px;vertical-align:-2px}.ct-sep{opacity:.4}</style>"""
def links(): return (f'<a href="mailto:{EMAIL}">✉ {EMAIL}</a><span class="ct-sep">·</span><a href="{FB}" target="_blank" rel="noopener">Facebook</a><span class="ct-sep">·</span>'
                     f'<a href="https://orcid.org/{ORCID}" target="_blank" rel="noopener"><span class="ct-orcid">iD</span>ORCID {ORCID}</a>')
def top(): return f'{MARK}<div class="ct-bar"><b>{NAME}</b>{links()}</div>'
def bottom(): return f'{MARK}<footer class="ct-foot"><div><b>{FULL}</b></div><div>{links()}</div><div>All repositories: <a href="https://github.com/michaelrendier" target="_blank" rel="noopener">github.com/michaelrendier</a> · <a href="https://michaelrendier.github.io/" target="_blank" rel="noopener">michaelrendier.github.io</a></div></footer>'
def inject(html):
    if MARK in html: return html
    if "</head>" in html: html = html.replace("</head>", CSS + "</head>", 1)
    else: html = CSS + html
    m = re.search(r"<body[^>]*>", html)
    html = html[:m.end()] + top() + html[m.end():] if m else top() + html
    return html.replace("</body>", bottom() + "</body>", 1) if "</body>" in html else html + bottom()
if __name__ == "__main__":
    for f in sys.argv[1:]:
        s = open(f, errors="ignore").read(); t = inject(s)
        if t != s: open(f, "w").write(t); print("injected", f)
        else: print("already", f)
