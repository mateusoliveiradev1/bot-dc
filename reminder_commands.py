#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comandos de Gerenciamento de Lembretes
Comandos para configurar e gerenciar lembretes automáticos

Autor: Desenvolvedor Sênior
Versão: 1.0.0
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger('HawkBot.ReminderCommands')

class ReminderCommands(commands.Cog):
    """Comandos para gerenciamento de lembretes"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Comandos de Lembretes carregados")
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário é administrador"""
        return (interaction.user.guild_permissions.administrator or 
                any(role.name.lower() in ['admin', 'administrador', 'moderador'] 
                    for role in interaction.user.roles))
    
    @app_commands.command(name="lembrete_criar", description="Criar um lembrete personalizado")
    @app_commands.describe(
        titulo="Título do lembrete",
        mensagem="Mensagem do lembrete",
        tempo="Tempo para o lembrete (ex: 30m, 2h, 1d)",
        canal="Canal onde enviar o lembrete (opcional)"
    )
    async def criar_lembrete(self, interaction: discord.Interaction, 
                           titulo: str, mensagem: str, tempo: str,
                           canal: Optional[discord.TextChannel] = None):
        """Cria um lembrete personalizado"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando.", 
                ephemeral=True
            )
            return
        
        try:
            # Parsear tempo
            reminder_time = self._parse_time(tempo)
            if not reminder_time:
                await interaction.response.send_message(
                    "❌ Formato de tempo inválido. Use: 30m, 2h, 1d, etc.", 
                    ephemeral=True
                )
                return
            
            # Criar lembrete
            channel_id = canal.id if canal else interaction.channel.id
            reminder_id = self.bot.checkin_reminders.create_custom_reminder(
                title=titulo,
                message=mensagem,
                reminder_time=reminder_time,
                channel_id=channel_id,
                author=str(interaction.user)
            )
            
            embed = discord.Embed(
                title="✅ Lembrete Criado",
                description=f"Lembrete **{titulo}** criado com sucesso!",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Detalhes",
                value=f"**ID:** {reminder_id}\n"
                      f"**Mensagem:** {mensagem}\n"
                      f"**Horário:** <t:{int(reminder_time.timestamp())}:F>\n"
                      f"**Canal:** {canal.mention if canal else interaction.channel.mention}",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Lembrete criado por {interaction.user}: {titulo}")
            
        except Exception as e:
            logger.error(f"Erro ao criar lembrete: {e}")
            await interaction.response.send_message(
                "❌ Erro ao criar lembrete. Tente novamente.", 
                ephemeral=True
            )
    
    @app_commands.command(name="lembrete_listar", description="Listar lembretes personalizados")
    async def listar_lembretes(self, interaction: discord.Interaction):
        """Lista todos os lembretes personalizados"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando.", 
                ephemeral=True
            )
            return
        
        try:
            reminders = self.bot.checkin_reminders.get_custom_reminders()
            
            if not reminders:
                await interaction.response.send_message(
                    "📝 Nenhum lembrete personalizado encontrado.", 
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📋 Lembretes Personalizados",
                description=f"Total: {len(reminders)} lembretes",
                color=0x3498DB,
                timestamp=datetime.now()
            )
            
            for reminder in reminders[:10]:  # Limitar a 10 para não sobrecarregar
                status = "✅ Enviado" if reminder.get('sent', False) else "⏳ Pendente"
                reminder_time = datetime.fromisoformat(reminder['time'])
                
                embed.add_field(
                    name=f"🔔 {reminder['title']}",
                    value=f"**Status:** {status}\n"
                          f"**Horário:** <t:{int(reminder_time.timestamp())}:R>\n"
                          f"**ID:** `{reminder['id']}`",
                    inline=True
                )
            
            if len(reminders) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(reminders)} lembretes")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao listar lembretes: {e}")
            await interaction.response.send_message(
                "❌ Erro ao listar lembretes.", 
                ephemeral=True
            )
    
    @app_commands.command(name="lembrete_remover", description="Remover um lembrete personalizado")
    @app_commands.describe(reminder_id="ID do lembrete a ser removido")
    async def remover_lembrete(self, interaction: discord.Interaction, reminder_id: str):
        """Remove um lembrete personalizado"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando.", 
                ephemeral=True
            )
            return
        
        try:
            success = self.bot.checkin_reminders.delete_custom_reminder(reminder_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Lembrete Removido",
                    description=f"Lembrete `{reminder_id}` removido com sucesso!",
                    color=0x00FF00,
                    timestamp=datetime.now()
                )
                logger.info(f"Lembrete removido por {interaction.user}: {reminder_id}")
            else:
                embed = discord.Embed(
                    title="❌ Lembrete Não Encontrado",
                    description=f"Lembrete `{reminder_id}` não foi encontrado.",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao remover lembrete: {e}")
            await interaction.response.send_message(
                "❌ Erro ao remover lembrete.", 
                ephemeral=True
            )
    
    @app_commands.command(name="lembrete_config", description="Configurar lembretes automáticos")
    @app_commands.describe(
        tipo="Tipo de lembrete",
        ativo="Ativar ou desativar",
        tempos="Tempos em minutos (separados por vírgula)"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Início de Sessão", value="session_start"),
        app_commands.Choice(name="Deadline Check-in", value="checkin_deadline"),
        app_commands.Choice(name="Fim de Sessão", value="session_end"),
        app_commands.Choice(name="Lembrete Check-out", value="checkout_reminder")
    ])
    async def configurar_lembretes(self, interaction: discord.Interaction, 
                                 tipo: str, ativo: bool, 
                                 tempos: Optional[str] = None):
        """Configura lembretes automáticos"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando.", 
                ephemeral=True
            )
            return
        
        try:
            # Parsear tempos se fornecidos
            time_list = None
            if tempos:
                try:
                    time_list = [int(t.strip()) for t in tempos.split(',')]
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Formato de tempos inválido. Use números separados por vírgula (ex: 30,15,5).", 
                        ephemeral=True
                    )
                    return
            
            # Atualizar configurações
            success = self.bot.checkin_reminders.update_reminder_settings(
                reminder_type=tipo,
                enabled=ativo,
                times=time_list
            )
            
            if success:
                tipo_names = {
                    "session_start": "Início de Sessão",
                    "checkin_deadline": "Deadline Check-in",
                    "session_end": "Fim de Sessão",
                    "checkout_reminder": "Lembrete Check-out"
                }
                
                embed = discord.Embed(
                    title="✅ Configuração Atualizada",
                    description=f"Lembretes de **{tipo_names.get(tipo, tipo)}** configurados!",
                    color=0x00FF00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📋 Configurações",
                    value=f"**Status:** {'✅ Ativo' if ativo else '❌ Inativo'}\n"
                          f"**Tempos:** {', '.join(map(str, time_list)) + ' minutos' if time_list else 'Não alterado'}",
                    inline=False
                )
                
                logger.info(f"Configuração de lembrete atualizada por {interaction.user}: {tipo}")
            else:
                embed = discord.Embed(
                    title="❌ Erro na Configuração",
                    description="Não foi possível atualizar as configurações.",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao configurar lembretes: {e}")
            await interaction.response.send_message(
                "❌ Erro ao configurar lembretes.", 
                ephemeral=True
            )
    
    @app_commands.command(name="lembrete_status", description="Ver status das configurações de lembretes")
    async def status_lembretes(self, interaction: discord.Interaction):
        """Mostra o status atual das configurações de lembretes"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando.", 
                ephemeral=True
            )
            return
        
        try:
            settings = self.bot.checkin_reminders.get_reminder_settings()
            
            embed = discord.Embed(
                title="⚙️ Status dos Lembretes",
                description="Configurações atuais do sistema de lembretes",
                color=0x3498DB,
                timestamp=datetime.now()
            )
            
            # Status dos lembretes automáticos
            enabled = settings.get('enabled_reminders', {})
            defaults = settings.get('default_reminders', {})
            
            tipo_names = {
                "session_start": "🚀 Início de Sessão",
                "checkin_deadline": "⏰ Deadline Check-in",
                "session_end": "🏁 Fim de Sessão",
                "checkout_reminder": "👋 Lembrete Check-out"
            }
            
            for tipo, nome in tipo_names.items():
                status = "✅ Ativo" if enabled.get(tipo, True) else "❌ Inativo"
                tempos = defaults.get(tipo, [])
                tempos_str = ', '.join(map(str, tempos)) + ' min' if tempos else 'Não configurado'
                
                embed.add_field(
                    name=nome,
                    value=f"**Status:** {status}\n**Tempos:** {tempos_str}",
                    inline=True
                )
            
            # Lembretes personalizados
            custom_count = len(settings.get('custom_reminders', {}))
            embed.add_field(
                name="📝 Lembretes Personalizados",
                value=f"**Total:** {custom_count} lembretes",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar status dos lembretes: {e}")
            await interaction.response.send_message(
                "❌ Erro ao carregar status dos lembretes.", 
                ephemeral=True
            )
    
    @app_commands.command(name="lembrete_limpar", description="Limpar lembretes antigos")
    @app_commands.describe(dias="Número de dias (lembretes mais antigos serão removidos)")
    async def limpar_lembretes(self, interaction: discord.Interaction, dias: int = 7):
        """Limpa lembretes antigos"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                "❌ Você precisa ser administrador para usar este comando.", 
                ephemeral=True
            )
            return
        
        try:
            if dias < 1 or dias > 365:
                await interaction.response.send_message(
                    "❌ Número de dias deve estar entre 1 e 365.", 
                    ephemeral=True
                )
                return
            
            # Realizar limpeza
            self.bot.checkin_reminders.cleanup_old_reminders(dias)
            
            embed = discord.Embed(
                title="🧹 Limpeza Concluída",
                description=f"Lembretes mais antigos que {dias} dias foram removidos.",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Informações",
                value=f"**Critério:** Lembretes com mais de {dias} dias\n"
                      f"**Executado por:** {interaction.user.mention}",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Limpeza de lembretes executada por {interaction.user} ({dias} dias)")
            
        except Exception as e:
            logger.error(f"Erro ao limpar lembretes: {e}")
            await interaction.response.send_message(
                "❌ Erro ao limpar lembretes.", 
                ephemeral=True
            )
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Converte string de tempo em datetime futuro"""
        try:
            time_str = time_str.lower().strip()
            now = datetime.now()
            
            if time_str.endswith('m'):
                minutes = int(time_str[:-1])
                return now + timedelta(minutes=minutes)
            elif time_str.endswith('h'):
                hours = int(time_str[:-1])
                return now + timedelta(hours=hours)
            elif time_str.endswith('d'):
                days = int(time_str[:-1])
                return now + timedelta(days=days)
            else:
                # Tentar parsear como minutos
                minutes = int(time_str)
                return now + timedelta(minutes=minutes)
                
        except (ValueError, IndexError):
            return None

async def setup(bot):
    """Carrega a extensão"""
    await bot.add_cog(ReminderCommands(bot))
    logger.info("Extensão ReminderCommands carregada")