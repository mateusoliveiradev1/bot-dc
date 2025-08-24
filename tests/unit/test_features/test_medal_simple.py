#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples da integração Medal sem dependências do bot
"""

import asyncio
import os
from storage import DataStorage
from medal_integration import MedalIntegration

class MockBot:
    def __init__(self):
        self.user = None

async def test_medal_simple():
    """Teste simples da Medal integration"""
    try:
        print("=== TESTE SIMPLES MEDAL INTEGRATION ===")
        
        # Inicializar
        storage = DataStorage("data.json")
        bot = MockBot()
        medal = MedalIntegration(bot, storage)
        
        # Testar URLs
        test_urls = [
            "https://medal.tv/games/pubg/clips/abc123",
            "https://medal.tv/clips/def456",
            "https://www.youtube.com/watch?v=test"
        ]
        
        print("\n1. Testando detecção de URLs:")
        for url in test_urls:
            is_medal = medal.is_medal_url(url)
            print(f"  {url[:50]}... -> {'✅' if is_medal else '❌'}")
        
        # Testar embed
        print("\n2. Testando criação de embed:")
        embed = await medal.create_clips_list_embed("343264130905669632")
        print(f"  Título: {embed.title}")
        print(f"  Cor: {embed.color}")
        print(f"  Campos: {len(embed.fields)}")
        
        # Testar estatísticas
        print("\n3. Testando estatísticas:")
        stats = await medal.get_clips_stats()
        print(f"  Total clipes: {stats.get('total_clips', 0)}")
        print(f"  Jogadores únicos: {stats.get('unique_players', 0)}")
        
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_medal_simple())