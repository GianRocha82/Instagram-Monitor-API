#!/bin/bash
# Instagram Monitor API - Startup Script for Unix/Linux/macOS

set -e

echo "============================================"
echo "  Instagram Monitor API - Inicialização"
echo "============================================"
echo

# Check Python
echo "[1/4] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado. Instale Python 3.10+"
    exit 1
fi
python3 --version

# Create/activate virtual environment
echo
echo "[2/4] Criando/Ativando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Ambiente virtual criado."
fi

source venv/bin/activate

# Install dependencies
echo
echo "[3/4] Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependências"
    exit 1
fi

# Start server
echo
echo "[4/4] Iniciando servidor..."
echo
echo "============================================"
echo "  API rodando em: http://localhost:8000"
echo "  Pressione Ctrl+C para parar"
echo "============================================"
echo

python -m app.main