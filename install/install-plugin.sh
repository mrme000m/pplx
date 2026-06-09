#!/usr/bin/env bash
# install-plugin.sh — Install pplx-plugin for detected agent harnesses
# Usage: source install-plugin.sh <plugin_dir> [claude|opencode|codex|all]

set -euo pipefail

PPLX_PLUGIN_DIR="${1:-}"
TARGET_HARNESS="${2:-all}"

if [[ -z "$PPLX_PLUGIN_DIR" ]]; then
    echo "Error: Plugin directory not provided"
    echo "Usage: source install-plugin.sh <plugin_dir> [claude|opencode|codex|all]"
    return 1 2>/dev/null || exit 1
fi

PPLX_PLUGIN_DIR="$(cd "$PPLX_PLUGIN_DIR" && pwd)"
REPO_DIR="$(cd "$PPLX_PLUGIN_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# -----------------------------------------------------------------------------
# Claude Code
# -----------------------------------------------------------------------------
install_claude() {
    local claude_dir=""
    local installed=false

    # Check for Claude Code
    if command -v claude &>/dev/null || command -v cc &>/dev/null; then
        info "Claude Code detected"
    else
        warn "Claude Code not found in PATH"
        return 0
    fi

    # Determine Claude config directory
    if [[ -n "${CLAUDE_CONFIG_DIR:-}" ]]; then
        claude_dir="$CLAUDE_CONFIG_DIR"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        claude_dir="$HOME/Library/Application Support/Claude"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        claude_dir="${XDG_CONFIG_HOME:-$HOME/.config}/claude"
    fi

    if [[ -z "$claude_dir" ]]; then
        warn "Could not determine Claude Code config directory"
        return 0
    fi

    local plugins_dir="$claude_dir/plugins"
    local target_dir="$plugins_dir/pplx-plugin"

    info "Claude Code plugins directory: $plugins_dir"
    mkdir -p "$plugins_dir"

    # Install plugin — symlink for dev, copy for distribution
    if [[ -d "$target_dir" ]]; then
        if [[ -L "$target_dir" ]]; then
            rm "$target_dir"
        else
            rm -rf "$target_dir"
        fi
    fi

    ln -sf "$PPLX_PLUGIN_DIR" "$target_dir"
    ok "Linked pplx-plugin to Claude Code: $target_dir"

    # Check for settings.json and suggest plugin entry
    local settings_file="$claude_dir/settings.json"
    if [[ -f "$settings_file" ]]; then
        info "Found Claude Code settings.json"
        if grep -q "pplx-plugin" "$settings_file" 2>/dev/null; then
            ok "pplx-plugin already referenced in settings.json"
        else
            warn "Add plugin reference to $settings_file if using plugin manifest"
        fi
    fi

    installed=true

    # Create/update .zshrc / .bashrc hints
    local shell_rc=""
    if [[ -f "$HOME/.zshrc" ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        shell_rc="$HOME/.bashrc"
    elif [[ -f "$HOME/.bash_profile" ]]; then
        shell_rc="$HOME/.bash_profile"
    fi

    if [[ -n "$shell_rc" ]]; then
        # Add PPLX env vars if not present
        if ! grep -q "PPLX_REPO_DIR" "$shell_rc" 2>/dev/null; then
            info "Adding PPLX environment variables to $shell_rc"
            cat >> "$shell_rc" <<EOF

# PPLX (Perplexity AI) configuration
export PPLX_REPO_DIR="$REPO_DIR"
export PPLX_PLUGIN_DIR="$PPLX_PLUGIN_DIR"
EOF
            ok "Added PPLX env vars to $shell_rc"
        fi
    fi

    if [[ "$installed" == true ]]; then
        ok "Claude Code plugin installation complete"
        info "Restart Claude Code to load the plugin: exit and run 'claude' again"
        info "Verify with: claude --help | grep -i pplx"
    fi
}

# -----------------------------------------------------------------------------
# OpenCode
# -----------------------------------------------------------------------------
install_opencode() {
    local opencode_dir=""
    local installed=false

    if command -v opencode &>/dev/null; then
        info "OpenCode detected"
    else
        warn "OpenCode not found in PATH"
        return 0
    fi

    # Determine OpenCode config directory
    if [[ -n "${OPENCODE_CONFIG_DIR:-}" ]]; then
        opencode_dir="$OPENCODE_CONFIG_DIR"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        opencode_dir="$HOME/Library/Application Support/opencode"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        opencode_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
    fi

    if [[ -z "$opencode_dir" ]]; then
        warn "Could not determine OpenCode config directory"
        return 0
    fi

    local config_file="$opencode_dir/opencode.json"
    local skills_dir="$opencode_dir/skills"

    info "OpenCode config directory: $opencode_dir"
    mkdir -p "$skills_dir"

    # Link plugin skills directory
    local target_skills="$skills_dir/pplx-plugin"
    if [[ -d "$target_skills" ]]; then
        if [[ -L "$target_skills" ]]; then
            rm "$target_skills"
        else
            rm -rf "$target_skills"
        fi
    fi
    ln -sf "$PPLX_PLUGIN_DIR" "$target_skills"
    ok "Linked pplx-plugin to OpenCode skills: $target_skills"

    # Update or create config
    if [[ -f "$config_file" ]]; then
        info "Found OpenCode config: $config_file"
        if grep -q "pplx-plugin" "$config_file" 2>/dev/null; then
            ok "pplx-plugin already in OpenCode config"
        else
            warn "Manually add to $config_file skills.paths: \"$PPLX_PLUGIN_DIR\""
        fi
    else
        info "Creating OpenCode config: $config_file"
        mkdir -p "$opencode_dir"
        cat > "$config_file" <<EOF
{
  "skills": {
    "paths": [
      "$PPLX_PLUGIN_DIR"
    ]
  }
}
EOF
        ok "Created OpenCode config with pplx-plugin"
    fi

    installed=true
    ok "OpenCode plugin installation complete"
    info "Restart OpenCode to load the plugin"
}

# -----------------------------------------------------------------------------
# Codex (OpenAI Codex CLI)
# -----------------------------------------------------------------------------
install_codex() {
    local codex_dir=""
    local installed=false

    if command -v codex &>/dev/null; then
        info "Codex CLI detected"
    else
        warn "Codex CLI not found in PATH"
        return 0
    fi

    # Determine Codex config directory
    if [[ -n "${CODEX_CONFIG_DIR:-}" ]]; then
        codex_dir="$CODEX_CONFIG_DIR"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        codex_dir="$HOME/Library/Application Support/Codex"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        codex_dir="${XDG_CONFIG_HOME:-$HOME/.config}/codex"
    fi

    if [[ -z "$codex_dir" ]]; then
        warn "Could not determine Codex config directory"
        return 0
    fi

    local scripts_dir="$codex_dir/scripts"

    info "Codex config directory: $codex_dir"
    mkdir -p "$scripts_dir"

    # Link plugin scripts for Codex to discover
    local target_scripts="$scripts_dir/pplx-plugin"
    if [[ -d "$target_scripts" ]]; then
        if [[ -L "$target_scripts" ]]; then
            rm "$target_scripts"
        else
            rm -rf "$target_scripts"
        fi
    fi
    ln -sf "$PPLX_PLUGIN_DIR/scripts" "$target_scripts"
    ok "Linked pplx-plugin scripts to Codex: $target_scripts"

    # Create env hints file
    local env_file="$codex_dir/.pplx-env"
    cat > "$env_file" <<EOF
# PPLX plugin environment for Codex
# Source this file or add these exports to your shell profile
export PPLX_REPO_DIR="$REPO_DIR"
export PPLX_PLUGIN_DIR="$PPLX_PLUGIN_DIR"
# export BWS_ACCESS_TOKEN=<your-bitwarden-secrets-manager-token>
# export PERPLEXITY_COOKIES_PATH=/path/to/cookies.json
EOF
    ok "Created Codex env hints: $env_file"

    installed=true
    ok "Codex plugin installation complete"
    info "Source $env_file or restart Codex CLI"
}

# -----------------------------------------------------------------------------
# Shell-native agents (generic)
# -----------------------------------------------------------------------------
install_shell() {
    info "Setting up for shell-native agents..."

    local shell_rc=""
    if [[ -f "$HOME/.zshrc" ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        shell_rc="$HOME/.bashrc"
    elif [[ -f "$HOME/.bash_profile" ]]; then
        shell_rc="$HOME/.bash_profile"
    fi

    if [[ -n "$shell_rc" ]]; then
        if ! grep -q "PPLX_REPO_DIR" "$shell_rc" 2>/dev/null; then
            info "Adding PPLX environment variables to $shell_rc"
            cat >> "$shell_rc" <<EOF

# PPLX (Perplexity AI) configuration
export PPLX_REPO_DIR="$REPO_DIR"
export PPLX_PLUGIN_DIR="$PPLX_PLUGIN_DIR"
# Add pplx CLI to PATH if installed in venv
if [[ -d "$REPO_DIR/.venv/bin" ]]; then
    export PATH="$REPO_DIR/.venv/bin:\$PATH"
fi
EOF
            ok "Added PPLX env vars and PATH to $shell_rc"
        else
            ok "PPLX env vars already in $shell_rc"
        fi
    fi

    ok "Shell-native agent setup complete"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
main() {
    info "Installing pplx-plugin for agent harnesses..."
    info "Plugin directory: $PPLX_PLUGIN_DIR"
    info "Target harness: $TARGET_HARNESS"
    echo ""

    case "$TARGET_HARNESS" in
        claude)
            install_claude
            ;;
        opencode)
            install_opencode
            ;;
        codex)
            install_codex
            ;;
        all)
            install_claude
            echo ""
            install_opencode
            echo ""
            install_codex
            echo ""
            install_shell
            ;;
        *)
            warn "Unknown harness: $TARGET_HARNESS"
            warn "Use: claude, opencode, codex, or all"
            return 1
            ;;
    esac

    echo ""
    ok "Plugin installation complete!"
    info "Restart your agent harness to load the plugin."
}

main
