#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Economia Virtual

Script para testar as funcionalidades do sistema de economia.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from features.economy import EconomySystem, CurrencyType, ItemCategory, InvestmentType

async def test_economy_system():
    """Testar funcionalidades do sistema de economia"""
    print("🚀 Iniciando teste do Sistema de Economia Virtual...")
    
    # Criar mock do bot para teste
    class MockBot:
        def __init__(self):
            self.user = type('User', (), {'id': 123456789, 'name': 'TestBot'})()
    
    # Inicializar sistema
    mock_bot = MockBot()
    economy = EconomySystem(mock_bot)
    await economy._initialize_system()
    
    print("✅ Sistema de economia inicializado com sucesso!")
    
    # Testar usuário de exemplo
    test_user_id = "123456789"
    
    # 1. Testar carteira
    print("\n💳 Testando sistema de carteira...")
    wallet = await economy.get_wallet(test_user_id)
    print(f"Carteira inicial: {wallet.balances}")
    
    # 2. Adicionar moedas
    print("\n💰 Adicionando moedas...")
    await economy.add_currency(test_user_id, CurrencyType.COINS, 1000)
    await economy.add_currency(test_user_id, CurrencyType.GEMS, 5000)
    
    wallet = await economy.get_wallet(test_user_id)
    print(f"Carteira após adicionar moedas: {wallet.balances}")
    
    # 3. Testar loja
    print("\n🛒 Testando sistema de loja...")
    shop_items = await economy.get_shop_items()
    print(f"Itens da loja: {len(shop_items[:5])} itens disponíveis (mostrando primeiros 5)")
    
    for item in shop_items[:3]:
        price_str = ", ".join([f"{amount} {currency.value}" for currency, amount in item.price.items()])
        print(f"  - {item.name}: {price_str}")
    
    # 4. Testar compra
    if shop_items:
        print("\n🛍️ Testando compra de item...")
        first_item = shop_items[0]
        success = await economy.purchase_item(test_user_id, first_item.item_id, 1)
        print(f"Compra do item '{first_item.name}': {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # 5. Testar inventário
    print("\n📦 Testando inventário...")
    inventory = await economy.get_user_inventory(test_user_id)
    print(f"Inventário: {len(inventory)} tipos de itens")
    
    for item in inventory[:3]:
        print(f"  - {item.name}: {item.quantity}x")
    
    # 6. Testar investimentos
    print("\n📈 Testando sistema de investimentos...")
    investment_success = await economy.create_investment(
        test_user_id,
        InvestmentType.SAVINGS,
        CurrencyType.COINS,
        100
    )
    print(f"Investimento em poupança: {'✅ Sucesso' if investment_success else '❌ Falhou'}")
    
    # 7. Testar bônus diário
    print("\n🎁 Testando bônus diário...")
    bonus_result = await economy.claim_daily_bonus(test_user_id)
    print(f"Bônus diário: {'✅ Coletado' if bonus_result['success'] else '❌ Falhou'}")
    if bonus_result['success']:
         print(f"  Streak: {bonus_result['streak']}x")
         print(f"  Bônus recebidos: {bonus_result['bonuses']}")
    
    # 8. Testar estatísticas
    print("\n📊 Testando estatísticas econômicas...")
    stats = await economy.get_user_economy_stats(test_user_id)
    print(f"Patrimônio líquido: {stats['net_worth']}")
    print(f"Valor da carteira: {stats['total_wallet_value']}")
    print(f"Transações realizadas: {stats['total_transactions']}")
    print(f"Valor do inventário: {stats['inventory_value']}")
    print(f"Valor dos investimentos: {stats['total_investment_value']}")
    
    # 9. Testar saúde do sistema
    print("\n🏥 Verificando saúde do sistema...")
    health = await economy.get_system_health()
    print(f"Status do sistema: {'✅ Saudável' if health['status'] == 'healthy' else '❌ Com problemas'}")
    print(f"Total de carteiras: {health['total_wallets']}")
    print(f"Total de transações: {health['total_transactions']}")
    print(f"Itens da loja: {health['total_shop_items']}")
    
    # Finalizar
    print("\n🔄 Finalizando sistema...")
    await economy.shutdown()
    print("✅ Teste concluído com sucesso!")

if __name__ == "__main__":
    try:
        asyncio.run(test_economy_system())
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()