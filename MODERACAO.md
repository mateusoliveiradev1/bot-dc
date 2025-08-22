# 🛡️ Sistema de Moderação Automática - Hawk Bot

## Visão Geral

O sistema de moderação automática do Hawk Bot oferece proteção avançada contra spam, toxicidade, raids e comportamentos inadequados no servidor Discord.

## Funcionalidades

### 🚫 Detecção Automática
- **Anti-Spam**: Detecta mensagens repetitivas, excesso de maiúsculas, muitas menções
- **Filtro de Toxicidade**: Identifica palavras ofensivas e linguagem tóxica
- **Proteção Anti-Raid**: Monitora entradas suspeitas em massa
- **Detecção de Links Maliciosos**: Bloqueia links suspeitos e encurtadores

### ⚠️ Sistema de Advertências
- Sistema progressivo de punições
- Advertências acumulativas com ações escaláveis
- Histórico completo de infrações
- Limpeza de advertências por administradores

### 🔧 Configuração Flexível
- Arquivo `moderation_config.json` para personalização
- Configurações por servidor
- Thresholds ajustáveis
- Ativação/desativação de funcionalidades

## Comandos Disponíveis

### Para Moderadores

#### `/warn <usuário> [motivo]`
- Aplica advertência manual a um usuário
- **Permissão**: `Moderate Members`
- **Exemplo**: `/warn @usuario Spam no chat`

#### `/warnings [usuário]`
- Mostra advertências de um usuário
- Se não especificar usuário, mostra suas próprias advertências
- **Permissão**: `Moderate Members` (para ver outros usuários)

### Para Administradores

#### `/clear_warnings <usuário>`
- Remove todas as advertências de um usuário
- **Permissão**: `Administrator`
- **Exemplo**: `/clear_warnings @usuario`

#### `/automod <ação> [valor]`
- Configura o sistema de moderação automática
- **Permissão**: `Administrator`

**Ações disponíveis:**
- `toggle`: Ativa/desativa o sistema
- `spam_limit`: Define limite de mensagens para spam
- `toxicity_filter`: Ativa/desativa filtro de toxicidade
- `raid_protection`: Ativa/desativa proteção anti-raid
- `status`: Mostra status atual das configurações

**Exemplos:**
```
/automod toggle
/automod spam_limit 5
/automod toxicity_filter true
/automod status
```

## Configuração (moderation_config.json)

### Palavras Proibidas
```json
"banned_words": [
  "spam", "hack", "cheat", "bot", "fake", "scam",
  "virus", "malware", "phishing", "discord.gg"
]
```

### Palavras Tóxicas
```json
"toxic_words": [
  "idiota", "burro", "estupido", "lixo"
]
```

### Configurações de Spam
```json
"spam_settings": {
  "max_messages": 5,        // Máximo de mensagens
  "time_window": 10,        // Janela de tempo (segundos)
  "max_duplicates": 3,      // Máximo de mensagens duplicadas
  "max_mentions": 3,        // Máximo de menções por mensagem
  "max_emojis": 10,         // Máximo de emojis por mensagem
  "max_caps_percentage": 70 // Máximo de maiúsculas (%)
}
```

### Proteção Anti-Raid
```json
"raid_protection": {
  "enabled": true,                    // Ativar proteção
  "max_joins_per_minute": 10,        // Máximo de entradas por minuto
  "new_account_threshold_days": 7,   // Dias para considerar conta nova
  "auto_kick_new_accounts": false    // Auto-kick contas novas durante raid
}
```

### Thresholds de Advertências
```json
"warning_thresholds": {
  "timeout_warnings": 3,  // Advertências para timeout
  "kick_warnings": 5,     // Advertências para kick
  "ban_warnings": 7       // Advertências para ban
}
```

### Durações de Timeout
```json
"timeout_durations": {
  "first_offense": 300,   // 5 minutos
  "second_offense": 900,  // 15 minutos
  "third_offense": 3600   // 1 hora
}
```

## Sistema de Punições

### Progressão Automática
1. **1-2 Advertências**: Apenas aviso
2. **3 Advertências**: Timeout (5-15 minutos)
3. **4 Advertências**: Timeout (15 minutos - 1 hora)
4. **5 Advertências**: Kick do servidor
5. **7+ Advertências**: Ban permanente

### Tipos de Violações
- **Spam**: Mensagens repetitivas ou excessivas
- **Toxicidade**: Linguagem ofensiva ou tóxica
- **Raid**: Participação em ataques coordenados
- **Links Maliciosos**: Compartilhamento de links suspeitos
- **Caps Spam**: Excesso de maiúsculas
- **Mention Spam**: Excesso de menções

## Logs de Moderação

Todas as ações são registradas em:
- Canal de logs de moderação (se configurado)
- Arquivo de log do bot
- Banco de dados interno

### Informações Registradas
- Usuário infrator
- Tipo de violação
- Ação tomada
- Moderador responsável (se manual)
- Data e hora
- Contexto da infração

## Configuração Inicial

1. **Execute o comando de setup do servidor**:
   ```
   /setup_server confirmar:CONFIRMAR
   ```

2. **Configure o sistema de moderação**:
   ```
   /automod toggle
   /automod status
   ```

3. **Personalize as configurações** editando `moderation_config.json`

4. **Reinicie o bot** para aplicar as mudanças

## Permissões Necessárias

### Para o Bot
- `Manage Messages` - Deletar mensagens de spam
- `Timeout Members` - Aplicar timeouts
- `Kick Members` - Expulsar usuários
- `Ban Members` - Banir usuários
- `View Audit Log` - Registrar ações
- `Send Messages` - Enviar logs e avisos

### Para Moderadores
- `Moderate Members` - Usar comandos básicos de moderação
- `Administrator` - Configurar sistema e limpar advertências

## Troubleshooting

### Bot não está moderando
1. Verifique se o sistema está ativo: `/automod status`
2. Confirme as permissões do bot
3. Verifique os logs para erros

### Configurações não aplicadas
1. Verifique a sintaxe do `moderation_config.json`
2. Reinicie o bot após mudanças
3. Use `/automod status` para confirmar

### Falsos positivos
1. Ajuste os thresholds no arquivo de configuração
2. Adicione exceções para palavras específicas
3. Configure canais isentos de moderação

## Suporte

Para suporte adicional ou reportar bugs:
- Verifique os logs do bot em `hawk_bot.log`
- Consulte a documentação completa
- Entre em contato com a equipe de desenvolvimento