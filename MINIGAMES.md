# 🎮 Sistema de Mini-Games - Hawk Bot

## Visão Geral

O sistema de mini-games do Hawk Bot oferece entretenimento interativo e engajamento para a comunidade, com jogos divertidos, desafios diários e um sistema de pontuação competitivo.

## 🎯 Funcionalidades Principais

### 1. **Pedra, Papel, Tesoura** 🪨📄✂️
- Jogue contra o bot em partidas rápidas
- Sistema de pontuação baseado no resultado
- Estatísticas de vitórias registradas

### 2. **Quiz PUBG** 🧠
- Perguntas sobre PUBG em 3 níveis de dificuldade
- Sistema interativo com reações
- Pontuação baseada na dificuldade
- Estatísticas de precisão

### 3. **Roleta da Sorte** 🎰
- Aposte seus pontos para ganhar mais
- Múltiplos resultados possíveis
- Sistema de probabilidades balanceado
- Jackpots especiais

### 4. **Desafios Diários** 🏆
- Desafios únicos renovados diariamente
- Recompensas em pontos e títulos especiais
- Progresso rastreado automaticamente
- Variedade de tipos de desafios

### 5. **Sistema de Ranking** 📊
- Rankings por diferentes categorias
- Estatísticas detalhadas por jogador
- Leaderboards do servidor
- Histórico de performance

## 🎮 Comandos Disponíveis

### `/pedra_papel_tesoura [escolha]`
**Descrição:** Jogue pedra, papel, tesoura contra o bot
**Parâmetros:**
- `escolha`: Sua jogada (pedra, papel ou tesoura)

**Pontuação:**
- Vitória: +50 pontos
- Empate: +10 pontos
- Derrota: +5 pontos

### `/quiz_pubg [dificuldade]`
**Descrição:** Teste seus conhecimentos sobre PUBG
**Parâmetros:**
- `dificuldade`: Nível da pergunta (fácil, médio, difícil, aleatório)

**Pontuação:**
- Fácil: +25 pontos (acerto) / +5 pontos (erro)
- Médio: +50 pontos (acerto) / +5 pontos (erro)
- Difícil: +100 pontos (acerto) / +5 pontos (erro)

**Como jogar:**
1. Use o comando para receber uma pergunta
2. Reaja com o emoji correspondente à resposta (1️⃣, 2️⃣, 3️⃣, 4️⃣)
3. Receba o resultado instantaneamente

### `/roleta [pontos]`
**Descrição:** Aposte seus pontos na roleta da sorte
**Parâmetros:**
- `pontos`: Quantidade de pontos para apostar

**Resultados Possíveis:**
- 💀 Perdeu tudo (40% chance)
- 😢 Perdeu metade (20% chance)
- 😐 Empatou (15% chance)
- 😊 Ganhou 50% (10% chance)
- 🎉 Dobrou (8% chance)
- 🤑 Triplicou (5% chance)
- 💰 JACKPOT x5 (2% chance)

### `/stats_jogos [usuario]`
**Descrição:** Veja estatísticas detalhadas dos mini-games
**Parâmetros:**
- `usuario`: Usuário para consultar (opcional, padrão: você)

**Informações mostradas:**
- Jogos totais e vitórias
- Taxa de vitória geral
- Pontos acumulados
- Precisão no quiz
- Vitórias por jogo específico

### `/desafio_diario`
**Descrição:** Veja seu desafio diário atual

**Tipos de Desafios:**
- **Mestre das Palavras:** Enviar mensagens
- **Socialização:** Reagir a mensagens
- **Gamer Ativo:** Tempo em canal de voz
- **Quiz Master:** Acertar perguntas no quiz
- **Sortudo:** Ganhar na roleta
- **Competidor:** Jogar pedra-papel-tesoura
- **Estudioso:** Responder perguntas no quiz

### `/ranking_jogos [categoria]`
**Descrição:** Veja o ranking dos mini-games do servidor
**Categorias:**
- `points`: Pontos totais (padrão)
- `games`: Jogos jogados
- `wins`: Vitórias
- `quiz`: Acertos no quiz

## ⚙️ Configuração

### Arquivo de Configuração: `minigames_config.json`

O sistema utiliza um arquivo JSON para configurações flexíveis:

```json
{
  "quiz_questions": {
    "easy": [...],
    "medium": [...],
    "hard": [...]
  },
  "daily_challenges": [...],
  "roulette_settings": {...},
  "points_system": {...},
  "game_settings": {...}
}
```

### Personalização

1. **Adicionar Perguntas:** Edite a seção `quiz_questions`
2. **Novos Desafios:** Modifique `daily_challenges`
3. **Ajustar Roleta:** Configure `roulette_settings`
4. **Sistema de Pontos:** Altere `points_system`

## 📈 Sistema de Pontuação

### Pontos Iniciais
- Novos jogadores começam com **100 pontos**

### Formas de Ganhar Pontos
- Jogar mini-games (sempre ganha algo)
- Completar desafios diários
- Acertar perguntas no quiz
- Ganhar na roleta

### Uso dos Pontos
- Apostar na roleta
- Competir nos rankings
- Futuros recursos premium

## 🏆 Sistema de Desafios Diários

### Características
- **Renovação:** Meia-noite (horário do servidor)
- **Personalização:** Cada usuário recebe um desafio diferente
- **Progresso:** Rastreado automaticamente
- **Recompensas:** Pontos + títulos especiais

### Tipos de Progresso Rastreado
- Mensagens enviadas
- Reações adicionadas
- Tempo em canal de voz
- Acertos no quiz
- Vitórias na roleta
- Jogos de pedra-papel-tesoura

## 📊 Estatísticas e Rankings

### Dados Coletados
- Jogos totais jogados
- Vitórias e derrotas
- Pontos acumulados
- Precisão no quiz
- Vitórias por tipo de jogo
- Desafios diários completados

### Rankings Disponíveis
- **Top 10** por categoria
- Filtrado por servidor
- Atualização em tempo real
- Medalhas visuais (🥇🥈🥉🏅)

## 🔧 Administração

### Arquivos de Dados
- `minigames_data.json`: Estatísticas dos jogadores
- `minigames_config.json`: Configurações do sistema

### Backup e Manutenção
- Dados salvos automaticamente após cada jogo
- Backup recomendado dos arquivos JSON
- Logs detalhados para debugging

## 🚀 Recursos Futuros

### Planejados
- Torneios de mini-games
- Loja de recompensas
- Novos tipos de jogos
- Integração com sistema de conquistas
- Apostas entre jogadores

## 🛠️ Solução de Problemas

### Problemas Comuns

**Quiz não responde às reações:**
- Verifique se o bot tem permissão para adicionar reações
- Aguarde até 5 minutos antes que a sessão expire

**Pontos não salvando:**
- Verifique permissões de escrita no diretório
- Consulte logs para erros de JSON

**Desafios não atualizando:**
- Reinicie o bot à meia-noite
- Verifique configuração de fuso horário

### Logs e Debug
- Logs detalhados em `hawk_bot.log`
- Categoria: `HawkBot.MinigamesSystem`
- Nível de log configurável

## 📞 Suporte

Para suporte técnico ou sugestões:
- Consulte os logs do sistema
- Verifique configurações JSON
- Reporte bugs com detalhes específicos

---

**Desenvolvido para Hawk Esports** 🦅
*Sistema de Mini-Games v1.0.0*