"""Comandos do Sistema de Economia Virtual

Comandos Discord para interagir com o sistema de economia avançado.
"""

import discord
from discord.ext import commands
from typing import Optional, Union
from datetime import datetime

from src.features.economy import (
    EconomySystem, CurrencyType, ItemCategory, ItemRarity,
    InvestmentType, OrderType
)
from src.utils.embed_templates import create_embed, create_error_embed
from src.core.secure_logger import SecureLogger

class EconomyCog(commands.Cog):
    """Cog para comandos de economia"""
    
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomySystem()
        self.logger = SecureLogger("EconomyCog")
    
    async def cog_load(self):
        """Inicializar sistema de economia"""
        await self.economy.initialize()
        self.logger.info("Sistema de economia inicializado")
    
    async def cog_unload(self):
        """Desligar sistema de economia"""
        await self.economy.shutdown()
        self.logger.info("Sistema de economia desligado")
    
    @commands.group(name='economia', aliases=['eco', 'economy'], invoke_without_command=True)
    async def economy_group(self, ctx):
        """Comandos do sistema de economia"""
        embed = create_embed(
            title="💰 Sistema de Economia Virtual",
            description="Use os subcomandos para interagir com a economia!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="💳 Carteira",
            value="`economia carteira` - Ver seu saldo\n`economia transferir` - Transferir moedas",
            inline=False
        )
        
        embed.add_field(
            name="🛒 Loja",
            value="`economia loja` - Ver itens da loja\n`economia comprar` - Comprar item",
            inline=False
        )
        
        embed.add_field(
            name="📦 Inventário",
            value="`economia inventario` - Ver seus itens",
            inline=False
        )
        
        embed.add_field(
            name="📈 Investimentos",
            value="`economia investir` - Fazer investimento\n`economia investimentos` - Ver investimentos",
            inline=False
        )
        
        embed.add_field(
            name="🏪 Mercado P2P",
            value="`economia mercado` - Ver mercado\n`economia vender` - Criar ordem de venda",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Bônus",
            value="`economia bonus` - Reivindicar bônus diário",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @economy_group.command(name='carteira', aliases=['wallet', 'saldo', 'balance'])
    async def wallet_command(self, ctx, user: Optional[discord.Member] = None):
        """Ver carteira de um usuário"""
        target_user = user or ctx.author
        user_id = str(target_user.id)
        
        try:
            wallet = await self.economy.get_wallet(user_id)
            stats = await self.economy.get_user_economy_stats(user_id)
            
            embed = create_embed(
                title=f"💳 Carteira de {target_user.display_name}",
                color=discord.Color.gold()
            )
            
            # Saldos das moedas
            for currency in CurrencyType:
                amount = wallet.currencies.get(currency, 0)
                emoji = self._get_currency_emoji(currency)
                embed.add_field(
                    name=f"{emoji} {currency.value.title()}",
                    value=f"{amount:,.2f}",
                    inline=True
                )
            
            # Estatísticas adicionais
            embed.add_field(
                name="📊 Estatísticas",
                value=(
                    f"💎 Valor do Inventário: {stats['inventory_value']:,.2f}\n"
                    f"📈 Valor dos Investimentos: {stats['investment_value']:,.2f}\n"
                    f"💰 Patrimônio Total: {stats['total_wealth']:,.2f}"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar carteira: {e}")
            await ctx.send(embed=create_error_embed("Erro ao acessar carteira"))
    
    @economy_group.command(name='transferir', aliases=['transfer', 'enviar', 'send'])
    async def transfer_command(self, ctx, user: discord.Member, currency: str, amount: float):
        """Transferir moedas para outro usuário"""
        if user.bot:
            await ctx.send(embed=create_error_embed("Não é possível transferir para bots"))
            return
        
        if user.id == ctx.author.id:
            await ctx.send(embed=create_error_embed("Não é possível transferir para si mesmo"))
            return
        
        try:
            # Validar tipo de moeda
            currency_type = None
            for curr in CurrencyType:
                if curr.value.lower() == currency.lower():
                    currency_type = curr
                    break
            
            if not currency_type:
                await ctx.send(embed=create_error_embed("Tipo de moeda inválido"))
                return
            
            # Realizar transferência
            success = await self.economy.transfer_currency(
                str(ctx.author.id),
                str(user.id),
                currency_type,
                amount
            )
            
            if success:
                emoji = self._get_currency_emoji(currency_type)
                embed = create_embed(
                    title="✅ Transferência Realizada",
                    description=(
                        f"Você transferiu {emoji} **{amount:,.2f} {currency_type.value}** "
                        f"para {user.mention}"
                    ),
                    color=discord.Color.green()
                )
            else:
                embed = create_error_embed("Falha na transferência. Verifique seu saldo.")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro na transferência: {e}")
            await ctx.send(embed=create_error_embed("Erro durante a transferência"))
    
    @economy_group.command(name='loja', aliases=['shop', 'store'])
    async def shop_command(self, ctx, categoria: Optional[str] = None, pagina: int = 1):
        """Ver itens da loja"""
        try:
            # Filtrar por categoria se especificada
            category_filter = None
            if categoria:
                for cat in ItemCategory:
                    if cat.value.lower() == categoria.lower():
                        category_filter = cat
                        break
            
            items = await self.economy.get_shop_items(
                category=category_filter,
                limit=10,
                offset=(pagina - 1) * 10
            )
            
            if not items:
                await ctx.send(embed=create_error_embed("Nenhum item encontrado na loja"))
                return
            
            embed = create_embed(
                title="🛒 Loja Virtual",
                description=f"Página {pagina} - {len(items)} itens",
                color=discord.Color.blue()
            )
            
            for item in items:
                rarity_emoji = self._get_rarity_emoji(item.rarity)
                currency_emoji = self._get_currency_emoji(item.currency_type)
                
                stock_text = f"Estoque: {item.stock}" if item.stock is not None else "Ilimitado"
                
                embed.add_field(
                    name=f"{rarity_emoji} {item.name}",
                    value=(
                        f"{item.description}\n"
                        f"💰 Preço: {currency_emoji} {item.price:,.2f}\n"
                        f"📦 {stock_text}"
                    ),
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar loja: {e}")
            await ctx.send(embed=create_error_embed("Erro ao acessar a loja"))
    
    @economy_group.command(name='comprar', aliases=['buy', 'purchase'])
    async def buy_command(self, ctx, item_id: str, quantidade: int = 1):
        """Comprar item da loja"""
        try:
            success = await self.economy.purchase_item(
                str(ctx.author.id),
                item_id,
                quantidade
            )
            
            if success:
                embed = create_embed(
                    title="✅ Compra Realizada",
                    description=f"Você comprou **{quantidade}x {item_id}** com sucesso!",
                    color=discord.Color.green()
                )
            else:
                embed = create_error_embed("Falha na compra. Verifique saldo e estoque.")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro na compra: {e}")
            await ctx.send(embed=create_error_embed("Erro durante a compra"))
    
    @economy_group.command(name='inventario', aliases=['inventory', 'inv', 'items'])
    async def inventory_command(self, ctx, user: Optional[discord.Member] = None):
        """Ver inventário de um usuário"""
        target_user = user or ctx.author
        user_id = str(target_user.id)
        
        try:
            inventory = await self.economy.get_user_inventory(user_id)
            
            if not inventory:
                await ctx.send(embed=create_error_embed("Inventário vazio"))
                return
            
            embed = create_embed(
                title=f"📦 Inventário de {target_user.display_name}",
                description=f"{len(inventory)} tipos de itens",
                color=discord.Color.purple()
            )
            
            for item in inventory[:15]:  # Limitar a 15 itens
                rarity_emoji = self._get_rarity_emoji(item.rarity)
                
                embed.add_field(
                    name=f"{rarity_emoji} {item.name}",
                    value=(
                        f"Quantidade: **{item.quantity}**\n"
                        f"Valor unitário: 💰 {item.value:,.2f}"
                    ),
                    inline=True
                )
            
            if len(inventory) > 15:
                embed.set_footer(text=f"... e mais {len(inventory) - 15} itens")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar inventário: {e}")
            await ctx.send(embed=create_error_embed("Erro ao acessar inventário"))
    
    @economy_group.command(name='bonus', aliases=['daily', 'diario'])
    async def daily_bonus_command(self, ctx):
        """Reivindicar bônus diário"""
        try:
            result = await self.economy.claim_daily_bonus(str(ctx.author.id))
            
            if result['success']:
                embed = create_embed(
                    title="🎁 Bônus Diário Coletado!",
                    description=(
                        f"Você recebeu:\n"
                        f"💰 **{result['coins_earned']:,.0f} Coins**\n"
                        f"💎 **{result['gems_earned']:,.0f} Gems**\n\n"
                        f"🔥 Sequência atual: **{result['current_streak']} dias**"
                    ),
                    color=discord.Color.gold()
                )
                
                if result['current_streak'] > 1:
                    embed.add_field(
                        name="🚀 Bônus de Sequência",
                        value=f"Multiplicador: **{result['streak_multiplier']:.1f}x**",
                        inline=False
                    )
            else:
                info = await self.economy.get_daily_bonus_info(str(ctx.author.id))
                next_claim = info['next_claim_time']
                
                embed = create_error_embed(
                    f"Você já coletou seu bônus hoje!\n"
                    f"Próximo bônus disponível: <t:{int(next_claim.timestamp())}:R>"
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro no bônus diário: {e}")
            await ctx.send(embed=create_error_embed("Erro ao processar bônus diário"))
    
    @economy_group.command(name='investir', aliases=['invest'])
    async def invest_command(self, ctx, tipo: str, valor: float):
        """Fazer um investimento"""
        try:
            # Validar tipo de investimento
            investment_type = None
            for inv_type in InvestmentType:
                if inv_type.value.lower() == tipo.lower():
                    investment_type = inv_type
                    break
            
            if not investment_type:
                await ctx.send(embed=create_error_embed("Tipo de investimento inválido"))
                return
            
            success = await self.economy.create_investment(
                str(ctx.author.id),
                investment_type,
                valor
            )
            
            if success:
                embed = create_embed(
                    title="📈 Investimento Realizado",
                    description=(
                        f"Você investiu **💰 {valor:,.2f} Coins** em **{investment_type.value}**\n"
                        f"Acompanhe o rendimento com `economia investimentos`"
                    ),
                    color=discord.Color.green()
                )
            else:
                embed = create_error_embed("Falha no investimento. Verifique seu saldo.")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro no investimento: {e}")
            await ctx.send(embed=create_error_embed("Erro durante o investimento"))
    
    @economy_group.command(name='investimentos', aliases=['investments'])
    async def investments_command(self, ctx, user: Optional[discord.Member] = None):
        """Ver investimentos de um usuário"""
        target_user = user or ctx.author
        user_id = str(target_user.id)
        
        try:
            investments = await self.economy.get_user_investments(user_id)
            
            if not investments:
                await ctx.send(embed=create_error_embed("Nenhum investimento encontrado"))
                return
            
            embed = create_embed(
                title=f"📈 Investimentos de {target_user.display_name}",
                description=f"{len(investments)} investimentos ativos",
                color=discord.Color.green()
            )
            
            total_invested = 0
            total_current = 0
            
            for inv in investments:
                profit_loss = inv.current_value - inv.initial_amount
                profit_percent = (profit_loss / inv.initial_amount) * 100
                
                status_emoji = "📈" if profit_loss >= 0 else "📉"
                
                embed.add_field(
                    name=f"{status_emoji} {inv.investment_type.value.title()}",
                    value=(
                        f"Investido: 💰 {inv.initial_amount:,.2f}\n"
                        f"Atual: 💰 {inv.current_value:,.2f}\n"
                        f"Lucro: {profit_loss:+,.2f} ({profit_percent:+.1f}%)"
                    ),
                    inline=True
                )
                
                total_invested += inv.initial_amount
                total_current += inv.current_value
            
            total_profit = total_current - total_invested
            total_percent = (total_profit / total_invested) * 100 if total_invested > 0 else 0
            
            embed.add_field(
                name="💼 Resumo Total",
                value=(
                    f"Investido: 💰 {total_invested:,.2f}\n"
                    f"Valor Atual: 💰 {total_current:,.2f}\n"
                    f"Lucro Total: {total_profit:+,.2f} ({total_percent:+.1f}%)"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar investimentos: {e}")
            await ctx.send(embed=create_error_embed("Erro ao acessar investimentos"))
    
    def _get_currency_emoji(self, currency: CurrencyType) -> str:
        """Obter emoji para tipo de moeda"""
        emojis = {
            CurrencyType.COINS: "💰",
            CurrencyType.GEMS: "💎",
            CurrencyType.TOKENS: "🪙",
            CurrencyType.CREDITS: "⭐",
            CurrencyType.EXPERIENCE: "✨"
        }
        return emojis.get(currency, "💰")
    
    def _get_rarity_emoji(self, rarity: ItemRarity) -> str:
        """Obter emoji para raridade do item"""
        emojis = {
            ItemRarity.COMMON: "⚪",
            ItemRarity.UNCOMMON: "🟢",
            ItemRarity.RARE: "🔵",
            ItemRarity.EPIC: "🟣",
            ItemRarity.LEGENDARY: "🟡",
            ItemRarity.MYTHIC: "🔴"
        }
        return emojis.get(rarity, "⚪")

async def setup(bot):
    """Configurar o cog"""
    await bot.add_cog(EconomyCog(bot))