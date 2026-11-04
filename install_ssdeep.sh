#!/usr/bin/env bash
#
# install_ssdeep.sh - Automated installer for ssdeep library and Python bindings
#
# This script handles the complex installation of ssdeep, which requires both
# a system library (libfuzzy) and Python bindings that need to be compiled.
#
# Usage:
#   ./install_ssdeep.sh
#
# Supports: macOS (Homebrew), Debian/Ubuntu, Fedora/RHEL

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PYTHON_CMD=""

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    elif [[ -f /etc/redhat-release ]]; then
        echo "redhat"
    else
        echo "unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect Python interpreter (prefer active pyenv interpreter when available)
detect_python() {
    if command_exists pyenv; then
        if PYENV_PYTHON=$(pyenv which python 2>/dev/null); then
            PYTHON_CMD="$PYENV_PYTHON"
            print_info "Using pyenv Python: $PYTHON_CMD ($(pyenv version-name))"
            return 0
        fi
    fi

    if command_exists python3; then
        PYTHON_CMD="$(command -v python3)"
    elif command_exists python; then
        PYTHON_CMD="$(command -v python)"
    else
        print_error "Python not found. Please install Python 3 first."
        exit 1
    fi

    print_info "Using Python: $PYTHON_CMD"
}

# Install ssdeep system library on macOS
install_macos() {
    print_info "Detected macOS"
    
    if ! command_exists brew; then
        print_error "Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    print_info "Installing ssdeep via Homebrew..."
    if brew list ssdeep &>/dev/null; then
        print_info "ssdeep already installed via Homebrew"
    else
        brew install ssdeep
        print_info "ssdeep system library installed successfully"
    fi
    
    # Set compiler flags for Python installation
    BREW_PREFIX=$(brew --prefix)
    export CFLAGS="-I${BREW_PREFIX}/include"
    export LDFLAGS="-L${BREW_PREFIX}/lib"
}

# Install ssdeep system library on Debian/Ubuntu
install_debian() {
    print_info "Detected Debian/Ubuntu system"
    
    print_info "Installing build dependencies..."
    sudo apt-get update
    sudo apt-get install -y build-essential libffi-dev libssl-dev python3-dev
    
    # Check if ssdeep is available in repos
    if apt-cache show libfuzzy-dev &>/dev/null; then
        print_info "Installing ssdeep from repository..."
        sudo apt-get install -y libfuzzy-dev ssdeep
    else
        print_warning "ssdeep not in repositories, building from source..."
        install_from_source
    fi
}

# Install ssdeep system library on RedHat/Fedora
install_redhat() {
    print_info "Detected RedHat/Fedora system"
    
    print_info "Installing build dependencies..."
    sudo dnf install -y gcc make libffi-devel openssl-devel python3-devel
    
    # Check if ssdeep is available in repos
    if dnf list ssdeep-devel &>/dev/null; then
        print_info "Installing ssdeep from repository..."
        sudo dnf install -y ssdeep-devel ssdeep
    else
        print_warning "ssdeep not in repositories, building from source..."
        install_from_source
    fi
}

# Build ssdeep from source (fallback)
install_from_source() {
    print_info "Building ssdeep from source..."
    
    TMPDIR=$(mktemp -d)
    cd "$TMPDIR"
    
    print_info "Downloading ssdeep 2.14.1..."
    curl -L -o ssdeep.tar.gz https://github.com/ssdeep-project/ssdeep/releases/download/release-2.14.1/ssdeep-2.14.1.tar.gz
    
    print_info "Extracting..."
    tar xzf ssdeep.tar.gz
    cd ssdeep-2.14.1
    
    print_info "Configuring and building..."
    ./configure
    make
    sudo make install
    
    # Update library cache on Linux
    if [[ "$(detect_os)" != "macos" ]]; then
        sudo ldconfig
    fi
    
    cd -
    rm -rf "$TMPDIR"
    
    print_info "ssdeep built and installed from source"
}

# Install Python ssdeep package
install_python_package() {
    print_info "Installing Python ssdeep package..."

    detect_python

    if ! "$PYTHON_CMD" -m pip --version >/dev/null 2>&1; then
        print_error "pip is not available for $PYTHON_CMD"
        print_info "Install pip for this interpreter, then re-run this script."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    print_info "Using Python version: $PYTHON_VERSION"
    
    # Try to install the package
    print_info "Attempting to install Python ssdeep package..."

    # First, try regular pip install. If this fails with externally-managed-environment,
    # fall back to --user, then --break-system-packages.
    if ! INSTALL_OUTPUT=$("$PYTHON_CMD" -m pip install ssdeep 2>&1); then
        if echo "$INSTALL_OUTPUT" | grep -q "externally-managed-environment"; then
            print_warning "Externally managed Python environment detected"
            print_info "Trying with --user flag..."
            if ! "$PYTHON_CMD" -m pip install --user ssdeep; then
                print_warning "Failed with --user, trying --break-system-packages..."
                "$PYTHON_CMD" -m pip install --break-system-packages ssdeep
            fi
        else
            # pyenv + modern pip/setuptools can fail with ssdeep's legacy build metadata.
            # Retry on macOS with local build tooling and no build isolation.
            if [[ "$(detect_os)" == "macos" ]]; then
                print_warning "Initial install failed. Retrying with no build isolation..."
                "$PYTHON_CMD" -m pip install setuptools wheel six cffi

                BREW_PREFIX=$(brew --prefix)
                if CFLAGS="-I${BREW_PREFIX}/include" \
                   LDFLAGS="-L${BREW_PREFIX}/lib" \
                   CPPFLAGS="-I${BREW_PREFIX}/include" \
                   "$PYTHON_CMD" -m pip install --no-build-isolation ssdeep; then
                    print_info "Python ssdeep package installed successfully"
                    return 0
                fi
            fi

            print_error "Failed to install Python ssdeep package"
            echo "$INSTALL_OUTPUT"
            print_info "If you're using a virtual environment, activate it and run:"
            echo "  CFLAGS=\"-I\$(brew --prefix)/include\" LDFLAGS=\"-L\$(brew --prefix)/lib\" \"$PYTHON_CMD\" -m pip install --no-build-isolation ssdeep"
            exit 1
        fi
    fi
    
    print_info "Python ssdeep package installed successfully"
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    detect_python

    # Verify Python import
    if "$PYTHON_CMD" -c "import ssdeep; print('ssdeep version:', ssdeep.__version__)" 2>/dev/null; then
        print_info "✓ Python ssdeep package working correctly"
        return 0
    else
        print_error "✗ Python ssdeep package import failed"
        return 1
    fi
}

# Main installation flow
main() {
    echo ""
    print_info "ssdeep Installation Script for srtermtools"
    echo ""
    
    OS_TYPE=$(detect_os)
    
    case $OS_TYPE in
        macos)
            install_macos
            ;;
        debian)
            install_debian
            ;;
        redhat)
            install_redhat
            ;;
        *)
            print_error "Unsupported operating system: $OSTYPE"
            print_info "Please install ssdeep manually:"
            echo "  1. Install libfuzzy/ssdeep system library"
            echo "  2. Run: python3 -m pip install ssdeep"
            exit 1
            ;;
    esac
    
    echo ""
    install_python_package
    
    echo ""
    if verify_installation; then
        echo ""
        print_info "════════════════════════════════════════"
        print_info "  ssdeep installation completed! ✓"
        print_info "════════════════════════════════════════"
        echo ""
    else
        echo ""
        print_error "════════════════════════════════════════"
        print_error "  Installation verification failed"
        print_error "════════════════════════════════════════"
        echo ""
        print_info "Troubleshooting tips:"
        echo "  1. Make sure you have development tools installed"
        echo "  2. Check that ssdeep headers are in your include path"
        echo "  3. For macOS: export CFLAGS=\"-I\$(brew --prefix)/include\" LDFLAGS=\"-L\$(brew --prefix)/lib\""
        echo "  4. Try installing in a virtual environment:"
        echo "     python3 -m venv venv"
        echo "     source venv/bin/activate"
        echo "     python -m pip install ssdeep"
        exit 1
    fi
}

# Run main function
main
