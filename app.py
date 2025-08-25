#!/usr/bin/env python3
"""Arquivo principal para deploy no Render."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Adiciona o diretório src ao path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def main():
    """Função principal que inicializa o bot com configurações do Render."""
    try:
        # Configurar porta do Render
        port = int(os.environ.get('PORT', 10000))
        os.environ['WEB_PORT'] = str(port)
        os.environ['RENDER'] = 'true'  # Flag para indicar ambiente Render
        
        print(f"🚀 Iniciando Hawk Bot no Render...")
        print(f"📡 Porta configurada: {port}")
        
        # Verificar token
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
            sys.exit(1)
        
        print(f"✅ Token encontrado: {token[:20]}...")
        
        # Importa e executa o bot
        print("📦 Importando módulo do bot...")
        from bot import bot
        
        print("🎯 Executando bot...")
        # Executar bot
        bot.run(token)
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("📁 Tentando importação alternativa...")
        try:
            # Importação alternativa
            import bot as bot_module
            bot_module.main()
        except Exception as e2:
            print(f"❌ Erro na importação alternativa: {e2}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao inicializar o bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()