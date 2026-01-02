param(
    [string]$PythonVersion = "3.11.8",
    [string]$RuntimeDir = "runtime/python-embed",
    [string]$VenvDir = ".venv",
    [string]$RequirementsFile = "requirements.txt",
    [switch]$AutoInstallDeps,
    [switch]$LaunchDashboard
)

$ErrorActionPreference = "Stop"

# Ensure all relative paths resolve from repo root
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptRoot "..")
Push-Location $RepoRoot
try {

function Write-Info($msg) { Write-Host "[info] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[warn] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[error] $msg" -ForegroundColor Red }

$LogPath = Join-Path $RepoRoot "bootstrap.log"
try {
    if (Test-Path $LogPath) { Remove-Item $LogPath -Force }
    Start-Transcript -Path $LogPath -Force | Out-Null
    Write-Info "Transcript logging to $LogPath"
}
catch {
    Write-Warn "Could not start transcript logging: $_"
    $LogPath = $null
}

trap {
    Write-Err "Unhandled error: $_"
    if ($LogPath) { Write-Err "See log: $LogPath" }
    exit 1
}

$AutoInstallDepsFlag = $AutoInstallDeps.IsPresent
$LaunchDashboardFlag = $LaunchDashboard.IsPresent

function Resolve-RepoPath {
    param([string]$PathValue)
    if ([IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
    return (Join-Path $RepoRoot $PathValue)
}

function Resolve-Python {
    param([string]$Candidate)
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $null }
    if (Test-Path $Candidate) { return (Resolve-Path $Candidate).Path }
    $resolved = (Get-Command $Candidate -ErrorAction SilentlyContinue)
    if ($resolved) { return $resolved.Source }
    return $null
}

# 1) Find or provision Python runtime
$pythonExe = $null
$venvRoot = Resolve-RepoPath $VenvDir
$venvPython = Join-Path $venvRoot "Scripts/python.exe"
$runtimeRoot = Resolve-RepoPath $RuntimeDir
$embedPython = Join-Path $runtimeRoot "python.exe"

$pythonExe = Resolve-Python $venvPython
if (-not $pythonExe) { $pythonExe = Resolve-Python $embedPython }
if (-not $pythonExe) { $pythonExe = Resolve-Python "python" }
if (-not $pythonExe) { $pythonExe = Resolve-Python "py" }

if (-not $pythonExe) {
    Write-Info "Python not found; downloading embeddable runtime $PythonVersion..."
    $base = "https://www.python.org/ftp/python/$PythonVersion"
    $zipName = "python-$PythonVersion-embed-amd64.zip"
    $zipPath = Join-Path $runtimeRoot $zipName
    if (-not (Test-Path $runtimeRoot)) { New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null }
    Invoke-WebRequest -Uri "$base/$zipName" -OutFile $zipPath
    Write-Info "Expanding embeddable runtime..."
    Expand-Archive -Path $zipPath -DestinationPath $runtimeRoot -Force
    Remove-Item $zipPath -Force
    $pythonExe = Resolve-Python $embedPython
}

if (-not $pythonExe) { Write-Err "Could not locate or install Python."; exit 1 }
Write-Info "Using Python: $pythonExe"

# 2) Create / refresh venv
if (-not (Test-Path $venvRoot)) {
    Write-Info "Creating venv at $venvRoot"
    & $pythonExe -m venv $venvRoot
}
else {
    Write-Info "Using existing venv at $venvRoot"
}
$venvPython = Resolve-Python $venvPython
if (-not $venvPython) { Write-Err "Failed to resolve venv python."; exit 1 }

# 3) Upgrade pip and install requirements
Write-Info "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

$resolvedRequirements = Resolve-RepoPath $RequirementsFile
if (-not (Test-Path $resolvedRequirements)) { Write-Err "Requirements file not found: $resolvedRequirements"; exit 1 }
Write-Info "Installing from $resolvedRequirements"
& $venvPython -m pip install -r $resolvedRequirements

# 4) Quick Python health check
Write-Info "Checking Python runtime"
& $venvPython -c "import sys; print(f'python_version={sys.version}')"
if ($LASTEXITCODE -ne 0) { Write-Err "Python health check failed."; exit $LASTEXITCODE }

# 5) Run friendly startup check (headless)
$mainArgs = @("--startup-check-only")
if ($AutoInstallDepsFlag) { $mainArgs += "--auto-install-deps" }
Write-Info "Running startup check"
$mainScript = Join-Path $RepoRoot "main.py"
& $venvPython $mainScript @mainArgs
if ($LASTEXITCODE -ne 0) { Write-Err "Startup check reported missing dependencies (see bootstrap.log)."; exit $LASTEXITCODE }

# 6) Optional: launch dashboard
if ($LaunchDashboardFlag) {
    Write-Info "Launching Streamlit dashboard"
    & $venvPython -m streamlit --version
    if ($LASTEXITCODE -ne 0) { Write-Err "Streamlit not available; ensure requirements are installed."; exit $LASTEXITCODE }
    & $venvPython -m streamlit run (Join-Path $RepoRoot "ui/dashboard.py") --logger.level=warning
}

Write-Info "Bootstrap completed."
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
    Pop-Location
}
