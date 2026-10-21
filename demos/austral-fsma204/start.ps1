$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$Root\api"
if (-not (Test-Path .venv)) { python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt }
.\.venv\Scripts\python -c "from seed import seed; seed('fsma.db')"
Start-Process -NoNewWindow .\.venv\Scripts\uvicorn -ArgumentList "app:app","--host","0.0.0.0","--port","8017"
Set-Location "$Root\web"
if (-not (Test-Path node_modules)) { npm install }
npm run dev
