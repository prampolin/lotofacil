#!/bin/bash
source venv/bin/activate

# Silencia o aviso chato do LibreSSL/OpenSSL no Mac
export PYTHONWARNINGS="ignore"

# Inicia o menu interativo
python main.py
