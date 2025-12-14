#!/bin/bash

# Readers-Writers Simulation Launcher
# For Ubuntu/Debian/Arch Linux

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Readers-Writers Synchronization System"
    echo "=========================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[*] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_error() {
    echo -e "${RED}[!] $1${NC}"
}

check_python() {
    print_step "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 1 ]]; then
            print_success "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python3 not found"
        return 1
    fi
}

check_venv() {
    print_step "Checking virtual environment..."
    if [ -d "venv" ]; then
        print_success "Virtual environment found"
        return 0
    else
        print_step "Creating virtual environment..."
        python3 -m venv venv
        if [ $? -eq 0 ]; then
            print_success "Virtual environment created"
            return 0
        else
            print_error "Failed to create virtual environment"
            return 1
        fi
    fi
}

activate_venv() {
    print_step "Activating virtual environment..."
    source venv/bin/activate
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated"
        return 0
    else
        print_error "Failed to activate virtual environment"
        return 1
    fi
}

install_dependencies() {
    print_step "Installing dependencies..."
    pip install PyQt6 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed"
        return 0
    else
        print_error "Failed to install dependencies"
        return 1
    fi
}

check_dependencies() {
    print_step "Checking dependencies..."
    if python3 -c "import PyQt6" 2>/dev/null; then
        print_success "PyQt6 is installed"
        return 0
    else
        print_step "PyQt6 not found, installing..."
        install_dependencies
        return $?
    fi
}

run_application() {
    print_step "Starting application..."
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Application Starting..."
    echo "  Close the window to exit"
    echo "=========================================="
    echo -e "${NC}"
    
    python3 main.py
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        print_success "Application closed successfully"
    else
        print_error "Application exited with code $EXIT_CODE"
    fi
    
    return $EXIT_CODE
}

cleanup() {
    print_step "Deactivating virtual environment..."
    deactivate 2>/dev/null
    print_success "Cleanup complete"
}

main() {
    print_header
    
    # Check Python
    if ! check_python; then
        exit 1
    fi
    
    # Setup virtual environment
    if ! check_venv; then
        exit 1
    fi
    
    # Activate virtual environment
    if ! activate_venv; then
        exit 1
    fi
    
    # Check/install dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Run application
    run_application
    APP_EXIT=$?
    
    # Cleanup
    cleanup
    
    exit $APP_EXIT
}

# Handle script interruption
trap 'print_error "Interrupted"; cleanup; exit 1' INT

# Run main function
main