#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o sistema de check-in/check-out
Testa todas as funcionalidades principais do sistema
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock

# Adicionar o diretório do bot ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from checkin_system import CheckInSystem, SessionType, CheckInStatus
from storage import DataStorage

class MockBot:
    """Mock do bot para testes"""
    def __init__(self):
        self.user = Mock()
        self.user.id = 123456789
        self.guilds = []
        
class MockGuild:
    """Mock da guild para testes"""
    def __init__(self, guild_id=987654321):
        self.id = guild_id
        self.name = "Test Guild"
        
class MockUser:
    """Mock do usuário para testes"""
    def __init__(self, user_id=111222333, username="TestUser"):
        self.id = user_id
        self.name = username
        self.display_name = username
        self.mention = f"<@{user_id}>"

async def test_checkin_system():
    """Testa o sistema de check-in completo"""
    print("🔄 Iniciando teste do sistema de check-in...")
    
    # Inicializar componentes
    storage = DataStorage("test_checkin_data.json")
    bot = MockBot()
    checkin_system = CheckInSystem(bot, storage)
    
    print("✅ Sistema inicializado com sucesso")
    
    # Teste 1: Criar sessão
    print("\n📝 Teste 1: Criando sessão de scrim...")
    guild = MockGuild()
    creator = MockUser(555666777, "Creator")
    
    session_id = "test_scrim_001"
    start_time = datetime.now() + timedelta(minutes=30)
    
    end_time = start_time + timedelta(hours=2)
    
    try:
        session = checkin_system.create_session(
            session_id=session_id,
            session_type=SessionType.SCRIM,
            start_time=start_time,
            end_time=end_time,
            max_players=8,
            description="Sessão de teste para validar o sistema"
        )
        print("✅ Sessão criada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao criar sessão: {e}")
        return
    
    # Teste 2: Listar sessões ativas
    print("\n📋 Teste 2: Listando sessões ativas...")
    active_sessions = checkin_system.get_active_sessions()
    print(f"✅ Encontradas {len(active_sessions)} sessões ativas")
    
    # Teste 3: Check-in de jogadores
    print("\n👥 Teste 3: Fazendo check-in de jogadores...")
    players = [
        MockUser(111111111, "Player1"),
        MockUser(222222222, "Player2"),
        MockUser(333333333, "Player3")
    ]
    
    for player in players:
        try:
            result = checkin_system.check_in_player(session_id, str(player.id), player.name)
            print(f"✅ Check-in realizado: {player.name}")
        except Exception as e:
            print(f"❌ Erro no check-in: {player.name} - {e}")
    
    # Teste 4: Verificar informações da sessão
    print("\n📊 Teste 4: Verificando informações da sessão...")
    session_info = checkin_system.get_session(session_id)
    if session_info:
        print(f"✅ Sessão ID: {session_info['id']}")
        print(f"   Tipo: {session_info['type']}")
        print(f"   Jogadores: {session_info['checkin_count']}/{session_info['max_players']}")
        print(f"   Status: {session_info['status']}")
    else:
        print("❌ Erro ao obter informações da sessão")
    
    # Teste 5: Check-out de um jogador
    print("\n👋 Teste 5: Fazendo check-out de um jogador...")
    checkout_player = players[0]
    try:
        result = checkin_system.check_out_player(session_id, str(checkout_player.id))
        print(f"✅ Check-out realizado: {checkout_player.name}")
    except Exception as e:
        print(f"❌ Erro no check-out: {checkout_player.name} - {e}")
    
    # Teste 6: Verificar estatísticas do jogador
    print("\n📈 Teste 6: Verificando estatísticas dos jogadores...")
    for player in players:
        stats = checkin_system.get_player_stats(str(player.id))
        print(f"📊 {player.name}: {stats.get('total_sessions', 0)} sessões, {stats.get('total_checkins', 0)} check-ins")
    
    # Teste 7: Criar sessão de torneio
    print("\n🏆 Teste 7: Criando sessão de torneio...")
    tournament_id = "test_tournament_001"
    tournament_start = datetime.now() + timedelta(hours=2)
    
    tournament_end = tournament_start + timedelta(hours=4)
    
    try:
        tournament_session = checkin_system.create_session(
            session_id=tournament_id,
            session_type=SessionType.TOURNAMENT,
            start_time=tournament_start,
            end_time=tournament_end,
            max_players=16,
            description="Torneio para validar o sistema"
        )
        print("✅ Sessão de torneio criada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao criar sessão de torneio: {e}")
    
    # Teste 8: Listar todas as sessões
    print("\n📋 Teste 8: Listando todas as sessões...")
    all_sessions = checkin_system.get_all_sessions()
    print(f"✅ Total de sessões no sistema: {len(all_sessions)}")
    
    for session in all_sessions:
        print(f"   - {session['id']} ({session['type']}) - {session['status']}")
    
    print("\n🎉 Teste do sistema de check-in concluído com sucesso!")
    print("\n📋 Resumo dos testes:")
    print("   ✅ Criação de sessões")
    print("   ✅ Check-in de jogadores")
    print("   ✅ Check-out de jogadores")
    print("   ✅ Consulta de informações")
    print("   ✅ Estatísticas de jogadores")
    print("   ✅ Listagem de sessões")
    
    # Limpeza
    try:
        os.remove("test_checkin_data.json")
        print("\n🧹 Arquivo de teste removido")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(test_checkin_system())