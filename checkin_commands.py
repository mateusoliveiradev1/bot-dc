import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
from checkin_system import CheckInSystem, SessionType
import asyncio

class CheckInCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checkin_system = None
    
    def setup_checkin_system(self, storage):
        """Configura o sistema de check-in"""
        self.checkin_system = CheckInSystem(self.bot, storage)
    
    @app_commands.command(name="criar_sessao", description="Cria uma nova sessão de check-in")
    @app_commands.describe(
        tipo="Tipo da sessão (scrim, ranked, mm, tournament)",
        inicio="Horário de início (formato: DD/MM/YYYY HH:MM)",
        fim="Horário de fim (formato: DD/MM/YYYY HH:MM)",
        max_jogadores="Número máximo de jogadores (opcional)",
        descricao="Descrição da sessão (opcional)"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Scrim", value="scrim"),
        app_commands.Choice(name="Ranked", value="ranked"),
        app_commands.Choice(name="MM (Matchmaking)", value="mm"),
        app_commands.Choice(name="Torneio", value="tournament")
    ])
    async def criar_sessao(self, interaction: discord.Interaction, tipo: str, inicio: str, fim: str, 
                          max_jogadores: Optional[int] = None, descricao: Optional[str] = ""):
        """Cria uma nova sessão de check-in"""
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
        
        # Verifica permissões (apenas administradores ou moderadores)
        if not any(role.name.lower() in ['admin', 'administrador', 'moderador', 'mod'] for role in interaction.user.roles):
            await interaction.response.send_message("❌ Você não tem permissão para criar sessões.", ephemeral=True)
            return
        
        try:
            # Parse das datas
            start_time = datetime.strptime(inicio, "%d/%m/%Y %H:%M")
            end_time = datetime.strptime(fim, "%d/%m/%Y %H:%M")
            
            # Validações
            if start_time <= datetime.now():
                await interaction.response.send_message("❌ O horário de início deve ser no futuro.", ephemeral=True)
                return
            
            if end_time <= start_time:
                await interaction.response.send_message("❌ O horário de fim deve ser após o início.", ephemeral=True)
                return
            
            # Gera ID único para a sessão
            session_id = f"{tipo}_{start_time.strftime('%Y%m%d_%H%M')}"
            
            # Cria a sessão
            session = self.checkin_system.create_session(
                session_id=session_id,
                session_type=SessionType(tipo),
                start_time=start_time,
                end_time=end_time,
                max_players=max_jogadores,
                description=descricao or f"Sessão de {tipo.upper()}"
            )
            
            # Configurar notificações automáticas
            await self.bot.checkin_notifications.setup_session_notifications(
                session_id, interaction.channel.id
            )
            
            # Cria embed de confirmação
            embed = discord.Embed(
                title="✅ Sessão Criada com Sucesso!",
                description=f"**{session['description']}**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="🆔 ID da Sessão", value=f"`{session_id}`", inline=False)
            embed.add_field(name="📅 Tipo", value=tipo.upper(), inline=True)
            embed.add_field(name="⏰ Início", value=f"<t:{int(start_time.timestamp())}:F>", inline=True)
            embed.add_field(name="⏱️ Fim", value=f"<t:{int(end_time.timestamp())}:F>", inline=True)
            
            if max_jogadores:
                embed.add_field(name="👥 Máx. Jogadores", value=str(max_jogadores), inline=True)
            
            embed.add_field(name="📊 Status", value="🟢 Ativa", inline=True)
            embed.add_field(name="👤 Check-ins", value="0", inline=True)
            
            embed.set_footer(text=f"Criado por {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError as e:
            if "time data" in str(e):
                await interaction.response.send_message("❌ Formato de data inválido. Use: DD/MM/YYYY HH:MM", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="checkin", description="Faz check-in em uma sessão")
    @app_commands.describe(sessao_id="ID da sessão para fazer check-in")
    async def checkin(self, interaction: discord.Interaction, sessao_id: str):
        """Comando para fazer check-in"""
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
        
        try:
            result = self.checkin_system.check_in_player(
                session_id=sessao_id,
                user_id=str(interaction.user.id),
                username=interaction.user.display_name
            )
            
            session = result["session"]
            
            embed = discord.Embed(
                title="✅ Check-in Realizado!",
                description=f"**{session['description']}**",
                color=0x00ff00,
                timestamp=result["checkin_time"]
            )
            
            embed.add_field(name="👤 Jogador", value=interaction.user.mention, inline=True)
            embed.add_field(name="📍 Posição", value=f"#{result['position']}", inline=True)
            embed.add_field(name="⏰ Horário", value=f"<t:{int(result['checkin_time'].timestamp())}:T>", inline=True)
            
            embed.add_field(name="📊 Sessão", value=f"`{sessao_id}`", inline=False)
            embed.add_field(name="👥 Check-ins", value=f"{session['checkin_count']}", inline=True)
            
            if session["max_players"]:
                embed.add_field(name="🎯 Limite", value=f"{session['checkin_count']}/{session['max_players']}", inline=True)
            
            embed.set_footer(text="Use /checkout para sair da sessão")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="checkout", description="Faz check-out de uma sessão")
    @app_commands.describe(sessao_id="ID da sessão para fazer check-out")
    async def checkout(self, interaction: discord.Interaction, sessao_id: str):
        """Comando para fazer check-out"""
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
        
        try:
            result = self.checkin_system.check_out_player(
                session_id=sessao_id,
                user_id=str(interaction.user.id)
            )
            
            session = result["session"]
            
            embed = discord.Embed(
                title="👋 Check-out Realizado!",
                description=f"**{session['description']}**",
                color=0xff9900,
                timestamp=result["checkout_time"]
            )
            
            embed.add_field(name="👤 Jogador", value=interaction.user.mention, inline=True)
            embed.add_field(name="⏰ Horário", value=f"<t:{int(result['checkout_time'].timestamp())}:T>", inline=True)
            embed.add_field(name="📊 Sessão", value=f"`{sessao_id}`", inline=False)
            
            embed.add_field(name="👥 Check-outs", value=f"{session['checkout_count']}", inline=True)
            embed.add_field(name="🔄 Ainda Ativos", value=f"{session['checkin_count'] - session['checkout_count']}", inline=True)
            
            embed.set_footer(text="Obrigado pela participação!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Enviar notificação de check-out
            await self.bot.checkin_notifications.send_checkout_notification(
                sessao_id, interaction.user.id, interaction.channel.id
            )
            
        except ValueError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="sessoes_ativas", description="Lista todas as sessões ativas")
    async def sessoes_ativas(self, interaction: discord.Interaction):
        """Lista sessões ativas"""
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
        
        active_sessions = self.checkin_system.get_active_sessions()
        
        if not active_sessions:
            embed = discord.Embed(
                title="📋 Sessões Ativas",
                description="Nenhuma sessão ativa no momento.",
                color=0x999999
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Sessões Ativas",
            description=f"**{len(active_sessions)} sessão(ões) ativa(s)**",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        for session in active_sessions[:10]:  # Limita a 10 sessões
            start_time = datetime.fromisoformat(session["start_time"])
            end_time = datetime.fromisoformat(session["end_time"])
            
            status_emoji = "🟢" if datetime.now() < start_time else "🔴" if datetime.now() > end_time else "🟡"
            
            field_value = f"**Tipo:** {session['type'].upper()}\n"
            field_value += f"**Início:** <t:{int(start_time.timestamp())}:R>\n"
            field_value += f"**Fim:** <t:{int(end_time.timestamp())}:R>\n"
            field_value += f"**Check-ins:** {session['checkin_count']}"
            
            if session["max_players"]:
                field_value += f"/{session['max_players']}"
            
            embed.add_field(
                name=f"{status_emoji} `{session['id']}`",
                value=field_value,
                inline=True
            )
        
        embed.set_footer(text="Use /checkin <sessao_id> para participar")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="info_sessao", description="Mostra informações detalhadas de uma sessão")
    @app_commands.describe(sessao_id="ID da sessão")
    async def info_sessao(self, interaction: discord.Interaction, sessao_id: str):
        """Mostra informações de uma sessão"""
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
        
        summary = self.checkin_system.get_session_summary(sessao_id)
        
        if not summary:
            await interaction.response.send_message(f"❌ Sessão `{sessao_id}` não encontrada.", ephemeral=True)
            return
        
        session_info = summary["session_info"]
        stats = summary["stats"]
        players = summary["players"]
        
        start_time = datetime.fromisoformat(session_info["start_time"])
        end_time = datetime.fromisoformat(session_info["end_time"])
        
        # Determina status da sessão
        now = datetime.now()
        if now < start_time:
            status = "🟡 Aguardando"
        elif now > end_time:
            status = "🔴 Finalizada"
        else:
            status = "🟢 Em Andamento"
        
        embed = discord.Embed(
            title=f"📊 Informações da Sessão",
            description=f"**{session_info['description']}**",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="🆔 ID", value=f"`{session_info['id']}`", inline=True)
        embed.add_field(name="📅 Tipo", value=session_info['type'].upper(), inline=True)
        embed.add_field(name="📊 Status", value=status, inline=True)
        
        embed.add_field(name="⏰ Início", value=f"<t:{int(start_time.timestamp())}:F>", inline=True)
        embed.add_field(name="⏱️ Fim", value=f"<t:{int(end_time.timestamp())}:F>", inline=True)
        embed.add_field(name="⏳ Duração", value=f"{int((end_time - start_time).total_seconds() / 3600)}h", inline=True)
        
        embed.add_field(name="👥 Total Jogadores", value=str(stats['total_players']), inline=True)
        embed.add_field(name="✅ Check-ins", value=str(stats['checked_in']), inline=True)
        embed.add_field(name="👋 Check-outs", value=str(stats['checked_out']), inline=True)
        
        if stats['no_shows'] > 0:
            embed.add_field(name="❌ Faltas", value=str(stats['no_shows']), inline=True)
        
        # Lista jogadores (máximo 10)
        if players:
            player_list = []
            for user_id, player_data in list(players.items())[:10]:
                status_emoji = {
                    "checked_in": "✅",
                    "checked_out": "👋",
                    "no_show": "❌"
                }.get(player_data["status"], "❓")
                
                player_list.append(f"{status_emoji} {player_data['username']}")
            
            embed.add_field(
                name="👤 Jogadores",
                value="\n".join(player_list) or "Nenhum jogador",
                inline=False
            )
            
            if len(players) > 10:
                embed.add_field(name="➕ Mais", value=f"... e mais {len(players) - 10} jogador(es)", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="minhas_sessoes", description="Mostra suas sessões recentes")
    async def minhas_sessoes(self, interaction: discord.Interaction):
        """Mostra sessões do usuário"""
        if not self.checkin_system:
            await interaction.response.send_message("❌ Sistema de check-in não está configurado.", ephemeral=True)
            return
        
        user_sessions = self.checkin_system.get_player_sessions(str(interaction.user.id), limit=5)
        
        if not user_sessions:
            embed = discord.Embed(
                title="📋 Minhas Sessões",
                description="Você ainda não participou de nenhuma sessão.",
                color=0x999999
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 Minhas Sessões",
            description=f"**Suas {len(user_sessions)} sessões mais recentes**",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        for session in user_sessions:
            player_data = session["player_data"]
            start_time = datetime.fromisoformat(session["start_time"])
            
            status_emoji = {
                "checked_in": "✅",
                "checked_out": "👋",
                "no_show": "❌"
            }.get(player_data["status"], "❓")
            
            field_value = f"**Tipo:** {session['type'].upper()}\n"
            field_value += f"**Data:** <t:{int(start_time.timestamp())}:D>\n"
            field_value += f"**Status:** {status_emoji} {player_data['status'].replace('_', ' ').title()}"
            
            if player_data.get("checkin_time"):
                checkin_time = datetime.fromisoformat(player_data["checkin_time"])
                field_value += f"\n**Check-in:** <t:{int(checkin_time.timestamp())}:t>"
            
            embed.add_field(
                name=f"`{session['id']}`",
                value=field_value,
                inline=True
            )
        
        # Adiciona estatísticas do jogador
        stats = self.checkin_system.get_player_stats(str(interaction.user.id))
        
        embed.add_field(
            name="📊 Suas Estatísticas",
            value=f"**Check-ins:** {stats['total_checkins']}\n"
                  f"**Check-outs:** {stats['total_checkouts']}\n"
                  f"**Faltas:** {stats['no_shows']}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CheckInCommands(bot))