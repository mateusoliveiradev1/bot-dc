#!/usr/bin/env python3
"""
Ponto de entrada principal do Hawk Bot.
Este arquivo permite executar o bot como um módulo Python.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path para imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from core.config import settings
from bot import HawkBot

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