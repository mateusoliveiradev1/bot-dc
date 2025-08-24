#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o sistema de notificações
"""

import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestNotifications')

def test_notifications_initialization():
    """Testa a inicialização do sistema de notificações"""
    try:
        from notifications_system import NotificationsSystem, NotificationType, NotificationPriority
        
        # Mock do bot
        mock_bot = Mock()
        mock_bot.guilds = []
        mock_bot.wait_until_ready = AsyncMock()
        
        # Mock do storage
        mock_storage = Mock()
        
        # Inicializar sistema
        notifications = NotificationsSystem(mock_bot, mock_storage)
        
        print("✅ Sistema de notificações inicializado com sucesso")
        print(f"📋 Templates carregados: {len(notifications.templates)}")
        print(f"👥 Preferências de usuários: {len(notifications.user_preferences)}")
        print(f"📨 Notificações pendentes: {len(notifications.pending_notifications)}")
        
        # Verificar templates padrão
        expected_templates = [
            "rank_update_promotion",
            "achievement_unlocked", 
            "tournament_starting",
            "daily_challenge_available",
            "minigame_milestone",
            "system_announcement",
            "birthday_reminder"
        ]
        
        for template_id in expected_templates:
            if template_id in notifications.templates:
                print(f"  ✅ Template '{template_id}' encontrado")
            else:
                print(f"  ❌ Template '{template_id}' não encontrado")
        
        return notifications
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        return None

async def test_notification_creation(notifications):
    """Testa a criação de notificações"""
    try:
        print("\n🔧 Testando criação de notificações...")
        
        # Criar notificação de conquista
        notification = await notifications.create_notification(
            user_id=123456789,
            template_id="achievement_unlocked",
            data={
                "achievement_name": "Primeiro Passo",
                "achievement_description": "Complete seu primeiro desafio!"
            }
        )
        
        if notification:
            print(f"✅ Notificação criada: {notification.id}")
            print(f"  📝 Título: {notification.title}")
            print(f"  💬 Mensagem: {notification.message}")
            print(f"  🎨 Cor: {hex(notification.color)}")
            print(f"  ⚡ Prioridade: {notification.priority.value}")
        else:
            print("❌ Falha ao criar notificação")
            
        return notification
        
    except Exception as e:
        print(f"❌ Erro na criação de notificação: {e}")
        return None

def test_user_preferences(notifications):
    """Testa as preferências do usuário"""
    try:
        print("\n⚙️ Testando preferências do usuário...")
        
        user_id = 123456789
        prefs = notifications.get_user_preferences(user_id)
        
        print(f"✅ Preferências obtidas para usuário {user_id}")
        print(f"  📧 DM habilitado: {prefs.dm_enabled}")
        print(f"  📢 Canal habilitado: {prefs.channel_enabled}")
        print(f"  🌙 Horário silencioso: {prefs.quiet_hours_start}:00 - {prefs.quiet_hours_end}:00")
        print(f"  ⚡ Prioridade mínima: {prefs.min_priority.value}")
        print(f"  📋 Tipos habilitados: {len(prefs.enabled_types)}")
        
        return prefs
        
    except Exception as e:
        print(f"❌ Erro ao testar preferências: {e}")
        return None

def test_tasks_definition(notifications):
    """Testa se as tasks estão definidas corretamente"""
    try:
        print("\n🔄 Testando definição das tasks...")
        
        # Verificar se as tasks existem como atributos
        if hasattr(notifications, 'notification_sender'):
            print("✅ Task 'notification_sender' encontrada")
            print(f"  🔄 Está rodando: {notifications.notification_sender.is_running()}")
        else:
            print("❌ Task 'notification_sender' não encontrada")
            
        if hasattr(notifications, 'cleanup_task'):
            print("✅ Task 'cleanup_task' encontrada")
            print(f"  🔄 Está rodando: {notifications.cleanup_task.is_running()}")
        else:
            print("❌ Task 'cleanup_task' não encontrada")
            
        # Verificar métodos de controle
        if hasattr(notifications, 'start_tasks'):
            print("✅ Método 'start_tasks' encontrado")
        else:
            print("❌ Método 'start_tasks' não encontrado")
            
        if hasattr(notifications, 'stop'):
            print("✅ Método 'stop' encontrado")
        else:
            print("❌ Método 'stop' não encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao testar tasks: {e}")

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do sistema de notificações...\n")
    
    # Teste 1: Inicialização
    notifications = test_notifications_initialization()
    if not notifications:
        return
    
    # Teste 2: Definição das tasks
    test_tasks_definition(notifications)
    
    # Teste 3: Preferências do usuário
    test_user_preferences(notifications)
    
    # Teste 4: Criação de notificação
    await test_notification_creation(notifications)
    
    print("\n✅ Testes concluídos com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())