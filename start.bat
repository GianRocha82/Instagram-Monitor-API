@echo off
title Instagram Monitor API
echo ============================================
echo  Instagram Monitor API - Inicializacao
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Verificando Python...
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale Python 3.10+
    pause
    exit /b 1
)

echo.
echo [2/4] Criando/Ativando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    echo Ambiente virtual criado.
)

call venv\Scripts\activate.bat

echo.
echo [3/4] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias
    pause
    exit /b 1
)

echo.
echo [4/4] Iniciando servidor...
echo.
echo ============================================
echo  API rodando em: http://localhost:8000
echo  Pressione Ctrl+C para parar
echo ============================================
echo.

python -m app.main

pause