#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Relatórios e Estatísticas de Check-in
Gera relatórios detalhados sobre participação e estatísticas

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import logging
import json

logger = logging.getLogger('HawkBot.CheckInReports')

class CheckInReports:
    """Sistema de relatórios e estatísticas de check-in"""
    
    def __init__(self, bot, checkin_system, storage):
        self.bot = bot
        self.checkin_system = checkin_system
        self.storage = storage
        
        logger.info("Sistema de Relatórios de Check-in inicializado")
    
    def generate_participation_report(self, days: int = 30) -> Dict[str, Any]:
        """Gera relatório de participação dos últimos N dias"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obter todas as sessões do período
            all_sessions = self.checkin_system.get_all_sessions()
            period_sessions = [
                session for session in all_sessions
                if start_date <= datetime.fromisoformat(session['created_at']) <= end_date
            ]
            
            # Estatísticas gerais
            total_sessions = len(period_sessions)
            total_checkins = sum(session.get('checkin_count', 0) for session in period_sessions)
            total_checkouts = sum(session.get('checkout_count', 0) for session in period_sessions)
            
            # Estatísticas por tipo de sessão
            session_types = Counter(session['type'] for session in period_sessions)
            
            # Estatísticas por jogador
            player_stats = self._calculate_player_stats(period_sessions)
            
            # Estatísticas por dia da semana
            weekday_stats = self._calculate_weekday_stats(period_sessions)
            
            # Estatísticas por horário
            hourly_stats = self._calculate_hourly_stats(period_sessions)
            
            # Taxa de participação
            participation_rate = (total_checkouts / total_checkins * 100) if total_checkins > 0 else 0
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_sessions': total_sessions,
                    'total_checkins': total_checkins,
                    'total_checkouts': total_checkouts,
                    'participation_rate': round(participation_rate, 2),
                    'avg_players_per_session': round(total_checkins / total_sessions, 2) if total_sessions > 0 else 0
                },
                'session_types': dict(session_types),
                'player_stats': player_stats,
                'weekday_stats': weekday_stats,
                'hourly_stats': hourly_stats,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Relatório de participação gerado para {days} dias")
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de participação: {e}")
            return {}
    
    def _calculate_player_stats(self, sessions: List[Dict]) -> Dict[str, Dict]:
        """Calcula estatísticas por jogador"""
        player_stats = defaultdict(lambda: {
            'checkins': 0,
            'checkouts': 0,
            'sessions_participated': 0,
            'session_types': defaultdict(int),
            'total_time': 0,  # em minutos
            'avg_session_time': 0
        })
        
        for session in sessions:
            session_duration = self._calculate_session_duration(session)
            
            # Processar check-ins
            for player_id in session.get('checked_in_players', []):
                stats = player_stats[player_id]
                stats['checkins'] += 1
                stats['sessions_participated'] += 1
                stats['session_types'][session['type']] += 1
                
                # Se o jogador fez check-out, adicionar tempo
                if player_id in session.get('checked_out_players', []):
                    stats['checkouts'] += 1
                    stats['total_time'] += session_duration
        
        # Calcular médias
        for player_id, stats in player_stats.items():
            if stats['checkouts'] > 0:
                stats['avg_session_time'] = round(stats['total_time'] / stats['checkouts'], 2)
            stats['session_types'] = dict(stats['session_types'])
        
        return dict(player_stats)
    
    def _calculate_weekday_stats(self, sessions: List[Dict]) -> Dict[str, int]:
        """Calcula estatísticas por dia da semana"""
        weekday_names = {
            0: 'Segunda-feira',
            1: 'Terça-feira', 
            2: 'Quarta-feira',
            3: 'Quinta-feira',
            4: 'Sexta-feira',
            5: 'Sábado',
            6: 'Domingo'
        }
        
        weekday_counts = defaultdict(int)
        
        for session in sessions:
            session_date = datetime.fromisoformat(session['start_time'])
            weekday = session_date.weekday()
            weekday_counts[weekday_names[weekday]] += 1
        
        return dict(weekday_counts)
    
    def _calculate_hourly_stats(self, sessions: List[Dict]) -> Dict[str, int]:
        """Calcula estatísticas por horário"""
        hourly_counts = defaultdict(int)
        
        for session in sessions:
            session_time = datetime.fromisoformat(session['start_time'])
            hour_range = f"{session_time.hour:02d}:00-{(session_time.hour + 1) % 24:02d}:00"
            hourly_counts[hour_range] += 1
        
        return dict(sorted(hourly_counts.items()))
    
    def _calculate_session_duration(self, session: Dict) -> int:
        """Calcula duração da sessão em minutos"""
        try:
            start_time = datetime.fromisoformat(session['start_time'])
            end_time = datetime.fromisoformat(session['end_time'])
            duration = (end_time - start_time).total_seconds() / 60
            return int(duration)
        except:
            return 0
    
    def generate_player_report(self, player_id: str, days: int = 30) -> Dict[str, Any]:
        """Gera relatório individual de um jogador"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obter sessões do jogador
            all_sessions = self.checkin_system.get_all_sessions()
            player_sessions = [
                session for session in all_sessions
                if (start_date <= datetime.fromisoformat(session['created_at']) <= end_date and
                    player_id in session.get('checked_in_players', []))
            ]
            
            if not player_sessions:
                return {
                    'player_id': player_id,
                    'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
                    'message': 'Nenhuma participação encontrada no período'
                }
            
            # Calcular estatísticas
            total_sessions = len(player_sessions)
            total_checkins = total_sessions
            total_checkouts = sum(1 for session in player_sessions 
                                if player_id in session.get('checked_out_players', []))
            
            # Tipos de sessão
            session_types = Counter(session['type'] for session in player_sessions)
            
            # Tempo total
            total_time = sum(
                self._calculate_session_duration(session) 
                for session in player_sessions 
                if player_id in session.get('checked_out_players', [])
            )
            
            # Frequência por dia da semana
            weekday_frequency = self._calculate_player_weekday_frequency(player_sessions)
            
            # Horários preferidos
            preferred_hours = self._calculate_player_preferred_hours(player_sessions)
            
            # Taxa de conclusão
            completion_rate = (total_checkouts / total_checkins * 100) if total_checkins > 0 else 0
            
            report = {
                'player_id': player_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_sessions': total_sessions,
                    'total_checkins': total_checkins,
                    'total_checkouts': total_checkouts,
                    'completion_rate': round(completion_rate, 2),
                    'total_time_minutes': total_time,
                    'avg_session_time': round(total_time / total_checkouts, 2) if total_checkouts > 0 else 0
                },
                'session_types': dict(session_types),
                'weekday_frequency': weekday_frequency,
                'preferred_hours': preferred_hours,
                'recent_sessions': self._get_recent_sessions(player_sessions, 5),
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Relatório individual gerado para jogador {player_id}")
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório do jogador: {e}")
            return {}
    
    def _calculate_player_weekday_frequency(self, sessions: List[Dict]) -> Dict[str, int]:
        """Calcula frequência do jogador por dia da semana"""
        weekday_names = {
            0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
            3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
        }
        
        weekday_counts = defaultdict(int)
        for session in sessions:
            session_date = datetime.fromisoformat(session['start_time'])
            weekday = session_date.weekday()
            weekday_counts[weekday_names[weekday]] += 1
        
        return dict(weekday_counts)
    
    def _calculate_player_preferred_hours(self, sessions: List[Dict]) -> List[str]:
        """Calcula horários preferidos do jogador"""
        hour_counts = defaultdict(int)
        
        for session in sessions:
            session_time = datetime.fromisoformat(session['start_time'])
            hour_counts[session_time.hour] += 1
        
        # Retornar top 3 horários
        top_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return [f"{hour:02d}:00-{(hour + 1) % 24:02d}:00" for hour, _ in top_hours]
    
    def _get_recent_sessions(self, sessions: List[Dict], limit: int = 5) -> List[Dict]:
        """Obtém sessões mais recentes"""
        sorted_sessions = sorted(
            sessions, 
            key=lambda x: datetime.fromisoformat(x['start_time']), 
            reverse=True
        )
        
        return [{
            'id': session['id'],
            'type': session['type'],
            'start_time': session['start_time'],
            'duration_minutes': self._calculate_session_duration(session)
        } for session in sorted_sessions[:limit]]
    
    def generate_leaderboard(self, metric: str = 'participation', days: int = 30, limit: int = 10) -> List[Dict]:
        """Gera leaderboard baseado em métricas"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obter estatísticas de todos os jogadores
            all_sessions = self.checkin_system.get_all_sessions()
            period_sessions = [
                session for session in all_sessions
                if start_date <= datetime.fromisoformat(session['created_at']) <= end_date
            ]
            
            player_stats = self._calculate_player_stats(period_sessions)
            
            # Ordenar baseado na métrica
            if metric == 'participation':
                sorted_players = sorted(
                    player_stats.items(),
                    key=lambda x: x[1]['sessions_participated'],
                    reverse=True
                )
            elif metric == 'completion_rate':
                sorted_players = sorted(
                    player_stats.items(),
                    key=lambda x: (x[1]['checkouts'] / x[1]['checkins'] * 100) if x[1]['checkins'] > 0 else 0,
                    reverse=True
                )
            elif metric == 'total_time':
                sorted_players = sorted(
                    player_stats.items(),
                    key=lambda x: x[1]['total_time'],
                    reverse=True
                )
            else:
                sorted_players = sorted(
                    player_stats.items(),
                    key=lambda x: x[1]['sessions_participated'],
                    reverse=True
                )
            
            # Formatar leaderboard
            leaderboard = []
            for rank, (player_id, stats) in enumerate(sorted_players[:limit], 1):
                completion_rate = (stats['checkouts'] / stats['checkins'] * 100) if stats['checkins'] > 0 else 0
                
                leaderboard.append({
                    'rank': rank,
                    'player_id': player_id,
                    'sessions_participated': stats['sessions_participated'],
                    'total_checkins': stats['checkins'],
                    'total_checkouts': stats['checkouts'],
                    'completion_rate': round(completion_rate, 2),
                    'total_time_minutes': stats['total_time'],
                    'avg_session_time': stats['avg_session_time']
                })
            
            logger.info(f"Leaderboard gerado para métrica '{metric}' ({days} dias)")
            return leaderboard
            
        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard: {e}")
            return []
    
    def generate_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Gera análise detalhada de uma sessão específica"""
        try:
            session = self.checkin_system.get_session(session_id)
            if not session:
                return {'error': 'Sessão não encontrada'}
            
            # Informações básicas
            start_time = datetime.fromisoformat(session['start_time'])
            end_time = datetime.fromisoformat(session['end_time'])
            duration = self._calculate_session_duration(session)
            
            # Estatísticas de participação
            total_checkins = session.get('checkin_count', 0)
            total_checkouts = session.get('checkout_count', 0)
            max_players = session.get('max_players', 0)
            
            # Taxa de ocupação
            occupancy_rate = (total_checkins / max_players * 100) if max_players > 0 else 0
            
            # Taxa de conclusão
            completion_rate = (total_checkouts / total_checkins * 100) if total_checkins > 0 else 0
            
            # Jogadores que não fizeram check-out
            checked_in = set(session.get('checked_in_players', []))
            checked_out = set(session.get('checked_out_players', []))
            incomplete_players = list(checked_in - checked_out)
            
            analytics = {
                'session_info': {
                    'id': session_id,
                    'type': session['type'],
                    'start_time': session['start_time'],
                    'end_time': session['end_time'],
                    'duration_minutes': duration,
                    'max_players': max_players
                },
                'participation': {
                    'total_checkins': total_checkins,
                    'total_checkouts': total_checkouts,
                    'occupancy_rate': round(occupancy_rate, 2),
                    'completion_rate': round(completion_rate, 2),
                    'incomplete_players': len(incomplete_players)
                },
                'player_details': {
                    'checked_in_players': session.get('checked_in_players', []),
                    'checked_out_players': session.get('checked_out_players', []),
                    'incomplete_players': incomplete_players
                },
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Análise de sessão gerada para {session_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Erro ao gerar análise de sessão: {e}")
            return {}
    
    def export_report_to_json(self, report: Dict[str, Any], filename: str) -> bool:
        """Exporta relatório para arquivo JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Relatório exportado para {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            return False
    
    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """Obtém estatísticas resumidas para dashboard"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            all_sessions = self.checkin_system.get_all_sessions()
            recent_sessions = [
                session for session in all_sessions
                if start_date <= datetime.fromisoformat(session['created_at']) <= end_date
            ]
            
            # Estatísticas básicas
            total_sessions = len(recent_sessions)
            total_checkins = sum(session.get('checkin_count', 0) for session in recent_sessions)
            total_checkouts = sum(session.get('checkout_count', 0) for session in recent_sessions)
            
            # Jogadores únicos
            unique_players = set()
            for session in recent_sessions:
                unique_players.update(session.get('checked_in_players', []))
            
            # Sessão mais popular
            most_popular_session = None
            if recent_sessions:
                most_popular_session = max(
                    recent_sessions, 
                    key=lambda x: x.get('checkin_count', 0)
                )
            
            summary = {
                'period_days': days,
                'total_sessions': total_sessions,
                'total_checkins': total_checkins,
                'total_checkouts': total_checkouts,
                'unique_players': len(unique_players),
                'avg_players_per_session': round(total_checkins / total_sessions, 2) if total_sessions > 0 else 0,
                'completion_rate': round(total_checkouts / total_checkins * 100, 2) if total_checkins > 0 else 0,
                'most_popular_session': {
                    'id': most_popular_session['id'],
                    'type': most_popular_session['type'],
                    'checkins': most_popular_session.get('checkin_count', 0)
                } if most_popular_session else None,
                'generated_at': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas resumidas: {e}")
            return {}