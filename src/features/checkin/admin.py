import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List
from .system import CheckInSystem, SessionType
import asyncio

class CheckInAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checkin_system = None
        
    def setup_checkin_system(self, storage):
        """Configura o sistema de check-in"""
        self.checkin_system = CheckInSystem(self.bot, storage)
        
    @app_commands.command(name="admin_cancelar_sessao", description="[ADMIN] Cancela uma sessão ativa")
    @app_commands.describe(sessao_id="ID da sessão para cancelar")
    async def admin_cancelar_sessao(self, interaction: discord.Interaction, sessao_id: str):
        """Cancela uma sessão (apenas administradores)"""
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
            
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Obter informações da sessão
            session = self.checkin_system.get_session_info(sessao_id)
            if not session:
                embed = discord.Embed(
                    title="❌ Sessão Não Encontrada",
                    description="A sessão especificada não existe.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            # Cancelar a sessão
            success = self.checkin_system.cancel_session(sessao_id)
            
            if not success:
                embed = discord.Embed(
                    title="❌ Erro ao Cancelar",
                    description="Não foi possível cancelar a sessão.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            # Cancelar notificações
            await self.bot.checkin_notifications.cancel_session_notifications(sessao_id)
            
            embed = discord.Embed(
                title="✅ Sessão Cancelada",
                description=f"A sessão **{session['name']}** foi cancelada com sucesso.",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Tipo",
                value=session['session_type'].replace('_', ' ').title(),
                inline=True
            )
            
            embed.add_field(
                name="Participantes Afetados",
                value=f"{len(session['checked_in_players'])}",
                inline=True
            )
            
            embed.add_field(
                name="Cancelado por",
                value=interaction.user.mention,
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
            
    @app_commands.command(name="admin_forcar_checkin", description="[ADMIN] Força check-in de um usuário")
    @app_commands.describe(
        sessao_id="ID da sessão",
        usuario="Usuário para fazer check-in"
    )
    async def admin_forcar_checkin(self, interaction: discord.Interaction, sessao_id: str, usuario: discord.Member):
        """Força check-in de um usuário (apenas administradores)"""
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
            
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Fazer check-in forçado
            success = self.checkin_system.checkin_player(sessao_id, usuario.id)
            
            if not success:
                embed = discord.Embed(
                    title="❌ Check-in Falhou",
                    description="Não foi possível fazer check-in. Verifique se a sessão existe e está ativa.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            session = self.checkin_system.get_session_info(sessao_id)
            
            embed = discord.Embed(
                title="✅ Check-in Forçado",
                description=f"Check-in realizado para {usuario.mention} na sessão **{session['name']}**.",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Administrador",
                value=interaction.user.mention,
                inline=True
            )
            
            embed.add_field(
                name="Participantes",
                value=f"{len(session['checked_in_players'])}{f'/{session["max_players"]}' if session['max_players'] else ''}",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
            # Enviar notificação
            await self.bot.checkin_notifications.send_checkin_notification(
                sessao_id, usuario.id, interaction.channel.id
            )
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
            
    @app_commands.command(name="admin_forcar_checkout", description="[ADMIN] Força check-out de um usuário")
    @app_commands.describe(
        sessao_id="ID da sessão",
        usuario="Usuário para fazer check-out"
    )
    async def admin_forcar_checkout(self, interaction: discord.Interaction, sessao_id: str, usuario: discord.Member):
        """Força check-out de um usuário (apenas administradores)"""
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
            
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Fazer check-out forçado
            success = self.checkin_system.checkout_player(sessao_id, usuario.id)
            
            if not success:
                embed = discord.Embed(
                    title="❌ Check-out Falhou",
                    description="Não foi possível fazer check-out. Verifique se o usuário está na sessão.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            session = self.checkin_system.get_session_info(sessao_id)
            
            embed = discord.Embed(
                title="✅ Check-out Forçado",
                description=f"Check-out realizado para {usuario.mention} da sessão **{session['name']}**.",
                color=0xFF9900,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Administrador",
                value=interaction.user.mention,
                inline=True
            )
            
            embed.add_field(
                name="Participantes Ativos",
                value=f"{len(session['checked_in_players'])}",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
            # Enviar notificação
            await self.bot.checkin_notifications.send_checkout_notification(
                sessao_id, usuario.id, interaction.channel.id
            )
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
            
    @app_commands.command(name="admin_estatisticas_sessao", description="[ADMIN] Mostra estatísticas detalhadas de uma sessão")
    @app_commands.describe(sessao_id="ID da sessão")
    async def admin_estatisticas_sessao(self, interaction: discord.Interaction, sessao_id: str):
        """Mostra estatísticas detalhadas de uma sessão (apenas administradores)"""
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
            
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            session = self.checkin_system.get_session_info(sessao_id)
            if not session:
                embed = discord.Embed(
                    title="❌ Sessão Não Encontrada",
                    description="A sessão especificada não existe.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            # Calcular estatísticas
            total_checkins = len(session.get('checkin_history', []))
            total_checkouts = len(session.get('checkout_history', []))
            currently_active = len(session['checked_in_players'])
            
            # Calcular tempo médio de participação
            avg_duration = "N/A"
            if session.get('checkout_history'):
                durations = []
                for checkout in session['checkout_history']:
                    checkin_time = None
                    for checkin in session.get('checkin_history', []):
                        if checkin['user_id'] == checkout['user_id']:
                            checkin_time = datetime.fromisoformat(checkin['timestamp'])
                            break
                    if checkin_time:
                        checkout_time = datetime.fromisoformat(checkout['timestamp'])
                        duration = (checkout_time - checkin_time).total_seconds() / 60
                        durations.append(duration)
                        
                if durations:
                    avg_duration = f"{sum(durations) / len(durations):.1f} min"
            
            embed = discord.Embed(
                title="📊 Estatísticas da Sessão",
                description=f"**{session['name']}**",
                color=0x0099FF,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎮 Tipo",
                value=session['session_type'].replace('_', ' ').title(),
                inline=True
            )
            
            embed.add_field(
                name="📅 Status",
                value=session['status'].title(),
                inline=True
            )
            
            embed.add_field(
                name="👤 Criador",
                value=f"<@{session['creator_id']}>",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total Check-ins",
                value=f"{total_checkins}",
                inline=True
            )
            
            embed.add_field(
                name="📉 Total Check-outs",
                value=f"{total_checkouts}",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Atualmente Ativos",
                value=f"{currently_active}",
                inline=True
            )
            
            embed.add_field(
                name="⏱️ Tempo Médio",
                value=avg_duration,
                inline=True
            )
            
            if session['max_players']:
                embed.add_field(
                    name="🎯 Taxa de Ocupação",
                    value=f"{(currently_active / session['max_players'] * 100):.1f}%",
                    inline=True
                )
            
            # Adicionar lista de participantes ativos
            if currently_active > 0:
                active_users = [f"<@{user_id}>" for user_id in session['checked_in_players']]
                embed.add_field(
                    name="👥 Participantes Ativos",
                    value="\n".join(active_users[:10]) + ("\n..." if len(active_users) > 10 else ""),
                    inline=False
                )
            
            embed.set_footer(text=f"ID da Sessão: {sessao_id}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
            
    @app_commands.command(name="admin_listar_todas_sessoes", description="[ADMIN] Lista todas as sessões (ativas e inativas)")
    @app_commands.describe(
        status="Filtrar por status específico",
        limite="Número máximo de sessões para mostrar"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Todas", value="all"),
        app_commands.Choice(name="Ativas", value="active"),
        app_commands.Choice(name="Completadas", value="completed"),
        app_commands.Choice(name="Canceladas", value="cancelled")
    ])
    async def admin_listar_todas_sessoes(self, interaction: discord.Interaction, status: str = "all", limite: int = 20):
        """Lista todas as sessões com filtros (apenas administradores)"""
        # Verificar permissões de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
            
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Obter todas as sessões
            all_sessions = self.checkin_system.get_all_sessions()
            
            # Filtrar por status se especificado
            if status != "all":
                all_sessions = [s for s in all_sessions if s['status'] == status]
                
            # Limitar número de resultados
            sessions = all_sessions[:limite]
            
            if not sessions:
                embed = discord.Embed(
                    title="📋 Sessões",
                    description="Nenhuma sessão encontrada com os filtros especificados.",
                    color=0x999999
                )
                await interaction.followup.send(embed=embed)
                return
                
            embed = discord.Embed(
                title="📋 Todas as Sessões",
                description=f"**{len(sessions)} sessão(ões) encontrada(s)** (de {len(all_sessions)} total)",
                color=0x0099FF,
                timestamp=datetime.now()
            )
            
            for session in sessions:
                status_emoji = {
                    'active': '🟢',
                    'completed': '✅',
                    'cancelled': '❌',
                    'scheduled': '⏰'
                }.get(session['status'], '❓')
                
                start_time = datetime.fromisoformat(session['start_time'])
                
                embed.add_field(
                    name=f"{status_emoji} {session['name']}",
                    value=f"**Tipo:** {session['session_type'].replace('_', ' ').title()}\n" +
                          f"**ID:** `{session['session_id']}`\n" +
                          f"**Início:** <t:{int(start_time.timestamp())}:R>\n" +
                          f"**Participantes:** {len(session['checked_in_players'])}{f'/{session["max_players"]}' if session['max_players'] else ''}",
                    inline=True
                )
                
            embed.set_footer(text=f"Filtro: {status.title()} | Limite: {limite}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
            
async def setup(bot):
    await bot.add_cog(CheckInAdmin(bot))