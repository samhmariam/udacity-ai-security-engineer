#!/usr/bin/env bash
# =============================================================================
# setup_lab.sh — Northstar Research Agent Lab Environment Setup
#
# Run this script once on a fresh container to configure the full lab
# environment for students. Everything is installed system-wide so that
# all users in the container have access without activating a virtualenv.
#
# Usage (from the directory where you unzipped the lab package):
#   sudo bash setup_lab.sh
#
# What this script does:
#   1. Install system dependencies (Python 3, pip, curl, git)
#   2. Install Python packages system-wide
#   3. Install Ollama
#   4. Start the Ollama service
#   5. Pull the Mistral 7B model
#   6. Copy project files to /project
#   7. Initialize the ChromaDB knowledge base
#   8. Set permissions so students can write to output directories
#   9. Run a final verification check
# =============================================================================

set -e  # Exit immediately on any error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PATH="/project"
OLLAMA_MODEL="mistral:7b-instruct-v0.2-q4_0"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
section() { echo; echo -e "${GREEN}======================================${NC}"; echo -e "${GREEN}  $1${NC}"; echo -e "${GREEN}======================================${NC}"; }

# Ensure running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    error "Please run this script with sudo: sudo bash setup_lab.sh"
fi

section "Step 1 — System Dependencies"

info "Updating package index..."
sudo apt-get update -q

info "Installing system packages..."
sudo apt-get install -y -q \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    git \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev

info "Python version: $(python3 --version)"
info "pip version: $(pip3 --version)"

section "Step 2 — Python Packages"

info "Installing Python packages system-wide..."
sudo pip3 install --quiet --upgrade pip
sudo pip3 install --quiet \
    "pysqlite3-binary" \
    "chromadb>=0.5.0,<1.0.0" \
    "requests>=2.31.0" \
    "Pillow>=10.0.0" \
    "sentence-transformers>=2.2.0"

info "Verifying Python packages..."
python3 -c "
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb
print('  chromadb:', chromadb.__version__)
"
python3 -c "import requests; print('  requests:', requests.__version__)"
python3 -c "import PIL; print('  Pillow:', PIL.__version__)"
python3 -c "import sentence_transformers; print('  sentence-transformers:', sentence_transformers.__version__)"

section "Step 3 — Install Ollama"

if command -v ollama &>/dev/null; then
    info "Ollama already installed: $(ollama --version)"
else
    info "Downloading and installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sudo sh
    info "Ollama installed: $(ollama --version)"
fi

section "Step 4 — Start Ollama Service"

# Kill any existing ollama process
sudo pkill -f "ollama serve" 2>/dev/null || true
sleep 1

info "Starting Ollama service in the background..."
sudo nohup ollama serve > /var/log/ollama.log 2>&1 &
OLLAMA_PID=$!
sudo sh -c "echo $OLLAMA_PID > /var/run/ollama.pid"

info "Waiting for Ollama to become ready..."
MAX_WAIT=30
WAITED=0
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
    WAITED=$((WAITED + 1))
    if [ $WAITED -ge $MAX_WAIT ]; then
        error "Ollama did not start within ${MAX_WAIT} seconds. Check /var/log/ollama.log"
    fi
done
info "Ollama is ready (PID: $OLLAMA_PID)"

section "Step 5 — Pull Mistral 7B Model"

if sudo ollama list | grep -q "mistral:7b-instruct-v0.2-q4_0"; then
    info "Model already downloaded: $OLLAMA_MODEL"
else
    info "Pulling $OLLAMA_MODEL (~4.1 GB — this may take several minutes)..."
    sudo ollama pull "$OLLAMA_MODEL"
    info "Model downloaded successfully."
fi

sudo ollama list

section "Step 6 — Deploy Project Files"

info "Installing project files to $INSTALL_PATH ..."

if [ "$PROJECT_DIR" = "$INSTALL_PATH" ]; then
    info "Already running from $INSTALL_PATH — skipping copy."
else
    sudo mkdir -p "$INSTALL_PATH"
    sudo cp -r "$PROJECT_DIR"/. "$INSTALL_PATH/"
    info "Files copied to $INSTALL_PATH"
fi

# Create all student output directories
sudo mkdir -p "$INSTALL_PATH/student_work/attacks"
sudo mkdir -p "$INSTALL_PATH/student_work/defenses"
sudo mkdir -p "$INSTALL_PATH/student_work/reports"
sudo mkdir -p "$INSTALL_PATH/chroma_data"

section "Step 7 — Initialize ChromaDB Knowledge Base"

info "Loading Northstar knowledge base into ChromaDB..."
cd "$INSTALL_PATH"
sudo python3 load_knowledge_base.py

section "Step 8 — Set Permissions"

info "Setting permissions on student work directories..."
sudo chmod -R 777 "$INSTALL_PATH/student_work"
sudo chmod -R 777 "$INSTALL_PATH/chroma_data"
sudo chmod -R 755 "$INSTALL_PATH/knowledge_base"
sudo chmod -R 755 "$INSTALL_PATH/templates"
sudo chmod 644 "$INSTALL_PATH/northstar_agent.py"
sudo chmod 644 "$INSTALL_PATH/load_knowledge_base.py"

info "Permissions set."

section "Step 9 — Verification"

info "Running baseline agent demo..."
cd "$INSTALL_PATH"
sudo python3 northstar_agent.py --demo

echo
info "Checking Ollama model list..."
sudo ollama list

echo
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Lab setup complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo
echo "  Project location : $INSTALL_PATH"
echo "  Ollama model     : $OLLAMA_MODEL"
echo "  Ollama log       : /var/log/ollama.log"
echo
echo "  Students should start with:"
echo "    cat $INSTALL_PATH/README.docx   (or open README.docx)"
echo "    cat $INSTALL_PATH/PROJECT_GUIDE.md"
echo
echo "  To restart Ollama if needed:"
echo "    sudo pkill -f 'ollama serve'"
echo "    sudo nohup ollama serve > /var/log/ollama.log 2>&1 &"
echo
