"""Simple FastAPI server to serve interactive chart HTML and an index for review.

Mounts the `reports/charts` directory as static files and exposes a small API
to list available policies and their chart files.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Dict, List

app = FastAPI(title="Polisim Charts Server")

# Serve the reports/charts directory at /charts
CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports', 'charts')
if not os.path.exists(CHARTS_DIR):
    os.makedirs(CHARTS_DIR, exist_ok=True)

app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")


def discover_charts() -> Dict[str, List[str]]:
    """Return a mapping policy_name -> list of chart html file paths (relative to /charts)."""
    mapping: Dict[str, List[str]] = {}
    if not os.path.exists(CHARTS_DIR):
        return mapping
    for policy_dir in os.listdir(CHARTS_DIR):
        pdir = os.path.join(CHARTS_DIR, policy_dir)
        if not os.path.isdir(pdir):
            continue
        htmls = [f for f in os.listdir(pdir) if f.lower().endswith('.html')]
        # Build URLs relative to /charts
        urls = [f"/charts/{policy_dir}/{h}" for h in sorted(htmls)]
        mapping[policy_dir] = urls
    return mapping


@app.get('/', response_class=HTMLResponse)
def index():
    mapping = discover_charts()
    if not mapping:
        return HTMLResponse('<h2>No charts found. Run `run_visualize.py` or `run_report.py` to generate charts.</h2>')
    lines = ['<h1>Polisim Charts</h1>']
    for policy, urls in mapping.items():
        lines.append(f'<h2>{policy}</h2><ul>')
        for u in urls:
            lines.append(f'<li><a href="{u}" target="_blank">{os.path.basename(u)}</a></li>')
        lines.append('</ul>')
    return HTMLResponse('\n'.join(lines))


@app.get('/api/policies')
def api_policies():
    return JSONResponse(discover_charts())


@app.get('/api/policy/{policy_name}/chart/{chart_fname}')
def get_chart(policy_name: str, chart_fname: str):
    pdir = os.path.join(CHARTS_DIR, policy_name)
    if not os.path.isdir(pdir):
        raise HTTPException(status_code=404, detail='Policy not found')
    fpath = os.path.join(pdir, chart_fname)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail='Chart not found')
    # Serve the file (HTML or image)
    return FileResponse(fpath)


def run(port: int = 8000):
    import uvicorn
    uvicorn.run('ui.server:app', host='127.0.0.1', port=port, log_level='info', reload=False)


if __name__ == '__main__':
    print('Starting Polisim Charts Server on http://127.0.0.1:8000')
    run()
