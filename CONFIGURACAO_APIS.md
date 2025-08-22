# 🔧 Configuração de APIs - Hawk Esports Bot

## 📋 APIs Necessárias

### 1. PUBG API
**Status:** ❌ Não configurada
**Necessária para:** Rankings PUBG, estatísticas de jogadores, badges automáticos

**Como configurar:**
1. Acesse: https://developer.pubg.com/
2. Crie uma conta ou faça login
3. Vá em "My Apps" → "Create New App"
4. Preencha:
   - **App Name:** Hawk Esports Bot
   - **Description:** Bot Discord para clã de PUBG
   - **Website:** (opcional)
5. Após criar, copie a **API Key**
6. No arquivo `.env`, substitua:
   ```
   PUBG_API_KEY=sua_chave_aqui
   ```

**Limitações da API gratuita:**
- 10 requisições por minuto
- Dados de até 14 dias
- Apenas shards públicos

### 2. Medal API
**Status:** ❌ Não configurada
**Necessária para:** Integração com clipes do Medal.tv

**Como configurar:**
1. Acesse: https://medal.tv/developers
2. Crie uma conta de desenvolvedor
3. Registre sua aplicação
4. Copie a **API Key**
5. No arquivo `.env`, substitua:
   ```
   MEDAL_API_KEY=sua_chave_aqui
   ```

## 🧪 Testando as APIs

### Comandos de Teste Disponíveis:

1. **Teste PUBG API:**
   ```
   /test_pubg_api
   /debug_pubg_raw jogador:SeuNick
   ```

2. **Verificar configuração:**
   ```
   /status
   ```

## ⚠️ Problemas Conhecidos

### PUBG API não configurada:
- Comandos `/ranking_pubg`, `/badges_pubg` não funcionam
- Sistema de cargos automáticos inativo
- Estatísticas reais indisponíveis

### Medal API não configurada:
- Integração com clipes desabilitada
- Comandos de medal não funcionam

## 🔄 Após Configurar

1. **Reinicie o bot** (no Render ou localmente)
2. **Teste os comandos** de API
3. **Configure os sistemas automáticos:**
   - `/pubg_roles_config acao:enable`
   - `/badges_config acao:enable`

## 📊 Monitoramento

**Logs importantes:**
- `PUBG API inicializada com sucesso` ✅
- `PUBG_API_KEY não encontrada` ❌
- `Erro na API PUBG: 401` (chave inválida) ❌
- `Erro na API PUBG: 429` (limite excedido) ⚠️

---

**Nota:** O bot funciona parcialmente sem essas APIs, mas muitas funcionalidades ficam limitadas.