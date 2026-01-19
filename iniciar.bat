@echo off
TITLE Sistema de Gestao de PII
CLS

echo INICIANDO O SISTEMA...
echo ---------------------

:: 1. Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    echo Instale o Python do site python.org.
    pause
    exit /b
)

:: 2. Cria Ambiente Virtual
if not exist venv (
    echo [1/4] Criando ambiente virtual...
    python -m venv venv
)

:: 3. Ativa Ambiente
echo [2/4] Ativando ambiente...
call venv\Scripts\activate

:: 4. Instala Dependencias
echo [3/4] Instalando bibliotecas (isso pode demorar)...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 5. Verifica IA
echo [4/4] Verificando modelo de inteligencia artificial...
python -c "import spacy; spacy.load('pt_core_news_lg')" >nul 2>&1
if %errorlevel% neq 0 (
    echo Baixando modelo de linguagem...
    python -m spacy download pt_core_news_lg
)

:: 6. Inicia
echo.
echo TUDO PRONTO. O SISTEMA VAI ABRIR AGORA.
echo ---------------------------------------
streamlit run app.py

pause