import discord
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

token = os.getenv('DISCORD_TOKEN')
print(f"Token encontrado: {'Sim' if token else 'Não'}")
print(f"Token válido: {token[:20]}...{token[-10:] if token else 'N/A'}")

# Teste básico de conexão
class TestBot(discord.Client):
    async def on_ready(self):
        print(f'✅ Bot conectado como {self.user} (ID: {self.user.id})')
        print(f'🌐 Conectado a {len(self.guilds)} servidores')
        await self.close()
    
    async def on_connect(self):
        print('🔗 Conectado ao Discord!')
    
    async def on_disconnect(self):
        print('❌ Desconectado do Discord')

if token:
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        client = TestBot(intents=intents)
        client.run(token)
    except Exception as e:
        print(f'❌ Erro ao conectar: {e}')
else:
    print('❌ Token não encontrado no arquivo .env')