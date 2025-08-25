#!/bin/bash
# Script de inicialização para Render
echo "🚀 Iniciando Hawk Bot no Render..."
echo "📁 Diretório atual: $(pwd)"
echo "📋 Listando arquivos:"
ls -la
echo "🐍 Versão do Python: $(python --version)"
echo "📦 Instalando dependências..."
pip install -r requirements.txt
echo "🤖 Iniciando bot..."
python main.py