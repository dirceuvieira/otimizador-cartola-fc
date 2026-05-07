#!/bin/bash
# Script para executar a aplicação Streamlit

# Ativar ambiente virtual
source .venv/Scripts/activate

# Executar Streamlit
streamlit run app.py --logger.level=info