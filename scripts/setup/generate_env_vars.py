#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Variáveis de Ambiente para Deploy no Render
Hawk Esports Bot - Deploy Automático
"""

def generate_render_env_vars():
    """Gera as variáveis de ambiente completas para o Render"""
    
    # Discord token já configurado
    discord_token = "MTQwODE1NTczNTQ1MTM2OTUzNA.GUEGAW.umvZoNwDCiLZlTnM67sEsc5XpZh5qbuzktBBvw"
    
    env_vars = f"""
# ============================================================
# VARIÁVEIS DE AMBIENTE PARA RENDER - HAWK ESPORTS BOT
# ============================================================
# Cole estas variáveis no painel do Render (Environment Variables)

# 🤖 DISCORD BOT
DISCORD_TOKEN={discord_token}

# 🗄️ BANCO DE DADOS SUPABASE (SUBSTITUA COM SEUS DADOS)
DATABASE_URL=postgresql://postgres:[SUA_SENHA]@db.[SEU_PROJECT_ID].supabase.co:5432/postgres

# 🎮 PUBG API (Opcional - deixe vazio se não usar)
PUBG_API_KEY=

# 🏆 MEDAL.TV API (Opcional - deixe vazio se não usar)
MEDAL_API_KEY=

# ⚙️ CONFIGURAÇÕES GERAIS
BOT_PREFIX=!
DEBUG=false
RENDER=true
TIMEZONE=America/Sao_Paulo
LOG_LEVEL=INFO

# 🌐 WEB DASHBOARD (Opcional)
WEB_PORT=10000
WEB_HOST=0.0.0.0

# ============================================================
# PRÓXIMOS PASSOS:
# ============================================================
# 1. Crie um projeto no Supabase (https://supabase.com)
# 2. Execute o SQL do arquivo 'supabase_setup.sql' no SQL Editor
# 3. Copie a connection string do Supabase
# 4. Substitua DATABASE_URL acima com sua connection string
# 5. Cole todas as variáveis no Render
# 6. Faça o deploy!
# ============================================================
"""
    
    return env_vars

def main():
    print("🤖 HAWK ESPORTS BOT - GERADOR DE VARIÁVEIS DE AMBIENTE")
    print("=" * 60)
    
    # Gerar variáveis
    env_vars = generate_render_env_vars()
    
    # Salvar em arquivo
    with open("RENDER_ENV_VARS_FINAL.txt", "w", encoding="utf-8") as f:
        f.write(env_vars)
    
    print("✅ Variáveis de ambiente geradas com sucesso!")
    print("📁 Arquivo salvo: RENDER_ENV_VARS_FINAL.txt")
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("1. 🗄️  Crie um projeto no Supabase (https://supabase.com)")
    print("2. 📝  Execute o SQL do arquivo 'supabase_setup.sql'")
    print("3. 🔗  Copie a connection string do Supabase")
    print("4. 📋  Abra o arquivo RENDER_ENV_VARS_FINAL.txt")
    print("5. ✏️   Substitua DATABASE_URL com sua connection string")
    print("6. 🚀  Cole todas as variáveis no Render e faça o deploy!")
    print()
    print("💡 Seu bot estará online em 5 minutos após o deploy!")

if __name__ == "__main__":
    main()