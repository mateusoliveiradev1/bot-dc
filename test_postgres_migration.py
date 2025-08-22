#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para migração PostgreSQL
Testa a funcionalidade do sistema de armazenamento PostgreSQL
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import json

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from postgres_storage import PostgreSQLStorage
from storage import DataStorage

async def test_postgres_connection():
    """Testa a conexão com PostgreSQL"""
    print("🔍 Testando conexão PostgreSQL...")
    
    # Verificar variáveis de ambiente
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("💡 Configure as variáveis de ambiente ou use o arquivo .env")
        return False
    
    try:
        storage = PostgreSQLStorage()
        await storage.initialize()
        print("✅ Conexão PostgreSQL estabelecida com sucesso!")
        await storage.close()
        return True
    except Exception as e:
        print(f"❌ Erro na conexão PostgreSQL: {e}")
        return False

async def test_data_migration():
    """Testa a migração de dados JSON para PostgreSQL"""
    print("\n🔄 Testando migração de dados...")
    
    # Criar dados de teste no formato JSON
    test_data = {
        "users": {
            "123456789": {
                "user_id": "123456789",
                "username": "TestUser",
                "total_sessions": 5,
                "total_time": 3600,
                "last_checkin": "2024-01-15T10:00:00",
                "current_session": None,
                "stats": {
                    "completed_sessions": 4,
                    "incomplete_sessions": 1,
                    "average_session_time": 720,
                    "longest_session": 1800,
                    "shortest_session": 300
                }
            }
        },
        "sessions": {
            "session_1": {
                "session_id": "session_1",
                "user_id": "123456789",
                "start_time": "2024-01-15T10:00:00",
                "end_time": "2024-01-15T11:00:00",
                "duration": 3600,
                "completed": True
            }
        },
        "bot_settings": {
            "checkin_channel": "987654321",
            "admin_role": "111111111",
            "timezone": "America/Sao_Paulo"
        }
    }
    
    # Salvar dados de teste em arquivo JSON temporário
    test_file = "test_data.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    try:
        # Testar migração
        storage = PostgreSQLStorage()
        await storage.initialize()
        
        # Migrar dados do arquivo de teste
        await storage.migrate_from_json(test_file)
        print("✅ Migração de dados concluída!")
        
        # Verificar se os dados foram migrados corretamente
        user_data = await storage.get_user_data("123456789")
        if user_data and user_data.get('username') == 'TestUser':
            print("✅ Dados de usuário migrados corretamente")
        else:
            print("❌ Erro na migração de dados de usuário")
        
        # Verificar configurações
        settings = await storage.get_all_bot_settings()
        if settings.get('checkin_channel') == '987654321':
            print("✅ Configurações migradas corretamente")
        else:
            print("❌ Erro na migração de configurações")
        
        await storage.close()
        
        # Limpar arquivo de teste
        os.remove(test_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

async def test_storage_operations():
    """Testa operações básicas do storage PostgreSQL"""
    print("\n🧪 Testando operações do storage...")
    
    try:
        storage = PostgreSQLStorage()
        await storage.initialize()
        
        # Teste 1: Criar/atualizar usuário
        test_user_id = "test_user_123"
        user_data = {
            "user_id": test_user_id,
            "username": "TestUser123",
            "total_sessions": 0,
            "total_time": 0
        }
        
        await storage.update_user_data(test_user_id, user_data)
        retrieved_data = await storage.get_user_data(test_user_id)
        
        if retrieved_data and retrieved_data.get('username') == 'TestUser123':
            print("✅ Operações de usuário funcionando")
        else:
            print("❌ Erro nas operações de usuário")
        
        # Teste 2: Configurações do bot
        await storage.set_bot_setting('test_setting', 'test_value')
        setting_value = await storage.get_bot_setting('test_setting')
        
        if setting_value == 'test_value':
            print("✅ Operações de configuração funcionando")
        else:
            print("❌ Erro nas operações de configuração")
        
        # Teste 3: Sessões
        session_id = await storage.start_session(test_user_id)
        if session_id:
            await storage.end_session(session_id, completed=True)
            print("✅ Operações de sessão funcionando")
        else:
            print("❌ Erro nas operações de sessão")
        
        await storage.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro nas operações: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes de migração PostgreSQL\n")
    
    # Teste 1: Conexão
    connection_ok = await test_postgres_connection()
    
    if not connection_ok:
        print("\n❌ Testes interrompidos - falha na conexão")
        return
    
    # Teste 2: Migração
    migration_ok = await test_data_migration()
    
    # Teste 3: Operações
    operations_ok = await test_storage_operations()
    
    # Resumo
    print("\n📊 Resumo dos testes:")
    print(f"   Conexão PostgreSQL: {'✅' if connection_ok else '❌'}")
    print(f"   Migração de dados: {'✅' if migration_ok else '❌'}")
    print(f"   Operações básicas: {'✅' if operations_ok else '❌'}")
    
    if all([connection_ok, migration_ok, operations_ok]):
        print("\n🎉 Todos os testes passaram! Sistema pronto para deploy.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique a configuração.")

if __name__ == "__main__":
    asyncio.run(main())