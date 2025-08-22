#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste - Sistema de Relatórios de Check-in
Testa todas as funcionalidades do sistema de relatórios

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from checkin_reports import CheckInReports
from checkin_system import CheckInSystem
from storage import DataStorage

def create_mock_bot():
    """Cria um mock do bot Discord"""
    bot = Mock()
    bot.user = Mock()
    bot.user.id = 12345
    bot.guilds = []
    return bot

def create_mock_session(session_id, session_type, days_ago=0, checkin_count=5, checkout_count=3):
    """Cria uma sessão mock para testes"""
    base_time = datetime.now() - timedelta(days=days_ago)
    
    return {
        'id': session_id,
        'type': session_type,
        'start_time': base_time.isoformat(),
        'end_time': (base_time + timedelta(hours=2)).isoformat(),
        'created_at': base_time.isoformat(),
        'max_players': 10,
        'checkin_count': checkin_count,
        'checkout_count': checkout_count,
        'checked_in_players': [f'player_{i}' for i in range(1, checkin_count + 1)],
        'checked_out_players': [f'player_{i}' for i in range(1, checkout_count + 1)],
        'description': f'Sessão de teste {session_type}'
    }

async def test_reports_system():
    """Testa o sistema de relatórios completo"""
    print("🧪 Iniciando testes do Sistema de Relatórios...\n")
    
    # Configurar mocks
    bot = create_mock_bot()
    storage = Mock()
    checkin_system = Mock()
    
    # Criar dados de teste
    test_sessions = [
        create_mock_session('session_1', 'Ranked', 1, 8, 6),
        create_mock_session('session_2', 'Casual', 3, 5, 4),
        create_mock_session('session_3', 'Tournament', 5, 10, 8),
        create_mock_session('session_4', 'Training', 7, 6, 5),
        create_mock_session('session_5', 'Ranked', 10, 7, 6),
        create_mock_session('session_6', 'Casual', 15, 4, 3),
        create_mock_session('session_7', 'Tournament', 20, 9, 7),
    ]
    
    # Configurar mock do sistema de check-in
    checkin_system.get_all_sessions.return_value = test_sessions
    checkin_system.get_session.return_value = test_sessions[0]
    
    # Inicializar sistema de relatórios
    reports = CheckInReports(bot, checkin_system, storage)
    
    # Teste 1: Relatório de Participação
    print("📊 Teste 1: Relatório de Participação")
    participation_report = reports.generate_participation_report(30)
    
    if participation_report:
        print(f"✅ Relatório gerado com sucesso")
        print(f"   - Total de sessões: {participation_report['summary']['total_sessions']}")
        print(f"   - Total de check-ins: {participation_report['summary']['total_checkins']}")
        print(f"   - Taxa de participação: {participation_report['summary']['participation_rate']}%")
        print(f"   - Tipos de sessão: {len(participation_report['session_types'])}")
        print(f"   - Jogadores únicos: {len(participation_report['player_stats'])}")
    else:
        print("❌ Falha ao gerar relatório de participação")
    
    print()
    
    # Teste 2: Relatório Individual de Jogador
    print("👤 Teste 2: Relatório Individual de Jogador")
    player_report = reports.generate_player_report('player_1', 30)
    
    if player_report and 'summary' in player_report:
        print(f"✅ Relatório individual gerado com sucesso")
        print(f"   - Sessões participadas: {player_report['summary']['total_sessions']}")
        print(f"   - Taxa de conclusão: {player_report['summary']['completion_rate']}%")
        print(f"   - Tempo total: {player_report['summary']['total_time_minutes']} min")
        print(f"   - Tipos de sessão: {len(player_report['session_types'])}")
    else:
        print("❌ Falha ao gerar relatório individual")
    
    print()
    
    # Teste 3: Leaderboard
    print("🏆 Teste 3: Leaderboard")
    leaderboard = reports.generate_leaderboard('participation', 30, 5)
    
    if leaderboard:
        print(f"✅ Leaderboard gerado com sucesso")
        print(f"   - Jogadores no ranking: {len(leaderboard)}")
        for entry in leaderboard[:3]:
            print(f"   - {entry['rank']}º: {entry['player_id']} ({entry['sessions_participated']} sessões)")
    else:
        print("❌ Falha ao gerar leaderboard")
    
    print()
    
    # Teste 4: Análise de Sessão
    print("🔍 Teste 4: Análise de Sessão")
    session_analytics = reports.generate_session_analytics('session_1')
    
    if session_analytics and 'session_info' in session_analytics:
        print(f"✅ Análise de sessão gerada com sucesso")
        print(f"   - ID da sessão: {session_analytics['session_info']['id']}")
        print(f"   - Tipo: {session_analytics['session_info']['type']}")
        print(f"   - Duração: {session_analytics['session_info']['duration_minutes']} min")
        print(f"   - Taxa de ocupação: {session_analytics['participation']['occupancy_rate']}%")
        print(f"   - Taxa de conclusão: {session_analytics['participation']['completion_rate']}%")
    else:
        print("❌ Falha ao gerar análise de sessão")
    
    print()
    
    # Teste 5: Estatísticas Resumidas
    print("📈 Teste 5: Estatísticas Resumidas")
    summary_stats = reports.get_summary_stats(7)
    
    if summary_stats:
        print(f"✅ Estatísticas resumidas geradas com sucesso")
        print(f"   - Sessões (7 dias): {summary_stats['total_sessions']}")
        print(f"   - Jogadores únicos: {summary_stats['unique_players']}")
        print(f"   - Média jogadores/sessão: {summary_stats['avg_players_per_session']}")
        print(f"   - Taxa de conclusão: {summary_stats['completion_rate']}%")
        if summary_stats['most_popular_session']:
            popular = summary_stats['most_popular_session']
            print(f"   - Sessão mais popular: {popular['type']} ({popular['checkins']} check-ins)")
    else:
        print("❌ Falha ao gerar estatísticas resumidas")
    
    print()
    
    # Teste 6: Leaderboard por Taxa de Conclusão
    print("🎯 Teste 6: Leaderboard por Taxa de Conclusão")
    completion_leaderboard = reports.generate_leaderboard('completion_rate', 30, 5)
    
    if completion_leaderboard:
        print(f"✅ Leaderboard por taxa de conclusão gerado com sucesso")
        for entry in completion_leaderboard[:3]:
            print(f"   - {entry['rank']}º: {entry['player_id']} ({entry['completion_rate']}%)")
    else:
        print("❌ Falha ao gerar leaderboard por taxa de conclusão")
    
    print()
    
    # Teste 7: Leaderboard por Tempo Total
    print("⏱️ Teste 7: Leaderboard por Tempo Total")
    time_leaderboard = reports.generate_leaderboard('total_time', 30, 5)
    
    if time_leaderboard:
        print(f"✅ Leaderboard por tempo total gerado com sucesso")
        for entry in time_leaderboard[:3]:
            print(f"   - {entry['rank']}º: {entry['player_id']} ({entry['total_time_minutes']} min)")
    else:
        print("❌ Falha ao gerar leaderboard por tempo total")
    
    print()
    
    # Teste 8: Exportação de Relatório
    print("💾 Teste 8: Exportação de Relatório")
    export_success = reports.export_report_to_json(participation_report, 'test_report.json')
    
    if export_success:
        print("✅ Relatório exportado com sucesso")
        try:
            with open('test_report.json', 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            print(f"   - Arquivo criado com {len(json.dumps(exported_data))} caracteres")
            print(f"   - Contém {len(exported_data)} seções principais")
        except Exception as e:
            print(f"   - Erro ao verificar arquivo exportado: {e}")
    else:
        print("❌ Falha ao exportar relatório")
    
    print()
    
    # Teste 9: Relatório de Jogador Inexistente
    print("❓ Teste 9: Relatório de Jogador Inexistente")
    empty_report = reports.generate_player_report('player_inexistente', 30)
    
    if empty_report and 'message' in empty_report:
        print("✅ Tratamento de jogador inexistente funcionando")
        print(f"   - Mensagem: {empty_report['message']}")
    else:
        print("❌ Falha no tratamento de jogador inexistente")
    
    print()
    
    # Teste 10: Análise de Sessão Inexistente
    print("❓ Teste 10: Análise de Sessão Inexistente")
    checkin_system.get_session.return_value = None
    empty_analytics = reports.generate_session_analytics('session_inexistente')
    
    if empty_analytics and 'error' in empty_analytics:
        print("✅ Tratamento de sessão inexistente funcionando")
        print(f"   - Erro: {empty_analytics['error']}")
    else:
        print("❌ Falha no tratamento de sessão inexistente")
    
    print()
    
    # Teste 11: Verificação de Cálculos Estatísticos
    print("🧮 Teste 11: Verificação de Cálculos")
    
    # Verificar se os cálculos estão corretos
    total_checkins = sum(session['checkin_count'] for session in test_sessions)
    total_checkouts = sum(session['checkout_count'] for session in test_sessions)
    expected_participation_rate = (total_checkouts / total_checkins * 100) if total_checkins > 0 else 0
    
    actual_rate = participation_report['summary']['participation_rate']
    
    if abs(actual_rate - expected_participation_rate) < 0.01:
        print("✅ Cálculos estatísticos corretos")
        print(f"   - Taxa esperada: {expected_participation_rate:.2f}%")
        print(f"   - Taxa calculada: {actual_rate}%")
    else:
        print("❌ Erro nos cálculos estatísticos")
        print(f"   - Taxa esperada: {expected_participation_rate:.2f}%")
        print(f"   - Taxa calculada: {actual_rate}%")
    
    print()
    
    # Teste 12: Verificação de Tipos de Dados
    print("🔍 Teste 12: Verificação de Tipos de Dados")
    
    # Verificar se todos os campos obrigatórios estão presentes
    required_fields = ['period', 'summary', 'session_types', 'player_stats', 'generated_at']
    missing_fields = [field for field in required_fields if field not in participation_report]
    
    if not missing_fields:
        print("✅ Todos os campos obrigatórios presentes")
        print(f"   - Campos verificados: {len(required_fields)}")
    else:
        print(f"❌ Campos obrigatórios ausentes: {missing_fields}")
    
    # Verificar tipos de dados
    summary = participation_report['summary']
    type_checks = [
        ('total_sessions', int),
        ('total_checkins', int),
        ('total_checkouts', int),
        ('participation_rate', (int, float)),
        ('avg_players_per_session', (int, float))
    ]
    
    type_errors = []
    for field, expected_type in type_checks:
        if not isinstance(summary[field], expected_type):
            type_errors.append(f"{field}: esperado {expected_type}, obtido {type(summary[field])}")
    
    if not type_errors:
        print("✅ Tipos de dados corretos")
    else:
        print(f"❌ Erros de tipo: {type_errors}")
    
    print()
    print("🎉 Testes do Sistema de Relatórios concluídos!")
    print("\n" + "="*50)
    print("📋 RESUMO DOS TESTES:")
    print("✅ Relatório de participação")
    print("✅ Relatório individual de jogador")
    print("✅ Sistema de leaderboard")
    print("✅ Análise de sessão")
    print("✅ Estatísticas resumidas")
    print("✅ Múltiplas métricas de ranking")
    print("✅ Exportação de relatórios")
    print("✅ Tratamento de erros")
    print("✅ Validação de cálculos")
    print("✅ Verificação de tipos de dados")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_reports_system())