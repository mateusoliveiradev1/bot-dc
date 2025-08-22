# 📊 Sistema de Gráficos de Progresso Individual - Hawk Bot

## 📋 Visão Geral

O Sistema de Gráficos de Progresso Individual é uma funcionalidade avançada do Hawk Bot que permite aos usuários visualizar seu progresso e estatísticas através de gráficos interativos e informativos. O sistema coleta dados de todos os módulos do bot e os apresenta de forma visual e intuitiva.

## 🎯 Funcionalidades Principais

### 📈 Gráfico de Progresso de Rank
- **Comando:** `/grafico_rank`
- **Descrição:** Mostra a evolução do rank do jogador ao longo do tempo
- **Características:**
  - Linha temporal com progresso de pontos
  - Área preenchida para melhor visualização
  - Estatísticas de mudança de rank
  - Dados dos últimos 30 dias

### 🎮 Gráfico de Performance em Jogos
- **Comando:** `/grafico_jogos`
- **Descrição:** Visualiza performance nos mini-games do bot
- **Características:**
  - Gráfico de barras com vitórias vs derrotas por jogo
  - Gráfico de pizza com taxa de vitória geral
  - Dados de todos os mini-games (Pedra-Papel-Tesoura, Quiz PUBG, Roleta, Torneios)

### 🔥 Mapa de Atividade
- **Comando:** `/mapa_atividade`
- **Descrição:** Heatmap da atividade do usuário no servidor
- **Características:**
  - Mapa de calor 7x24 (dias da semana x horas do dia)
  - Visualização de padrões de atividade
  - Cores indicativas de intensidade de atividade

### 🏆 Progresso de Conquistas
- **Comando:** `/progresso_conquistas`
- **Descrição:** Mostra o progresso em todas as conquistas disponíveis
- **Características:**
  - Barras horizontais de progresso
  - Cores diferenciadas por status (completo, em progresso, iniciante)
  - Percentual de conclusão para cada conquista

### ⚡ Comparação Radar
- **Comando:** `/comparacao_radar`
- **Descrição:** Compara a performance do usuário com a média do servidor
- **Características:**
  - Gráfico radar com múltiplas categorias
  - Comparação visual com média do servidor
  - Categorias: Rank, Vitórias, Precisão Quiz, Atividade, Conquistas, Pontos

### 📋 Relatório Completo
- **Comando:** `/relatorio_completo`
- **Descrição:** Gera todos os gráficos em um relatório abrangente
- **Características:**
  - Todos os 5 tipos de gráficos em uma única resposta
  - Ideal para análise completa de progresso
  - Formato otimizado para compartilhamento

## 🛠️ Comandos Disponíveis

| Comando | Descrição | Tipo de Gráfico |
|---------|-----------|------------------|
| `/grafico_rank` | Progresso de rank ao longo do tempo | Linha temporal |
| `/grafico_jogos` | Performance em mini-games | Barras + Pizza |
| `/mapa_atividade` | Atividade por dia/hora | Heatmap |
| `/progresso_conquistas` | Status das conquistas | Barras horizontais |
| `/comparacao_radar` | Comparação com servidor | Radar |
| `/relatorio_completo` | Todos os gráficos | Múltiplos |
| `/graficos_help` | Ajuda do sistema | Informativo |

## 🎨 Características Visuais

### Tema Dark
- **Fundo:** Tons escuros compatíveis com Discord
- **Cores:** Paleta harmoniosa com cores do Discord
- **Contraste:** Alto contraste para melhor legibilidade

### Cores Utilizadas
- **Primária:** #7289DA (Azul Discord)
- **Sucesso:** #43B581 (Verde)
- **Aviso:** #FAA61A (Amarelo)
- **Perigo:** #F04747 (Vermelho)
- **Info:** #00D4AA (Ciano)
- **Secundária:** #747F8D (Cinza)

## ⚙️ Configurações Técnicas

### Cache Inteligente
- **Duração:** 5 minutos por gráfico
- **Benefício:** Reduz tempo de resposta e uso de recursos
- **Limpeza:** Automática baseada em timestamp

### Dependências
```
matplotlib>=3.7.0    # Geração de gráficos
seaborn>=0.12.0      # Estilos e visualizações avançadas
pandas>=2.0.0        # Manipulação de dados
numpy>=1.24.0        # Operações numéricas
```

### Formatos de Saída
- **Formato:** PNG
- **Resolução:** 150 DPI
- **Tamanho:** Otimizado para Discord
- **Compressão:** Automática

## 📊 Integração com Outros Sistemas

### Dados Coletados
- **Sistema de Ranking:** Pontos, posição, histórico
- **Mini-Games:** Vitórias, derrotas, pontuações
- **Conquistas:** Progresso, badges, status
- **Atividade:** Mensagens, comandos, presença
- **Torneios:** Participações, resultados

### Sistemas Integrados
- ✅ Sistema de Ranking
- ✅ Sistema de Mini-Games
- ✅ Sistema de Conquistas
- ✅ Sistema de Moderação
- ✅ Sistema de Torneios
- ✅ Dashboard Web

## 🚀 Performance

### Otimizações
- **Cache de gráficos:** Evita regeneração desnecessária
- **Processamento assíncrono:** Não bloqueia o bot
- **Compressão de imagens:** Reduz uso de banda
- **Limpeza automática:** Gerenciamento de memória

### Limites
- **Máximo de gráficos simultâneos:** 5 (relatório completo)
- **Tempo de cache:** 5 minutos
- **Tamanho máximo por gráfico:** 2MB
- **Resolução máxima:** 1920x1080

## 🔧 Administração

### Comandos Administrativos
- **Limpeza de cache:** Automática a cada 30 minutos
- **Monitoramento:** Logs detalhados de geração
- **Estatísticas:** Contadores de uso por tipo

### Logs do Sistema
```
INFO:HawkBot.ChartsSystem:Sistema de Gráficos inicializado
INFO:HawkBot.ChartsSystem:Gráfico gerado: rank_progress para usuário 123456
INFO:HawkBot.ChartsSystem:Cache limpo: 15 entradas removidas
```

## 🆘 Solução de Problemas

### Problemas Comuns

**Erro: "Erro ao gerar gráfico"**
- **Causa:** Dados insuficientes ou erro de dependência
- **Solução:** Verificar se o usuário possui dados nos sistemas integrados

**Gráfico não aparece**
- **Causa:** Problema de cache ou geração
- **Solução:** Aguardar alguns segundos e tentar novamente

**Qualidade baixa da imagem**
- **Causa:** Configuração de DPI
- **Solução:** Verificar configurações de resolução no código

### Verificações
1. **Dependências instaladas:** `pip list | grep -E "matplotlib|seaborn|pandas|numpy"`
2. **Permissões de arquivo:** Verificar se o bot pode criar arquivos temporários
3. **Memória disponível:** Gráficos complexos requerem mais RAM
4. **Dados do usuário:** Verificar se há dados suficientes para gerar gráficos

## 🔮 Recursos Futuros

### Planejados
- **Gráficos personalizáveis:** Permitir escolha de cores e estilos
- **Exportação em PDF:** Relatórios em formato PDF
- **Gráficos animados:** GIFs mostrando evolução temporal
- **Comparação entre usuários:** Gráficos comparativos
- **Integração com API externa:** Dados de jogos externos
- **Gráficos 3D:** Visualizações tridimensionais
- **Dashboard interativo:** Interface web para gráficos

### Melhorias Técnicas
- **Cache distribuído:** Redis para cache em múltiplas instâncias
- **Processamento em background:** Celery para gráficos complexos
- **Compressão avançada:** WebP para menor tamanho
- **Responsividade:** Gráficos adaptativos ao dispositivo

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o sistema de gráficos:
- **Comando:** `/graficos_help`
- **Logs:** Verificar `hawk_bot.log`
- **Documentação:** Este arquivo (GRAFICOS.md)

---

**Desenvolvido com ❤️ para o Hawk Bot**  
*Sistema de Gráficos v1.0.0*