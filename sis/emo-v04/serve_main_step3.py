from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pathlib

app = FastAPI()

@app.get("/docs", response_class=HTMLResponse)
async def docs():
    p = pathlib.Path("main-step3.py")
    if not p.exists():
        return HTMLResponse("<h3>File not found: main-step3.py</h3>", status_code=404)
    text = p.read_text(encoding="utf-8")
    import html
    safe = html.escape(text)
    html_content = f"""<html>
<head>
<meta charset='utf-8'>
<title>main-step3.py</title>
<style>body{{font-family: monospace; padding:16px;}} pre{{white-space:pre-wrap;}}</style>
</head>
<body>
<h2>main-step3.py</h2>
<pre>{safe}</pre>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("<html><body><a href='/docs'>View main-step3.py</a></body></html>")
