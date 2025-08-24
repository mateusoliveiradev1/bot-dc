"""Sistema de Economia Virtual Avançado

Sistema completo de economia virtual com múltiplas moedas, transações seguras,
loja virtual, investimentos, mercado P2P e análise econômica com IA.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import random
import math

# Importar sistemas core modernos (com fallbacks)
try:
    from src.core.secure_logger import SecureLogger
    from src.core.smart_cache import SmartCache
    from src.core.metrics_collector import MetricsCollector
    from src.core.data_validator import DataValidator
    from src.core.event_system import EventSystem
    from src.core.rate_limiter import RateLimiter
except ImportError:
    # Fallbacks simples para testes
    class SecureLogger:
        def __init__(self, name): self.name = name
        def info(self, msg): print(f"[INFO] {self.name}: {msg}")
        def error(self, msg): print(f"[ERROR] {self.name}: {msg}")
        def warning(self, msg): print(f"[WARNING] {self.name}: {msg}")
    
    class SmartCache:
        def __init__(self): self._cache = {}
        async def get(self, key): return self._cache.get(key)
        async def set(self, key, value, ttl=None): self._cache[key] = value
        async def delete(self, key): self._cache.pop(key, None)
        async def clear(self): self._cache.clear()
    
    class MetricsCollector:
        def __init__(self): pass
        async def increment(self, metric, value=1, tags=None): pass
        async def gauge(self, metric, value, tags=None): pass
        async def timing(self, metric, value, tags=None): pass
    
    class DataValidator:
        def __init__(self): pass
        def validate_user_id(self, user_id): return isinstance(user_id, str) and user_id.isdigit()
        def validate_amount(self, amount): return isinstance(amount, (int, float)) and amount > 0
    
    class EventSystem:
        def __init__(self): pass
        async def emit(self, event, data): pass
    
    class RateLimiter:
        def __init__(self): pass
        async def is_rate_limited(self, key): return False
        async def increment(self, key): pass

class CurrencyType(Enum):
    """Tipos de moedas no sistema"""
    COINS = "coins"  # Moeda principal
    GEMS = "gems"    # Moeda premium
    TOKENS = "tokens"  # Moeda de eventos
    CREDITS = "credits"  # Moeda de atividades
    EXPERIENCE = "experience"  # XP como moeda

class TransactionType(Enum):
    """Tipos de transações"""
    PURCHASE = "purchase"  # Compra na loja
    SALE = "sale"  # Venda de item
    TRANSFER = "transfer"  # Transferência entre usuários
    REWARD = "reward"  # Recompensa do sistema
    PENALTY = "penalty"  # Penalidade/multa
    INVESTMENT = "investment"  # Investimento
    DIVIDEND = "dividend"  # Dividendo de investimento
    TRADE = "trade"  # Troca P2P
    AUCTION = "auction"  # Leilão
    GAMBLING = "gambling"  # Jogos de azar
    DAILY_BONUS = "daily_bonus"  # Bônus diário
    ACHIEVEMENT = "achievement"  # Conquista
    TOURNAMENT = "tournament"  # Torneio
    MINIGAME = "minigame"  # Minijogo

class TransactionStatus(Enum):
    """Status de transações"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class ItemRarity(Enum):
    """Raridade de itens"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

class ItemCategory(Enum):
    """Categorias de itens"""
    COSMETIC = "cosmetic"  # Cosméticos
    BOOST = "boost"  # Multiplicadores
    BADGE = "badge"  # Emblemas
    TITLE = "title"  # Títulos
    ROLE = "role"  # Cargos temporários
    UTILITY = "utility"  # Utilitários
    COLLECTIBLE = "collectible"  # Colecionáveis
    CONSUMABLE = "consumable"  # Consumíveis

class InvestmentType(Enum):
    """Tipos de investimentos"""
    SAVINGS = "savings"  # Poupança
    STOCKS = "stocks"  # Ações do servidor
    BONDS = "bonds"  # Títulos
    CRYPTO = "crypto"  # Criptomoedas fictícias
    REAL_ESTATE = "real_estate"  # Imóveis virtuais

class MarketOrderType(Enum):
    """Tipos de ordens no mercado"""
    BUY = "buy"
    SELL = "sell"

class MarketOrderStatus(Enum):
    """Status de ordens no mercado"""
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

# Modelos Pydantic
class CurrencyBalance(BaseModel):
    """Saldo de uma moeda específica"""
    currency: CurrencyType
    amount: Decimal = Field(default=Decimal('0'), ge=0)
    locked_amount: Decimal = Field(default=Decimal('0'), ge=0)  # Valor bloqueado em transações
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def available_amount(self) -> Decimal:
        """Valor disponível para uso"""
        return self.amount - self.locked_amount

class WalletModel(BaseModel):
    """Carteira do usuário"""
    user_id: int
    balances: Dict[CurrencyType, CurrencyBalance] = Field(default_factory=dict)
    total_earned: Dict[CurrencyType, Decimal] = Field(default_factory=dict)
    total_spent: Dict[CurrencyType, Decimal] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    
    def get_balance(self, currency: CurrencyType) -> Decimal:
        """Obter saldo de uma moeda"""
        if currency not in self.balances:
            self.balances[currency] = CurrencyBalance(currency=currency)
        return self.balances[currency].amount
    
    def get_available_balance(self, currency: CurrencyType) -> Decimal:
        """Obter saldo disponível de uma moeda"""
        if currency not in self.balances:
            self.balances[currency] = CurrencyBalance(currency=currency)
        return self.balances[currency].available_amount

class TransactionModel(BaseModel):
    """Modelo de transação"""
    transaction_id: str
    from_user_id: Optional[int] = None
    to_user_id: Optional[int] = None
    transaction_type: TransactionType
    currency: CurrencyType
    amount: Decimal = Field(gt=0)
    fee: Decimal = Field(default=Decimal('0'), ge=0)
    status: TransactionStatus = TransactionStatus.PENDING
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }

class ShopItemModel(BaseModel):
    """Item da loja"""
    item_id: str
    name: str
    description: str
    category: ItemCategory
    rarity: ItemRarity
    price: Dict[CurrencyType, Decimal] = Field(default_factory=dict)
    stock: Optional[int] = None  # None = estoque infinito
    max_per_user: Optional[int] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    effects: Dict[str, Any] = Field(default_factory=dict)
    duration: Optional[timedelta] = None  # Para itens temporários
    emoji: str = "📦"
    image_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('price')
    def validate_price(cls, v):
        """Validar que pelo menos um preço foi definido"""
        if not v:
            raise ValueError("Item deve ter pelo menos um preço definido")
        return v

class UserInventoryItem(BaseModel):
    """Item no inventário do usuário"""
    item_id: str
    quantity: int = Field(default=1, ge=1)
    acquired_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Verificar se o item expirou"""
        return self.expires_at is not None and datetime.now() > self.expires_at

class InvestmentModel(BaseModel):
    """Modelo de investimento"""
    investment_id: str
    user_id: int
    investment_type: InvestmentType
    currency: CurrencyType
    principal_amount: Decimal = Field(gt=0)
    current_value: Decimal = Field(gt=0)
    interest_rate: Decimal = Field(ge=0)  # Taxa de juros anual
    created_at: datetime = Field(default_factory=datetime.now)
    maturity_date: Optional[datetime] = None
    last_dividend: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def profit_loss(self) -> Decimal:
        """Lucro ou prejuízo atual"""
        return self.current_value - self.principal_amount
    
    @property
    def return_percentage(self) -> Decimal:
        """Percentual de retorno"""
        if self.principal_amount == 0:
            return Decimal('0')
        return (self.profit_loss / self.principal_amount) * 100

class MarketOrderModel(BaseModel):
    """Ordem no mercado P2P"""
    order_id: str
    user_id: int
    order_type: MarketOrderType
    item_id: str
    quantity: int = Field(ge=1)
    price_per_unit: Decimal = Field(gt=0)
    currency: CurrencyType
    status: MarketOrderStatus = MarketOrderStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    filled_quantity: int = Field(default=0, ge=0)
    
    @property
    def remaining_quantity(self) -> int:
        """Quantidade restante"""
        return self.quantity - self.filled_quantity
    
    @property
    def total_price(self) -> Decimal:
        """Preço total da ordem"""
        return self.price_per_unit * self.quantity
    
    @property
    def is_expired(self) -> bool:
        """Verificar se a ordem expirou"""
        return datetime.now() > self.expires_at

class EconomicIndicators(BaseModel):
    """Indicadores econômicos do servidor"""
    total_currency_supply: Dict[CurrencyType, Decimal] = Field(default_factory=dict)
    daily_transactions: int = 0
    daily_volume: Dict[CurrencyType, Decimal] = Field(default_factory=dict)
    inflation_rate: Decimal = Field(default=Decimal('0'))
    market_activity: Dict[str, Any] = Field(default_factory=dict)
    top_items: List[Dict[str, Any]] = Field(default_factory=list)
    wealth_distribution: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

class ModernEconomySystem:
    """Sistema de Economia Virtual Avançado"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = SecureLogger("ModernEconomySystem")
        self.cache = SmartCache()
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.events = EventSystem()
        self.rate_limiter = RateLimiter()
        
        # Configurações
        self.config = {
            "currencies": {
                CurrencyType.COINS: {
                    "name": "Moedas",
                    "emoji": "🪙",
                    "daily_bonus": Decimal('100'),
                    "max_daily_bonus": Decimal('500'),
                    "transfer_fee_rate": Decimal('0.02'),  # 2%
                    "min_transfer": Decimal('10')
                },
                CurrencyType.GEMS: {
                    "name": "Gemas",
                    "emoji": "💎",
                    "daily_bonus": Decimal('5'),
                    "max_daily_bonus": Decimal('25'),
                    "transfer_fee_rate": Decimal('0.05'),  # 5%
                    "min_transfer": Decimal('1')
                },
                CurrencyType.TOKENS: {
                    "name": "Tokens",
                    "emoji": "🎫",
                    "daily_bonus": Decimal('10'),
                    "max_daily_bonus": Decimal('50'),
                    "transfer_fee_rate": Decimal('0.01'),  # 1%
                    "min_transfer": Decimal('5')
                },
                CurrencyType.CREDITS: {
                    "name": "Créditos",
                    "emoji": "⭐",
                    "daily_bonus": Decimal('50'),
                    "max_daily_bonus": Decimal('200'),
                    "transfer_fee_rate": Decimal('0.03'),  # 3%
                    "min_transfer": Decimal('25')
                },
                CurrencyType.EXPERIENCE: {
                    "name": "Experiência",
                    "emoji": "✨",
                    "daily_bonus": Decimal('200'),
                    "max_daily_bonus": Decimal('1000'),
                    "transfer_fee_rate": Decimal('0.10'),  # 10%
                    "min_transfer": Decimal('100')
                }
            },
            "transaction_limits": {
                "daily_transfer_limit": {
                    CurrencyType.COINS: Decimal('10000'),
                    CurrencyType.GEMS: Decimal('100'),
                    CurrencyType.TOKENS: Decimal('500'),
                    CurrencyType.CREDITS: Decimal('2000'),
                    CurrencyType.EXPERIENCE: Decimal('5000')
                },
                "max_transaction_amount": {
                    CurrencyType.COINS: Decimal('50000'),
                    CurrencyType.GEMS: Decimal('1000'),
                    CurrencyType.TOKENS: Decimal('5000'),
                    CurrencyType.CREDITS: Decimal('25000'),
                    CurrencyType.EXPERIENCE: Decimal('50000')
                }
            },
            "investment_options": {
                InvestmentType.SAVINGS: {
                    "min_amount": Decimal('1000'),
                    "interest_rate": Decimal('0.05'),  # 5% anual
                    "compound_frequency": "daily",
                    "withdrawal_penalty": Decimal('0.02')  # 2%
                },
                InvestmentType.STOCKS: {
                    "min_amount": Decimal('500'),
                    "volatility": Decimal('0.15'),  # 15% volatilidade
                    "dividend_rate": Decimal('0.03'),  # 3% dividendos
                    "dividend_frequency": "weekly"
                },
                InvestmentType.BONDS: {
                    "min_amount": Decimal('2000'),
                    "interest_rate": Decimal('0.08'),  # 8% anual
                    "maturity_days": 30,
                    "early_withdrawal_penalty": Decimal('0.10')  # 10%
                },
                InvestmentType.CRYPTO: {
                    "min_amount": Decimal('100'),
                    "volatility": Decimal('0.30'),  # 30% volatilidade
                    "staking_reward": Decimal('0.12'),  # 12% anual
                },
                InvestmentType.REAL_ESTATE: {
                    "min_amount": Decimal('10000'),
                    "appreciation_rate": Decimal('0.06'),  # 6% anual
                    "rental_yield": Decimal('0.04'),  # 4% anual
                    "maintenance_cost": Decimal('0.01')  # 1% anual
                }
            },
            "market_settings": {
                "order_expiry_days": 7,
                "max_orders_per_user": 10,
                "market_fee_rate": Decimal('0.05'),  # 5%
                "min_order_value": Decimal('10')
            }
        }
        
        # Dados em memória
        self.wallets: Dict[int, WalletModel] = {}
        self.transactions: Dict[str, TransactionModel] = {}
        self.shop_items: Dict[str, ShopItemModel] = {}
        self.user_inventories: Dict[int, List[UserInventoryItem]] = {}
        self.investments: Dict[str, InvestmentModel] = {}
        self.market_orders: Dict[str, MarketOrderModel] = {}
        self.economic_indicators = EconomicIndicators()
        
        # Dados de usuário
        self.user_data: Dict[int, Dict[str, Any]] = {}
        
        # Inicialização
        asyncio.create_task(self._initialize_system())
    
    async def _initialize_system(self):
        """Inicializar o sistema de economia"""
        try:
            await self._load_data()
            await self._create_default_shop_items()
            await self._start_background_tasks()
            
            self.logger.info("Sistema de Economia Virtual inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistema de economia: {e}")
    
    async def _load_data(self):
        """Carregar dados do sistema"""
        try:
            # Carregar carteiras
            wallets_data = await self._load_json_file("economy_wallets.json")
            for user_id_str, wallet_data in wallets_data.items():
                user_id = int(user_id_str)
                # Converter dados para modelo Pydantic
                wallet_data['user_id'] = user_id
                self.wallets[user_id] = WalletModel(**wallet_data)
            
            # Carregar transações
            transactions_data = await self._load_json_file("economy_transactions.json")
            for transaction_id, transaction_data in transactions_data.items():
                self.transactions[transaction_id] = TransactionModel(**transaction_data)
            
            # Carregar itens da loja
            shop_data = await self._load_json_file("economy_shop.json")
            for item_id, item_data in shop_data.items():
                self.shop_items[item_id] = ShopItemModel(**item_data)
            
            # Carregar inventários
            inventories_data = await self._load_json_file("economy_inventories.json")
            for user_id_str, items_data in inventories_data.items():
                user_id = int(user_id_str)
                self.user_inventories[user_id] = [
                    UserInventoryItem(**item_data) for item_data in items_data
                ]
            
            # Carregar investimentos
            investments_data = await self._load_json_file("economy_investments.json")
            for investment_id, investment_data in investments_data.items():
                self.investments[investment_id] = InvestmentModel(**investment_data)
            
            # Carregar ordens do mercado
            orders_data = await self._load_json_file("economy_market_orders.json")
            for order_id, order_data in orders_data.items():
                self.market_orders[order_id] = MarketOrderModel(**order_data)
            
            # Carregar indicadores econômicos
            indicators_data = await self._load_json_file("economy_indicators.json")
            if indicators_data:
                self.economic_indicators = EconomicIndicators(**indicators_data)
            
            # Carregar dados de usuário
            self.user_data = await self._load_json_file("economy_user_data.json")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados da economia: {e}")
    
    async def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Carregar arquivo JSON"""
        try:
            # Implementar carregamento de arquivo
            # Por enquanto retorna dicionário vazio
            return {}
        except Exception as e:
            self.logger.error(f"Erro ao carregar {filename}: {e}")
            return {}
    
    async def _save_data(self):
        """Salvar dados do sistema"""
        try:
            # Salvar carteiras
            wallets_data = {
                str(user_id): wallet.dict() for user_id, wallet in self.wallets.items()
            }
            await self._save_json_file("economy_wallets.json", wallets_data)
            
            # Salvar transações
            transactions_data = {
                transaction_id: transaction.dict() 
                for transaction_id, transaction in self.transactions.items()
            }
            await self._save_json_file("economy_transactions.json", transactions_data)
            
            # Salvar itens da loja
            shop_data = {
                item_id: item.dict() for item_id, item in self.shop_items.items()
            }
            await self._save_json_file("economy_shop.json", shop_data)
            
            # Salvar inventários
            inventories_data = {
                str(user_id): [item.dict() for item in items]
                for user_id, items in self.user_inventories.items()
            }
            await self._save_json_file("economy_inventories.json", inventories_data)
            
            # Salvar investimentos
            investments_data = {
                investment_id: investment.dict()
                for investment_id, investment in self.investments.items()
            }
            await self._save_json_file("economy_investments.json", investments_data)
            
            # Salvar ordens do mercado
            orders_data = {
                order_id: order.dict() for order_id, order in self.market_orders.items()
            }
            await self._save_json_file("economy_market_orders.json", orders_data)
            
            # Salvar indicadores econômicos
            await self._save_json_file("economy_indicators.json", self.economic_indicators.dict())
            
            # Salvar dados de usuário
            await self._save_json_file("economy_user_data.json", self.user_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados da economia: {e}")
    
    async def _save_json_file(self, filename: str, data: Dict[str, Any]):
        """Salvar arquivo JSON"""
        try:
            # Implementar salvamento de arquivo
            pass
        except Exception as e:
            self.logger.error(f"Erro ao salvar {filename}: {e}")
    
    async def _create_default_shop_items(self):
        """Criar itens padrão da loja"""
        default_items = [
            {
                "item_id": "daily_boost_2x",
                "name": "Boost Diário 2x",
                "description": "Dobra os ganhos de moedas por 24 horas",
                "category": ItemCategory.BOOST,
                "rarity": ItemRarity.COMMON,
                "price": {CurrencyType.COINS: Decimal('500')},
                "effects": {"daily_multiplier": 2.0},
                "duration": timedelta(hours=24),
                "emoji": "⚡"
            },
            {
                "item_id": "vip_badge",
                "name": "Emblema VIP",
                "description": "Emblema exclusivo VIP permanente",
                "category": ItemCategory.BADGE,
                "rarity": ItemRarity.EPIC,
                "price": {CurrencyType.GEMS: Decimal('50')},
                "max_per_user": 1,
                "emoji": "👑"
            },
            {
                "item_id": "lucky_charm",
                "name": "Amuleto da Sorte",
                "description": "Aumenta a chance de drops raros em 25%",
                "category": ItemCategory.UTILITY,
                "rarity": ItemRarity.RARE,
                "price": {CurrencyType.TOKENS: Decimal('100')},
                "effects": {"luck_bonus": 0.25},
                "duration": timedelta(days=7),
                "emoji": "🍀"
            },
            {
                "item_id": "premium_title",
                "name": "Título Premium",
                "description": "Título personalizado por 30 dias",
                "category": ItemCategory.TITLE,
                "rarity": ItemRarity.LEGENDARY,
                "price": {CurrencyType.GEMS: Decimal('100'), CurrencyType.COINS: Decimal('5000')},
                "duration": timedelta(days=30),
                "emoji": "🏆"
            },
            {
                "item_id": "mystery_box",
                "name": "Caixa Misteriosa",
                "description": "Contém um item aleatório de qualquer raridade",
                "category": ItemCategory.CONSUMABLE,
                "rarity": ItemRarity.UNCOMMON,
                "price": {CurrencyType.COINS: Decimal('200')},
                "effects": {"random_item": True},
                "emoji": "📦"
            }
        ]
        
        for item_data in default_items:
            if item_data["item_id"] not in self.shop_items:
                self.shop_items[item_data["item_id"]] = ShopItemModel(**item_data)
    
    async def _start_background_tasks(self):
        """Iniciar tarefas em segundo plano"""
        # Processar investimentos
        asyncio.create_task(self._process_investments_loop())
        
        # Limpar ordens expiradas
        asyncio.create_task(self._cleanup_expired_orders_loop())
        
        # Atualizar indicadores econômicos
        asyncio.create_task(self._update_economic_indicators_loop())
        
        # Salvar dados periodicamente
        asyncio.create_task(self._periodic_save_loop())
    
    # === MÉTODOS DE CARTEIRA ===
    
    async def get_wallet(self, user_id: int) -> WalletModel:
        """Obter carteira do usuário"""
        if user_id not in self.wallets:
            self.wallets[user_id] = WalletModel(user_id=user_id)
            
            # Inicializar saldos
            for currency in CurrencyType:
                self.wallets[user_id].balances[currency] = CurrencyBalance(currency=currency)
        
        return self.wallets[user_id]
    
    async def add_currency(self, user_id: int, currency: CurrencyType, 
                          amount: Decimal, reason: str = "") -> bool:
        """Adicionar moeda à carteira do usuário"""
        try:
            if amount <= 0:
                return False
            
            wallet = await self.get_wallet(user_id)
            
            if currency not in wallet.balances:
                wallet.balances[currency] = CurrencyBalance(currency=currency)
            
            wallet.balances[currency].amount += amount
            wallet.balances[currency].last_updated = datetime.now()
            wallet.last_activity = datetime.now()
            
            # Atualizar total ganho
            if currency not in wallet.total_earned:
                wallet.total_earned[currency] = Decimal('0')
            wallet.total_earned[currency] += amount
            
            # Registrar transação
            await self._create_transaction(
                to_user_id=user_id,
                transaction_type=TransactionType.REWARD,
                currency=currency,
                amount=amount,
                description=reason or "Adição de moeda"
            )
            
            # Emitir evento
            await self.events.emit("currency_added", {
                "user_id": user_id,
                "currency": currency.value,
                "amount": str(amount),
                "reason": reason
            })
            
            self.logger.info(f"Adicionado {amount} {currency.value} para usuário {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar moeda: {e}")
            return False
    
    async def remove_currency(self, user_id: int, currency: CurrencyType, 
                             amount: Decimal, reason: str = "") -> bool:
        """Remover moeda da carteira do usuário"""
        try:
            if amount <= 0:
                return False
            
            wallet = await self.get_wallet(user_id)
            
            if currency not in wallet.balances:
                return False
            
            if wallet.balances[currency].available_amount < amount:
                return False
            
            wallet.balances[currency].amount -= amount
            wallet.balances[currency].last_updated = datetime.now()
            wallet.last_activity = datetime.now()
            
            # Atualizar total gasto
            if currency not in wallet.total_spent:
                wallet.total_spent[currency] = Decimal('0')
            wallet.total_spent[currency] += amount
            
            # Registrar transação
            await self._create_transaction(
                from_user_id=user_id,
                transaction_type=TransactionType.PENALTY,
                currency=currency,
                amount=amount,
                description=reason or "Remoção de moeda"
            )
            
            # Emitir evento
            await self.events.emit("currency_removed", {
                "user_id": user_id,
                "currency": currency.value,
                "amount": str(amount),
                "reason": reason
            })
            
            self.logger.info(f"Removido {amount} {currency.value} do usuário {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover moeda: {e}")
            return False
    
    async def transfer_currency(self, from_user_id: int, to_user_id: int, 
                               currency: CurrencyType, amount: Decimal) -> Dict[str, Any]:
        """Transferir moeda entre usuários"""
        try:
            # Validações
            if from_user_id == to_user_id:
                return {"success": False, "error": "Não é possível transferir para si mesmo"}
            
            if amount <= 0:
                return {"success": False, "error": "Valor deve ser positivo"}
            
            currency_config = self.config["currencies"][currency]
            min_transfer = currency_config["min_transfer"]
            
            if amount < min_transfer:
                return {
                    "success": False, 
                    "error": f"Valor mínimo para transferência: {min_transfer} {currency_config['name']}"
                }
            
            # Verificar rate limit
            rate_limit_key = f"transfer_{from_user_id}_{currency.value}"
            if not await self.rate_limiter.check_rate_limit(rate_limit_key, 10, 3600):  # 10 por hora
                return {"success": False, "error": "Limite de transferências excedido"}
            
            # Verificar limite diário
            daily_limit = self.config["transaction_limits"]["daily_transfer_limit"][currency]
            daily_transferred = await self._get_daily_transferred(from_user_id, currency)
            
            if daily_transferred + amount > daily_limit:
                return {
                    "success": False, 
                    "error": f"Limite diário de transferência excedido ({daily_limit} {currency_config['name']})"
                }
            
            # Calcular taxa
            fee_rate = currency_config["transfer_fee_rate"]
            fee = amount * fee_rate
            total_deducted = amount + fee
            
            from_wallet = await self.get_wallet(from_user_id)
            
            if from_wallet.get_available_balance(currency) < total_deducted:
                return {"success": False, "error": "Saldo insuficiente"}
            
            # Executar transferência
            await self.remove_currency(from_user_id, currency, total_deducted, 
                                     f"Transferência para usuário {to_user_id}")
            await self.add_currency(to_user_id, currency, amount, 
                                  f"Transferência do usuário {from_user_id}")
            
            # Registrar transação de transferência
            transaction_id = await self._create_transaction(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                transaction_type=TransactionType.TRANSFER,
                currency=currency,
                amount=amount,
                fee=fee,
                description=f"Transferência de {from_user_id} para {to_user_id}"
            )
            
            # Emitir evento
            await self.events.emit("currency_transferred", {
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "currency": currency.value,
                "amount": str(amount),
                "fee": str(fee),
                "transaction_id": transaction_id
            })
            
            return {
                "success": True,
                "amount": amount,
                "fee": fee,
                "transaction_id": transaction_id
            }
            
        except Exception as e:
            self.logger.error(f"Erro na transferência: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def _get_daily_transferred(self, user_id: int, currency: CurrencyType) -> Decimal:
        """Obter total transferido hoje pelo usuário"""
        today = datetime.now().date()
        total = Decimal('0')
        
        for transaction in self.transactions.values():
            if (transaction.from_user_id == user_id and 
                transaction.transaction_type == TransactionType.TRANSFER and
                transaction.currency == currency and
                transaction.created_at.date() == today and
                transaction.status == TransactionStatus.COMPLETED):
                total += transaction.amount
        
        return total
    
    # === MÉTODOS DE TRANSAÇÕES ===
    
    async def _create_transaction(self, transaction_type: TransactionType, 
                                 currency: CurrencyType, amount: Decimal,
                                 from_user_id: Optional[int] = None,
                                 to_user_id: Optional[int] = None,
                                 fee: Decimal = Decimal('0'),
                                 description: str = "",
                                 metadata: Dict[str, Any] = None) -> str:
        """Criar nova transação"""
        transaction_id = f"tx_{int(datetime.now().timestamp() * 1000)}_{random.randint(1000, 9999)}"
        
        transaction = TransactionModel(
            transaction_id=transaction_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            transaction_type=transaction_type,
            currency=currency,
            amount=amount,
            fee=fee,
            description=description,
            metadata=metadata or {},
            status=TransactionStatus.COMPLETED
        )
        
        self.transactions[transaction_id] = transaction
        
        # Atualizar métricas
        await self.metrics.increment("economy.transactions.total")
        await self.metrics.increment(f"economy.transactions.{transaction_type.value}")
        
        return transaction_id
    
    async def get_transaction_history(self, user_id: int, limit: int = 50) -> List[TransactionModel]:
        """Obter histórico de transações do usuário"""
        user_transactions = []
        
        for transaction in self.transactions.values():
            if transaction.from_user_id == user_id or transaction.to_user_id == user_id:
                user_transactions.append(transaction)
        
        # Ordenar por data (mais recentes primeiro)
        user_transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_transactions[:limit]
    
    # === MÉTODOS DA LOJA ===
    
    async def get_shop_items(self, category: Optional[ItemCategory] = None, 
                            rarity: Optional[ItemRarity] = None) -> List[ShopItemModel]:
        """Obter itens da loja com filtros opcionais"""
        items = []
        
        for item in self.shop_items.values():
            if not item.is_active:
                continue
            
            if category and item.category != category:
                continue
            
            if rarity and item.rarity != rarity:
                continue
            
            items.append(item)
        
        # Ordenar por raridade e preço
        rarity_order = {
            ItemRarity.COMMON: 1,
            ItemRarity.UNCOMMON: 2,
            ItemRarity.RARE: 3,
            ItemRarity.EPIC: 4,
            ItemRarity.LEGENDARY: 5,
            ItemRarity.MYTHIC: 6
        }
        
        items.sort(key=lambda x: (rarity_order.get(x.rarity, 0), min(x.price.values())))
        
        return items
    
    async def purchase_item(self, user_id: int, item_id: str, 
                           currency: CurrencyType, quantity: int = 1) -> Dict[str, Any]:
        """Comprar item da loja"""
        try:
            # Verificar se o item existe
            if item_id not in self.shop_items:
                return {"success": False, "error": "Item não encontrado"}
            
            item = self.shop_items[item_id]
            
            if not item.is_active:
                return {"success": False, "error": "Item não está disponível"}
            
            # Verificar se a moeda é aceita
            if currency not in item.price:
                return {"success": False, "error": "Moeda não aceita para este item"}
            
            price_per_unit = item.price[currency]
            total_price = price_per_unit * quantity
            
            # Verificar saldo
            wallet = await self.get_wallet(user_id)
            if wallet.get_available_balance(currency) < total_price:
                return {"success": False, "error": "Saldo insuficiente"}
            
            # Verificar estoque
            if item.stock is not None and item.stock < quantity:
                return {"success": False, "error": f"Estoque insuficiente (disponível: {item.stock})"}
            
            # Verificar limite por usuário
            if item.max_per_user is not None:
                current_owned = await self._get_user_item_count(user_id, item_id)
                if current_owned + quantity > item.max_per_user:
                    return {
                        "success": False, 
                        "error": f"Limite por usuário excedido (máximo: {item.max_per_user})"
                    }
            
            # Verificar requisitos
            if not await self._check_item_requirements(user_id, item):
                return {"success": False, "error": "Requisitos não atendidos"}
            
            # Executar compra
            await self.remove_currency(user_id, currency, total_price, 
                                     f"Compra de {quantity}x {item.name}")
            
            # Adicionar ao inventário
            await self._add_to_inventory(user_id, item_id, quantity, item.duration)
            
            # Atualizar estoque
            if item.stock is not None:
                item.stock -= quantity
            
            # Registrar transação
            transaction_id = await self._create_transaction(
                from_user_id=user_id,
                transaction_type=TransactionType.PURCHASE,
                currency=currency,
                amount=total_price,
                description=f"Compra de {quantity}x {item.name}",
                metadata={"item_id": item_id, "quantity": quantity}
            )
            
            # Emitir evento
            await self.events.emit("item_purchased", {
                "user_id": user_id,
                "item_id": item_id,
                "quantity": quantity,
                "currency": currency.value,
                "total_price": str(total_price),
                "transaction_id": transaction_id
            })
            
            return {
                "success": True,
                "item_name": item.name,
                "quantity": quantity,
                "total_price": total_price,
                "transaction_id": transaction_id
            }
            
        except Exception as e:
            self.logger.error(f"Erro na compra: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def _get_user_item_count(self, user_id: int, item_id: str) -> int:
        """Obter quantidade de um item no inventário do usuário"""
        if user_id not in self.user_inventories:
            return 0
        
        total = 0
        for inventory_item in self.user_inventories[user_id]:
            if inventory_item.item_id == item_id and not inventory_item.is_expired:
                total += inventory_item.quantity
        
        return total
    
    async def _check_item_requirements(self, user_id: int, item: ShopItemModel) -> bool:
        """Verificar se o usuário atende aos requisitos do item"""
        if not item.requirements:
            return True
        
        # Implementar verificação de requisitos específicos
        # Por exemplo: nível mínimo, conquistas, etc.
        return True
    
    async def _add_to_inventory(self, user_id: int, item_id: str, 
                               quantity: int, duration: Optional[timedelta] = None):
        """Adicionar item ao inventário do usuário"""
        if user_id not in self.user_inventories:
            self.user_inventories[user_id] = []
        
        expires_at = None
        if duration:
            expires_at = datetime.now() + duration
        
        # Verificar se já existe o item no inventário
        existing_item = None
        for inventory_item in self.user_inventories[user_id]:
            if (inventory_item.item_id == item_id and 
                inventory_item.expires_at == expires_at and
                not inventory_item.is_expired):
                existing_item = inventory_item
                break
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = UserInventoryItem(
                item_id=item_id,
                quantity=quantity,
                expires_at=expires_at
            )
            self.user_inventories[user_id].append(new_item)
    
    async def get_user_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """Obter inventário do usuário com detalhes dos itens"""
        if user_id not in self.user_inventories:
            return []
        
        inventory_with_details = []
        
        for inventory_item in self.user_inventories[user_id]:
            if inventory_item.is_expired:
                continue
            
            if inventory_item.item_id in self.shop_items:
                shop_item = self.shop_items[inventory_item.item_id]
                inventory_with_details.append({
                    "item_id": inventory_item.item_id,
                    "name": shop_item.name,
                    "description": shop_item.description,
                    "category": shop_item.category.value,
                    "rarity": shop_item.rarity.value,
                    "emoji": shop_item.emoji,
                    "quantity": inventory_item.quantity,
                    "acquired_at": inventory_item.acquired_at,
                    "expires_at": inventory_item.expires_at,
                    "is_expired": inventory_item.is_expired
                })
        
        return inventory_with_details
    
    # === MÉTODOS DE INVESTIMENTOS ===
    
    async def create_investment(self, user_id: int, investment_type: InvestmentType,
                               currency: CurrencyType, amount: Decimal) -> Dict[str, Any]:
        """Criar novo investimento"""
        try:
            # Verificar configuração do investimento
            if investment_type not in self.config["investment_options"]:
                return {"success": False, "error": "Tipo de investimento não disponível"}
            
            investment_config = self.config["investment_options"][investment_type]
            min_amount = investment_config["min_amount"]
            
            if amount < min_amount:
                return {
                    "success": False, 
                    "error": f"Valor mínimo para investimento: {min_amount} {currency.value}"
                }
            
            # Verificar saldo
            wallet = await self.get_wallet(user_id)
            if wallet.get_available_balance(currency) < amount:
                return {"success": False, "error": "Saldo insuficiente"}
            
            # Remover valor da carteira
            await self.remove_currency(user_id, currency, amount, 
                                     f"Investimento em {investment_type.value}")
            
            # Criar investimento
            investment_id = f"inv_{int(datetime.now().timestamp() * 1000)}_{random.randint(1000, 9999)}"
            
            maturity_date = None
            if "maturity_days" in investment_config:
                maturity_date = datetime.now() + timedelta(days=investment_config["maturity_days"])
            
            investment = InvestmentModel(
                investment_id=investment_id,
                user_id=user_id,
                investment_type=investment_type,
                currency=currency,
                principal_amount=amount,
                current_value=amount,
                interest_rate=investment_config.get("interest_rate", Decimal('0')),
                maturity_date=maturity_date
            )
            
            self.investments[investment_id] = investment
            
            # Registrar transação
            transaction_id = await self._create_transaction(
                from_user_id=user_id,
                transaction_type=TransactionType.INVESTMENT,
                currency=currency,
                amount=amount,
                description=f"Investimento em {investment_type.value}",
                metadata={"investment_id": investment_id}
            )
            
            # Emitir evento
            await self.events.emit("investment_created", {
                "user_id": user_id,
                "investment_id": investment_id,
                "investment_type": investment_type.value,
                "currency": currency.value,
                "amount": str(amount)
            })
            
            return {
                "success": True,
                "investment_id": investment_id,
                "investment_type": investment_type.value,
                "amount": amount,
                "transaction_id": transaction_id
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao criar investimento: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def withdraw_investment(self, user_id: int, investment_id: str) -> Dict[str, Any]:
        """Retirar investimento"""
        try:
            if investment_id not in self.investments:
                return {"success": False, "error": "Investimento não encontrado"}
            
            investment = self.investments[investment_id]
            
            if investment.user_id != user_id:
                return {"success": False, "error": "Investimento não pertence ao usuário"}
            
            if not investment.is_active:
                return {"success": False, "error": "Investimento já foi retirado"}
            
            # Calcular valor atual
            await self._update_investment_value(investment)
            
            withdrawal_amount = investment.current_value
            penalty = Decimal('0')
            
            # Verificar penalidade por retirada antecipada
            investment_config = self.config["investment_options"][investment.investment_type]
            
            if (investment.maturity_date and 
                datetime.now() < investment.maturity_date and
                "early_withdrawal_penalty" in investment_config):
                penalty_rate = investment_config["early_withdrawal_penalty"]
                penalty = withdrawal_amount * penalty_rate
                withdrawal_amount -= penalty
            
            # Adicionar valor à carteira
            await self.add_currency(user_id, investment.currency, withdrawal_amount,
                                  f"Retirada de investimento {investment_id}")
            
            # Marcar investimento como inativo
            investment.is_active = False
            
            # Registrar transação
            transaction_id = await self._create_transaction(
                to_user_id=user_id,
                transaction_type=TransactionType.INVESTMENT,
                currency=investment.currency,
                amount=withdrawal_amount,
                fee=penalty,
                description=f"Retirada de investimento {investment_id}",
                metadata={"investment_id": investment_id, "penalty": str(penalty)}
            )
            
            return {
                "success": True,
                "withdrawal_amount": withdrawal_amount,
                "penalty": penalty,
                "profit_loss": investment.profit_loss,
                "transaction_id": transaction_id
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao retirar investimento: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def get_user_investments(self, user_id: int) -> List[Dict[str, Any]]:
        """Obter investimentos do usuário"""
        user_investments = []
        
        for investment in self.investments.values():
            if investment.user_id == user_id and investment.is_active:
                # Atualizar valor atual
                await self._update_investment_value(investment)
                
                user_investments.append({
                    "investment_id": investment.investment_id,
                    "investment_type": investment.investment_type.value,
                    "currency": investment.currency.value,
                    "principal_amount": investment.principal_amount,
                    "current_value": investment.current_value,
                    "profit_loss": investment.profit_loss,
                    "return_percentage": investment.return_percentage,
                    "interest_rate": investment.interest_rate,
                    "created_at": investment.created_at,
                    "maturity_date": investment.maturity_date
                })
        
        return user_investments
    
    async def _update_investment_value(self, investment: InvestmentModel):
        """Atualizar valor do investimento"""
        investment_config = self.config["investment_options"][investment.investment_type]
        
        if investment.investment_type == InvestmentType.SAVINGS:
            # Poupança com juros compostos
            days_elapsed = (datetime.now() - investment.created_at).days
            daily_rate = investment.interest_rate / 365
            investment.current_value = investment.principal_amount * (1 + daily_rate) ** days_elapsed
            
        elif investment.investment_type == InvestmentType.STOCKS:
            # Ações com volatilidade
            volatility = investment_config["volatility"]
            days_elapsed = (datetime.now() - investment.created_at).days
            
            # Simulação de movimento de preço com volatilidade
            random_factor = random.uniform(-volatility, volatility)
            time_factor = math.sqrt(days_elapsed / 365)  # Volatilidade aumenta com o tempo
            
            price_change = random_factor * time_factor
            investment.current_value = investment.principal_amount * (1 + price_change)
            
        elif investment.investment_type == InvestmentType.BONDS:
            # Títulos com juros fixos
            days_elapsed = (datetime.now() - investment.created_at).days
            daily_rate = investment.interest_rate / 365
            investment.current_value = investment.principal_amount * (1 + daily_rate * days_elapsed)
            
        elif investment.investment_type == InvestmentType.CRYPTO:
            # Criptomoedas com alta volatilidade
            volatility = investment_config["volatility"]
            hours_elapsed = (datetime.now() - investment.created_at).total_seconds() / 3600
            
            # Movimento mais frequente e volátil
            random_factor = random.uniform(-volatility, volatility)
            time_factor = math.sqrt(hours_elapsed / (24 * 365))  # Base horária
            
            price_change = random_factor * time_factor
            investment.current_value = investment.principal_amount * (1 + price_change)
            
        elif investment.investment_type == InvestmentType.REAL_ESTATE:
            # Imóveis com apreciação e custos
            days_elapsed = (datetime.now() - investment.created_at).days
            
            appreciation_rate = investment_config["appreciation_rate"]
            rental_yield = investment_config["rental_yield"]
            maintenance_cost = investment_config["maintenance_cost"]
            
            # Apreciação do imóvel
            daily_appreciation = appreciation_rate / 365
            appreciated_value = investment.principal_amount * (1 + daily_appreciation) ** days_elapsed
            
            # Renda de aluguel
            daily_rental = (investment.principal_amount * rental_yield) / 365
            rental_income = daily_rental * days_elapsed
            
            # Custos de manutenção
            daily_maintenance = (investment.principal_amount * maintenance_cost) / 365
            maintenance_costs = daily_maintenance * days_elapsed
            
            investment.current_value = appreciated_value + rental_income - maintenance_costs
        
        # Garantir que o valor não seja negativo
        investment.current_value = max(investment.current_value, Decimal('0'))
    
    # === MÉTODOS DO MERCADO P2P ===
    
    async def create_market_order(self, user_id: int, order_type: MarketOrderType,
                                 item_id: str, quantity: int, price_per_unit: Decimal,
                                 currency: CurrencyType) -> Dict[str, Any]:
        """Criar ordem no mercado P2P"""
        try:
            # Verificar se o item existe
            if item_id not in self.shop_items:
                return {"success": False, "error": "Item não encontrado"}
            
            # Verificar limites
            market_config = self.config["market_settings"]
            
            # Verificar número máximo de ordens por usuário
            user_orders = sum(1 for order in self.market_orders.values() 
                            if order.user_id == user_id and order.status == MarketOrderStatus.ACTIVE)
            
            if user_orders >= market_config["max_orders_per_user"]:
                return {
                    "success": False, 
                    "error": f"Máximo de {market_config['max_orders_per_user']} ordens ativas por usuário"
                }
            
            # Verificar valor mínimo da ordem
            total_value = price_per_unit * quantity
            if total_value < market_config["min_order_value"]:
                return {
                    "success": False, 
                    "error": f"Valor mínimo da ordem: {market_config['min_order_value']} {currency.value}"
                }
            
            if order_type == MarketOrderType.SELL:
                # Verificar se o usuário possui o item
                user_item_count = await self._get_user_item_count(user_id, item_id)
                if user_item_count < quantity:
                    return {"success": False, "error": "Quantidade insuficiente do item"}
                
                # Remover itens do inventário (bloquear)
                await self._remove_from_inventory(user_id, item_id, quantity)
                
            elif order_type == MarketOrderType.BUY:
                # Verificar se o usuário possui moedas suficientes
                wallet = await self.get_wallet(user_id)
                if wallet.get_available_balance(currency) < total_value:
                    return {"success": False, "error": "Saldo insuficiente"}
                
                # Bloquear moedas
                await self._lock_currency(user_id, currency, total_value)
            
            # Criar ordem
            order_id = f"order_{int(datetime.now().timestamp() * 1000)}_{random.randint(1000, 9999)}"
            expires_at = datetime.now() + timedelta(days=market_config["order_expiry_days"])
            
            order = MarketOrderModel(
                order_id=order_id,
                user_id=user_id,
                order_type=order_type,
                item_id=item_id,
                quantity=quantity,
                price_per_unit=price_per_unit,
                currency=currency,
                expires_at=expires_at
            )
            
            self.market_orders[order_id] = order
            
            # Tentar executar ordem imediatamente
            await self._try_execute_order(order_id)
            
            # Emitir evento
            await self.events.emit("market_order_created", {
                "user_id": user_id,
                "order_id": order_id,
                "order_type": order_type.value,
                "item_id": item_id,
                "quantity": quantity,
                "price_per_unit": str(price_per_unit),
                "currency": currency.value
            })
            
            return {
                "success": True,
                "order_id": order_id,
                "order_type": order_type.value,
                "expires_at": expires_at
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao criar ordem no mercado: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def _lock_currency(self, user_id: int, currency: CurrencyType, amount: Decimal):
        """Bloquear moeda na carteira"""
        wallet = await self.get_wallet(user_id)
        if currency not in wallet.balances:
            wallet.balances[currency] = CurrencyBalance(currency=currency)
        
        wallet.balances[currency].locked_amount += amount
    
    async def _unlock_currency(self, user_id: int, currency: CurrencyType, amount: Decimal):
        """Desbloquear moeda na carteira"""
        wallet = await self.get_wallet(user_id)
        if currency in wallet.balances:
            wallet.balances[currency].locked_amount = max(
                Decimal('0'), 
                wallet.balances[currency].locked_amount - amount
            )
    
    async def _remove_from_inventory(self, user_id: int, item_id: str, quantity: int):
        """Remover item do inventário"""
        if user_id not in self.user_inventories:
            return
        
        remaining_to_remove = quantity
        
        for inventory_item in self.user_inventories[user_id]:
            if inventory_item.item_id == item_id and not inventory_item.is_expired:
                if inventory_item.quantity <= remaining_to_remove:
                    remaining_to_remove -= inventory_item.quantity
                    inventory_item.quantity = 0
                else:
                    inventory_item.quantity -= remaining_to_remove
                    remaining_to_remove = 0
                
                if remaining_to_remove == 0:
                    break
        
        # Remover itens com quantidade 0
        self.user_inventories[user_id] = [
            item for item in self.user_inventories[user_id] if item.quantity > 0
        ]
    
    async def _try_execute_order(self, order_id: str):
        """Tentar executar ordem no mercado"""
        if order_id not in self.market_orders:
            return
        
        order = self.market_orders[order_id]
        
        if order.status != MarketOrderStatus.ACTIVE:
            return
        
        # Buscar ordens compatíveis
        compatible_orders = []
        
        for other_order_id, other_order in self.market_orders.items():
            if (other_order_id != order_id and
                other_order.status == MarketOrderStatus.ACTIVE and
                other_order.item_id == order.item_id and
                other_order.currency == order.currency and
                other_order.order_type != order.order_type):
                
                # Verificar compatibilidade de preço
                if order.order_type == MarketOrderType.BUY:
                    if order.price_per_unit >= other_order.price_per_unit:
                        compatible_orders.append(other_order)
                else:  # SELL
                    if order.price_per_unit <= other_order.price_per_unit:
                        compatible_orders.append(other_order)
        
        # Ordenar por melhor preço
        if order.order_type == MarketOrderType.BUY:
            compatible_orders.sort(key=lambda x: x.price_per_unit)  # Menor preço primeiro
        else:
            compatible_orders.sort(key=lambda x: x.price_per_unit, reverse=True)  # Maior preço primeiro
        
        # Executar trades
        for compatible_order in compatible_orders:
            if order.remaining_quantity == 0:
                break
            
            trade_quantity = min(order.remaining_quantity, compatible_order.remaining_quantity)
            trade_price = compatible_order.price_per_unit  # Preço do maker
            
            await self._execute_trade(order, compatible_order, trade_quantity, trade_price)
    
    async def _execute_trade(self, order1: MarketOrderModel, order2: MarketOrderModel,
                            quantity: int, price_per_unit: Decimal):
        """Executar trade entre duas ordens"""
        try:
            total_value = price_per_unit * quantity
            market_fee = total_value * self.config["market_settings"]["market_fee_rate"]
            
            buyer_order = order1 if order1.order_type == MarketOrderType.BUY else order2
            seller_order = order2 if order2.order_type == MarketOrderType.SELL else order1
            
            # Transferir item do vendedor para o comprador
            await self._add_to_inventory(buyer_order.user_id, order1.item_id, quantity)
            
            # Transferir moedas do comprador para o vendedor (menos taxa)
            seller_receives = total_value - market_fee
            
            await self._unlock_currency(buyer_order.user_id, order1.currency, total_value)
            await self.remove_currency(buyer_order.user_id, order1.currency, total_value, 
                                     f"Compra no mercado P2P - {quantity}x {order1.item_id}")
            
            await self.add_currency(seller_order.user_id, order1.currency, seller_receives,
                                  f"Venda no mercado P2P - {quantity}x {order1.item_id}")
            
            # Atualizar ordens
            order1.filled_quantity += quantity
            order2.filled_quantity += quantity
            
            # Verificar se as ordens foram completamente preenchidas
            if order1.remaining_quantity == 0:
                order1.status = MarketOrderStatus.FILLED
            
            if order2.remaining_quantity == 0:
                order2.status = MarketOrderStatus.FILLED
            
            # Registrar transações
            await self._create_transaction(
                from_user_id=buyer_order.user_id,
                to_user_id=seller_order.user_id,
                transaction_type=TransactionType.TRADE,
                currency=order1.currency,
                amount=seller_receives,
                fee=market_fee,
                description=f"Trade P2P - {quantity}x {order1.item_id}",
                metadata={
                    "buyer_order_id": buyer_order.order_id,
                    "seller_order_id": seller_order.order_id,
                    "quantity": quantity,
                    "price_per_unit": str(price_per_unit)
                }
            )
            
            # Emitir evento
            await self.events.emit("trade_executed", {
                "buyer_id": buyer_order.user_id,
                "seller_id": seller_order.user_id,
                "item_id": order1.item_id,
                "quantity": quantity,
                "price_per_unit": str(price_per_unit),
                "total_value": str(total_value),
                "market_fee": str(market_fee)
            })
            
            self.logger.info(f"Trade executado: {quantity}x {order1.item_id} por {total_value} {order1.currency.value}")
            
        except Exception as e:
            self.logger.error(f"Erro ao executar trade: {e}")
    
    async def cancel_market_order(self, user_id: int, order_id: str) -> Dict[str, Any]:
        """Cancelar ordem no mercado"""
        try:
            if order_id not in self.market_orders:
                return {"success": False, "error": "Ordem não encontrada"}
            
            order = self.market_orders[order_id]
            
            if order.user_id != user_id:
                return {"success": False, "error": "Ordem não pertence ao usuário"}
            
            if order.status != MarketOrderStatus.ACTIVE:
                return {"success": False, "error": "Ordem não está ativa"}
            
            # Devolver recursos bloqueados
            if order.order_type == MarketOrderType.BUY:
                # Desbloquear moedas
                remaining_value = order.price_per_unit * order.remaining_quantity
                await self._unlock_currency(user_id, order.currency, remaining_value)
            else:
                # Devolver itens ao inventário
                await self._add_to_inventory(user_id, order.item_id, order.remaining_quantity)
            
            # Marcar ordem como cancelada
            order.status = MarketOrderStatus.CANCELLED
            
            return {"success": True, "message": "Ordem cancelada com sucesso"}
            
        except Exception as e:
            self.logger.error(f"Erro ao cancelar ordem: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def get_market_orders(self, item_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Obter ordens ativas no mercado"""
        buy_orders = []
        sell_orders = []
        
        for order in self.market_orders.values():
            if order.status != MarketOrderStatus.ACTIVE:
                continue
            
            if order.is_expired:
                continue
            
            if item_id and order.item_id != item_id:
                continue
            
            order_data = {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "item_id": order.item_id,
                "quantity": order.remaining_quantity,
                "price_per_unit": order.price_per_unit,
                "total_price": order.price_per_unit * order.remaining_quantity,
                "currency": order.currency.value,
                "created_at": order.created_at,
                "expires_at": order.expires_at
            }
            
            if order.order_type == MarketOrderType.BUY:
                buy_orders.append(order_data)
            else:
                sell_orders.append(order_data)
        
        # Ordenar ordens
        buy_orders.sort(key=lambda x: x["price_per_unit"], reverse=True)  # Maior preço primeiro
        sell_orders.sort(key=lambda x: x["price_per_unit"])  # Menor preço primeiro
        
        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders
        }
    
    # === MÉTODOS DE ANÁLISE E ESTATÍSTICAS ===
    
    async def get_user_economy_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas econômicas do usuário"""
        wallet = await self.get_wallet(user_id)
        
        # Calcular valor total da carteira
        total_wallet_value = sum(balance.amount for balance in wallet.balances.values())
        
        # Calcular valor dos investimentos
        investments = await self.get_user_investments(user_id)
        total_investment_value = sum(Decimal(inv["current_value"]) for inv in investments)
        
        # Calcular valor do inventário (estimativa)
        inventory = await self.get_user_inventory(user_id)
        inventory_value = Decimal('0')
        for item in inventory:
            if item["item_id"] in self.shop_items:
                shop_item = self.shop_items[item["item_id"]]
                if shop_item.price:
                    min_price = min(shop_item.price.values())
                    inventory_value += min_price * item["quantity"]
        
        # Estatísticas de transações
        transactions = await self.get_transaction_history(user_id, 1000)
        
        total_earned = {currency: Decimal('0') for currency in CurrencyType}
        total_spent = {currency: Decimal('0') for currency in CurrencyType}
        
        for transaction in transactions:
            if transaction.to_user_id == user_id:
                total_earned[transaction.currency] += transaction.amount
            elif transaction.from_user_id == user_id:
                total_spent[transaction.currency] += transaction.amount
        
        return {
            "user_id": user_id,
            "wallet_balances": {currency.value: str(balance.amount) for currency, balance in wallet.balances.items()},
            "total_wallet_value": str(total_wallet_value),
            "total_investment_value": str(total_investment_value),
            "inventory_value": str(inventory_value),
            "net_worth": str(total_wallet_value + total_investment_value + inventory_value),
            "total_earned": {currency.value: str(amount) for currency, amount in total_earned.items()},
            "total_spent": {currency.value: str(amount) for currency, amount in total_spent.items()},
            "total_transactions": len(transactions),
            "active_investments": len(investments),
            "inventory_items": len(inventory)
        }
    
    async def get_economy_leaderboard(self, category: str = "net_worth", limit: int = 10) -> List[Dict[str, Any]]:
        """Obter ranking econômico"""
        leaderboard = []
        
        for user_id in self.wallets.keys():
            stats = await self.get_user_economy_stats(user_id)
            
            if category == "net_worth":
                value = Decimal(stats["net_worth"])
            elif category in stats["wallet_balances"]:
                value = Decimal(stats["wallet_balances"][category])
            else:
                continue
            
            leaderboard.append({
                "user_id": user_id,
                "value": value,
                "stats": stats
            })
        
        # Ordenar por valor
        leaderboard.sort(key=lambda x: x["value"], reverse=True)
        
        return leaderboard[:limit]
    
    async def get_market_analytics(self) -> Dict[str, Any]:
        """Obter análises do mercado"""
        # Análise de ordens ativas
        active_orders = [order for order in self.market_orders.values() 
                        if order.status == MarketOrderStatus.ACTIVE]
        
        # Análise por item
        item_analytics = {}
        for order in active_orders:
            if order.item_id not in item_analytics:
                item_analytics[order.item_id] = {
                    "buy_orders": 0,
                    "sell_orders": 0,
                    "total_buy_volume": Decimal('0'),
                    "total_sell_volume": Decimal('0'),
                    "avg_buy_price": Decimal('0'),
                    "avg_sell_price": Decimal('0'),
                    "highest_buy": Decimal('0'),
                    "lowest_sell": Decimal('999999')
                }
            
            analytics = item_analytics[order.item_id]
            
            if order.order_type == MarketOrderType.BUY:
                analytics["buy_orders"] += 1
                analytics["total_buy_volume"] += order.remaining_quantity
                analytics["highest_buy"] = max(analytics["highest_buy"], order.price_per_unit)
            else:
                analytics["sell_orders"] += 1
                analytics["total_sell_volume"] += order.remaining_quantity
                analytics["lowest_sell"] = min(analytics["lowest_sell"], order.price_per_unit)
        
        # Calcular preços médios
        for item_id, analytics in item_analytics.items():
            buy_orders = [o for o in active_orders if o.item_id == item_id and o.order_type == MarketOrderType.BUY]
            sell_orders = [o for o in active_orders if o.item_id == item_id and o.order_type == MarketOrderType.SELL]
            
            if buy_orders:
                analytics["avg_buy_price"] = sum(o.price_per_unit for o in buy_orders) / len(buy_orders)
            
            if sell_orders:
                analytics["avg_sell_price"] = sum(o.price_per_unit for o in sell_orders) / len(sell_orders)
        
        # Análise de transações recentes
        recent_transactions = [t for t in self.transactions.values() 
                             if t.transaction_type == TransactionType.TRADE and
                             (datetime.now() - t.created_at).days <= 7]
        
        return {
            "active_orders_count": len(active_orders),
            "total_buy_orders": sum(1 for o in active_orders if o.order_type == MarketOrderType.BUY),
            "total_sell_orders": sum(1 for o in active_orders if o.order_type == MarketOrderType.SELL),
            "item_analytics": {item_id: {k: str(v) if isinstance(v, Decimal) else v 
                                        for k, v in analytics.items()}
                              for item_id, analytics in item_analytics.items()},
            "recent_trades_count": len(recent_transactions),
            "market_activity": "high" if len(active_orders) > 50 else "medium" if len(active_orders) > 20 else "low"
        }
    
    # === TAREFAS EM SEGUNDO PLANO ===
    
    async def _process_investments_loop(self):
        """Loop para processar investimentos"""
        while True:
            try:
                await asyncio.sleep(3600)  # A cada hora
                
                for investment in self.investments.values():
                    if investment.is_active:
                        await self._update_investment_value(investment)
                        
                        # Processar dividendos se aplicável
                        await self._process_investment_dividends(investment)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de investimentos: {e}")
    
    async def _process_investment_dividends(self, investment: InvestmentModel):
        """Processar dividendos de investimentos"""
        investment_config = self.config["investment_options"][investment.investment_type]
        
        if "dividend_rate" not in investment_config:
            return
        
        dividend_frequency = investment_config.get("dividend_frequency", "monthly")
        
        # Verificar se é hora de pagar dividendos
        now = datetime.now()
        should_pay = False
        
        if dividend_frequency == "daily":
            should_pay = (investment.last_dividend is None or 
                         (now - investment.last_dividend).days >= 1)
        elif dividend_frequency == "weekly":
            should_pay = (investment.last_dividend is None or 
                         (now - investment.last_dividend).days >= 7)
        elif dividend_frequency == "monthly":
            should_pay = (investment.last_dividend is None or 
                         (now - investment.last_dividend).days >= 30)
        
        if should_pay:
            dividend_rate = investment_config["dividend_rate"]
            dividend_amount = investment.principal_amount * dividend_rate
            
            if dividend_frequency == "daily":
                dividend_amount /= 365
            elif dividend_frequency == "weekly":
                dividend_amount /= 52
            elif dividend_frequency == "monthly":
                dividend_amount /= 12
            
            # Pagar dividendo
            await self.add_currency(investment.user_id, investment.currency, dividend_amount,
                                  f"Dividendo de investimento {investment.investment_id}")
            
            investment.last_dividend = now
            
            # Registrar transação
            await self._create_transaction(
                to_user_id=investment.user_id,
                transaction_type=TransactionType.DIVIDEND,
                currency=investment.currency,
                amount=dividend_amount,
                description=f"Dividendo de {investment.investment_type.value}",
                metadata={"investment_id": investment.investment_id}
            )
    
    async def _cleanup_expired_orders_loop(self):
        """Loop para limpar ordens expiradas"""
        while True:
            try:
                await asyncio.sleep(1800)  # A cada 30 minutos
                
                expired_orders = []
                
                for order_id, order in self.market_orders.items():
                    if order.status == MarketOrderStatus.ACTIVE and order.is_expired:
                        expired_orders.append(order_id)
                
                for order_id in expired_orders:
                    order = self.market_orders[order_id]
                    
                    # Devolver recursos bloqueados
                    if order.order_type == MarketOrderType.BUY:
                        remaining_value = order.price_per_unit * order.remaining_quantity
                        await self._unlock_currency(order.user_id, order.currency, remaining_value)
                    else:
                        await self._add_to_inventory(order.user_id, order.item_id, order.remaining_quantity)
                    
                    # Marcar como expirada
                    order.status = MarketOrderStatus.EXPIRED
                    
                    self.logger.info(f"Ordem {order_id} expirada e recursos devolvidos")
                
            except Exception as e:
                self.logger.error(f"Erro na limpeza de ordens: {e}")
    
    async def _update_economic_indicators_loop(self):
        """Loop para atualizar indicadores econômicos"""
        while True:
            try:
                await asyncio.sleep(7200)  # A cada 2 horas
                
                # Calcular oferta total de moedas
                total_supply = {currency: Decimal('0') for currency in CurrencyType}
                
                for wallet in self.wallets.values():
                    for currency, balance in wallet.balances.items():
                        total_supply[currency] += balance.amount
                
                self.economic_indicators.total_currency_supply = total_supply
                
                # Calcular transações diárias
                today = datetime.now().date()
                daily_transactions = sum(1 for t in self.transactions.values() 
                                       if t.created_at.date() == today)
                
                self.economic_indicators.daily_transactions = daily_transactions
                
                # Calcular volume diário
                daily_volume = {currency: Decimal('0') for currency in CurrencyType}
                
                for transaction in self.transactions.values():
                    if transaction.created_at.date() == today:
                        daily_volume[transaction.currency] += transaction.amount
                
                self.economic_indicators.daily_volume = daily_volume
                
                # Atualizar timestamp
                self.economic_indicators.last_updated = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Erro na atualização de indicadores: {e}")
    
    async def _periodic_save_loop(self):
        """Loop para salvar dados periodicamente"""
        while True:
            try:
                await asyncio.sleep(300)  # A cada 5 minutos
                await self._save_data()
                
            except Exception as e:
                self.logger.error(f"Erro no salvamento periódico: {e}")
    
    # === MÉTODOS DE BÔNUS E RECOMPENSAS ===
    
    async def claim_daily_bonus(self, user_id: int) -> Dict[str, Any]:
        """Reivindicar bônus diário"""
        try:
            # Verificar se já reivindicou hoje
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            
            user_data = self.user_data[user_id]
            today = datetime.now().date().isoformat()
            
            if user_data.get("last_daily_bonus") == today:
                return {"success": False, "error": "Bônus diário já reivindicado hoje"}
            
            # Calcular streak
            yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
            current_streak = user_data.get("daily_streak", 0)
            
            if user_data.get("last_daily_bonus") == yesterday:
                current_streak += 1
            else:
                current_streak = 1
            
            # Calcular bônus com base no streak
            base_bonuses = {
                CurrencyType.COINS: self.config["currencies"][CurrencyType.COINS]["daily_bonus"],
                CurrencyType.GEMS: self.config["currencies"][CurrencyType.GEMS]["daily_bonus"],
                CurrencyType.TOKENS: self.config["currencies"][CurrencyType.TOKENS]["daily_bonus"],
                CurrencyType.CREDITS: self.config["currencies"][CurrencyType.CREDITS]["daily_bonus"],
                CurrencyType.EXPERIENCE: self.config["currencies"][CurrencyType.EXPERIENCE]["daily_bonus"]
            }
            
            # Multiplicador de streak (máximo 2x)
            streak_multiplier = min(1 + (current_streak - 1) * 0.1, 2.0)
            
            bonuses_received = {}
            
            for currency, base_amount in base_bonuses.items():
                bonus_amount = base_amount * Decimal(str(streak_multiplier))
                max_bonus = self.config["currencies"][currency]["max_daily_bonus"]
                bonus_amount = min(bonus_amount, max_bonus)
                
                await self.add_currency(user_id, currency, bonus_amount, 
                                      f"Bônus diário (streak {current_streak}x)")
                
                bonuses_received[currency.value] = str(bonus_amount)
            
            # Atualizar dados do usuário
            user_data["last_daily_bonus"] = today
            user_data["daily_streak"] = current_streak
            
            return {
                "success": True,
                "bonuses": bonuses_received,
                "streak": current_streak,
                "streak_multiplier": streak_multiplier
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao reivindicar bônus diário: {e}")
            return {"success": False, "error": "Erro interno do sistema"}
    
    async def get_daily_bonus_info(self, user_id: int) -> Dict[str, Any]:
        """Obter informações sobre o bônus diário"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        
        user_data = self.user_data[user_id]
        today = datetime.now().date().isoformat()
        
        can_claim = user_data.get("last_daily_bonus") != today
        current_streak = user_data.get("daily_streak", 0)
        
        # Calcular próximo bônus
        next_streak = current_streak + 1 if can_claim else current_streak
        streak_multiplier = min(1 + (next_streak - 1) * 0.1, 2.0)
        
        next_bonuses = {}
        for currency in CurrencyType:
            base_amount = self.config["currencies"][currency]["daily_bonus"]
            bonus_amount = base_amount * Decimal(str(streak_multiplier))
            max_bonus = self.config["currencies"][currency]["max_daily_bonus"]
            bonus_amount = min(bonus_amount, max_bonus)
            next_bonuses[currency.value] = str(bonus_amount)
        
        return {
            "can_claim": can_claim,
            "current_streak": current_streak,
            "next_streak": next_streak,
            "streak_multiplier": streak_multiplier,
            "next_bonuses": next_bonuses,
            "last_claimed": user_data.get("last_daily_bonus")
        }
    
    # === MÉTODOS DE UTILIDADE ===
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Verificar saúde do sistema de economia"""
        try:
            return {
                "status": "healthy",
                "total_wallets": len(self.wallets),
                "total_transactions": len(self.transactions),
                "total_shop_items": len(self.shop_items),
                "active_investments": sum(1 for inv in self.investments.values() if inv.is_active),
                "active_market_orders": sum(1 for order in self.market_orders.values() 
                                           if order.status == MarketOrderStatus.ACTIVE),
                "cache_size": len(self.cache._cache) if hasattr(self.cache, '_cache') else 0,
                "last_save": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Erro ao verificar saúde do sistema: {e}")
            return {"status": "error", "error": str(e)}
    
    async def shutdown(self):
        """Desligar o sistema graciosamente"""
        try:
            self.logger.info("Iniciando desligamento do sistema de economia...")
            
            # Salvar todos os dados
            await self._save_data()
            
            # Limpar cache
            if hasattr(self.cache, 'clear'):
                await self.cache.clear()
            
            self.logger.info("Sistema de economia desligado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro durante desligamento: {e}")