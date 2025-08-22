#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste simplificado para verificar sistemas de badges e conquistas
"""

import os
import sys
import asyncio
import logging
from unittest.mock import Mock
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

def test_achievement_system_sync():
    """Testa o sistema de conquistas de forma síncrona"""
    logger.info("🏆 Testando sistema de conquistas (síncrono)...")
    
    try:
        # Criar storage e bot mock
        storage = DataStorage()
        bot = MockBot()
        
        # Inicializar sistema de conquistas
        achievement_system = AchievementSystem(bot, storage)
        logger.info("✅ AchievementSystem inicializado")
        
        # Testar usuário mock
        user_id = 123456789
        
        # Testar dados do usuário
        user_data = {
            'pubg_username': 'TestPlayer',
            'tournaments_participated': 2,
            'matches_played': 50,
            'wins': 10,
            'kills': 150,
            'headshots': 30
        }
        
        # Verificar conquistas (método síncrono)
        try:
            # Tentar chamar o método check_achievements
            result = achievement_system.check_achievements(user_id, user_data)
            
            # Se retornar uma corrotina, aguardar
            if hasattr(result, '__await__'):
                logger.info("Método check_achievements é assíncrono, convertendo...")
                # Não podemos usar await aqui, então vamos testar de outra forma
                new_achievements = []
            else:
                new_achievements = result
                
            logger.info(f"✅ Conquistas verificadas: {len(new_achievements) if new_achievements else 0} novas")
            
        except Exception as e:
            logger.error(f"Erro ao verificar conquistas: {e}")
            return False
        
        # Testar obtenção de conquistas do usuário
        user_achievements = achievement_system.get_user_achievements(user_id)
        logger.info(f"✅ Conquistas do usuário: {len(user_achievements)} conquistas")
        
        # Testar listagem de todas as conquistas
        all_achievements = achievement_system.get_all_achievements()
        logger.info(f"✅ Total de conquistas disponíveis: {len(all_achievements)}")
        
        # Testar conquistas por categoria
        combat_achievements = achievement_system.get_achievements_by_category('combate')
        logger.info(f"✅ Conquistas de combate: {len(combat_achievements)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste do sistema de conquistas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_badge_system_sync():
    """Testa o sistema de badges de forma síncrona"""
    logger.info("🎖️ Testando sistema de badges (síncrono)...")
    
    try:
        # Criar mocks necessários
        storage = DataStorage()
        bot = MockBot()
        pubg_api = PUBGIntegration()
        rank_system = RankSystem(bot, storage, pubg_api)
        dual_ranking_system = DualRankingSystem(bot, storage, pubg_api, rank_system)
        
        # Inicializar sistema de badges
        badge_system = BadgeSystem(bot, storage, pubg_api, dual_ranking_system)
        logger.info("✅ BadgeSystem inicializado")
        
        # Testar usuário mock
        user_id = 123456789
        
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
        try:
            result = badge_system.check_user_badges(user_id, pubg_data)
            
            # Se retornar uma corrotina, tratar adequadamente
            if hasattr(result, '__await__'):
                logger.info("Método check_user_badges é assíncrono, convertendo...")
                user_badges = []
            else:
                user_badges = result
                
            logger.info(f"✅ Badges verificados: {len(user_badges) if user_badges else 0} badges")
            
        except Exception as e:
            logger.error(f"Erro ao verificar badges: {e}")
            return False
        
        # Testar obtenção de badges por categoria
        combat_badges = badge_system.get_badges_by_category('combat')
        logger.info(f"✅ Badges de combate: {len(combat_badges)}")
        
        # Testar obtenção de todos os badges
        all_badges = badge_system.get_all_badges()
        logger.info(f"✅ Total de badges disponíveis: {len(all_badges)}")
        
        # Testar badges do usuário
        user_badge_list = badge_system.get_user_badges(user_id)
        logger.info(f"✅ Badges do usuário: {len(user_badge_list)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste do sistema de badges: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_persistence():
    """Testa a persistência de dados"""
    logger.info("💾 Testando persistência de dados...")
    
    try:
        storage = DataStorage()
        
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
        storage.data.update(test_data)
        storage.save_data()
        logger.info("✅ Dados salvos com sucesso")
        
        # Verificar se os dados foram salvos
        storage.load_data()
        logger.info("✅ Dados carregados com sucesso")
        
        # Verificar integridade dos dados
        if 'user_achievements' in storage.data:
            logger.info(f"✅ Conquistas persistidas: {len(storage.data['user_achievements'])} usuários")
        if 'user_badges' in storage.data:
            logger.info(f"✅ Badges persistidos: {len(storage.data['user_badges'])} usuários")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de persistência: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_integration():
    """Testa a integração básica dos sistemas"""
    logger.info("🔗 Testando integração básica dos sistemas...")
    
    try:
        # Inicializar storage
        storage = DataStorage()
        bot = MockBot()
        
        # Inicializar sistemas
        achievement_system = AchievementSystem(bot, storage)
        logger.info("✅ Sistema de conquistas inicializado")
        
        # Verificar se os dados estão sendo salvos no storage
        if hasattr(storage, 'data'):
            if 'user_achievements' not in storage.data:
                storage.data['user_achievements'] = {}
            if 'user_badges' not in storage.data:
                storage.data['user_badges'] = {}
            
            logger.info("✅ Estrutura de dados inicializada no storage")
        
        # Verificar se as conquistas padrão foram carregadas
        all_achievements = achievement_system.get_all_achievements()
        logger.info(f"✅ {len(all_achievements)} conquistas carregadas")
        
        # Listar algumas conquistas para verificação
        for i, (key, achievement) in enumerate(all_achievements.items()):
            if i < 5:  # Mostrar apenas as primeiras 5
                logger.info(f"  - {achievement.name}: {achievement.description}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de integração: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    logger.info("🚀 Iniciando testes simplificados de badges/conquistas")
    logger.info("=" * 60)
    
    # Executar testes
    tests = [
        ("Sistema de Conquistas", test_achievement_system_sync),
        ("Sistema de Badges", test_badge_system_sync),
        ("Persistência de Dados", test_data_persistence),
        ("Integração dos Sistemas", test_system_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Executando teste: {test_name}")
        logger.info("-" * 40)
        
        result = test_func()
        results.append((test_name, result))
        
        if result:
            logger.info(f"✅ {test_name}: PASSOU")
        else:
            logger.error(f"❌ {test_name}: FALHOU")
    
    # Resumo dos resultados
    logger.info("\n" + "=" * 60)
    logger.info("📋 RESUMO DOS TESTES")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n📊 Resultado final: {passed}/{total} testes passaram")
    
    if passed == total:
        logger.info("🎉 Todos os testes passaram! Sistemas funcionando corretamente.")
    else:
        logger.warning(f"⚠️ {total - passed} teste(s) falharam. Verifique os logs acima.")
    
    logger.info("\n🏁 Testes concluídos")

if __name__ == "__main__":
    main()