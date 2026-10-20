$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$Root\api"
if (-not (Test-Path .venv)) {
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
}
.\.venv\Scripts\python -c "from seed import seed; seed()"
Start-Process -NoNewWindow .\.venv\Scripts\uvicorn -ArgumentList "app:app","--host","127.0.0.1","--port","8016"
Set-Location "$Root\web"
if (-not (Test-Path node_modules)) { npm install }
npm run dev
