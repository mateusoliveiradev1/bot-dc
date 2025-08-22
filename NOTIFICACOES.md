# 🔔 Sistema de Notificações Push - Hawk Bot

## 📋 Visão Geral

O Sistema de Notificações Push é uma funcionalidade avançada que permite ao Hawk Bot enviar alertas personalizados e em tempo real para os usuários sobre eventos importantes, conquistas, atualizações de rank, torneios e muito mais.

## ✨ Principais Funcionalidades

### 🎯 Tipos de Notificações
- **Rank Updates**: Promoções e mudanças de ranking
- **Conquistas**: Novas conquistas desbloqueadas
- **Torneios**: Início, resultados e lembretes de torneios
- **Desafios Diários**: Novos desafios e conclusões
- **Mini-games**: Marcos, recordes e conquistas
- **Moderação**: Avisos, silenciamentos e punições
- **Sistema**: Anúncios importantes e manutenções
- **Lembretes**: Lembretes personalizados criados pelo usuário
- **Aniversários**: Lembretes de aniversário automáticos
- **PUBG Stats**: Atualizações de estatísticas do jogo
- **Eventos**: Lembretes de eventos especiais

### 🚀 Recursos Avançados
- **Notificações Push Inteligentes**: Envio automático baseado em eventos
- **Personalização Completa**: Configurações individuais por usuário
- **Horário Silencioso**: Modo "não perturbe" configurável
- **Prioridades**: Sistema de 4 níveis de prioridade
- **Múltiplos Canais**: DM e canais do servidor
- **Agendamento**: Lembretes e notificações programadas
- **Expiração Automática**: Notificações com tempo de vida
- **Cache Inteligente**: Sistema otimizado de armazenamento

## 🎮 Comandos Disponíveis

### `/notificacoes`
**Descrição**: Visualizar suas notificações
**Parâmetros**:
- `apenas_nao_lidas` (opcional): Mostrar apenas não lidas
- `limite` (opcional): Número máximo a mostrar (1-20)

**Exemplo**: `/notificacoes apenas_nao_lidas:True limite:5`

### `/marcar_lidas`
**Descrição**: Marcar todas as notificações como lidas
**Uso**: `/marcar_lidas`

### `/config_notificacoes`
**Descrição**: Configurar preferências de notificações
**Parâmetros**:
- `dm_habilitado`: Receber por mensagem direta
- `canal_habilitado`: Receber no canal do servidor
- `horario_silencioso_inicio`: Hora de início do modo silencioso (0-23)
- `horario_silencioso_fim`: Hora de fim do modo silencioso (0-23)
- `prioridade_minima`: Prioridade mínima (low/medium/high/urgent)

**Exemplo**: `/config_notificacoes dm_habilitado:True horario_silencioso_inicio:22 horario_silencioso_fim:8`

### `/lembrete`
**Descrição**: Criar um lembrete personalizado
**Parâmetros**:
- `titulo`: Título do lembrete
- `mensagem`: Mensagem do lembrete
- `tempo`: Tempo para o lembrete (30m, 2h, 1d)
- `prioridade`: Prioridade (low/medium/high)

**Exemplo**: `/lembrete titulo:"Treino" mensagem:"Hora do treino!" tempo:2h prioridade:medium`

### `/notificacoes_help`
**Descrição**: Ajuda completa sobre o sistema
**Uso**: `/notificacoes_help`

## ⚙️ Configurações e Personalização

### 🎯 Níveis de Prioridade

| Prioridade | Descrição | Cor | Comportamento |
|------------|-----------|-----|---------------|
| **Low** | Informações gerais | 🔵 Azul | Respeitam horário silencioso |
| **Medium** | Eventos importantes | 🟡 Amarelo | Respeitam horário silencioso |
| **High** | Conquistas e promoções | 🟠 Laranja | Respeitam horário silencioso |
| **Urgent** | Alertas críticos | 🔴 Vermelho | **Ignoram horário silencioso** |

### 🌙 Horário Silencioso
- **Padrão**: 22:00 - 08:00
- **Configurável**: Cada usuário pode definir seu horário
- **Exceções**: Notificações urgentes sempre passam
- **Flexível**: Suporta horários que atravessam meia-noite

### 📱 Canais de Entrega
1. **Mensagem Direta (DM)**: Prioridade principal
2. **Canal do Servidor**: Fallback se DM falhar
3. **Canais Suportados**: `#notificações`, `#geral`, `#avisos`

## 🔧 Configuração Técnica

### 📁 Arquivos do Sistema
- `notifications_system.py`: Sistema principal
- `notifications_config.json`: Configurações e templates
- `notifications_data.json`: Dados dos usuários (auto-gerado)
- `notification_templates.json`: Templates personalizados (auto-gerado)

### 🎨 Templates de Notificação

O sistema utiliza templates JSON configuráveis:

```json
{
  "rank_update_promotion": {
    "title": "🎉 Promoção de Rank!",
    "message": "Parabéns! Você subiu para o rank **{new_rank}** com {points} pontos!",
    "color": 4437377,
    "priority": "high",
    "expires_after": 1440
  }
}
```

### 🔄 Integração com Outros Sistemas

O sistema se integra automaticamente com:
- **Sistema de Ranking**: Notificações de promoção/rebaixamento
- **Sistema de Conquistas**: Novas conquistas desbloqueadas
- **Sistema de Torneios**: Início, resultados e lembretes
- **Sistema de Mini-games**: Marcos e recordes
- **Sistema de Moderação**: Avisos e punições
- **PUBG API**: Atualizações de estatísticas

## 📊 Estatísticas e Monitoramento

### 📈 Métricas Disponíveis
- Total de notificações enviadas
- Usuários ativos no sistema
- Notificações pendentes
- Distribuição por tipo
- Distribuição por prioridade
- Taxa de entrega

### 🔍 Logs e Debugging
- Logs detalhados de envio
- Rastreamento de falhas
- Métricas de performance
- Limpeza automática de dados antigos

## 🛠️ Administração

### 👨‍💼 Comandos Administrativos

**Broadcast de Anúncios**:
```python
# Enviar anúncio para todos os usuários
count = await bot.notifications_system.broadcast_announcement(
    title="Manutenção Programada",
    message="O bot entrará em manutenção às 02:00",
    priority=NotificationPriority.HIGH
)
```

**Criar Notificação Personalizada**:
```python
# Criar notificação específica
notification = await bot.notifications_system.create_notification(
    user_id=123456789,
    template_id="achievement_unlocked",
    data={"achievement_name": "Primeira Vitória", "achievement_description": "Ganhou sua primeira partida!"}
)
```

### 🔧 Manutenção
- **Limpeza Automática**: Remove notificações antigas (7 dias)
- **Backup de Dados**: Salvamento automático em JSON
- **Otimização**: Cache inteligente para melhor performance
- **Monitoramento**: Logs detalhados de todas as operações

## 🚨 Solução de Problemas

### ❌ Problemas Comuns

**Notificações não chegam**:
1. Verificar se DM está habilitado
2. Verificar horário silencioso
3. Verificar prioridade mínima
4. Verificar se o tipo está habilitado

**Bot não consegue enviar DM**:
- O sistema automaticamente tenta o canal do servidor
- Usuário pode ter DMs desabilitadas
- Verificar se o bot tem permissões no canal

**Notificações duplicadas**:
- Sistema possui proteção contra duplicatas
- Verificar se há múltiplas instâncias rodando

### 🔧 Comandos de Debug

```python
# Verificar estatísticas
stats = bot.notifications_system.get_notification_stats()
print(f"Total: {stats['total_notifications']}")

# Verificar preferências do usuário
prefs = bot.notifications_system.get_user_preferences(user_id)
print(f"DM habilitado: {prefs.dm_enabled}")
```

## 🔮 Recursos Futuros

### 🎯 Próximas Implementações
- [ ] **Notificações Web**: Push notifications no dashboard
- [ ] **Integração Mobile**: Notificações via app móvel
- [ ] **Templates Visuais**: Editor gráfico de templates
- [ ] **Análise Avançada**: Dashboard de métricas
- [ ] **Notificações por Webhook**: Integração com serviços externos
- [ ] **Filtros Avançados**: Regras complexas de filtragem
- [ ] **Notificações de Grupo**: Alertas para grupos específicos
- [ ] **Histórico Completo**: Arquivo permanente de notificações

### 🔄 Melhorias Planejadas
- **Performance**: Otimização para grandes volumes
- **Escalabilidade**: Suporte a múltiplos servidores
- **Personalização**: Mais opções de customização
- **Integração**: Conectores para mais sistemas

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o sistema de notificações:
- Use `/notificacoes_help` para ajuda rápida
- Consulte os logs do bot para debugging
- Verifique as configurações em `notifications_config.json`
- Entre em contato com a administração do servidor

---

**Hawk Bot - Sistema de Notificações Push v1.0.0**  
*Desenvolvido para proporcionar a melhor experiência de comunicação e engajamento no servidor.*