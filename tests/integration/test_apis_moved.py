#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste para APIs do Hawk Esports Bot
Testa conectividade e configuração das APIs PUBG e Medal
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

class APITester:
    def __init__(self):
        self.pubg_api_key = os.getenv('PUBG_API_KEY')
        self.medal_api_key = os.getenv('MEDAL_API_KEY')
        self.results = {
            'pubg': {'configured': False, 'working': False, 'error': None},
            'medal': {'configured': False, 'working': False, 'error': None}
        }
    
    def print_header(self):
        print("\n" + "="*60)
        print("🔧 TESTE DE APIS - HAWK ESPORTS BOT")
        print("="*60)
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60 + "\n")
    
    def check_configuration(self):
        print("📋 VERIFICANDO CONFIGURAÇÃO...\n")
        
        # PUBG API
        if self.pubg_api_key and self.pubg_api_key.strip():
            self.results['pubg']['configured'] = True
            print("✅ PUBG_API_KEY: Configurada")
            print(f"   Chave: {self.pubg_api_key[:8]}...{self.pubg_api_key[-4:]}")
        else:
            print("❌ PUBG_API_KEY: Não configurada ou vazia")
        
        # Medal API
        if self.medal_api_key and self.medal_api_key.strip():
            self.results['medal']['configured'] = True
            print("✅ MEDAL_API_KEY: Configurada")
            print(f"   Chave: {self.medal_api_key[:8]}...{self.medal_api_key[-4:]}")
        else:
            print("❌ MEDAL_API_KEY: Não configurada ou vazia")
        
        print()
    
    async def test_pubg_api(self):
        print("🎮 TESTANDO PUBG API...\n")
        
        if not self.results['pubg']['configured']:
            print("⏭️  Pulando teste - API não configurada\n")
            return
        
        try:
            # Teste 1: Verificar se a chave é válida
            print("1️⃣ Testando autenticação...")
            
            headers = {
                'Authorization': f'Bearer {self.pubg_api_key}',
                'Accept': 'application/vnd.api+json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Testar com endpoint de temporadas (mais leve)
                url = "https://api.pubg.com/shards/steam/seasons"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        print("   ✅ Autenticação bem-sucedida")
                        data = await response.json()
                        seasons = data.get('data', [])
                        print(f"   📊 {len(seasons)} temporadas disponíveis")
                        
                        # Teste 2: Buscar jogador de teste
                        print("\n2️⃣ Testando busca de jogador...")
                        
                        test_url = "https://api.pubg.com/shards/steam/players"
                        test_params = {'filter[playerNames]': 'shroud'}  # Jogador conhecido
                        
                        async with session.get(test_url, params=test_params, headers=headers) as test_response:
                            if test_response.status == 200:
                                test_data = await test_response.json()
                                players = test_data.get('data', [])
                                if players:
                                    print("   ✅ Busca de jogador funcionando")
                                    print(f"   👤 Jogador encontrado: {players[0]['attributes']['name']}")
                                    self.results['pubg']['working'] = True
                                else:
                                    print("   ⚠️  Nenhum jogador encontrado (normal para jogador de teste)")
                                    self.results['pubg']['working'] = True
                            elif test_response.status == 404:
                                print("   ✅ API funcionando (jogador não encontrado é normal)")
                                self.results['pubg']['working'] = True
                            else:
                                print(f"   ❌ Erro na busca: {test_response.status}")
                                error_text = await test_response.text()
                                print(f"   📝 Detalhes: {error_text[:200]}...")
                    
                    elif response.status == 401:
                        print("   ❌ Chave de API inválida")
                        self.results['pubg']['error'] = "Chave inválida"
                    elif response.status == 429:
                        print("   ⚠️  Limite de requisições excedido")
                        self.results['pubg']['error'] = "Rate limit"
                    else:
                        print(f"   ❌ Erro HTTP: {response.status}")
                        error_text = await response.text()
                        self.results['pubg']['error'] = f"HTTP {response.status}"
                        print(f"   📝 Detalhes: {error_text[:200]}...")
        
        except Exception as e:
            print(f"   💥 Erro de conexão: {str(e)}")
            self.results['pubg']['error'] = str(e)
        
        print()
    
    async def test_medal_api(self):
        print("🏅 TESTANDO MEDAL API...\n")
        
        if not self.results['medal']['configured']:
            print("⏭️  Pulando teste - API não configurada\n")
            return
        
        try:
            # Medal API tem endpoints diferentes, teste básico
            print("1️⃣ Testando conectividade...")
            
            headers = {
                'Authorization': f'Bearer {self.medal_api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Endpoint de teste (pode variar conforme documentação da Medal)
                url = "https://developers.medal.tv/v1/latest"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        print("   ✅ Conectividade OK")
                        self.results['medal']['working'] = True
                    elif response.status == 401:
                        print("   ❌ Chave de API inválida")
                        self.results['medal']['error'] = "Chave inválida"
                    else:
                        print(f"   ⚠️  Status: {response.status}")
                        self.results['medal']['error'] = f"HTTP {response.status}"
        
        except Exception as e:
            print(f"   💥 Erro de conexão: {str(e)}")
            self.results['medal']['error'] = str(e)
        
        print()
    
    def print_summary(self):
        print("📊 RESUMO DOS TESTES\n")
        
        # PUBG
        pubg_status = "🟢 OK" if self.results['pubg']['working'] else "🔴 ERRO" if self.results['pubg']['configured'] else "⚪ NÃO CONFIGURADA"
        print(f"🎮 PUBG API: {pubg_status}")
        if self.results['pubg']['error']:
            print(f"   ❌ Erro: {self.results['pubg']['error']}")
        
        # Medal
        medal_status = "🟢 OK" if self.results['medal']['working'] else "🔴 ERRO" if self.results['medal']['configured'] else "⚪ NÃO CONFIGURADA"
        print(f"🏅 Medal API: {medal_status}")
        if self.results['medal']['error']:
            print(f"   ❌ Erro: {self.results['medal']['error']}")
        
        print("\n" + "="*60)
        
        # Recomendações
        if not self.results['pubg']['configured']:
            print("💡 Para configurar PUBG API:")
            print("   1. Acesse: https://developer.pubg.com/")
            print("   2. Crie uma conta e gere uma API key")
            print("   3. Adicione no .env: PUBG_API_KEY=sua_chave")
            print()
        
        if not self.results['medal']['configured']:
            print("💡 Para configurar Medal API:")
            print("   1. Acesse: https://medal.tv/developers")
            print("   2. Registre sua aplicação")
            print("   3. Adicione no .env: MEDAL_API_KEY=sua_chave")
            print()
        
        if self.results['pubg']['working'] or self.results['medal']['working']:
            print("✅ Pelo menos uma API está funcionando!")
            print("🔄 Reinicie o bot para aplicar as configurações.")
        
        print("="*60)

async def main():
    tester = APITester()
    
    tester.print_header()
    tester.check_configuration()
    
    await tester.test_pubg_api()
    await tester.test_medal_api()
    
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())