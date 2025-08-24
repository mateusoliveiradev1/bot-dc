#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos de Relatórios e Estatísticas de Check-in
Comandos para gerar e visualizar relatórios de participação

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import json
import logging

logger = logging.getLogger('HawkBot.ReportCommands')

class ReportCommands(commands.Cog):
    """Comandos de relatórios e estatísticas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reports = bot.checkin_reports
        
        logger.info("Comandos de Relatórios carregados")
    
    @commands.group(name='report', aliases=['relatorio'], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def report_group(self, ctx):
        """Comandos de relatórios de check-in"""
        embed = discord.Embed(
            title="📊 Sistema de Relatórios",
            description="Comandos disponíveis para relatórios e estatísticas:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📈 Relatórios Gerais",
            value="`/report participation [dias]` - Relatório de participação\n"
                  "`/report summary [dias]` - Resumo estatístico\n"
                  "`/report leaderboard [métrica] [dias]` - Ranking de jogadores",
            inline=False
        )
        
        embed.add_field(
            name="👤 Relatórios Individuais",
            value="`/report player <usuário> [dias]` - Relatório de jogador\n"
                  "`/report session <id>` - Análise de sessão",
            inline=False
        )
        
        embed.add_field(
            name="💾 Exportação",
            value="`/report export <tipo> [dias]` - Exportar relatório",
            inline=False
        )
        
        embed.set_footer(text="Use os comandos para gerar relatórios detalhados")
        await ctx.send(embed=embed)
    
    @report_group.command(name='participation', aliases=['participacao'])
    @commands.has_permissions(manage_guild=True)
    async def participation_report(self, ctx, days: int = 30):
        """Gera relatório de participação"""
        if days < 1 or days > 365:
            await ctx.send("❌ Número de dias deve estar entre 1 e 365.")
            return
        
        await ctx.send("📊 Gerando relatório de participação...")
        
        try:
            report = self.reports.generate_participation_report(days)
            
            if not report:
                await ctx.send("❌ Erro ao gerar relatório.")
                return
            
            embed = discord.Embed(
                title=f"📈 Relatório de Participação ({days} dias)",
                color=discord.Color.green()
            )
            
            # Resumo geral
            summary = report['summary']
            embed.add_field(
                name="📊 Resumo Geral",
                value=f"**Sessões:** {summary['total_sessions']}\n"
                      f"**Check-ins:** {summary['total_checkins']}\n"
                      f"**Check-outs:** {summary['total_checkouts']}\n"
                      f"**Taxa de Participação:** {summary['participation_rate']}%\n"
                      f"**Média de Jogadores/Sessão:** {summary['avg_players_per_session']}",
                inline=True
            )
            
            # Tipos de sessão
            if report['session_types']:
                session_types_text = "\n".join([
                    f"**{tipo}:** {count}" 
                    for tipo, count in report['session_types'].items()
                ])
                embed.add_field(
                    name="🎮 Tipos de Sessão",
                    value=session_types_text,
                    inline=True
                )
            
            # Top 5 jogadores mais ativos
            if report['player_stats']:
                top_players = sorted(
                    report['player_stats'].items(),
                    key=lambda x: x[1]['sessions_participated'],
                    reverse=True
                )[:5]
                
                top_players_text = "\n".join([
                    f"<@{player_id}>: {stats['sessions_participated']} sessões"
                    for player_id, stats in top_players
                ])
                
                embed.add_field(
                    name="🏆 Top 5 Jogadores",
                    value=top_players_text,
                    inline=False
                )
            
            # Dias da semana mais ativos
            if report['weekday_stats']:
                weekday_text = "\n".join([
                    f"**{day}:** {count} sessões"
                    for day, count in sorted(report['weekday_stats'].items(), key=lambda x: x[1], reverse=True)[:3]
                ])
                embed.add_field(
                    name="📅 Dias Mais Ativos",
                    value=weekday_text,
                    inline=True
                )
            
            embed.set_footer(text=f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de participação: {e}")
            await ctx.send("❌ Erro interno ao gerar relatório.")
    
    @report_group.command(name='player', aliases=['jogador'])
    @commands.has_permissions(manage_guild=True)
    async def player_report(self, ctx, user: discord.Member, days: int = 30):
        """Gera relatório individual de um jogador"""
        if days < 1 or days > 365:
            await ctx.send("❌ Número de dias deve estar entre 1 e 365.")
            return
        
        await ctx.send(f"👤 Gerando relatório para {user.mention}...")
        
        try:
            report = self.reports.generate_player_report(str(user.id), days)
            
            if not report or 'message' in report:
                await ctx.send(f"❌ {report.get('message', 'Erro ao gerar relatório')}.")
                return
            
            embed = discord.Embed(
                title=f"👤 Relatório de {user.display_name}",
                description=f"Período: {days} dias",
                color=discord.Color.blue()
            )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Resumo
            summary = report['summary']
            embed.add_field(
                name="📊 Resumo",
                value=f"**Sessões:** {summary['total_sessions']}\n"
                      f"**Check-ins:** {summary['total_checkins']}\n"
                      f"**Check-outs:** {summary['total_checkouts']}\n"
                      f"**Taxa de Conclusão:** {summary['completion_rate']}%",
                inline=True
            )
            
            # Tempo
            embed.add_field(
                name="⏱️ Tempo",
                value=f"**Total:** {summary['total_time_minutes']} min\n"
                      f"**Média/Sessão:** {summary['avg_session_time']} min",
                inline=True
            )
            
            # Tipos de sessão preferidos
            if report['session_types']:
                session_types_text = "\n".join([
                    f"**{tipo}:** {count}"
                    for tipo, count in sorted(report['session_types'].items(), key=lambda x: x[1], reverse=True)[:3]
                ])
                embed.add_field(
                    name="🎮 Tipos Preferidos",
                    value=session_types_text,
                    inline=True
                )
            
            # Horários preferidos
            if report['preferred_hours']:
                embed.add_field(
                    name="🕐 Horários Preferidos",
                    value="\n".join(report['preferred_hours'][:3]),
                    inline=True
                )
            
            # Frequência semanal
            if report['weekday_frequency']:
                weekday_text = "\n".join([
                    f"**{day}:** {count}"
                    for day, count in sorted(report['weekday_frequency'].items(), key=lambda x: x[1], reverse=True)[:3]
                ])
                embed.add_field(
                    name="📅 Dias Mais Ativos",
                    value=weekday_text,
                    inline=True
                )
            
            # Sessões recentes
            if report['recent_sessions']:
                recent_text = "\n".join([
                    f"**{session['type']}** - {session['duration_minutes']}min"
                    for session in report['recent_sessions'][:3]
                ])
                embed.add_field(
                    name="📝 Sessões Recentes",
                    value=recent_text,
                    inline=False
                )
            
            embed.set_footer(text=f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório do jogador: {e}")
            await ctx.send("❌ Erro interno ao gerar relatório.")
    
    @report_group.command(name='leaderboard', aliases=['ranking'])
    @commands.has_permissions(manage_guild=True)
    async def leaderboard_report(self, ctx, metric: str = 'participation', days: int = 30, limit: int = 10):
        """Gera leaderboard de jogadores"""
        valid_metrics = ['participation', 'completion_rate', 'total_time']
        if metric not in valid_metrics:
            await ctx.send(f"❌ Métrica inválida. Use: {', '.join(valid_metrics)}")
            return
        
        if days < 1 or days > 365:
            await ctx.send("❌ Número de dias deve estar entre 1 e 365.")
            return
        
        if limit < 1 or limit > 20:
            await ctx.send("❌ Limite deve estar entre 1 e 20.")
            return
        
        await ctx.send(f"🏆 Gerando ranking por {metric}...")
        
        try:
            leaderboard = self.reports.generate_leaderboard(metric, days, limit)
            
            if not leaderboard:
                await ctx.send("❌ Nenhum dado encontrado para o período.")
                return
            
            metric_names = {
                'participation': 'Participação',
                'completion_rate': 'Taxa de Conclusão',
                'total_time': 'Tempo Total'
            }
            
            embed = discord.Embed(
                title=f"🏆 Ranking - {metric_names[metric]} ({days} dias)",
                color=discord.Color.gold()
            )
            
            # Adicionar jogadores ao ranking
            ranking_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for entry in leaderboard:
                rank = entry['rank']
                player_id = entry['player_id']
                
                # Emoji de posição
                if rank <= 3:
                    rank_emoji = medals[rank - 1]
                else:
                    rank_emoji = f"{rank}º"
                
                # Valor da métrica
                if metric == 'participation':
                    value = f"{entry['sessions_participated']} sessões"
                elif metric == 'completion_rate':
                    value = f"{entry['completion_rate']}%"
                elif metric == 'total_time':
                    value = f"{entry['total_time_minutes']} min"
                
                ranking_text += f"{rank_emoji} <@{player_id}> - {value}\n"
            
            embed.description = ranking_text
            embed.set_footer(text=f"Ranking gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard: {e}")
            await ctx.send("❌ Erro interno ao gerar ranking.")
    
    @report_group.command(name='session', aliases=['sessao'])
    @commands.has_permissions(manage_guild=True)
    async def session_report(self, ctx, session_id: str):
        """Gera análise detalhada de uma sessão"""
        await ctx.send(f"🔍 Analisando sessão {session_id}...")
        
        try:
            analytics = self.reports.generate_session_analytics(session_id)
            
            if not analytics or 'error' in analytics:
                await ctx.send(f"❌ {analytics.get('error', 'Erro ao analisar sessão')}.")
                return
            
            session_info = analytics['session_info']
            participation = analytics['participation']
            
            embed = discord.Embed(
                title=f"🔍 Análise da Sessão",
                description=f"**ID:** {session_id}\n**Tipo:** {session_info['type']}",
                color=discord.Color.purple()
            )
            
            # Informações da sessão
            start_time = datetime.fromisoformat(session_info['start_time'])
            end_time = datetime.fromisoformat(session_info['end_time'])
            
            embed.add_field(
                name="📅 Horário",
                value=f"**Início:** {start_time.strftime('%d/%m/%Y %H:%M')}\n"
                      f"**Fim:** {end_time.strftime('%d/%m/%Y %H:%M')}\n"
                      f"**Duração:** {session_info['duration_minutes']} min",
                inline=True
            )
            
            # Estatísticas de participação
            embed.add_field(
                name="📊 Participação",
                value=f"**Check-ins:** {participation['total_checkins']}\n"
                      f"**Check-outs:** {participation['total_checkouts']}\n"
                      f"**Taxa de Ocupação:** {participation['occupancy_rate']}%\n"
                      f"**Taxa de Conclusão:** {participation['completion_rate']}%",
                inline=True
            )
            
            # Capacidade
            embed.add_field(
                name="👥 Capacidade",
                value=f"**Máximo:** {session_info['max_players']}\n"
                      f"**Incompletos:** {participation['incomplete_players']}",
                inline=True
            )
            
            # Jogadores que fizeram check-in
            player_details = analytics['player_details']
            if player_details['checked_in_players']:
                checked_in_text = "\n".join([
                    f"<@{player_id}>"
                    for player_id in player_details['checked_in_players'][:10]
                ])
                if len(player_details['checked_in_players']) > 10:
                    checked_in_text += f"\n... e mais {len(player_details['checked_in_players']) - 10}"
                
                embed.add_field(
                    name="✅ Check-ins",
                    value=checked_in_text,
                    inline=True
                )
            
            # Jogadores que não fizeram check-out
            if player_details['incomplete_players']:
                incomplete_text = "\n".join([
                    f"<@{player_id}>"
                    for player_id in player_details['incomplete_players'][:5]
                ])
                if len(player_details['incomplete_players']) > 5:
                    incomplete_text += f"\n... e mais {len(player_details['incomplete_players']) - 5}"
                
                embed.add_field(
                    name="⚠️ Sem Check-out",
                    value=incomplete_text,
                    inline=True
                )
            
            embed.set_footer(text=f"Análise gerada em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao analisar sessão: {e}")
            await ctx.send("❌ Erro interno ao analisar sessão.")
    
    @report_group.command(name='summary', aliases=['resumo'])
    @commands.has_permissions(manage_guild=True)
    async def summary_report(self, ctx, days: int = 7):
        """Gera resumo estatístico"""
        if days < 1 or days > 30:
            await ctx.send("❌ Número de dias deve estar entre 1 e 30.")
            return
        
        try:
            summary = self.reports.get_summary_stats(days)
            
            if not summary:
                await ctx.send("❌ Erro ao gerar resumo.")
                return
            
            embed = discord.Embed(
                title=f"📈 Resumo Estatístico ({days} dias)",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Atividade Geral",
                value=f"**Sessões:** {summary['total_sessions']}\n"
                      f"**Check-ins:** {summary['total_checkins']}\n"
                      f"**Check-outs:** {summary['total_checkouts']}\n"
                      f"**Jogadores Únicos:** {summary['unique_players']}",
                inline=True
            )
            
            embed.add_field(
                name="📈 Médias",
                value=f"**Jogadores/Sessão:** {summary['avg_players_per_session']}\n"
                      f"**Taxa de Conclusão:** {summary['completion_rate']}%",
                inline=True
            )
            
            # Sessão mais popular
            if summary['most_popular_session']:
                popular = summary['most_popular_session']
                embed.add_field(
                    name="🏆 Sessão Mais Popular",
                    value=f"**Tipo:** {popular['type']}\n"
                          f"**Check-ins:** {popular['checkins']}\n"
                          f"**ID:** {popular['id'][:8]}...",
                    inline=True
                )
            
            embed.set_footer(text=f"Resumo gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            await ctx.send("❌ Erro interno ao gerar resumo.")
    
    @report_group.command(name='export', aliases=['exportar'])
    @commands.has_permissions(administrator=True)
    async def export_report(self, ctx, report_type: str, days: int = 30):
        """Exporta relatório para arquivo JSON"""
        valid_types = ['participation', 'summary']
        if report_type not in valid_types:
            await ctx.send(f"❌ Tipo inválido. Use: {', '.join(valid_types)}")
            return
        
        if days < 1 or days > 365:
            await ctx.send("❌ Número de dias deve estar entre 1 e 365.")
            return
        
        await ctx.send(f"💾 Exportando relatório {report_type}...")
        
        try:
            # Gerar relatório
            if report_type == 'participation':
                report = self.reports.generate_participation_report(days)
            elif report_type == 'summary':
                report = self.reports.get_summary_stats(days)
            
            if not report:
                await ctx.send("❌ Erro ao gerar relatório.")
                return
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{report_type}_{days}days_{timestamp}.json"
            
            # Exportar
            success = self.reports.export_report_to_json(report, filename)
            
            if success:
                # Enviar arquivo
                try:
                    with open(filename, 'rb') as f:
                        file = discord.File(f, filename)
                        await ctx.send("✅ Relatório exportado com sucesso!", file=file)
                except:
                    await ctx.send(f"✅ Relatório exportado para: `{filename}`")
            else:
                await ctx.send("❌ Erro ao exportar relatório.")
            
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            await ctx.send("❌ Erro interno ao exportar relatório.")
    
    @commands.command(name='stats', aliases=['estatisticas'])
    @commands.has_permissions(manage_guild=True)
    async def quick_stats(self, ctx):
        """Mostra estatísticas rápidas dos últimos 7 dias"""
        try:
            summary = self.reports.get_summary_stats(7)
            
            if not summary:
                await ctx.send("❌ Erro ao obter estatísticas.")
                return
            
            embed = discord.Embed(
                title="⚡ Estatísticas Rápidas (7 dias)",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📊 Resumo",
                value=f"**{summary['total_sessions']}** sessões\n"
                      f"**{summary['total_checkins']}** check-ins\n"
                      f"**{summary['unique_players']}** jogadores únicos\n"
                      f"**{summary['completion_rate']}%** taxa de conclusão",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas rápidas: {e}")
            await ctx.send("❌ Erro interno ao obter estatísticas.")

async def setup(bot):
    """Carrega a extensão de comandos de relatórios"""
    await bot.add_cog(ReportCommands(bot))
    logger.info("Extensão ReportCommands carregada")