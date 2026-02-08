#!/usr/bin/env bash
set -e

# Detect Python executable
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "❌ Python is not installed"
  exit 1
fi

echo "Using Python: $PYTHON"

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv .venv
fi

# Activate venv (Windows vs Unix)
if [ -f ".venv/Scripts/activate" ]; then
  echo "Activating virtual environment (Windows)..."
  source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
  echo "Activating virtual environment (Unix)..."
  source .venv/bin/activate
else
  echo "❌ Could not find virtual environment activation script"
  exit 1
fi

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Installing Playwright browser..."
playwright install chromium

echo "Running event checker..."
python src/check_events.py
