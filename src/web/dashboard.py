import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
# from flask_socketio import SocketIO, emit
import asyncio
import threading
from storage import DataStorage
from pubg_api import PUBGIntegration
from rank import RankSystem
import logging
import random

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WebDashboard')

class WebDashboard:
    def __init__(self, bot=None):
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.app.config['SECRET_KEY'] = 'hawk_esports_secret_key_2024'
        CORS(self.app)
        # self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Inicializar módulos
        self.storage = DataStorage()
        self.pubg_api = PUBGIntegration()
        self.bot = bot
        
        # Configurar rotas
        self.setup_routes()
        # self.setup_websocket_events()
        
        logger.info("Dashboard Web inicializado com sucesso!")

    # def setup_websocket_events(self):
    #     """Configurar eventos WebSocket para notificações em tempo real"""
    #     
    #     @self.socketio.on('connect')
    #     def handle_connect():
    #         logger.info('Cliente conectado ao WebSocket')
    #         emit('connected', {'message': 'Conectado ao sistema de notificações Hawk Esports'})
    #     
    #     @self.socketio.on('disconnect')
    #     def handle_disconnect():
    #         logger.info('Cliente desconectado do WebSocket')
    #     
    #     @self.socketio.on('join_notifications')
    #     def handle_join_notifications(data):
    #         """Cliente solicita para receber notificações"""
    #         logger.info(f'Cliente solicitou notificações: {data}')
    #         emit('notification_status', {'status': 'subscribed', 'message': 'Você está recebendo notificações em tempo real'})
    
    # def send_notification(self, notification_type, data):
    #     """Enviar notificação para todos os clientes conectados"""
    #     try:
    #         notification = {
    #             'type': notification_type,
    #             'timestamp': datetime.now().isoformat(),
    #             'data': data
    #         }
    #         self.socketio.emit('notification', notification)
    #         logger.info(f'Notificação enviada: {notification_type}')
    #     except Exception as e:
    #         logger.error(f'Erro ao enviar notificação: {e}')
    # 
    # def send_player_update(self, player_data):
    #     """Enviar atualização de jogador"""
    #     self.send_notification('player_update', {
    #         'player_name': player_data.get('discord_name', 'Jogador'),
    #         'message': f"{player_data.get('discord_name', 'Jogador')} atualizou suas estatísticas!",
    #         'stats': player_data.get('pubg_stats', {})
    #     })
    # 
    # def send_tournament_update(self, tournament_data):
    #     """Enviar atualização de torneio"""
    #     self.send_notification('tournament_update', {
    #         'tournament_name': tournament_data.get('name', 'Torneio'),
    #         'message': f"Torneio '{tournament_data.get('name', 'Torneio')}' foi atualizado!",
    #         'status': tournament_data.get('status', 'unknown')
    #     })
    
    # def send_new_clip(self, clip_data):
    #     """Enviar notificação de novo clipe"""
    #     self.send_notification('new_clip', {
    #         'player_name': clip_data.get('player_name', 'Jogador'),
    #         'clip_title': clip_data.get('title', 'Novo Clipe'),
    #         'message': f"{clip_data.get('player_name', 'Jogador')} postou um novo clipe: {clip_data.get('title', 'Novo Clipe')}",
    #         'url': clip_data.get('url', '#')
    #     })

    def setup_routes(self):
        """Configurar todas as rotas do dashboard"""
        
        @self.app.route('/')
        def dashboard():
            """Página principal do dashboard"""
            return render_template('dashboard.html')
        
        @self.app.route('/player')
        def player_profile():
            """Página de perfil do jogador"""
            return render_template('player_profile.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            """API para obter estatísticas gerais"""
            try:
                # Obter dados dos jogadores registrados
                data = self.storage.load_data()
                players_data = data.get('players', {})
                
                # Calcular estatísticas
                total_players = len(players_data)
                active_players = sum(1 for p in players_data.values() if (p.get('last_update') or 0) > (datetime.now().timestamp() - 604800))  # 7 dias
                
                # Obter dados de torneios
                tournaments_data = data.get('tournaments', {})
                active_tournaments = sum(1 for t in tournaments_data.values() if t.get('status') == 'active')
                
                # Obter dados de clipes
                clips_data = data.get('medal_clips', {})
                total_clips = len(clips_data)
                
                stats = {
                    'total_players': total_players,
                    'active_players': active_players,
                    'active_tournaments': active_tournaments,
                    'total_clips': total_clips,
                    'last_update': datetime.now().isoformat()
                }
                
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Erro ao obter estatísticas: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/leaderboard')
        def get_leaderboard():
            """API para obter leaderboard com filtros avançados"""
            try:
                mode = request.args.get('mode', 'squad')
                period = request.args.get('period', 'all')
                sort_by = request.args.get('sort_by', 'kd_ratio')
                limit = int(request.args.get('limit', 20))
                region = request.args.get('region', 'all')
                
                # Obter dados dos jogadores
                data = self.storage.load_data()
                players_data = data.get('players', {})
                leaderboard = []
                
                # Calcular timestamp para filtro de período
                now = datetime.now()
                period_filter = None
                if period == 'daily':
                    period_filter = now - timedelta(days=1)
                elif period == 'weekly':
                    period_filter = now - timedelta(days=7)
                elif period == 'monthly':
                    period_filter = now - timedelta(days=30)
                
                for discord_id, player_data in players_data.items():
                    # Filtro por período
                    if period_filter and 'last_update' in player_data:
                        try:
                            last_update = datetime.fromtimestamp(player_data['last_update'])
                            if last_update < period_filter:
                                continue
                        except:
                            continue
                    
                    # Filtro por região
                    if region != 'all' and player_data.get('shard', '').lower() != region.lower():
                        continue
                    
                    if 'pubg_stats' in player_data:
                        stats = player_data['pubg_stats'].get(mode, {})
                        if stats:
                            kills = stats.get('kills', 0)
                            deaths = stats.get('deaths', 0)
                            wins = stats.get('wins', 0)
                            matches = stats.get('roundsPlayed', 0)
                            damage = stats.get('damageDealt', 0)
                            
                            player_entry = {
                                'discord_id': discord_id,
                                'pubg_name': player_data.get('pubg_name', 'Unknown'),
                                'shard': player_data.get('shard', 'Unknown'),
                                'kills': kills,
                                'deaths': deaths,
                                'kd_ratio': round(kills / max(deaths, 1), 2),
                                'wins': wins,
                                'matches': matches,
                                'damage': damage,
                                'avg_damage': round(damage / max(matches, 1), 2),
                                'win_rate': round((wins / max(matches, 1)) * 100, 2),
                                'last_update': player_data.get('last_update', 0)
                            }
                            leaderboard.append(player_entry)
                
                # Ordenar por critério selecionado
                sort_key_map = {
                    'kd_ratio': lambda x: x['kd_ratio'],
                    'kills': lambda x: x['kills'],
                    'wins': lambda x: x['wins'],
                    'damage': lambda x: x['damage'],
                    'avg_damage': lambda x: x['avg_damage'],
                    'win_rate': lambda x: x['win_rate'],
                    'matches': lambda x: x['matches']
                }
                
                if sort_by in sort_key_map:
                    leaderboard.sort(key=sort_key_map[sort_by], reverse=True)
                else:
                    leaderboard.sort(key=lambda x: x['kd_ratio'], reverse=True)
                
                return jsonify(leaderboard[:limit])
            except Exception as e:
                logger.error(f"Erro ao obter leaderboard: {e}")
                return jsonify([])  # Retornar array vazio em caso de erro
        
        @self.app.route('/api/tournaments')
        def get_tournaments():
            """API para obter torneios"""
            try:
                data = self.storage.load_data()
                tournaments_data = data.get('tournaments', {})
                tournaments = []
                
                for tournament_id, tournament in tournaments_data.items():
                    tournaments.append({
                        'id': tournament_id,
                        'name': tournament.get('name', 'Unknown'),
                        'type': tournament.get('type', 'single_elimination'),
                        'status': tournament.get('status', 'pending'),
                        'participants': len(tournament.get('participants', [])),
                        'max_participants': tournament.get('max_participants', 16),
                        'created_at': tournament.get('created_at', ''),
                        'prize': tournament.get('prize', 'N/A')
                    })
                
                return jsonify(tournaments)
            except Exception as e:
                logger.error(f"Erro ao obter torneios: {e}")
                return jsonify([])  # Retornar array vazio em caso de erro
        
        @self.app.route('/api/clips')
        def get_clips():
            """API para obter clipes recentes"""
            try:
                data = self.storage.load_data()
                clips_data = data.get('medal_clips', {})
                clips = []
                
                for clip_id, clip in clips_data.items():
                    clips.append({
                        'id': clip_id,
                        'title': clip.get('title', 'Clip sem título'),
                        'player': clip.get('player_name', 'Unknown'),
                        'game': clip.get('game', 'PUBG'),
                        'url': clip.get('url', ''),
                        'created_at': clip.get('created_at', ''),
                        'views': clip.get('views', 0)
                    })
                
                # Ordenar por data de criação (mais recentes primeiro)
                clips.sort(key=lambda x: x['created_at'], reverse=True)
                
                return jsonify(clips[:10])  # 10 clipes mais recentes
            except Exception as e:
                logger.error(f"Erro ao obter clipes: {e}")
                return jsonify([])  # Retornar array vazio em caso de erro
        
        @self.app.route('/api/player/<discord_id>')
        def get_player_details(discord_id):
            """API para obter detalhes de um jogador específico"""
            try:
                data = self.storage.load_data()
                players_data = data.get('players', {})
                player = players_data.get(discord_id)
                
                if not player:
                    return jsonify({'error': 'Jogador não encontrado'}), 404
                
                # Obter clipes do jogador
                clips_data = data.get('medal_clips', {})
                player_clips = [clip for clip in clips_data.values() if clip.get('discord_id') == discord_id]
                
                # Calcular estatísticas avançadas
                stats = player.get('pubg_stats', {})
                squad_stats = stats.get('squad', {})
                advanced_stats = {
                    'headshot_rate': round((squad_stats.get('headshots', 0) / max(squad_stats.get('kills', 1), 1)) * 100, 1),
                    'survival_rate': round((squad_stats.get('top10s', 0) / max(squad_stats.get('roundsPlayed', 1), 1)) * 100, 1),
                    'avg_placement': squad_stats.get('avgRank', 0),
                    'longest_kill': squad_stats.get('longestKill', 0),
                    'vehicle_destroys': squad_stats.get('vehicleDestroys', 0),
                    'road_kills': squad_stats.get('roadKills', 0),
                    'team_kills': squad_stats.get('teamKills', 0),
                    'revives': squad_stats.get('revives', 0),
                    'boosts': squad_stats.get('boosts', 0)
                }
                
                player_details = {
                    'discord_id': discord_id,
                    'pubg_name': player.get('pubg_name', 'Unknown'),
                    'shard': player.get('shard', 'Unknown'),
                    'rank': player.get('rank', 'Sem Rank'),
                    'registration_date': player.get('registration_date', ''),
                    'last_update': player.get('last_update', ''),
                    'pubg_stats': stats,
                    'advanced_stats': advanced_stats,
                    'clips_count': len(player_clips),
                    'recent_clips': player_clips[:10],  # 10 clipes mais recentes
                    'achievements': player.get('achievements', []),
                    'join_date': player.get('registration_date', 'N/A'),
                    'last_active': player.get('last_update', 'N/A')
                }
                
                return jsonify(player_details)
            except Exception as e:
                logger.error(f"Erro ao obter detalhes do jogador: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/player/<discord_id>/stats-history')
        def get_player_stats_history(discord_id):
            """Obter histórico de estatísticas do jogador para gráficos"""
            try:
                # Simular dados históricos (em uma implementação real, isso viria do banco de dados)
                import random
                from datetime import datetime, timedelta
                
                history = []
                base_date = datetime.now() - timedelta(days=30)
                
                for i in range(30):
                    date = base_date + timedelta(days=i)
                    history.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'kills': random.randint(0, 15),
                        'damage': random.randint(0, 2500),
                        'matches': random.randint(0, 5),
                        'wins': random.randint(0, 2),
                        'kd_ratio': round(random.uniform(0.5, 3.0), 2)
                    })
                
                return jsonify(history)
            except Exception as e:
                logger.error(f"Erro ao obter histórico de estatísticas: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/test-notification')
        def test_notification():
            """Rota para testar notificações (apenas para desenvolvimento)"""
            try:
                notification_type = request.args.get('type', 'player_update')
                
                if notification_type == 'player_update':
                    # self.send_player_update({
                    #     'discord_name': 'TestPlayer',
                    #     'pubg_stats': {'squad': {'kills': 150, 'wins': 25}}
                    # })
                    pass
                elif notification_type == 'tournament_update':
                    # self.send_tournament_update({
                    #     'name': 'Torneio de Teste',
                    #     'status': 'active'
                    # })
                    pass
                elif notification_type == 'new_clip':
                    # self.send_new_clip({
                    #     'player_name': 'TestPlayer',
                    #     'title': 'Clipe Incrível!',
                    #     'url': '#'
                    # })
                    pass
                
                return jsonify({'success': True, 'message': f'Notificação {notification_type} enviada!'})
            except Exception as e:
                logger.error(f"Erro ao enviar notificação de teste: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/players-growth')
        def get_players_growth():
            """API para obter dados de crescimento de jogadores ao longo do tempo"""
            try:
                data = self.storage.load_data()
                players_data = data.get('players', {})
                
                # Simular dados históricos (em um cenário real, você teria dados históricos salvos)
                growth_data = []
                current_date = datetime.now()
                
                for i in range(30, 0, -1):  # Últimos 30 dias
                    date = current_date - timedelta(days=i)
                    # Simular crescimento gradual
                    player_count = max(1, len(players_data) - (i * 2))
                    growth_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'players': player_count
                    })
                
                return jsonify(growth_data)
            except Exception as e:
                logger.error(f"Erro ao obter dados de crescimento: {e}")
                return jsonify([])
        
        @self.app.route('/api/charts/activity')
        def get_activity_data():
            """API para obter dados de atividade dos jogadores"""
            try:
                data = self.storage.load_data()
                players_data = data.get('players', {})
                
                # Calcular atividade por dia da semana
                activity_by_day = {
                    'Segunda': 0, 'Terça': 0, 'Quarta': 0, 'Quinta': 0,
                    'Sexta': 0, 'Sábado': 0, 'Domingo': 0
                }
                
                days_map = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                
                for player_data in players_data.values():
                    if 'last_update' in player_data and player_data['last_update']:
                        try:
                            last_update = datetime.fromtimestamp(player_data['last_update'])
                            day_name = days_map[last_update.weekday()]
                            activity_by_day[day_name] += 1
                        except:
                            continue
                
                return jsonify({
                    'labels': list(activity_by_day.keys()),
                    'data': list(activity_by_day.values())
                })
            except Exception as e:
                logger.error(f"Erro ao obter dados de atividade: {e}")
                return jsonify({'labels': [], 'data': []})
        
        @self.app.route('/api/charts/performance')
        def get_performance_data():
            """API para obter dados de performance dos top jogadores"""
            try:
                data = self.storage.load_data()
                players_data = data.get('players', {})
                
                # Obter top 10 jogadores por K/D
                top_players = []
                for discord_id, player_data in players_data.items():
                    if 'pubg_stats' in player_data:
                        stats = player_data['pubg_stats'].get('squad', {})
                        if stats:
                            kd_ratio = stats.get('kills', 0) / max(stats.get('deaths', 1), 1)
                            top_players.append({
                                'name': player_data.get('pubg_name', 'Unknown')[:10],  # Limitar nome
                                'kd': round(kd_ratio, 2),
                                'kills': stats.get('kills', 0),
                                'wins': stats.get('wins', 0)
                            })
                
                # Ordenar e pegar top 10
                top_players.sort(key=lambda x: x['kd'], reverse=True)
                top_players = top_players[:10]
                
                return jsonify({
                    'labels': [p['name'] for p in top_players],
                    'kd_data': [p['kd'] for p in top_players],
                    'kills_data': [p['kills'] for p in top_players],
                    'wins_data': [p['wins'] for p in top_players]
                })
            except Exception as e:
                logger.error(f"Erro ao obter dados de performance: {e}")
                return jsonify({'labels': [], 'kd_data': [], 'kills_data': [], 'wins_data': []})
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Executar o servidor web"""
        logger.info(f"Iniciando dashboard web em http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    async def run_async(self, host='0.0.0.0', port=5000):
        """Executar o servidor web de forma assíncrona"""
        logger.info(f"Iniciando dashboard web assíncrono em http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    dashboard = WebDashboard()
    dashboard.run(host='0.0.0.0', port=5000, debug=True)