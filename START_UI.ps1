$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "my-work\module3_chat_ui"
$frontend = Join-Path $root "notebooks\module-3\agent-chat-ui"
$cli = Join-Path $root ".venv\Scripts\langgraph.exe"
if (!(Test-Path $cli)) { throw "Create the Python virtual environment (.venv) in the repository root first." }
if (!(Test-Path (Join-Path $root ".env"))) { throw "Create a private .env in the repository root from example.env. Never commit it." }
if (!(Test-Path (Join-Path $frontend "node_modules"))) { throw "Run corepack pnpm install once in notebooks\module-3\agent-chat-ui, then retry." }
Copy-Item (Join-Path $frontend ".env.example") (Join-Path $frontend ".env.local") -Force
$b = "Set-Location '" + $backend.Replace("'", "''") + "'; & '" + $cli.Replace("'", "''") + "' dev --no-browser --port 2024"
$f = "Set-Location '" + $frontend.Replace("'", "''") + "'; corepack pnpm dev"
Start-Process powershell.exe -ArgumentList @("-NoExit", "-Command", $b)
Start-Process powershell.exe -ArgumentList @("-NoExit", "-Command", $f)
Write-Host "After both servers are ready, open http://localhost:3000. Dummy login: julie@example.com / password123. API key field stays blank."
