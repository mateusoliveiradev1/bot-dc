#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste avançado para o sistema de notificações
"""

import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import discord

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestNotificationsAdvanced')

async def test_notification_sending():
    """Testa o envio de notificações"""
    try:
        from notifications_system import NotificationsSystem, NotificationType, NotificationPriority
        
        print("🚀 Testando envio de notificações...\n")
        
        # Mock do usuário Discord
        mock_user = Mock()
        mock_user.id = 123456789
        mock_user.display_name = "TestUser"
        mock_user.mention = "<@123456789>"
        mock_user.send = AsyncMock()
        
        # Mock do canal
        mock_channel = Mock()
        mock_channel.name = "notificações"
        mock_channel.send = AsyncMock()
        
        # Mock da guild
        mock_guild = Mock()
        mock_guild.channels = [mock_channel]
        mock_guild.system_channel = mock_channel
        
        # Mock do bot
        mock_bot = Mock()
        mock_bot.guilds = [mock_guild]
        mock_bot.get_user = Mock(return_value=mock_user)
        mock_bot.wait_until_ready = AsyncMock()
        
        # Mock do storage
        mock_storage = Mock()
        
        # Inicializar sistema
        notifications = NotificationsSystem(mock_bot, mock_storage)
        
        # Criar notificação
        notification = await notifications.create_notification(
            user_id=123456789,
            template_id="achievement_unlocked",
            data={
                "achievement_name": "Testador Experiente",
                "achievement_description": "Execute testes avançados com sucesso!"
            }
        )
        
        if notification:
            print(f"✅ Notificação criada: {notification.id}")
            
            # Testar envio
            result = await notifications.send_notification(notification)
            
            if result:
                print("✅ Notificação enviada com sucesso")
                print(f"  📧 Enviada via DM: {mock_user.send.called}")
                if mock_user.send.called:
                    # Verificar se o embed foi criado corretamente
                    call_args = mock_user.send.call_args
                    if call_args and 'embed' in call_args.kwargs:
                        embed = call_args.kwargs['embed']
                        print(f"  📝 Embed título: {embed.title}")
                        print(f"  💬 Embed descrição: {embed.description}")
                        print(f"  🎨 Embed cor: {embed.color}")
            else:
                print("❌ Falha no envio da notificação")
        else:
            print("❌ Falha ao criar notificação")
            
    except Exception as e:
        print(f"❌ Erro no teste de envio: {e}")
        import traceback
        traceback.print_exc()

async def test_tasks_functionality():
    """Testa a funcionalidade das tasks"""
    try:
        from notifications_system import NotificationsSystem
        
        print("\n🔄 Testando funcionalidade das tasks...\n")
        
        # Mock do bot
        mock_bot = Mock()
        mock_bot.guilds = []
        mock_bot.wait_until_ready = AsyncMock()
        
        # Mock do storage
        mock_storage = Mock()
        
        # Inicializar sistema
        notifications = NotificationsSystem(mock_bot, mock_storage)
        
        # Verificar se as tasks podem ser iniciadas
        try:
            notifications.start_tasks()
            print("✅ Método start_tasks executado sem erro")
            
            # Verificar status das tasks
            if hasattr(notifications, 'notification_sender'):
                print(f"  📤 notification_sender rodando: {notifications.notification_sender.is_running()}")
            
            if hasattr(notifications, 'cleanup_task'):
                print(f"  🧹 cleanup_task rodando: {notifications.cleanup_task.is_running()}")
                
        except Exception as e:
            print(f"❌ Erro ao iniciar tasks: {e}")
            
        # Testar parada das tasks
        try:
            notifications.stop()
            print("✅ Método stop executado sem erro")
        except Exception as e:
            print(f"❌ Erro ao parar tasks: {e}")
            
    except Exception as e:
        print(f"❌ Erro no teste de tasks: {e}")
        import traceback
        traceback.print_exc()

async def test_notification_queue():
    """Testa a fila de notificações"""
    try:
        from notifications_system import NotificationsSystem
        
        print("\n📋 Testando fila de notificações...\n")
        
        # Mock do bot
        mock_bot = Mock()
        mock_bot.guilds = []
        mock_bot.wait_until_ready = AsyncMock()
        
        # Mock do storage
        mock_storage = Mock()
        
        # Inicializar sistema
        notifications = NotificationsSystem(mock_bot, mock_storage)
        
        # Criar múltiplas notificações
        user_id = 123456789
        templates = ["achievement_unlocked", "rank_update_promotion", "daily_challenge_available"]
        
        created_notifications = []
        for i, template_id in enumerate(templates):
            notification = await notifications.create_notification(
                user_id=user_id,
                template_id=template_id,
                data={
                    "achievement_name": f"Teste {i+1}",
                    "achievement_description": f"Descrição do teste {i+1}",
                    "new_rank": "Ouro",
                    "points": "1500",
                    "challenge_name": f"Desafio {i+1}",
                    "reward": "100 XP"
                }
            )
            if notification:
                created_notifications.append(notification)
        
        print(f"✅ Criadas {len(created_notifications)} notificações")
        print(f"📨 Notificações pendentes: {len(notifications.pending_notifications)}")
        print(f"👤 Notificações do usuário: {len(notifications.user_notifications[user_id])}")
        
        # Verificar se as notificações estão na fila
        for notification in created_notifications:
            if notification in notifications.pending_notifications:
                print(f"  ✅ Notificação {notification.id[:8]}... está na fila")
            else:
                print(f"  ❌ Notificação {notification.id[:8]}... NÃO está na fila")
                
    except Exception as e:
        print(f"❌ Erro no teste de fila: {e}")
        import traceback
        traceback.print_exc()

async def test_user_preferences_filtering():
    """Testa filtragem por preferências do usuário"""
    try:
        from notifications_system import NotificationsSystem, NotificationType, NotificationPriority
        
        print("\n⚙️ Testando filtragem por preferências...\n")
        
        # Mock do bot
        mock_bot = Mock()
        mock_bot.guilds = []
        mock_bot.wait_until_ready = AsyncMock()
        
        # Mock do storage
        mock_storage = Mock()
        
        # Inicializar sistema
        notifications = NotificationsSystem(mock_bot, mock_storage)
        
        user_id = 123456789
        
        # Configurar preferências restritivas
        prefs = notifications.get_user_preferences(user_id)
        prefs.enabled_types = {NotificationType.NEW_ACHIEVEMENT}  # Apenas conquistas
        prefs.min_priority = NotificationPriority.HIGH  # Apenas alta prioridade
        
        print(f"📋 Tipos habilitados: {[t.value for t in prefs.enabled_types]}")
        print(f"⚡ Prioridade mínima: {prefs.min_priority.value}")
        
        # Tentar criar notificação de baixa prioridade (deve ser filtrada)
        notification1 = await notifications.create_notification(
            user_id=user_id,
            template_id="minigame_milestone",  # Prioridade LOW
            data={"milestone_name": "Teste", "description": "Teste"}
        )
        
        # Tentar criar notificação de conquista (deve passar)
        notification2 = await notifications.create_notification(
            user_id=user_id,
            template_id="achievement_unlocked",  # Prioridade MEDIUM, mas tipo habilitado
            data={"achievement_name": "Teste", "achievement_description": "Teste"}
        )
        
        if notification1 is None:
            print("✅ Notificação de baixa prioridade foi filtrada corretamente")
        else:
            print("❌ Notificação de baixa prioridade NÃO foi filtrada")
            
        if notification2 is None:
            print("❌ Notificação de conquista foi filtrada incorretamente")
        else:
            print("✅ Notificação de conquista passou pelo filtro")
            
    except Exception as e:
        print(f"❌ Erro no teste de filtragem: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes avançados do sistema de notificações...\n")
    
    await test_notification_sending()
    await test_tasks_functionality()
    await test_notification_queue()
    await test_user_preferences_filtering()
    
    print("\n✅ Todos os testes avançados concluídos!")

if __name__ == "__main__":
    asyncio.run(main())