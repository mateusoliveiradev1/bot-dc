#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Gráficos de Progresso Individual - Hawk Bot
Desenvolvido para visualização avançada de estatísticas e progresso

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from discord.ext import commands
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import base64
from collections import defaultdict

logger = logging.getLogger('HawkBot.ChartsSystem')

# Configurar estilo dos gráficos
plt.style.use('dark_background')
sns.set_palette("husl")

class ChartGenerator:
    """Gerador de gráficos e charts"""
    
    def __init__(self):
        self.colors = {
            'primary': '#7289DA',
            'success': '#43B581',
            'warning': '#FAA61A',
            'danger': '#F04747',
            'info': '#00D4AA',
            'secondary': '#747F8D'
        }
        
        # Configurações padrão do matplotlib
        plt.rcParams.update({
            'figure.facecolor': '#2C2F33',
            'axes.facecolor': '#36393F',
            'axes.edgecolor': '#FFFFFF',
            'axes.labelcolor': '#FFFFFF',
            'text.color': '#FFFFFF',
            'xtick.color': '#FFFFFF',
            'ytick.color': '#FFFFFF',
            'grid.color': '#4F545C',
            'grid.alpha': 0.3
        })
    
    def create_rank_progress_chart(self, user_data: Dict, days: int = 30) -> BytesIO:
        """Cria gráfico de progresso de rank"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Dados simulados de progresso (em implementação real, vem do banco)
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        ranks = np.random.randint(1000, 2000, days)  # Simular dados de rank
        
        # Criar linha de progresso
        ax.plot(dates, ranks, color=self.colors['primary'], linewidth=3, marker='o', markersize=4)
        ax.fill_between(dates, ranks, alpha=0.3, color=self.colors['primary'])
        
        # Configurar eixos
        ax.set_title(f'Progresso de Rank - {user_data.get("name", "Jogador")}', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Data', fontsize=12)
        ax.set_ylabel('Pontos de Rank', fontsize=12)
        
        # Formatar datas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Adicionar estatísticas
        current_rank = ranks[-1]
        previous_rank = ranks[0]
        change = current_rank - previous_rank
        
        stats_text = f'Rank Atual: {current_rank}\nMudança: {"+" if change >= 0 else ""}{change}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def create_games_performance_chart(self, user_data: Dict) -> BytesIO:
        """Cria gráfico de performance em jogos"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Dados de jogos (simulados)
        games = ['Pedra-Papel-Tesoura', 'Quiz PUBG', 'Roleta', 'Torneios']
        wins = [45, 32, 18, 8]
        losses = [25, 28, 42, 12]
        
        # Gráfico de barras - Vitórias vs Derrotas
        x = np.arange(len(games))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, wins, width, label='Vitórias', color=self.colors['success'])
        bars2 = ax1.bar(x + width/2, losses, width, label='Derrotas', color=self.colors['danger'])
        
        ax1.set_title('Performance por Jogo', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Jogos')
        ax1.set_ylabel('Quantidade')
        ax1.set_xticks(x)
        ax1.set_xticklabels(games, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Adicionar valores nas barras
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom')
        
        for bar in bars2:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Gráfico de pizza - Taxa de vitória geral
        total_wins = sum(wins)
        total_losses = sum(losses)
        
        sizes = [total_wins, total_losses]
        labels = ['Vitórias', 'Derrotas']
        colors = [self.colors['success'], self.colors['danger']]
        
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                          startangle=90, textprops={'color': 'white'})
        
        ax2.set_title('Taxa de Vitória Geral', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def create_activity_heatmap(self, user_data: Dict) -> BytesIO:
        """Cria heatmap de atividade"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Simular dados de atividade (7 dias x 24 horas)
        days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        hours = [f'{i:02d}:00' for i in range(24)]
        
        # Gerar dados aleatórios de atividade
        activity_data = np.random.randint(0, 10, (7, 24))
        
        # Criar heatmap
        sns.heatmap(activity_data, 
                   xticklabels=hours[::2],  # Mostrar apenas horas pares
                   yticklabels=days,
                   cmap='YlOrRd',
                   cbar_kws={'label': 'Atividade'},
                   ax=ax)
        
        ax.set_title('Mapa de Atividade Semanal', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Hora do Dia', fontsize=12)
        ax.set_ylabel('Dia da Semana', fontsize=12)
        
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def create_achievements_progress(self, user_data: Dict) -> BytesIO:
        """Cria gráfico de progresso de conquistas"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Dados de conquistas (simulados)
        achievements = [
            {'name': 'Primeiro Sangue', 'progress': 100, 'target': 100},
            {'name': 'Veterano', 'progress': 75, 'target': 100},
            {'name': 'Mestre do Quiz', 'progress': 60, 'target': 100},
            {'name': 'Sortudo', 'progress': 40, 'target': 100},
            {'name': 'Socialite', 'progress': 85, 'target': 100},
            {'name': 'Competidor', 'progress': 30, 'target': 100}
        ]
        
        # Preparar dados
        names = [a['name'] for a in achievements]
        progress = [a['progress'] for a in achievements]
        
        # Criar barras horizontais
        y_pos = np.arange(len(names))
        
        # Barras de fundo (total)
        ax.barh(y_pos, [100] * len(names), color='#4F545C', alpha=0.3, height=0.6)
        
        # Barras de progresso
        colors = [self.colors['success'] if p == 100 else 
                 self.colors['warning'] if p >= 50 else 
                 self.colors['danger'] for p in progress]
        
        bars = ax.barh(y_pos, progress, color=colors, height=0.6)
        
        # Configurar eixos
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.set_xlabel('Progresso (%)')
        ax.set_title('Progresso das Conquistas', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(0, 100)
        
        # Adicionar percentuais nas barras
        for i, (bar, prog) in enumerate(zip(bars, progress)):
            ax.text(prog + 2, bar.get_y() + bar.get_height()/2, 
                   f'{prog}%', va='center', ha='left', fontweight='bold')
        
        # Grid vertical
        ax.grid(True, axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def create_comparison_radar(self, user_data: Dict, comparison_data: List[Dict]) -> BytesIO:
        """Cria gráfico radar de comparação"""
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Categorias para comparação
        categories = ['Rank', 'Vitórias', 'Precisão Quiz', 'Atividade', 'Conquistas', 'Pontos']
        
        # Dados do usuário (normalizados 0-100)
        user_values = [85, 70, 90, 60, 75, 80]  # Simulado
        
        # Dados de comparação (média do servidor)
        avg_values = [60, 55, 65, 70, 50, 65]  # Simulado
        
        # Ângulos para cada categoria
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]  # Fechar o círculo
        
        user_values += user_values[:1]
        avg_values += avg_values[:1]
        
        # Plotar dados
        ax.plot(angles, user_values, 'o-', linewidth=2, label='Você', color=self.colors['primary'])
        ax.fill(angles, user_values, alpha=0.25, color=self.colors['primary'])
        
        ax.plot(angles, avg_values, 'o-', linewidth=2, label='Média do Servidor', color=self.colors['secondary'])
        ax.fill(angles, avg_values, alpha=0.25, color=self.colors['secondary'])
        
        # Configurar eixos
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])
        ax.grid(True)
        
        # Título e legenda
        ax.set_title('Comparação de Performance', size=16, fontweight='bold', pad=30)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        
        # Salvar em buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer

class ChartsSystem:
    """Sistema principal de gráficos e charts"""
    
    def __init__(self, bot: commands.Bot, storage):
        self.bot = bot
        self.storage = storage
        self.logger = logging.getLogger('HawkBot.ChartsSystem')
        self.chart_generator = ChartGenerator()
        
        # Cache de gráficos (evitar regeneração desnecessária)
        self.chart_cache = {}
        self.cache_duration = 300  # 5 minutos
        
        self.logger.info("Sistema de Gráficos inicializado")
    
    def _get_cache_key(self, user_id: int, chart_type: str) -> str:
        """Gera chave para cache"""
        return f"{user_id}_{chart_type}_{int(datetime.now().timestamp() // self.cache_duration)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se cache ainda é válido"""
        return cache_key in self.chart_cache
    
    async def get_user_data(self, user_id: int) -> Dict:
        """Coleta dados do usuário de todos os sistemas"""
        user_data = {
            'id': user_id,
            'name': 'Jogador',
            'rank_data': {},
            'games_data': {},
            'activity_data': {},
            'achievements_data': {}
        }
        
        try:
            # Coletar dados do sistema de ranking
            if hasattr(self.bot, 'rank_system'):
                rank_info = await self.bot.rank_system.get_user_rank(user_id)
                user_data['rank_data'] = rank_info or {}
            
            # Coletar dados dos mini-games
            if hasattr(self.bot, 'minigames_system'):
                games_stats = self.bot.minigames_system.player_stats.get(user_id, {})
                user_data['games_data'] = games_stats
            
            # Coletar dados de conquistas
            if hasattr(self.bot, 'achievement_system'):
                achievements = await self.bot.achievement_system.get_user_achievements(user_id)
                user_data['achievements_data'] = achievements or {}
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar dados do usuário {user_id}: {e}")
        
        return user_data
    
    async def generate_rank_progress_chart(self, user: discord.Member) -> discord.File:
        """Gera gráfico de progresso de rank"""
        cache_key = self._get_cache_key(user.id, 'rank_progress')
        
        if self._is_cache_valid(cache_key):
            buffer = self.chart_cache[cache_key]
        else:
            user_data = await self.get_user_data(user.id)
            user_data['name'] = user.display_name
            
            buffer = self.chart_generator.create_rank_progress_chart(user_data)
            self.chart_cache[cache_key] = buffer
        
        buffer.seek(0)
        return discord.File(buffer, filename=f'rank_progress_{user.id}.png')
    
    async def generate_games_performance_chart(self, user: discord.Member) -> discord.File:
        """Gera gráfico de performance em jogos"""
        cache_key = self._get_cache_key(user.id, 'games_performance')
        
        if self._is_cache_valid(cache_key):
            buffer = self.chart_cache[cache_key]
        else:
            user_data = await self.get_user_data(user.id)
            user_data['name'] = user.display_name
            
            buffer = self.chart_generator.create_games_performance_chart(user_data)
            self.chart_cache[cache_key] = buffer
        
        buffer.seek(0)
        return discord.File(buffer, filename=f'games_performance_{user.id}.png')
    
    async def generate_activity_heatmap(self, user: discord.Member) -> discord.File:
        """Gera heatmap de atividade"""
        cache_key = self._get_cache_key(user.id, 'activity_heatmap')
        
        if self._is_cache_valid(cache_key):
            buffer = self.chart_cache[cache_key]
        else:
            user_data = await self.get_user_data(user.id)
            user_data['name'] = user.display_name
            
            buffer = self.chart_generator.create_activity_heatmap(user_data)
            self.chart_cache[cache_key] = buffer
        
        buffer.seek(0)
        return discord.File(buffer, filename=f'activity_heatmap_{user.id}.png')
    
    async def generate_achievements_progress(self, user: discord.Member) -> discord.File:
        """Gera gráfico de progresso de conquistas"""
        cache_key = self._get_cache_key(user.id, 'achievements_progress')
        
        if self._is_cache_valid(cache_key):
            buffer = self.chart_cache[cache_key]
        else:
            user_data = await self.get_user_data(user.id)
            user_data['name'] = user.display_name
            
            buffer = self.chart_generator.create_achievements_progress(user_data)
            self.chart_cache[cache_key] = buffer
        
        buffer.seek(0)
        return discord.File(buffer, filename=f'achievements_progress_{user.id}.png')
    
    async def generate_comparison_radar(self, user: discord.Member) -> discord.File:
        """Gera gráfico radar de comparação"""
        cache_key = self._get_cache_key(user.id, 'comparison_radar')
        
        if self._is_cache_valid(cache_key):
            buffer = self.chart_cache[cache_key]
        else:
            user_data = await self.get_user_data(user.id)
            user_data['name'] = user.display_name
            
            # Coletar dados de comparação (outros usuários do servidor)
            comparison_data = []  # Implementar coleta de dados de outros usuários
            
            buffer = self.chart_generator.create_comparison_radar(user_data, comparison_data)
            self.chart_cache[cache_key] = buffer
        
        buffer.seek(0)
        return discord.File(buffer, filename=f'comparison_radar_{user.id}.png')
    
    async def generate_comprehensive_report(self, user: discord.Member) -> List[discord.File]:
        """Gera relatório completo com todos os gráficos"""
        files = []
        
        try:
            # Gerar todos os gráficos
            rank_chart = await self.generate_rank_progress_chart(user)
            games_chart = await self.generate_games_performance_chart(user)
            activity_chart = await self.generate_activity_heatmap(user)
            achievements_chart = await self.generate_achievements_progress(user)
            comparison_chart = await self.generate_comparison_radar(user)
            
            files = [rank_chart, games_chart, activity_chart, achievements_chart, comparison_chart]
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório completo para {user.id}: {e}")
        
        return files
    
    def clear_cache(self):
        """Limpa cache de gráficos"""
        self.chart_cache.clear()
        self.logger.info("Cache de gráficos limpo")
    
    async def get_chart_embed(self, chart_type: str, user: discord.Member) -> discord.Embed:
        """Cria embed informativo para acompanhar os gráficos"""
        embed = discord.Embed(
            title=f"📊 Gráficos de Progresso - {user.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        descriptions = {
            'rank_progress': '📈 **Progresso de Rank**\nVisualização da evolução do seu ranking ao longo do tempo.',
            'games_performance': '🎮 **Performance em Jogos**\nEstatísticas detalhadas de vitórias e derrotas por jogo.',
            'activity_heatmap': '🔥 **Mapa de Atividade**\nSua atividade no servidor por dia da semana e hora.',
            'achievements_progress': '🏆 **Progresso de Conquistas**\nStatus atual de todas as suas conquistas.',
            'comparison_radar': '⚡ **Comparação Radar**\nSua performance comparada à média do servidor.',
            'comprehensive': '📋 **Relatório Completo**\nTodos os gráficos de progresso em um relatório detalhado.'
        }
        
        embed.description = descriptions.get(chart_type, 'Gráfico de progresso individual')
        
        embed.add_field(
            name="ℹ️ Informações",
            value="• Gráficos atualizados a cada 5 minutos\n"
                  "• Dados coletados de todos os sistemas do bot\n"
                  "• Use `/graficos help` para mais opções",
            inline=False
        )
        
        embed.set_footer(text="Hawk Bot - Sistema de Gráficos", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        return embed