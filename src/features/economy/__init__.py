"""Módulo de Sistema de Economia Virtual Avançado

Sistema completo de economia virtual com múltiplas moedas, transações seguras,
loja virtual, investimentos, mercado P2P e análise econômica.
"""

from .modern_system import (
    ModernEconomySystem as EconomySystem,
    CurrencyType,
    TransactionType,
    TransactionStatus,
    ItemRarity,
    ItemCategory,
    InvestmentType,
    MarketOrderType as OrderType,
    MarketOrderStatus as OrderStatus,
    WalletModel as Wallet,
    TransactionModel as Transaction,
    ShopItemModel as ShopItem,
    UserInventoryItem as InventoryItem,
    InvestmentModel as Investment,
    MarketOrderModel as MarketOrder,
    EconomicIndicators
)

__all__ = [
    'EconomySystem',
    'CurrencyType',
    'TransactionType', 
    'TransactionStatus',
    'ItemRarity',
    'ItemCategory',
    'InvestmentType',
    'OrderType',
    'OrderStatus',
    'Wallet',
    'Transaction',
    'ShopItem',
    'InventoryItem',
    'Investment',
    'MarketOrder',
    'EconomicIndicators'
]

__version__ = '1.0.0'
__author__ = 'Bot Discord Team'
__description__ = 'Sistema de Economia Virtual Avançado'