#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para a API do PUBG
Testa todas as funcionalidades implementadas
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from features.pubg.api import PUBGIntegration
from core.config.settings import settings

async def test_pubg_api():
    """Testa todas as funcionalidades da API do PUBG"""
    print("=" * 60)
    print("TESTE COMPLETO DA API DO PUBG")
    print("=" * 60)
    
    # Inicializar a API
    pubg_api = PUBGIntegration()
    
    # Nome de jogador para teste (use um jogador real ou conhecido)
    test_player = "shroud"  # Jogador famoso para teste
    
    print(f"\n1. TESTANDO HEALTH CHECK...")
    try:
        health = await pubg_api.health_check()
        print(f"✅ Health Check: {health['status']}")
        print(f"   API Key válida: {health['api_key_valid']}")
        print(f"   API disponível: {health['api_available']}")
    except Exception as e:
        print(f"❌ Erro no Health Check: {e}")
    
    print(f"\n2. TESTANDO VALIDAÇÃO DE JOGADOR...")
    try:
        is_valid = await pubg_api.validate_player_with_fallback(test_player)
        print(f"✅ Jogador '{test_player}' válido: {is_valid}")
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
    
    print(f"\n3. TESTANDO DADOS ESSENCIAIS...")
    try:
        essential_data = await pubg_api.get_essential_player_data(test_player)
        print(f"✅ Dados essenciais obtidos")
        print(f"   Tipo de dados: {essential_data.get('data_type', 'N/A')}")
        print(f"   Fallback mode: {essential_data.get('fallback_mode', False)}")
        if 'player_info' in essential_data:
            print(f"   Nome: {essential_data['player_info'].get('name', 'N/A')}")
    except Exception as e:
        print(f"❌ Erro nos dados essenciais: {e}")
    
    print(f"\n4. TESTANDO DADOS DE RANKING...")
    try:
        rank_data = await pubg_api.get_quick_rank_data(test_player)
        print(f"✅ Dados de ranking obtidos")
        print(f"   K/D Ratio: {rank_data.get('kd_ratio', 0):.2f}")
        print(f"   Win Rate: {rank_data.get('win_rate', 0):.1f}%")
        print(f"   Rank Score: {rank_data.get('rank_score', 0)}")
        print(f"   Total Matches: {rank_data.get('total_matches', 0)}")
    except Exception as e:
        print(f"❌ Erro nos dados de ranking: {e}")
    
    print(f"\n5. TESTANDO ESTATÍSTICAS COMPLETAS COM FALLBACK...")
    try:
        full_stats = await pubg_api.get_player_stats_with_fallback(test_player, 'steam')
        print(f"✅ Estatísticas completas obtidas")
        print(f"   Fallback mode: {full_stats.get('fallback_mode', False)}")
        if 'cache_info' in full_stats:
            cache_info = full_stats['cache_info']
            print(f"   Cache hits: {cache_info.get('hits', 0)}")
            print(f"   Cache misses: {cache_info.get('misses', 0)}")
    except Exception as e:
        print(f"❌ Erro nas estatísticas completas: {e}")
    
    print(f"\n6. TESTANDO CONSULTA EM LOTE...")
    try:
        test_players = ["shroud", "DrDisrespect", "summit1g"]
        batch_results = await pubg_api.get_batch_player_stats(test_players, max_concurrent=2)
        print(f"✅ Consulta em lote concluída")
        print(f"   Jogadores processados: {len(batch_results)}")
        for player, data in batch_results.items():
            fallback = data.get('fallback_mode', False)
            print(f"   {player}: {'Fallback' if fallback else 'Dados reais'}")
    except Exception as e:
        print(f"❌ Erro na consulta em lote: {e}")
    
    print(f"\n7. TESTANDO ESTATÍSTICAS DO CACHE...")
    try:
        cache_stats = pubg_api.get_cache_stats()
        print(f"✅ Estatísticas do cache")
        print(f"   Total de entradas: {cache_stats['cache']['total_entries']}")
        print(f"   Hit rate: {cache_stats['cache']['hit_rate_percent']:.1f}%")
        print(f"   Rate limiting - Requests: {cache_stats['rate_limiting']['requests_in_window']}/{cache_stats['rate_limiting']['max_requests']}")
    except Exception as e:
        print(f"❌ Erro nas estatísticas do cache: {e}")
    
    print(f"\n8. TESTANDO OTIMIZAÇÕES...")
    try:
        optimization = pubg_api.optimize_api_usage()
        print(f"✅ Análise de otimização")
        print(f"   Sugestões: {len(optimization['optimization_suggestions'])}")
        for suggestion in optimization['optimization_suggestions'][:3]:  # Mostrar apenas 3
            print(f"   - {suggestion}")
    except Exception as e:
        print(f"❌ Erro na análise de otimização: {e}")
    
    print(f"\n9. TESTANDO LIMPEZA DE CACHE...")
    try:
        # Limpar cache expirado
        cleared = pubg_api.clear_expired_cache()
        print(f"✅ Cache expirado limpo: {cleared} entradas removidas")
    except Exception as e:
        print(f"❌ Erro na limpeza de cache: {e}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
    
    # Estatísticas finais
    try:
        final_stats = pubg_api.get_cache_stats()
        print(f"\nEstatísticas finais:")
        print(f"Cache entries: {final_stats['cache']['total_entries']}")
        print(f"Hit rate: {final_stats['cache']['hit_rate_percent']:.1f}%")
        print(f"API calls realizadas: {final_stats['rate_limiting']['requests_in_window']}")
        print(f"Status da API: {final_stats['api_health']['status']}")
    except Exception as e:
        print(f"Erro nas estatísticas finais: {e}")

if __name__ == "__main__":
    # Verificar se a API key está configurada
    if not settings.PUBG_API_KEY:
        print("❌ PUBG_API_KEY não configurada!")
        print("Configure a variável de ambiente PUBG_API_KEY antes de executar o teste.")
        sys.exit(1)
    
    print(f"🔑 API Key configurada: {settings.PUBG_API_KEY[:10]}...")
    
    # Executar testes
    try:
        asyncio.run(test_pubg_api())
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro geral no teste: {e}")
        import traceback
        traceback.print_exc()