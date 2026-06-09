# install-windows.ps1 — Install PPLX CLI + Plugin on Windows
# Usage: powershell -ExecutionPolicy Bypass -File install\windows.ps1 [-DevDir "C:\dev"]

param(
    [string]$DevDir = "$env:USERPROFILE\dev",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/mrme000m/pplx.git"
$InstallDir = Join-Path $DevDir "pplx"
$VenvDir = Join-Path $InstallDir ".venv"

function Check-Prereqs {
    Write-Host "Checking prerequisites..."

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "git is required. Install from: https://git-scm.com/download/win"
        exit 1
    }

    if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
        Write-Host "Python 3 is required. Install from: https://python.org/downloads/"
        exit 1
    }

    $pyVer = & $Python --version 2>&1
    Write-Host "  Python: $pyVer"

    $verCheck = & $Python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python 3.10+ is required. Found: $pyVer"
        exit 1
    }

    Write-Host "  git: OK"
    Write-Host "  Python 3.10+: OK"
}

function Clone-Repo {
    if (Test-Path (Join-Path $InstallDir ".git")) {
        Write-Host "Updating existing repo at $InstallDir..."
        Set-Location $InstallDir
        git pull --ff-only
    } else {
        Write-Host "Cloning $RepoUrl into $InstallDir..."
        New-Item -ItemType Directory -Force -Path $DevDir | Out-Null
        git clone $RepoUrl $InstallDir
        Set-Location $InstallDir
    }
}

function Setup-Venv {
    Write-Host "Setting up virtual environment..."
    if (-not (Test-Path $VenvDir)) {
        & $Python -m venv $VenvDir
    }

    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    . $activateScript

    Write-Host "  Upgrading pip..."
    pip install --quiet --upgrade pip
}

function Install-Package {
    Write-Host "Installing PPLX package..."
    pip install --quiet -e $InstallDir

    Write-Host "Installing plugin dependencies..."
    pip install --quiet curl-cffi bitwarden-sdk python-dotenv
}

function Verify-Install {
    Write-Host "Verifying installation..."

    $pplxPath = Join-Path $VenvDir "Scripts\pplx.exe"
    if (Test-Path $pplxPath) {
        Write-Host "  pplx CLI: $pplxPath"
        & $pplxPath --version
    } else {
        Write-Host "  pplx CLI: not found in expected location"
    }

    Write-Host ""
    Write-Host "Running health check (no live search)..."
    $healthScript = Join-Path $InstallDir "pplx-plugin\scripts\pplx-health.sh"
    if (Get-Command bash -ErrorAction SilentlyContinue) {
        bash $healthScript --no-search 2>$null
    } else {
        Write-Host "  Skipping health script (bash not available). Install Git Bash or WSL."
    }
}

function Print-NextSteps {
    Write-Host @"

========================================
  PPLX Installation Complete!
========================================

Next steps:

1. Activate the virtual environment:
   $($VenvDir)\Scripts\Activate.ps1

2. Set up Bitwarden authentication:
   - Install bw CLI: https://bitwarden.com/help/article/cli/
   - Create a Secure Note named "perplexity.ai" with your cookies JSON

3. Or use BWS (preferred):
   $env:BWS_ACCESS_TOKEN = "<your-token>"
   python scripts\setup_bws_secret.py setup-cookies C:\path\to\cookies.json

4. Test a search:
   pplx search "Hello world" --mode auto

5. Add to your agent harness:
   Claude Code: claude --plugin-dir "$InstallDir\pplx-plugin"
   OpenCode:    add "$InstallDir\pplx-plugin" to skills.paths

For help: pplx --help
For plugin commands: ls "$InstallDir\pplx-plugin\commands\"

"@
}

Write-Host "PPLX Installer for Windows"
Write-Host "=========================="

Check-Prereqs
Clone-Repo
Setup-Venv
Install-Package
Verify-Install
Print-NextSteps
