param(
    [string]$PythonVersion = "3.11.8",
    [string]$RuntimeDir = "runtime/python-embed",
    [string]$VenvDir = ".venv",
    [string]$RequirementsFile = "requirements.txt",
    [switch]$AutoInstallDeps,
    [switch]$LaunchDashboard
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[info] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[warn] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[error] $msg" -ForegroundColor Red }

$AutoInstallDepsFlag = $AutoInstallDeps.IsPresent
$LaunchDashboardFlag = $LaunchDashboard.IsPresent

# Resolve repo-root-relative paths regardless of current working directory
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptRoot "..")

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

# 4) Run friendly startup check (headless)
$autoFlag = ""
if ($AutoInstallDepsFlag) { $autoFlag = "--auto-install-deps" }
Write-Info "Running startup check"
$mainScript = Join-Path $RepoRoot "main.py"
& $venvPython $mainScript --startup-check-only $autoFlag
if ($LASTEXITCODE -ne 0) { Write-Err "Startup check reported missing dependencies."; exit $LASTEXITCODE }

# 5) Optional: launch dashboard
if ($LaunchDashboardFlag) {
    Write-Info "Launching Streamlit dashboard"
    & $venvPython -m streamlit run ui/dashboard.py --logger.level=warning
}

Write-Info "Bootstrap completed."
