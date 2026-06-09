# install-windows.ps1 — Install PPLX CLI + Plugin on Windows with agent harness setup
# Usage: powershell -ExecutionPolicy Bypass -File install\windows.ps1 [-DevDir "C:\dev"] [-SkipPlugin] [-PluginFor "claude|opencode|codex|all"]

param(
    [string]$DevDir = "$env:USERPROFILE\dev",
    [switch]$SkipPlugin,
    [string]$PluginFor = "all",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/mrme000m/pplx.git"
$InstallDir = Join-Path $DevDir "pplx"
$VenvDir = Join-Path $InstallDir ".venv"
$PluginDir = Join-Path $InstallDir "pplx-plugin"

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
        $env:PPLX_PYTHON = (Join-Path $VenvDir "Scripts\python.exe")
        bash $healthScript --no-search 2>$null
    } else {
        Write-Host "  Skipping health script (bash not available). Install Git Bash or WSL."
    }

    Write-Host ""
    Write-Host "Running Pro feature check..."
    $proCheckScript = Join-Path $InstallDir "pplx-plugin\scripts\pplx-pro-check.sh"
    if (Get-Command bash -ErrorAction SilentlyContinue) {
        bash $proCheckScript --verbose 2>$null
    }
}

function Install-Plugin {
    if ($SkipPlugin) {
        Write-Host "Skipping plugin installation (-SkipPlugin)"
        return
    }

    Write-Host ""
    Write-Host "========================================"
    Write-Host "  Installing Plugin for Agent Harnesses"
    Write-Host "========================================"
    Write-Host ""

    # Claude Code on Windows
    if ($PluginFor -eq "all" -or $PluginFor -eq "claude") {
        $claudeDir = "$env:APPDATA\Claude"
        $pluginsDir = Join-Path $claudeDir "plugins"
        $targetDir = Join-Path $pluginsDir "pplx-plugin"

        if (Test-Path $claudeDir) {
            Write-Host "[INFO] Claude Code detected"
            New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null

            if (Test-Path $targetDir) {
                Remove-Item -Recurse -Force $targetDir
            }

            # Create junction (Windows symlink)
            cmd /c mklink /J "$targetDir" "$PluginDir" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Linked pplx-plugin to Claude Code: $targetDir"
            } else {
                # Fallback: copy
                Copy-Item -Recurse -Force $PluginDir $targetDir
                Write-Host "[OK] Copied pplx-plugin to Claude Code: $targetDir"
            }
        } else {
            Write-Host "[WARN] Claude Code config directory not found at $claudeDir"
        }
    }

    # OpenCode on Windows
    if ($PluginFor -eq "all" -or $PluginFor -eq "opencode") {
        $opencodeDir = "$env:APPDATA\opencode"
        $configFile = Join-Path $opencodeDir "opencode.json"
        $skillsDir = Join-Path $opencodeDir "skills"

        if (Get-Command opencode -ErrorAction SilentlyContinue) {
            Write-Host "[INFO] OpenCode detected"
        }

        New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
        $targetSkills = Join-Path $skillsDir "pplx-plugin"

        if (Test-Path $targetSkills) {
            Remove-Item -Recurse -Force $targetSkills
        }

        cmd /c mklink /J "$targetSkills" "$PluginDir" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Copy-Item -Recurse -Force $PluginDir $targetSkills
        }
        Write-Host "[OK] Linked pplx-plugin to OpenCode skills: $targetSkills"

        # Update config
        if (Test-Path $configFile) {
            Write-Host "[INFO] Found OpenCode config: $configFile"
            $config = Get-Content $configFile | ConvertFrom-Json
            if (-not $config.skills) {
                $config | Add-Member -NotePropertyName skills -NotePropertyValue @{ paths = @() }
            }
            if (-not $config.skills.paths) {
                $config.skills.paths = @()
            }
            if ($config.skills.paths -notcontains $PluginDir) {
                $config.skills.paths += $PluginDir
                $config | ConvertTo-Json -Depth 10 | Set-Content $configFile
                Write-Host "[OK] Added pplx-plugin to OpenCode config"
            }
        } else {
            $defaultConfig = @{
                skills = @{
                    paths = @($PluginDir)
                }
            }
            $defaultConfig | ConvertTo-Json -Depth 10 | Set-Content $configFile
            Write-Host "[OK] Created OpenCode config with pplx-plugin"
        }
    }

    # Codex on Windows
    if ($PluginFor -eq "all" -or $PluginFor -eq "codex") {
        $codexDir = "$env:APPDATA\Codex"
        $scriptsDir = Join-Path $codexDir "scripts"

        if (Get-Command codex -ErrorAction SilentlyContinue) {
            Write-Host "[INFO] Codex CLI detected"
        }

        New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
        $targetScripts = Join-Path $scriptsDir "pplx-plugin"

        if (Test-Path $targetScripts) {
            Remove-Item -Recurse -Force $targetScripts
        }

        cmd /c mklink /J "$targetScripts" "$PluginDir\scripts" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Copy-Item -Recurse -Force "$PluginDir\scripts" $targetScripts
        }
        Write-Host "[OK] Linked pplx-plugin scripts to Codex: $targetScripts"
    }

    # Environment setup
    $shellProfile = "$PROFILE"
    if (-not (Test-Path $shellProfile)) {
        New-Item -ItemType File -Path $shellProfile -Force | Out-Null
    }

    $envLines = @(
        "# PPLX (Perplexity AI) configuration",
        "`$env:PPLX_REPO_DIR = `"$InstallDir`"",
        "`$env:PPLX_PLUGIN_DIR = `"$PluginDir`""
    )

    $profileContent = Get-Content $shellProfile -Raw -ErrorAction SilentlyContinue
    if ($profileContent -notmatch "PPLX_REPO_DIR") {
        Add-Content -Path $shellProfile -Value ($envLines -join "`n")
        Write-Host "[OK] Added PPLX environment variables to PowerShell profile"
    }

    Write-Host ""
    Write-Host "[OK] Plugin installation complete!"
    Write-Host "[INFO] Restart your agent harness to load the plugin."
}

function Print-NextSteps {
    Write-Host @"

========================================
  PPLX Installation Complete!
========================================

Installation directory: $InstallDir
Virtual environment:    $VenvDir
Plugin directory:       $PluginDir

1. Activate the virtual environment:
   $($VenvDir)\Scripts\Activate.ps1

2. Set up Bitwarden authentication:
   - Install bw CLI: https://bitwarden.com/help/article/cli/
   - Create a Secure Note named "perplexity.ai" with your cookies JSON

3. Or use BWS (preferred):
   `$env:BWS_ACCESS_TOKEN = "<your-token>"
   python scripts\setup_bws_secret.py setup-cookies C:\path\to\cookies.json

4. Test a search:
   pplx search "Hello world" --mode auto

5. Plugin commands available:
   /pplx-research      - Grounded web/Space research
   /pplx-orchestrate   - Multi-step research chains
   /pplx-space         - Space management
   /pplx-threads       - Thread workflows
   /pplx-upload        - File upload
   /pplx-settings      - Account audit
   /pplx-pro-optimizer - Mode optimization
   /pplx-persist       - Knowledge persistence
   /pplx-assets        - Asset management
   /pplx-cli-check     - Health diagnostics
   /pplx-bws-setup     - BWS configuration

6. Shell helpers:
   bash $($InstallDir)\pplx-plugin\scripts\pplx-health.sh --verbose --no-search
   bash $($InstallDir)\pplx-plugin\scripts\pplx-pro-check.sh --verbose

For help: pplx --help
For plugin docs: Get-Content "$($InstallDir)\pplx-plugin\README.md"

"@
}

Write-Host "PPLX Installer for Windows"
Write-Host "=========================="
Write-Host ""
Write-Host "Install directory: $InstallDir"
Write-Host "Plugin target: $PluginFor"
Write-Host ""

Check-Prereqs
Clone-Repo
Setup-Venv
Install-Package
Verify-Install
Install-Plugin
Print-NextSteps
