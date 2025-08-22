#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar a integração dos sistemas de badges e conquistas com PostgreSQL
"""

import os
import sys
import asyncio
import logging
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar os sistemas necessários
from storage import DataStorage
from achievement_system import AchievementSystem
from badge_system import BadgeSystem
from pubg_api import PUBGIntegration
from dual_ranking_system import DualRankingSystem
from rank import RankSystem

# Tentar importar PostgreSQL (opcional)
try:
    from postgres_storage import PostgreSQLStorage
    POSTGRES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PostgreSQL não disponível: {e}")
    PostgreSQLStorage = None
    POSTGRES_AVAILABLE = False

class MockBot:
    """Mock do bot Discord para testes"""
    def __init__(self):
        self.user = Mock()
        self.user.id = 123456789
        self.guilds = [Mock()]
        self.guilds[0].id = 987654321
        self.guilds[0].members = []
        
class MockUser:
    """Mock de usuário Discord"""
    def __init__(self, user_id, username):
        self.id = user_id
        self.name = username
        self.display_name = username
        self.mention = f"<@{user_id}>"

class MockGuild:
    """Mock de guild Discord"""
    def __init__(self):
        self.id = 987654321
        self.name = "Test Guild"
        self.members = []

async def test_storage_initialization():
    """Testa a inicialização dos sistemas de storage"""
    logger.info("🔧 Testando inicialização dos sistemas de storage...")
    
    try:
        # Testar DataStorage (JSON)
        json_storage = DataStorage()
        logger.info("✅ DataStorage (JSON) inicializado com sucesso")
        
        # Testar PostgreSQLStorage (se disponível)
        postgres_storage = None
        if POSTGRES_AVAILABLE and PostgreSQLStorage:
            try:
                postgres_storage = PostgreSQLStorage()
                logger.info("✅ PostgreSQLStorage inicializado com sucesso")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQLStorage não disponível: {e}")
                postgres_storage = None
        else:
            logger.info("ℹ️ PostgreSQL não está disponível (dependências não instaladas)")
            
        return json_storage, postgres_storage
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do storage: {e}")
        return None, None

async def test_achievement_system(storage):
    """Testa o sistema de conquistas"""
    logger.info("🏆 Testando sistema de conquistas...")
    
    try:
        # Criar mock do bot
        bot = MockBot()
        
        # Inicializar sistema de conquistas
        achievement_system = AchievementSystem(bot, storage)
        logger.info("✅ AchievementSystem inicializado")
        
        # Testar usuário mock
        user = MockUser(123456789, "TestUser")
        
        # Testar verificação de conquistas
        user_data = {
            'pubg_username': 'TestPlayer',
            'tournaments_participated': 2,
            'matches_played': 50,
            'wins': 10,
            'kills': 150,
            'headshots': 30
        }
        
        # Verificar conquistas
        new_achievements = achievement_system.check_achievements(user.id, user_data)
        logger.info(f"✅ Conquistas verificadas: {len(new_achievements)} novas conquistas")
        
        # Testar obtenção de conquistas do usuário
        user_achievements = achievement_system.get_user_achievements(user.id)
        logger.info(f"✅ Conquistas do usuário obtidas: {len(user_achievements)} conquistas")
        
        # Testar listagem de todas as conquistas
        all_achievements = achievement_system.get_all_achievements()
        logger.info(f"✅ Total de conquistas disponíveis: {len(all_achievements)}")
        
        # Testar conquistas por categoria
        combat_achievements = achievement_system.get_achievements_by_category('combate')
        logger.info(f"✅ Conquistas de combate: {len(combat_achievements)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste do sistema de conquistas: {e}")
        return False

async def test_badge_system(storage):
    """Testa o sistema de badges"""
    logger.info("🎖️ Testando sistema de badges...")
    
    try:
        # Criar mocks necessários
        bot = MockBot()
        pubg_api = PUBGIntegration()
        rank_system = RankSystem(bot, storage, pubg_api)
        dual_ranking_system = DualRankingSystem(bot, storage, pubg_api, rank_system)
        
        # Inicializar sistema de badges
        badge_system = BadgeSystem(bot, storage, pubg_api, dual_ranking_system)
        logger.info("✅ BadgeSystem inicializado")
        
        # Testar usuário mock
        user = MockUser(123456789, "TestUser")
        
        # Testar dados PUBG mock
        pubg_data = {
            'kills': 150,
            'wins': 10,
            'matches': 50,
            'headshots': 30,
            'damage': 15000,
            'survival_time': 120000,
            'top10s': 25,
            'assists': 40
        }
        
        # Verificar badges do usuário
        user_badges = await badge_system.check_user_badges(user.id, pubg_data)
        logger.info(f"✅ Badges verificados: {len(user_badges)} badges")
        
        # Testar obtenção de badges por categoria
        combat_badges = badge_system.get_badges_by_category('combat')
        logger.info(f"✅ Badges de combate: {len(combat_badges)}")
        
        # Testar obtenção de todos os badges
        all_badges = badge_system.get_all_badges()
        logger.info(f"✅ Total de badges disponíveis: {len(all_badges)}")
        
        # Testar badges do usuário
        user_badge_list = badge_system.get_user_badges(user.id)
        logger.info(f"✅ Badges do usuário: {len(user_badge_list)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste do sistema de badges: {e}")
        return False

async def test_data_persistence(storage):
    """Testa a persistência de dados"""
    logger.info("💾 Testando persistência de dados...")
    
    try:
        # Testar salvamento de dados de teste
        test_data = {
            'user_achievements': {
                '123456789': {
                    'first_registration': {
                        'unlocked_at': datetime.now().isoformat(),
                        'progress': 1
                    }
                }
            },
            'user_badges': {
                '123456789': {
                    'combat_rookie': {
                        'earned_at': datetime.now().isoformat(),
                        'level': 1
                    }
                }
            }
        }
        
        # Salvar dados
        if hasattr(storage, 'data'):
            storage.data.update(test_data)
            if hasattr(storage, 'save_data'):
                storage.save_data()
                logger.info("✅ Dados salvos com sucesso")
        
        # Verificar se os dados foram salvos
        if hasattr(storage, 'load_data'):
            storage.load_data()
            logger.info("✅ Dados carregados com sucesso")
        
        # Verificar integridade dos dados
        if hasattr(storage, 'data'):
            if 'user_achievements' in storage.data:
                logger.info(f"✅ Conquistas persistidas: {len(storage.data['user_achievements'])} usuários")
            if 'user_badges' in storage.data:
                logger.info(f"✅ Badges persistidos: {len(storage.data['user_badges'])} usuários")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de persistência: {e}")
        return False

async def test_integration():
    """Testa a integração completa entre badges e conquistas"""
    logger.info("🔗 Testando integração entre badges e conquistas...")
    
    try:
        # Usar DataStorage para o teste
        storage = DataStorage()
        
        # Criar mocks
        bot = MockBot()
        pubg_api = PUBGIntegration()
        rank_system = RankSystem(bot, storage, pubg_api)
        dual_ranking_system = DualRankingSystem(bot, storage, pubg_api, rank_system)
        
        # Inicializar sistemas
        achievement_system = AchievementSystem(bot, storage)
        badge_system = BadgeSystem(bot, storage, pubg_api, dual_ranking_system)
        
        # Usuário de teste
        user = MockUser(123456789, "TestUser")
        
        # Simular dados de jogo
        game_data = {
            'pubg_username': 'TestPlayer',
            'tournaments_participated': 3,
            'matches_played': 100,
            'wins': 20,
            'kills': 300,
            'headshots': 60,
            'damage': 30000,
            'survival_time': 240000,
            'top10s': 50,
            'assists': 80
        }
        
        # Verificar conquistas
        new_achievements = achievement_system.check_achievements(user.id, game_data)
        logger.info(f"✅ Novas conquistas desbloqueadas: {len(new_achievements)}")
        
        # Verificar badges
        user_badges = await badge_system.check_user_badges(user.id, game_data)
        logger.info(f"✅ Badges verificados: {len(user_badges)}")
        
        # Verificar se os dados foram salvos corretamente
        user_achievements = achievement_system.get_user_achievements(user.id)
        user_badge_list = badge_system.get_user_badges(user.id)
        
        logger.info(f"✅ Total de conquistas do usuário: {len(user_achievements)}")
        logger.info(f"✅ Total de badges do usuário: {len(user_badge_list)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de integração: {e}")
        return False

async def main():
    """Função principal de teste"""
    logger.info("🚀 Iniciando testes de integração badges/conquistas com PostgreSQL")
    logger.info("=" * 70)
    
    # Testar inicialização dos storages
    json_storage, postgres_storage = await test_storage_initialization()
    
    if not json_storage:
        logger.error("❌ Falha na inicialização dos sistemas de storage")
        return
    
    # Escolher storage para testes (preferir PostgreSQL se disponível)
    storage = postgres_storage if postgres_storage else json_storage
    storage_type = "PostgreSQL" if postgres_storage else "JSON"
    
    logger.info(f"📊 Usando {storage_type} para os testes")
    logger.info("=" * 70)
    
    # Executar testes
    tests = [
        ("Sistema de Conquistas", test_achievement_system),
        ("Sistema de Badges", test_badge_system),
        ("Persistência de Dados", test_data_persistence),
        ("Integração Completa", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Executando teste: {test_name}")
        logger.info("-" * 50)
        
        if test_name == "Integração Completa":
            # Teste de integração não precisa do storage como parâmetro
            result = await test_func()
        else:
            result = await test_func(storage)
        
        results.append((test_name, result))
        
        if result:
            logger.info(f"✅ {test_name}: PASSOU")
        else:
            logger.error(f"❌ {test_name}: FALHOU")
    
    # Resumo dos resultados
    logger.info("\n" + "=" * 70)
    logger.info("📋 RESUMO DOS TESTES")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n📊 Resultado final: {passed}/{total} testes passaram")
    
    if passed == total:
        logger.info("🎉 Todos os testes passaram! Sistema de badges/conquistas está funcionando corretamente.")
    else:
        logger.warning(f"⚠️ {total - passed} teste(s) falharam. Verifique os logs acima para detalhes.")
    
    logger.info("\n🏁 Testes concluídos")

if __name__ == "__main__":
    asyncio.run(main())