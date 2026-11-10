$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$nexusPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $nexusPython)) { throw 'Run the README environment setup first.' }
if (-not (Test-Path -LiteralPath 'models\signs.npz')) { Write-Warning 'No trained sign model yet. The app will show setup status.' }
Write-Host 'Open http://127.0.0.1:8765 in your browser. Press Ctrl+C here to stop Nexus.'
& $nexusPython -m nexus.app
