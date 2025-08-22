#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste completo para a integração Medal
"""

import asyncio
import sys
import os
from storage import DataStorage
from medal_integration import MedalIntegration
import discord
from datetime import datetime

class MockBot:
    """Mock do bot para teste"""
    def __init__(self):
        self.user = None

class MockMessage:
    """Mock de mensagem do Discord"""
    def __init__(self, content, author_id, channel_name="test"):
        self.content = content
        self.author = MockUser(author_id)
        self.channel = MockChannel(channel_name)
        self.created_at = datetime.now()
        self.embeds = []
        self.reactions = []
        self.id = "123456789"
        self.guild = MockGuild()

class MockUser:
    """Mock de usuário do Discord"""
    def __init__(self, user_id):
        self.id = int(user_id)
        self.display_name = f"TestUser{user_id}"
        self.bot = False

class MockChannel:
    """Mock de canal do Discord"""
    def __init__(self, name):
        self.name = name
        self.id = "987654321"

class MockGuild:
    """Mock de guilda do Discord"""
    def __init__(self):
        self.id = "111222333"

async def test_medal_integration():
    """Testa a integração Medal completa"""
    try:
        print("=== TESTE DA INTEGRAÇÃO MEDAL ===")
        print()
        
        # Inicializar componentes
        print("1. Inicializando storage...")
        storage = DataStorage("data.json")
        
        print("2. Inicializando mock bot...")
        mock_bot = MockBot()
        
        print("3. Inicializando medal integration...")
        medal_integration = MedalIntegration(mock_bot, storage)
        
        # Testar padrões de URL
        print("\n4. Testando padrões de URL do Medal:")
        test_urls = [
            "https://medal.tv/games/pubg/clips/abc123",
            "https://medal.tv/clips/def456",
            "https://medal.tv/games/valorant/clips/ghi789",
            "https://www.youtube.com/watch?v=test",  # Não deve ser detectado
            "https://medal.tv/user/test/clip/jkl012"
        ]
        
        for url in test_urls:
            is_medal = medal_integration.is_medal_url(url)
            print(f"  {url} -> {'✅ Medal' if is_medal else '❌ Não Medal'}")
        
        # Testar extração de ID
        print("\n5. Testando extração de IDs:")
        for url in test_urls[:4]:  # Apenas URLs do Medal
            if medal_integration.is_medal_url(url):
                clip_id = medal_integration._extract_clip_id(url)
                print(f"  {url} -> ID: {clip_id}")
        
        # Testar processamento de mensagem
        print("\n6. Testando processamento de mensagens:")
        
        # Registrar um jogador de teste
        test_user_id = "343264130905669632"
        storage.add_player(test_user_id, "TestPlayer", "steam", "111222333")
        print(f"  Jogador de teste registrado: {test_user_id}")
        
        # Criar mensagem de teste com clipe
        test_message = MockMessage(
            "Olha esse clipe incrível! https://medal.tv/games/pubg/clips/test123",
            test_user_id
        )
        
        print("  Processando mensagem com clipe...")
        result = await medal_integration.process_message(test_message)
        print(f"  Resultado: {'✅ Processado' if result else '❌ Não processado'}")
        
        # Verificar se o clipe foi salvo
        print("\n7. Verificando clipes salvos:")
        all_clips = storage.get_clips()
        print(f"  Total de clipes no storage: {len(all_clips)}")
        
        for clip in all_clips:
            print(f"  - ID: {clip.get('id', 'N/A')}")
            print(f"    URL: {clip.get('url', 'N/A')}")
            print(f"    Jogador: {clip.get('player_name', 'N/A')}")
            print(f"    Data: {clip.get('created_at', 'N/A')}")
            print()
        
        # Testar busca de clipes do jogador
        print("8. Testando busca de clipes do jogador:")
        player_clips = await medal_integration.get_player_clips(test_user_id)
        print(f"  Clipes encontrados para {test_user_id}: {len(player_clips)}")
        
        # Testar criação de embed
        print("\n9. Testando criação de embed:")
        embed = await medal_integration.create_clips_list_embed(test_user_id)
        print(f"  Embed criado: {embed.title}")
        print(f"  Descrição: {embed.description}")
        print(f"  Campos: {len(embed.fields)}")
        
        # Testar estatísticas
        print("\n10. Testando estatísticas:")
        stats = await medal_integration.get_clips_stats()
        print(f"  Total de clipes: {stats.get('total_clips', 0)}")
        print(f"  Clipes últimos 7 dias: {stats.get('clips_last_7_days', 0)}")
        print(f"  Jogadores únicos: {stats.get('unique_players', 0)}")
        
        print("\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_medal_integration())