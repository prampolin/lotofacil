#!/bin/bash
set -e

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH=".:$PYTHONPATH"
python3 backtesting/runner.py "$@"
