#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir a DATABASE_URL do Supabase
Substitui SEU_PROJECT_REF pela referência real do projeto
"""

import os
import re
from datetime import datetime

def corrigir_database_url():
    """
    Corrige a DATABASE_URL no arquivo .env
    """
    print("🔧 CORREÇÃO DA DATABASE_URL")
    print("=" * 50)
    
    # Ler arquivo .env atual
    env_path = '.env'
    if not os.path.exists(env_path):
        print("❌ Arquivo .env não encontrado!")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📋 DATABASE_URL atual:")
    # Encontrar a linha da DATABASE_URL
    database_line = None
    for line in content.split('\n'):
        if line.startswith('DATABASE_URL='):
            database_line = line
            break
    
    if database_line:
        print(f"   {database_line}")
    else:
        print("   ❌ DATABASE_URL não encontrada no .env")
        return False
    
    print("\n📝 Para corrigir, você precisa:")
    print("1. Ir ao seu projeto no Supabase (https://supabase.com/dashboard)")
    print("2. Clicar em 'Settings' → 'Database'")
    print("3. Copiar a 'Connection string' (URI)")
    print("4. Colar aqui quando solicitado")
    
    print("\n💡 Exemplo de URL correta:")
    print("   postgresql://postgres:SuaSenha@db.abcdefghijk.supabase.co:5432/postgres")
    
    # Solicitar a URL correta
    print("\n" + "="*50)
    nova_url = input("🔗 Cole sua DATABASE_URL completa do Supabase: ").strip()
    
    if not nova_url:
        print("❌ URL não fornecida. Operação cancelada.")
        return False
    
    # Validar formato básico
    if not nova_url.startswith('postgresql://') or 'supabase.co' not in nova_url:
        print("⚠️  URL parece incorreta. Continuando mesmo assim...")
    
    # Substituir no conteúdo
    novo_content = re.sub(
        r'DATABASE_URL=.*',
        f'DATABASE_URL={nova_url}',
        content
    )
    
    # Salvar arquivo
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(novo_content)
    
    print("\n✅ DATABASE_URL atualizada com sucesso!")
    print(f"📁 Arquivo .env salvo em: {os.path.abspath(env_path)}")
    
    # Mostrar resultado
    print("\n📋 Nova DATABASE_URL:")
    print(f"   DATABASE_URL={nova_url}")
    
    return True

def extrair_info_supabase(database_url):
    """
    Extrai informações da DATABASE_URL para configurar outras variáveis
    """
    try:
        # Regex para extrair componentes da URL
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, database_url)
        
        if match:
            user, password, host, port, database = match.groups()
            
            # Extrair project_ref do host
            project_ref = host.replace('db.', '').replace('.supabase.co', '')
            
            return {
                'DB_USER': user,
                'DB_PASSWORD': password,
                'DB_HOST': host,
                'DB_PORT': port,
                'DB_NAME': database,
                'PROJECT_REF': project_ref,
                'SUPABASE_URL': f'https://{project_ref}.supabase.co'
            }
    except Exception as e:
        print(f"⚠️  Erro ao extrair informações: {e}")
    
    return None

def atualizar_variaveis_supabase():
    """
    Atualiza todas as variáveis relacionadas ao Supabase
    """
    env_path = '.env'
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar DATABASE_URL
    database_url = None
    for line in content.split('\n'):
        if line.startswith('DATABASE_URL='):
            database_url = line.split('=', 1)[1]
            break
    
    if not database_url or 'SEU_PROJECT_REF' in database_url:
        print("❌ DATABASE_URL ainda não foi configurada corretamente.")
        return False
    
    # Extrair informações
    info = extrair_info_supabase(database_url)
    if not info:
        print("❌ Não foi possível extrair informações da DATABASE_URL.")
        return False
    
    print("\n🔄 Atualizando variáveis do Supabase...")
    
    # Atualizar variáveis no conteúdo
    updates = {
        'SUPABASE_URL': info['SUPABASE_URL'],
        'DB_HOST': info['DB_HOST'],
        'DB_USER': info['DB_USER'],
        'DB_PASSWORD': info['DB_PASSWORD'],
        'DB_PORT': info['DB_PORT'],
        'DB_NAME': info['DB_NAME']
    }
    
    for var, value in updates.items():
        # Substituir se existir, adicionar se não existir
        if f'{var}=' in content:
            content = re.sub(f'{var}=.*', f'{var}={value}', content)
        else:
            # Adicionar após a seção do Supabase
            if '# Supabase' in content:
                content = content.replace(
                    '# Supabase (Configure após criar projeto)',
                    f'# Supabase (Configure após criar projeto)\n{var}={value}'
                )
    
    # Salvar arquivo
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Todas as variáveis do Supabase foram atualizadas!")
    
    print("\n📋 Variáveis configuradas:")
    for var, value in updates.items():
        print(f"   {var}={value}")
    
    return True

if __name__ == "__main__":
    print("🚀 HAWK ESPORTS BOT - Correção Database URL")
    print("=" * 50)
    
    if corrigir_database_url():
        print("\n" + "="*50)
        resposta = input("\n🔄 Deseja atualizar automaticamente as outras variáveis do Supabase? (s/n): ").lower()
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            atualizar_variaveis_supabase()
        
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("\n📋 Próximos passos:")
        print("1. Verifique se o arquivo .env está correto")
        print("2. Faça commit das alterações para o GitHub")
        print("3. Configure as variáveis no Render")
        print("4. Faça o deploy!")
        
        print(f"\n⏰ Configuração realizada em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    else:
        print("\n❌ Configuração não realizada.")
        print("\n💡 Dica: Certifique-se de ter a DATABASE_URL correta do Supabase.")