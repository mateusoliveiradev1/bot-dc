#!/usr/bin/env python3
"""Arquivo principal para deploy no Render."""

import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def main():
    """Função principal que inicializa o bot com configurações do Render."""
    try:
        # Configurar porta do Render
        port = int(os.environ.get('PORT', 10000))
        os.environ['WEB_PORT'] = str(port)
        
        # Importa e executa o bot
        from bot import bot
        
        # Verificar token
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("DISCORD_TOKEN não encontrado!")
            sys.exit(1)
        
        print(f"Iniciando bot na porta {port}...")
        
        # Executar bot
        bot.run(token)
        
    except Exception as e:
        print(f"Erro ao inicializar o bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()