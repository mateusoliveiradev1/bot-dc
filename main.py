#!/usr/bin/env python3
"""Ponto de entrada principal do Hawk Bot."""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path para imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def main():
    """Função principal que inicializa o bot."""
    try:
        # Importa e executa o bot diretamente
        from bot import bot
        
        # Verificar token
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("DISCORD_TOKEN não encontrado no arquivo .env!")
            sys.exit(1)
        
        # Executar bot
        bot.run(token)
        
    except Exception as e:
        print(f"Erro ao inicializar o bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()