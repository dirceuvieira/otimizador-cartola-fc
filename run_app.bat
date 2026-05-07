@echo off
REM Script para executar a aplicação Streamlit no Windows

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Executar Streamlit
streamlit run app.py --logger.level=info

pause