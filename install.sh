#!/usr/bin/env bash
# ULTRAMAN Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/the1frombeyond/ultraman/main/install.sh | bash
#
# Safe • Idempotent • Production-Ready • Self-Healing
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
REPO="the1frombeyond/ultraman"
REPO_URL="https://github.com/${REPO}"
CURL_OPTS="-fSL --connect-timeout 10 --max-time 120"
MAX_RETRIES=3

# Resolve real user home (safe under sudo)
if [ -n "${SUDO_USER:-}" ]; then
    REAL_USER="$SUDO_USER"
    USER_HOME="$(eval echo "~${SUDO_USER}")"
elif [ -n "${USER:-}" ]; then
    REAL_USER="$USER"
    USER_HOME="$HOME"
else
    REAL_USER=""
    USER_HOME="$HOME"
fi

INSTALL_DIR="${USER_HOME}/.ultraman"
BIN_DIR="${USER_HOME}/.local/bin"
WRAPPER="$BIN_DIR/ultraman"
RELEASE_BASE="${REPO_URL}/releases/latest/download"

# ──────────────────────────────────────────────────────────────────────
# Colors & Helpers
# ──────────────────────────────────────────────────────────────────────
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
DIM='\033[2m'
RESET='\033[0m'

log()      { echo -e "${BLUE}▸${RESET} $1"; }
success()  { echo -e "${GREEN}✓${RESET} $1"; }
warn()     { echo -e "${YELLOW}⚠${RESET} $1"; }
err()      { echo -e "${RED}✗${RESET} $1" >&2; }
dim()      { echo -e "${DIM}  $1${RESET}"; }
info()     { echo -e "${BLUE}  $1${RESET}"; }

die() {
    err "$1"
    [ -n "${2:-}" ] && dim "$2"
    exit 1
}

# ──────────────────────────────────────────────────────────────────────
# 1. OS Detection
# ──────────────────────────────────────────────────────────────────────
detect_os() {
    local os
    os="$(uname -s)"
    case "$os" in
        Linux*)   echo "linux" ;;
        Darwin*)  echo "macos" ;;
        *)
            die "Unsupported OS: $os" "ULTRAMAN requires Linux or macOS."
            ;;
    esac
}

# ──────────────────────────────────────────────────────────────────────
# 2. Dependency Checks
# ──────────────────────────────────────────────────────────────────────
check_deps() {
    local os="$1"
    local missing=()

    for cmd in curl git python3; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        err "Missing required dependencies: ${missing[*]}"
        echo ""
        case "$os" in
            linux)
                dim "Install with one of:"
                dim "  Ubuntu/Debian:  sudo apt install ${missing[*]}"
                dim "  Fedora/RHEL:    sudo dnf install ${missing[*]}"
                dim "  Arch:           sudo pacman -S ${missing[*]}"
                dim "  Alpine:         sudo apk add ${missing[*]}"
                ;;
            macos)
                dim "Install with:"
                dim "  brew install ${missing[*]}"
                dim "  Or: xcode-select --install"
                ;;
        esac
        exit 1
    fi
}

# ──────────────────────────────────────────────────────────────────────
# 3. Download with Retry + Exponential Backoff
# ──────────────────────────────────────────────────────────────────────
download_with_retry() {
    local url="$1"
    local dest="$2"
    local attempt=0

    while [ $attempt -lt $MAX_RETRIES ]; do
        attempt=$((attempt + 1))
        info "  Attempt $attempt/$MAX_RETRIES → $(basename "$url")"
        local rc=0
        local tmp_out
        tmp_out="$(mktemp)"

        if curl $CURL_OPTS -o "$dest" -w '%{http_code}' "$url" 2>"$tmp_out"; then
            rm -f "$tmp_out"
            return 0
        else
            local err_msg
            err_msg="$(cat "$tmp_out" 2>/dev/null || echo "unknown")"
            rm -f "$tmp_out"
            rm -f "$dest"
            dim "  Failed: ${err_msg}"
        fi

        if [ $attempt -lt $MAX_RETRIES ]; then
            local delay=$((2 ** attempt))
            dim "  Retrying in ${delay}s..."
            sleep "$delay"
        fi
    done

    return 1
}

# ──────────────────────────────────────────────────────────────────────
# 4. Release Asset Candidates
# ──────────────────────────────────────────────────────────────────────
get_asset_candidates() {
    local os="$1"
    if [ "$os" = "linux" ]; then
        echo -e "ultraman-linux\nultraman\nultraman-x86_64"
    else
        echo -e "ultraman-macos\nultraman-darwin\nultraman"
    fi
}

# ──────────────────────────────────────────────────────────────────────
# 5. Download Logic — Binary → Source Fallback
# ──────────────────────────────────────────────────────────────────────
try_download_binary() {
    local os="$1"
    local bin_dest="$INSTALL_DIR/ultraman"
    local candidates
    candidates="$(get_asset_candidates "$os")"

    while IFS= read -r asset; do
        [ -z "$asset" ] && continue
        local url="${RELEASE_BASE}/${asset}"

        log "Trying release asset: ${asset}..."
        if download_with_retry "$url" "$bin_dest"; then
            if [ -s "$bin_dest" ]; then
                chmod +x "$bin_dest"
                success "Downloaded binary: ${asset}"
                echo "binary"
                return 0
            else
                rm -f "$bin_dest"
                dim "  Asset '${asset}' downloaded but empty — skipping"
            fi
        else
            rm -f "$bin_dest"
        fi
    done <<< "$candidates"

    return 1
}

# ──────────────────────────────────────────────────────────────────────
# 6. Git Source Fallback (self-healing)
# ──────────────────────────────────────────────────────────────────────
install_from_source() {
    local clone_dir="$INSTALL_DIR/src"

    warn "Pre-built binary unavailable. Installing from source..."

    if [ -d "$clone_dir/.git" ]; then
        log "Updating existing clone..."
        if ! git -C "$clone_dir" pull --rebase --quiet 2>/dev/null; then
            warn "Git pull failed — repo may be inconsistent. Re-cloning cleanly..."
            rm -rf "$clone_dir"
            git clone --depth 1 "$REPO_URL.git" "$clone_dir"
        fi
    else
        if [ -d "$clone_dir" ]; then
            warn "Stale source directory found — cleaning up..."
            rm -rf "$clone_dir"
        fi
        log "Cloning repository..."
        if ! git clone --depth 1 "$REPO_URL.git" "$clone_dir"; then
            die "Failed to clone repository" "Check network access to ${REPO_URL}"
        fi
    fi

    # Verify critical file
    if [ ! -f "$clone_dir/main.py" ]; then
        warn "main.py missing after clone — attempting fresh re-clone..."
        rm -rf "$clone_dir"
        if ! git clone --depth 1 "$REPO_URL.git" "$clone_dir"; then
            die "Repository does not contain main.py" "Please file an issue at ${REPO_URL}/issues"
        fi
        if [ ! -f "$clone_dir/main.py" ]; then
            die "main.py still missing after re-clone" "Repository structure may have changed."
        fi
    fi

    # Create self-healing launcher
    cat > "$INSTALL_DIR/ultraman" << 'PYWRAP'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
MAIN_PY="$SRC_DIR/main.py"

# Self-healing: re-clone if main.py is missing
if [ ! -f "$MAIN_PY" ]; then
    echo "ULTRAMAN: main.py missing — re-cloning source..." >&2
    rm -rf "$SRC_DIR"
    if command -v git &>/dev/null; then
        git clone --depth 1 "https://github.com/the1frombeyond/ultraman.git" "$SRC_DIR" || true
    fi
    if [ ! -f "$MAIN_PY" ]; then
        echo "Error: Still unable to locate main.py." >&2
        echo "Re-run the installer:" >&2
        echo "  curl -fsSL https://raw.githubusercontent.com/the1frombeyond/ultraman/main/install.sh | bash" >&2
        exit 1
    fi
fi

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not installed." >&2
    exit 1
fi

exec python3 "$MAIN_PY" "$@"
PYWRAP

    chmod +x "$INSTALL_DIR/ultraman"
    success "Python fallback installed (src/main.py)"
    echo "python"
}

download_ultraman() {
    local os="$1"
    mkdir -p "$INSTALL_DIR"

    if try_download_binary "$os"; then
        return
    fi

    install_from_source
}

# ──────────────────────────────────────────────────────────────────────
# 7. Global Command Wrapper (self-verifying)
# ──────────────────────────────────────────────────────────────────────
install_wrapper() {
    mkdir -p "$BIN_DIR"

    if [ -f "$WRAPPER" ]; then
        if grep -qF '.ultraman/ultraman' "$WRAPPER" 2>/dev/null; then
            dim "Command already linked: $WRAPPER"
            return
        fi
        warn "Unexpected content in $WRAPPER — replacing with ULTRAMAN wrapper"
    fi

    cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/usr/bin/env bash
# ULTRAMAN — Auto-generated wrapper (install.sh)
set -euo pipefail

BIN="$HOME/.ultraman/ultraman"

if [ ! -f "$BIN" ]; then
    echo "Error: ULTRAMAN binary not found at $BIN" >&2
    echo "" >&2
    echo "Re-run the installer:" >&2
    echo "  curl -fsSL https://raw.githubusercontent.com/the1frombeyond/ultraman/main/install.sh | bash" >&2
    exit 1
fi

exec "$BIN" "$@"
WRAPPER_EOF

    chmod +x "$WRAPPER"
    success "Command linked: ultraman → $INSTALL_DIR/ultraman"
}

# ──────────────────────────────────────────────────────────────────────
# 8. PATH Handling (shell-aware, strict no-duplicates)
# ──────────────────────────────────────────────────────────────────────
ensure_path() {
    case ":${PATH}:" in
        *:"${BIN_DIR}":*) return ;;
    esac

    local entry='export PATH="$HOME/.local/bin:$PATH"'
    local marker="# ULTRAMAN PATH"

    # Detect shell config file
    local shell_name="${SHELL##*/}"
    local rc_files=()
    case "$shell_name" in
        zsh)    rc_files=("$HOME/.zshrc") ;;
        fish)   rc_files=("$HOME/.config/fish/config.fish") ;;
        *)      rc_files=("$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc") ;;
    esac

    local added=false

    for rc in "${rc_files[@]}"; do
        local rc_dir
        rc_dir="$(dirname "$rc")"
        if [ -f "$rc" ] || [ -w "$rc_dir" ]; then
            if ! grep -qF "$marker" "$rc" 2>/dev/null; then
                echo "" >> "$rc"
                echo "$marker" >> "$rc"
                echo "$entry" >> "$rc"
                if [ "$added" = false ]; then
                    dim "Added ~/.local/bin to PATH in $(basename "$rc")"
                    added=true
                fi
            fi
        fi
    done

    if [ "$added" = true ]; then
        warn "Restart your terminal or run:"
        dim "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# ──────────────────────────────────────────────────────────────────────
# 9. First-Run Defaults (strictly idempotent)
# ──────────────────────────────────────────────────────────────────────
init_config() {
    local cfg="$INSTALL_DIR/config.yaml"
    if [ -f "$cfg" ]; then
        dim "Config exists: $cfg (preserved)"
        return
    fi

    cat > "$cfg" << 'CFG'
version: 1
mode: stable
ollama_host: http://127.0.0.1:11434
CFG

    success "Created default config"
}

# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────
main() {
    echo ""
    log "Installing ULTRAMAN..."
    if [ -n "$REAL_USER" ]; then
        dim "Installing for user: ${REAL_USER} (home: ${USER_HOME})"
    fi
    echo ""

    local os
    os="$(detect_os)"

    check_deps "$os"

    local mode
    mode="$(download_ultraman "$os")"

    install_wrapper
    ensure_path
    init_config

    echo ""
    success "ULTRAMAN installed successfully!"
    echo ""
    echo "  Run:"
    echo -e "    ${GREEN}ultraman${RESET}"
    echo ""

    if [ "$mode" = "python" ]; then
        warn "Running in Python mode (no pre-built binary found)"
        dim "Requires: ollama serve  (https://ollama.com)"
        echo ""
    fi
}

main "$@"
