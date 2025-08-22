#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para debugar o problema do comando /clipes
"""

import asyncio
import sys
import os
from storage import DataStorage
from medal_integration import MedalIntegration

class MockBot:
    """Mock do bot para teste"""
    def __init__(self):
        self.user = None

async def test_clips():
    """Testa o método create_clips_list_embed"""
    try:
        print("Inicializando storage...")
        storage = DataStorage("data.json")
        
        print("Inicializando mock bot...")
        mock_bot = MockBot()
        
        print("Inicializando medal integration...")
        medal_integration = MedalIntegration(mock_bot, storage)
        
        print("Testando create_clips_list_embed...")
        player_id = "343264130905669632"
        
        # Testar get_player_clips primeiro
        print("Testando get_player_clips...")
        clips = await medal_integration.get_player_clips(player_id)
        print(f"Clipes encontrados: {len(clips)}")
        for clip in clips:
            print(f"  - {clip.get('id', 'N/A')}: {clip.get('url', 'N/A')}")
        
        # Testar create_clips_list_embed
        print("Testando create_clips_list_embed...")
        embed = await medal_integration.create_clips_list_embed(player_id)
        print(f"Embed criado com sucesso: {embed.title}")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_clips())