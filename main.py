#!/usr/bin/env python3
"""Ponto de entrada principal do Hawk Bot."""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path para imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from core.config.settings import settings
from src.bot import HawkBot  # Importa o bot da estrutura src

def main():
    """Função principal que inicializa o bot."""
    try:
        # Valida as configurações antes de iniciar
        settings.validate()
        
        # Inicializa e executa o bot
        hawk_bot = HawkBot()
        hawk_bot.run(settings.DISCORD_TOKEN)
        
    except Exception as e:
        print(f"Erro ao inicializar o bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()