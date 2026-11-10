$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$nexusTools = Join-Path $PSScriptRoot '.tools'
python -m pip install --target $nexusTools uv==0.13.7
if ($LASTEXITCODE -ne 0) { throw 'Could not install the environment manager.' }
$nexusPreviousPythonPath = $env:PYTHONPATH
$nexusPreviousInstallDir = $env:UV_PYTHON_INSTALL_DIR
$nexusPreviousCacheDir = $env:UV_CACHE_DIR
try {
    $env:PYTHONPATH = $nexusTools
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.python'
    $env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.uv-cache'
    python -m uv python install 3.11.18
    if ($LASTEXITCODE -ne 0) { throw 'Python download failed.' }
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        python -m uv venv --python 3.11.18 .venv
        if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed.' }
    }
    python -m uv pip install --python .venv/Scripts/python.exe -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
} finally {
    $env:PYTHONPATH = $nexusPreviousPythonPath
    $env:UV_PYTHON_INSTALL_DIR = $nexusPreviousInstallDir
    $env:UV_CACHE_DIR = $nexusPreviousCacheDir
}
Write-Host 'Environment ready. See README for the research dataset preparation and training commands.'
