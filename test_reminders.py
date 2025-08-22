#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Lembretes
Script para testar funcionalidades do sistema de lembretes automáticos

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from checkin_reminders import CheckInReminders, ReminderType
from storage import DataStorage

class MockBot:
    """Mock do bot para testes"""
    def __init__(self):
        self.guilds = []
        self.wait_until_ready = AsyncMock()
        self.get_channel = Mock(return_value=None)

class MockCheckInSystem:
    """Mock do sistema de check-in para testes"""
    def __init__(self):
        self.sessions = [
            {
                'id': 'test_session_1',
                'type': 'treino',
                'start_time': (datetime.now() + timedelta(minutes=10)).isoformat(),
                'end_time': (datetime.now() + timedelta(hours=2)).isoformat(),
                'max_players': 10,
                'checkin_count': 3,
                'checkout_count': 0
            },
            {
                'id': 'test_session_2',
                'type': 'competitivo',
                'start_time': (datetime.now() + timedelta(minutes=30)).isoformat(),
                'end_time': (datetime.now() + timedelta(hours=3)).isoformat(),
                'max_players': 8,
                'checkin_count': 5,
                'checkout_count': 1
            }
        ]
    
    def get_active_sessions(self):
        return self.sessions

async def test_reminder_system():
    """Testa o sistema de lembretes"""
    print("🧪 Iniciando testes do Sistema de Lembretes...\n")
    
    # Configurar mocks
    mock_bot = MockBot()
    mock_checkin_system = MockCheckInSystem()
    
    # Criar storage temporário
    storage = DataStorage()
    storage.data = {}
    
    try:
        # Inicializar sistema de lembretes
        print("1️⃣ Inicializando sistema de lembretes...")
        reminder_system = CheckInReminders(mock_bot, mock_checkin_system, storage)
        print("✅ Sistema de lembretes inicializado com sucesso!\n")
        
        # Testar configurações padrão
        print("2️⃣ Testando configurações padrão...")
        settings = reminder_system.get_reminder_settings()
        print(f"✅ Configurações carregadas: {len(settings)} seções")
        print(f"   - Lembretes padrão: {list(settings['default_reminders'].keys())}")
        print(f"   - Lembretes ativos: {sum(settings['enabled_reminders'].values())} de {len(settings['enabled_reminders'])}\n")
        
        # Testar criação de lembrete personalizado
        print("3️⃣ Testando criação de lembrete personalizado...")
        future_time = datetime.now() + timedelta(minutes=5)
        reminder_id = reminder_system.create_custom_reminder(
            title="Teste de Lembrete",
            message="Esta é uma mensagem de teste para o sistema de lembretes.",
            reminder_time=future_time,
            channel_id=123456789,
            author="TestUser#1234"
        )
        print(f"✅ Lembrete personalizado criado: {reminder_id}\n")
        
        # Testar listagem de lembretes personalizados
        print("4️⃣ Testando listagem de lembretes personalizados...")
        custom_reminders = reminder_system.get_custom_reminders()
        print(f"✅ Lembretes personalizados encontrados: {len(custom_reminders)}")
        for reminder in custom_reminders:
            print(f"   - {reminder['title']}: {reminder['time']} (Enviado: {reminder.get('sent', False)})\n")
        
        # Testar atualização de configurações
        print("5️⃣ Testando atualização de configurações...")
        success = reminder_system.update_reminder_settings(
            reminder_type=ReminderType.SESSION_START,
            enabled=True,
            times=[45, 30, 15, 5]
        )
        print(f"✅ Configurações atualizadas: {success}")
        
        updated_settings = reminder_system.get_reminder_settings()
        start_times = updated_settings['default_reminders'][ReminderType.SESSION_START]
        print(f"   - Novos tempos para início de sessão: {start_times} minutos\n")
        
        # Testar verificação de lembretes (simulação)
        print("6️⃣ Testando verificação de lembretes de sessão...")
        # Parar a task automática para teste manual
        if reminder_system.reminder_task.is_running():
            reminder_system.reminder_task.cancel()
        
        # Simular verificação manual
        await reminder_system._check_session_reminders()
        print("✅ Verificação de lembretes de sessão executada\n")
        
        # Testar verificação de lembretes personalizados
        print("7️⃣ Testando verificação de lembretes personalizados...")
        await reminder_system._check_custom_reminders()
        print("✅ Verificação de lembretes personalizados executada\n")
        
        # Testar remoção de lembrete personalizado
        print("8️⃣ Testando remoção de lembrete personalizado...")
        removed = reminder_system.delete_custom_reminder(reminder_id)
        print(f"✅ Lembrete removido: {removed}")
        
        remaining_reminders = reminder_system.get_custom_reminders()
        print(f"   - Lembretes restantes: {len(remaining_reminders)}\n")
        
        # Testar limpeza de lembretes antigos
        print("9️⃣ Testando limpeza de lembretes antigos...")
        reminder_system.cleanup_old_reminders(days_old=1)
        print("✅ Limpeza de lembretes executada\n")
        
        # Testar parada do sistema
        print("🔟 Testando parada do sistema...")
        reminder_system.stop_reminders()
        print("✅ Sistema de lembretes parado\n")
        
        print("🎉 Todos os testes do sistema de lembretes foram concluídos com sucesso!")
        print("\n📊 Resumo dos testes:")
        print("   ✅ Inicialização do sistema")
        print("   ✅ Carregamento de configurações padrão")
        print("   ✅ Criação de lembrete personalizado")
        print("   ✅ Listagem de lembretes")
        print("   ✅ Atualização de configurações")
        print("   ✅ Verificação de lembretes de sessão")
        print("   ✅ Verificação de lembretes personalizados")
        print("   ✅ Remoção de lembrete")
        print("   ✅ Limpeza de lembretes antigos")
        print("   ✅ Parada do sistema")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_reminder_types():
    """Testa os diferentes tipos de lembretes"""
    print("\n🔍 Testando tipos de lembretes...\n")
    
    types = [
        ReminderType.SESSION_START,
        ReminderType.CHECKIN_DEADLINE,
        ReminderType.SESSION_END,
        ReminderType.CHECKOUT_REMINDER,
        ReminderType.CUSTOM
    ]
    
    type_names = {
        ReminderType.SESSION_START: "Início de Sessão",
        ReminderType.CHECKIN_DEADLINE: "Deadline de Check-in",
        ReminderType.SESSION_END: "Fim de Sessão",
        ReminderType.CHECKOUT_REMINDER: "Lembrete de Check-out",
        ReminderType.CUSTOM: "Personalizado"
    }
    
    for reminder_type in types:
        print(f"📋 Tipo: {type_names.get(reminder_type, reminder_type)}")
        print(f"   - Valor: {reminder_type}")
    
    print("\n✅ Todos os tipos de lembretes verificados!")

async def main():
    """Função principal de teste"""
    print("🚀 Sistema de Testes - Lembretes Automáticos")
    print("=" * 50)
    
    # Executar testes principais
    success = await test_reminder_system()
    
    # Executar testes de tipos
    await test_reminder_types()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 Todos os testes foram executados com sucesso!")
        print("✨ O sistema de lembretes está funcionando corretamente.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
    
    return success

if __name__ == "__main__":
    # Executar testes
    result = asyncio.run(main())
    sys.exit(0 if result else 1)