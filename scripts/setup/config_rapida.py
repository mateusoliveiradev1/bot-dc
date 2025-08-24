#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURACAO RAPIDA - HAWK ESPORTS BOT
Script para configurar variaveis do Supabase rapidamente
""""

def configure_supabase():
    print("🔧 CONFIGURAÇÃO RÁPIDA DO SUPABASE")
    print("=" * 40)
    
    project_ref = input("Project Reference (ex: abcdefghijklmnop): ").strip()
    anon_key = input("Anon Key: ").strip()
    
    if not project_ref or not anon_key:
        print("❌ Dados obrigatórios não fornecidos!")
        return
    
    # Atualizar .env
    with open('.env', 'r') as f:
        content = f.read()
    
    content = content.replace('SEU_PROJECT_REF', project_ref)
    content = content.replace('SUA_ANON_KEY', anon_key)
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("
✅ Configuração atualizada!")
    print(f"🗄️  Database: postgresql://postgres:HawkBot2024!@#@db.{project_ref}.supabase.co:5432/postgres")
    print(f"🌐 Supabase: https://{project_ref}.supabase.co")
    print("
🚀 Agora faça o deploy no Render!")

if __name__ == "__main__":
    configure_supabase()
