#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Mini-Games e Desafios Interativos - Hawk Bot
Desenvolvido para entretenimento e engajamento da comunidade

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from discord.ext import commands
import asyncio
import logging
import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

logger = logging.getLogger('HawkBot.MinigamesSystem')

class GameSession:
    """Classe para gerenciar sessões de jogos"""
    def __init__(self, game_type: str, players: List[discord.Member], channel: discord.TextChannel):
        self.game_type = game_type
        self.players = players
        self.channel = channel
        self.created_at = datetime.now()
        self.is_active = True
        self.game_data = {}
        self.scores = {player.id: 0 for player in players}
    
    def add_score(self, player_id: int, points: int):
        """Adiciona pontos ao jogador"""
        if player_id in self.scores:
            self.scores[player_id] += points
    
    def get_winner(self) -> Optional[discord.Member]:
        """Retorna o jogador com maior pontuação"""
        if not self.scores:
            return None
        
        max_score = max(self.scores.values())
        winner_id = next(pid for pid, score in self.scores.items() if score == max_score)
        return discord.utils.get(self.players, id=winner_id)

class PUBGQuiz:
    """Sistema de Quiz sobre PUBG"""
    def __init__(self):
        self.questions = self.load_questions()
    
    def load_questions(self):
        """Carrega perguntas do arquivo de configuração"""
        try:
            if os.path.exists('minigames_config.json'):
                with open('minigames_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    questions = []
                    for difficulty, q_list in config.get('quiz_questions', {}).items():
                        for q in q_list:
                            q['difficulty'] = difficulty
                            questions.append(q)
                    return questions
        except Exception as e:
            logger.error(f"Erro ao carregar perguntas: {e}")
        
        # Fallback para perguntas padrão
        return [
            {
                "question": "Qual é o tamanho do mapa Erangel?",
                "options": ["6x6 km", "8x8 km", "4x4 km", "10x10 km"],
                "correct": 1,
                "difficulty": "easy"
            },
            {
                "question": "Qual arma tem o maior dano por tiro?",
                "options": ["AWM", "Kar98k", "M24", "Win94"],
                "correct": 0,
                "difficulty": "medium"
            }
        ]
    
    def get_random_question(self, difficulty: str = None) -> dict:
        """Retorna uma pergunta aleatória"""
        if difficulty:
            filtered = [q for q in self.questions if q['difficulty'] == difficulty]
            return random.choice(filtered) if filtered else random.choice(self.questions)
        return random.choice(self.questions)

class DailyChallenge:
    """Sistema de desafios diários"""
    def __init__(self):
        self.challenges = self.load_challenges()
    
    def load_challenges(self):
        """Carrega desafios do arquivo de configuração"""
        try:
            if os.path.exists('minigames_config.json'):
                with open('minigames_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('daily_challenges', [])
        except Exception as e:
            logger.error(f"Erro ao carregar desafios: {e}")
        
        # Fallback para desafios padrão
        return [
            {
                "name": "Mestre das Palavras",
                "description": "Envie 50 mensagens no servidor hoje",
                "type": "messages",
                "target": 50,
                "reward_points": 100,
                "reward_title": "Tagarela do Dia"
            },
            {
                "name": "Quiz Master",
                "description": "Acerte 5 perguntas no quiz PUBG",
                "type": "quiz_correct",
                "target": 5,
                "reward_points": 200,
                "reward_title": "Especialista PUBG"
            }
        ]
    
    def get_daily_challenge(self, user_id: int) -> dict:
        """Retorna o desafio diário do usuário"""
        # Usar ID do usuário como seed para garantir consistência
        today = datetime.now().strftime('%Y-%m-%d')
        seed = hash(f"{user_id}_{today}") % len(self.challenges)
        return self.challenges[seed]

class MinigamesSystem:
    """Sistema principal de mini-games e desafios"""
    
    def __init__(self, bot: commands.Bot, storage):
        self.bot = bot
        self.storage = storage
        self.logger = logging.getLogger('HawkBot.MinigamesSystem')
        
        # Sistemas de jogos
        self.pubg_quiz = PUBGQuiz()
        self.daily_challenge = DailyChallenge()
        
        # Sessões ativas
        self.active_sessions: Dict[int, GameSession] = {}  # channel_id -> session
        
        # Estatísticas dos jogadores
        self.player_stats = defaultdict(lambda: {
            'games_played': 0,
            'games_won': 0,
            'total_points': 0,
            'quiz_correct': 0,
            'quiz_total': 0,
            'rps_wins': 0,
            'roulette_wins': 0,
            'daily_challenges_completed': 0,
            'last_daily_reset': None,
            'daily_progress': {}
        })
        
        # Carregar dados salvos
        self.load_data()
        
        self.logger.info("Sistema de Mini-Games inicializado")
    
    def load_data(self):
        """Carrega dados dos mini-games"""
        try:
            if os.path.exists('minigames_data.json'):
                with open('minigames_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Converter chaves string para int
                    for user_id_str, stats in data.get('player_stats', {}).items():
                        self.player_stats[int(user_id_str)] = stats
                self.logger.info("Dados dos mini-games carregados")
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados dos mini-games: {e}")
    
    def save_data(self):
        """Salva dados dos mini-games"""
        try:
            data = {
                'player_stats': {str(k): v for k, v in self.player_stats.items()},
                'last_save': datetime.now().isoformat()
            }
            with open('minigames_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados dos mini-games: {e}")
    
    def reset_daily_progress(self, user_id: int):
        """Reseta progresso diário do usuário"""
        today = datetime.now().strftime('%Y-%m-%d')
        stats = self.player_stats[user_id]
        
        if stats['last_daily_reset'] != today:
            stats['daily_progress'] = {
                'messages': 0,
                'reactions': 0,
                'voice_time': 0,
                'quiz_correct': 0,
                'roulette_wins': 0
            }
            stats['last_daily_reset'] = today
    
    async def play_rock_paper_scissors(self, interaction: discord.Interaction, choice: str) -> discord.Embed:
        """Jogo de Pedra, Papel, Tesoura"""
        choices = ['pedra', 'papel', 'tesoura']
        emojis = {'pedra': '🪨', 'papel': '📄', 'tesoura': '✂️'}
        
        if choice.lower() not in choices:
            return discord.Embed(
                title="❌ Escolha Inválida",
                description="Escolha entre: pedra, papel ou tesoura",
                color=discord.Color.red()
            )
        
        user_choice = choice.lower()
        bot_choice = random.choice(choices)
        
        # Determinar resultado
        if user_choice == bot_choice:
            result = "Empate!"
            color = discord.Color.yellow()
            points = 10
        elif (
            (user_choice == 'pedra' and bot_choice == 'tesoura') or
            (user_choice == 'papel' and bot_choice == 'pedra') or
            (user_choice == 'tesoura' and bot_choice == 'papel')
        ):
            result = "Você ganhou! 🎉"
            color = discord.Color.green()
            points = 50
            self.player_stats[interaction.user.id]['rps_wins'] += 1
        else:
            result = "Você perdeu! 😢"
            color = discord.Color.red()
            points = 5
        
        # Atualizar estatísticas
        stats = self.player_stats[interaction.user.id]
        stats['games_played'] += 1
        stats['total_points'] += points
        if points == 50:
            stats['games_won'] += 1
        
        self.save_data()
        
        embed = discord.Embed(
            title="🎮 Pedra, Papel, Tesoura",
            description=f"**Sua escolha:** {emojis[user_choice]} {user_choice.title()}\n"
                       f"**Minha escolha:** {emojis[bot_choice]} {bot_choice.title()}\n\n"
                       f"**Resultado:** {result}\n"
                       f"**Pontos ganhos:** +{points}",
            color=color
        )
        
        return embed
    
    async def play_quiz(self, interaction: discord.Interaction, difficulty: str = None) -> discord.Embed:
        """Inicia um quiz PUBG"""
        question_data = self.pubg_quiz.get_random_question(difficulty)
        
        embed = discord.Embed(
            title="🧠 Quiz PUBG",
            description=f"**Pergunta ({question_data['difficulty'].title()}):**\n{question_data['question']}",
            color=discord.Color.blue()
        )
        
        options_text = ""
        for i, option in enumerate(question_data['options']):
            emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣'][i]
            options_text += f"{emoji} {option}\n"
        
        embed.add_field(name="Opções:", value=options_text, inline=False)
        embed.add_field(name="Como responder:", value="Reaja com o emoji da resposta correta!", inline=False)
        
        # Salvar dados da pergunta para verificação posterior
        self.active_sessions[interaction.channel.id] = {
            'type': 'quiz',
            'question_data': question_data,
            'user_id': interaction.user.id,
            'timestamp': time.time()
        }
        
        return embed
    
    async def check_quiz_answer(self, reaction: discord.Reaction, user: discord.User) -> Optional[discord.Embed]:
        """Verifica resposta do quiz"""
        channel_id = reaction.message.channel.id
        if channel_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[channel_id]
        if session['type'] != 'quiz' or session['user_id'] != user.id:
            return None
        
        # Verificar se não expirou (5 minutos)
        if time.time() - session['timestamp'] > 300:
            del self.active_sessions[channel_id]
            return None
        
        emoji_to_index = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3}
        if str(reaction.emoji) not in emoji_to_index:
            return None
        
        user_answer = emoji_to_index[str(reaction.emoji)]
        correct_answer = session['question_data']['correct']
        difficulty = session['question_data']['difficulty']
        
        # Calcular pontos baseado na dificuldade
        points_map = {'easy': 25, 'medium': 50, 'hard': 100}
        base_points = points_map.get(difficulty, 25)
        
        stats = self.player_stats[user.id]
        stats['quiz_total'] += 1
        
        if user_answer == correct_answer:
            stats['quiz_correct'] += 1
            stats['total_points'] += base_points
            stats['games_won'] += 1
            
            # Progresso diário
            self.reset_daily_progress(user.id)
            stats['daily_progress']['quiz_correct'] += 1
            
            embed = discord.Embed(
                title="✅ Resposta Correta!",
                description=f"Parabéns! Você ganhou **{base_points} pontos**!\n\n"
                           f"**Resposta:** {session['question_data']['options'][correct_answer]}\n"
                           f"**Dificuldade:** {difficulty.title()}\n"
                           f"**Precisão:** {stats['quiz_correct']}/{stats['quiz_total']} "
                           f"({(stats['quiz_correct']/stats['quiz_total']*100):.1f}%)",
                color=discord.Color.green()
            )
        else:
            stats['total_points'] += 5  # Pontos de consolação
            
            embed = discord.Embed(
                title="❌ Resposta Incorreta",
                description=f"Que pena! A resposta correta era:\n"
                           f"**{session['question_data']['options'][correct_answer]}**\n\n"
                           f"Você ganhou **5 pontos** por tentar!\n"
                           f"**Precisão:** {stats['quiz_correct']}/{stats['quiz_total']} "
                           f"({(stats['quiz_correct']/stats['quiz_total']*100):.1f}%)",
                color=discord.Color.red()
            )
        
        stats['games_played'] += 1
        self.save_data()
        del self.active_sessions[channel_id]
        
        return embed
    
    async def play_roulette(self, interaction: discord.Interaction, bet_points: int) -> discord.Embed:
        """Jogo de roleta com pontos"""
        user_stats = self.player_stats[interaction.user.id]
        
        if bet_points <= 0:
            return discord.Embed(
                title="❌ Aposta Inválida",
                description="Você deve apostar pelo menos 1 ponto!",
                color=discord.Color.red()
            )
        
        if user_stats['total_points'] < bet_points:
            return discord.Embed(
                title="❌ Pontos Insuficientes",
                description=f"Você tem apenas **{user_stats['total_points']} pontos**!\n"
                           f"Aposta solicitada: **{bet_points} pontos**",
                color=discord.Color.red()
            )
        
        # Roleta com diferentes probabilidades
        outcomes = [
            {'multiplier': 0, 'probability': 0.4, 'name': 'Perdeu tudo', 'emoji': '💀'},
            {'multiplier': 0.5, 'probability': 0.2, 'name': 'Perdeu metade', 'emoji': '😢'},
            {'multiplier': 1, 'probability': 0.15, 'name': 'Empatou', 'emoji': '😐'},
            {'multiplier': 1.5, 'probability': 0.1, 'name': 'Ganhou 50%', 'emoji': '😊'},
            {'multiplier': 2, 'probability': 0.08, 'name': 'Dobrou!', 'emoji': '🎉'},
            {'multiplier': 3, 'probability': 0.05, 'name': 'Triplicou!', 'emoji': '🤑'},
            {'multiplier': 5, 'probability': 0.02, 'name': 'JACKPOT!', 'emoji': '💰'}
        ]
        
        # Selecionar resultado baseado na probabilidade
        rand = random.random()
        cumulative = 0
        selected_outcome = outcomes[0]  # fallback
        
        for outcome in outcomes:
            cumulative += outcome['probability']
            if rand <= cumulative:
                selected_outcome = outcome
                break
        
        # Calcular resultado
        if selected_outcome['multiplier'] == 0:
            points_change = -bet_points
        elif selected_outcome['multiplier'] == 0.5:
            points_change = -int(bet_points * 0.5)
        elif selected_outcome['multiplier'] == 1:
            points_change = 0
        else:
            points_change = int(bet_points * (selected_outcome['multiplier'] - 1))
        
        # Atualizar estatísticas
        user_stats['total_points'] += points_change
        user_stats['games_played'] += 1
        
        if points_change > 0:
            user_stats['games_won'] += 1
            user_stats['roulette_wins'] += 1
            
            # Progresso diário
            self.reset_daily_progress(interaction.user.id)
            user_stats['daily_progress']['roulette_wins'] += 1
        
        self.save_data()
        
        # Criar embed de resultado
        color = discord.Color.green() if points_change > 0 else discord.Color.red() if points_change < 0 else discord.Color.yellow()
        
        embed = discord.Embed(
            title=f"🎰 Roleta da Sorte {selected_outcome['emoji']}",
            description=f"**Resultado:** {selected_outcome['name']}\n"
                       f"**Aposta:** {bet_points} pontos\n"
                       f"**Mudança:** {'+' if points_change >= 0 else ''}{points_change} pontos\n"
                       f"**Saldo atual:** {user_stats['total_points']} pontos",
            color=color
        )
        
        return embed
    
    async def get_player_stats(self, user: discord.Member) -> discord.Embed:
        """Mostra estatísticas do jogador"""
        stats = self.player_stats[user.id]
        
        # Calcular taxa de vitória
        win_rate = (stats['games_won'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
        quiz_accuracy = (stats['quiz_correct'] / stats['quiz_total'] * 100) if stats['quiz_total'] > 0 else 0
        
        embed = discord.Embed(
            title=f"📊 Estatísticas de {user.display_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎮 Jogos Gerais",
            value=f"**Jogos:** {stats['games_played']}\n"
                  f"**Vitórias:** {stats['games_won']}\n"
                  f"**Taxa de vitória:** {win_rate:.1f}%\n"
                  f"**Pontos totais:** {stats['total_points']}",
            inline=True
        )
        
        embed.add_field(
            name="🧠 Quiz PUBG",
            value=f"**Perguntas:** {stats['quiz_total']}\n"
                  f"**Acertos:** {stats['quiz_correct']}\n"
                  f"**Precisão:** {quiz_accuracy:.1f}%",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Outros Jogos",
            value=f"**Pedra-Papel-Tesoura:** {stats['rps_wins']} vitórias\n"
                  f"**Roleta:** {stats['roulette_wins']} vitórias\n"
                  f"**Desafios diários:** {stats['daily_challenges_completed']}",
            inline=True
        )
        
        return embed
    
    async def get_daily_challenge_status(self, user: discord.Member) -> discord.Embed:
        """Mostra status do desafio diário"""
        self.reset_daily_progress(user.id)
        
        challenge = self.daily_challenge.get_daily_challenge(user.id)
        stats = self.player_stats[user.id]
        progress = stats['daily_progress']
        
        current_progress = progress.get(challenge['type'], 0)
        target = challenge['target']
        percentage = min(current_progress / target * 100, 100)
        
        # Barra de progresso visual
        filled_blocks = int(percentage / 10)
        progress_bar = '█' * filled_blocks + '░' * (10 - filled_blocks)
        
        embed = discord.Embed(
            title="🏆 Desafio Diário",
            description=f"**{challenge['name']}**\n{challenge['description']}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📈 Progresso",
            value=f"`{progress_bar}` {percentage:.1f}%\n"
                  f"**{current_progress}/{target}**",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Recompensa",
            value=f"**{challenge['reward_points']} pontos**\n"
                  f"Título: *{challenge['reward_title']}*",
            inline=False
        )
        
        if current_progress >= target:
            embed.add_field(
                name="✅ Concluído!",
                value="Parabéns! Você completou o desafio de hoje!",
                inline=False
            )
            embed.color = discord.Color.green()
        
        return embed
    
    async def get_leaderboard(self, guild: discord.Guild, category: str = 'points') -> discord.Embed:
        """Mostra ranking dos jogadores"""
        # Filtrar apenas membros do servidor atual
        guild_members = {member.id for member in guild.members}
        guild_stats = {uid: stats for uid, stats in self.player_stats.items() if uid in guild_members}
        
        if not guild_stats:
            return discord.Embed(
                title="📊 Ranking - Mini-Games",
                description="Nenhum jogador encontrado neste servidor.",
                color=discord.Color.blue()
            )
        
        # Ordenar baseado na categoria
        sort_key = {
            'points': 'total_points',
            'games': 'games_played',
            'wins': 'games_won',
            'quiz': 'quiz_correct'
        }.get(category, 'total_points')
        
        sorted_players = sorted(
            guild_stats.items(),
            key=lambda x: x[1].get(sort_key, 0),
            reverse=True
        )[:10]  # Top 10
        
        embed = discord.Embed(
            title=f"🏆 Ranking - {category.title()}",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        medals = ['🥇', '🥈', '🥉'] + ['🏅'] * 7
        
        for i, (user_id, stats) in enumerate(sorted_players):
            user = guild.get_member(user_id)
            if not user:
                continue
            
            value = stats.get(sort_key, 0)
            leaderboard_text += f"{medals[i]} **{user.display_name}**: {value}\n"
        
        if leaderboard_text:
            embed.description = leaderboard_text
        else:
            embed.description = "Nenhum dado disponível."
        
        return embed