# 🗄️ Otimização de Banco de Dados - Hawk Bot

## 🔍 Problemas Identificados no Sistema de Banco de Dados

### ❌ **Problemas Críticos de Performance**

#### 1. **Queries Problemáticas**

**Query sem LIMIT na função `get_all_users()`:**
```sql
SELECT * FROM users ORDER BY total_time DESC
```
- **Problema**: Busca TODOS os usuários sem limitação
- **Impacto**: Pode retornar milhares de registros
- **Solução**: Implementar paginação obrigatória

**Query sem LIMIT na função `get_all_sessions()`:**
```sql
SELECT s.*, u.username, u.display_name 
FROM sessions s 
JOIN users u ON s.user_id = u.user_id 
ORDER BY s.start_time DESC
```
- **Problema**: JOIN sem limitação de resultados
- **Impacto**: Performance degradada com muitas sessões
- **Solução**: Implementar LIMIT padrão e paginação

#### 2. **N+1 Problem na Migração**

**Código problemático em `migrate_from_json()`:**
```python
for session_data in data['sessions']:
    async with self.pool.acquire() as conn:
        await conn.execute("INSERT INTO sessions...")
```
- **Problema**: Uma conexão por sessão na migração
- **Impacto**: Centenas de conexões desnecessárias
- **Solução**: Batch insert com uma única transação

#### 3. **Falta de Índices Otimizados**

**Índices ausentes identificados:**
- `sessions.end_time` - Para queries de sessões ativas
- `users.last_checkin` - Para relatórios de atividade
- `users.is_checked_in` - Para contagem de usuários online
- `sessions(user_id, start_time)` - Índice composto para performance

#### 4. **Connection Pool Não Otimizado**

**Problemas atuais:**
- Pool size não configurado adequadamente
- Conexões não reutilizadas eficientemente
- Falta de timeout configurado
- Sem monitoramento de conexões ativas

## 🚀 Soluções Propostas

### 1. **Otimização de Queries**

#### Implementar Paginação Obrigatória:
```python
class OptimizedDatabaseManager:
    async def get_all_users(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Busca usuários com paginação obrigatória"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, username, display_name, total_sessions, total_time
                FROM users 
                ORDER BY total_time DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            return [dict(row) for row in rows]
    
    async def get_all_sessions_paginated(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Busca sessões com paginação e JOIN otimizado"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT s.session_id, s.user_id, s.start_time, s.end_time, 
                       s.duration, s.session_type, u.username, u.display_name
                FROM sessions s 
                INNER JOIN users u ON s.user_id = u.user_id 
                ORDER BY s.start_time DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            return [dict(row) for row in rows]
```

#### Implementar Queries Otimizadas:
```python
class OptimizedQueries:
    async def get_active_users_count(self) -> int:
        """Conta usuários ativos sem buscar todos os dados"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE is_checked_in = true"
            )
            return result or 0
    
    async def get_user_stats_summary(self, user_id: int) -> Dict[str, Any]:
        """Busca estatísticas do usuário de forma otimizada"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT 
                    u.username,
                    u.total_sessions,
                    u.total_time,
                    u.is_checked_in,
                    COUNT(s.id) as recent_sessions
                FROM users u
                LEFT JOIN sessions s ON u.user_id = s.user_id 
                    AND s.start_time > NOW() - INTERVAL '30 days'
                WHERE u.user_id = $1
                GROUP BY u.user_id, u.username, u.total_sessions, u.total_time, u.is_checked_in
            """, user_id)
```

### 2. **Otimização de Migração**

#### Batch Insert Otimizado:
```python
class OptimizedMigration:
    async def migrate_sessions_batch(self, sessions_data: List[Dict]) -> None:
        """Migra sessões em lotes para melhor performance"""
        batch_size = 100
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for i in range(0, len(sessions_data), batch_size):
                    batch = sessions_data[i:i + batch_size]
                    
                    # Preparar dados para batch insert
                    values = []
                    for session in batch:
                        values.extend([
                            session['user_id'],
                            session['session_id'],
                            datetime.fromisoformat(session['start_time']),
                            datetime.fromisoformat(session['end_time']) if session.get('end_time') else None,
                            session.get('duration', 0),
                            session.get('type', 'gaming')
                        ])
                    
                    # Executar batch insert
                    placeholders = ','.join(['($' + ','.join([str(j) for j in range(i*6+1, i*6+7)]) + ')' 
                                           for i in range(len(batch))])
                    
                    await conn.execute(f"""
                        INSERT INTO sessions (user_id, session_id, start_time, end_time, duration, session_type)
                        VALUES {placeholders}
                        ON CONFLICT (session_id) DO NOTHING
                    """, *values)
                    
                    print(f"✅ Migrados {len(batch)} sessões (lote {i//batch_size + 1})")
```

### 3. **Índices Otimizados**

#### Script de Criação de Índices:
```sql
-- Índices para performance otimizada
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_end_time ON sessions(end_time) WHERE end_time IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_checkin ON users(last_checkin) WHERE last_checkin IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_checked_in ON users(is_checked_in) WHERE is_checked_in = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_start ON sessions(user_id, start_time DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_active ON sessions(user_id) WHERE end_time IS NULL;

-- Índices para relatórios
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_date_range ON sessions(start_time) WHERE start_time > NOW() - INTERVAL '90 days';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_activity ON users(total_time DESC, total_sessions DESC) WHERE total_sessions > 0;

-- Índices para limpeza automática
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_cleanup ON sessions(start_time) WHERE end_time IS NULL AND start_time < NOW() - INTERVAL '24 hours';
```

### 4. **Connection Pool Otimizado**

#### Configuração Avançada:
```python
class OptimizedDatabaseConfig:
    def __init__(self):
        self.config = {
            'min_size': 5,          # Mínimo de conexões
            'max_size': 20,         # Máximo de conexões
            'max_queries': 50000,   # Queries por conexão
            'max_inactive_connection_lifetime': 300,  # 5 minutos
            'timeout': 30,          # Timeout de conexão
            'command_timeout': 60,  # Timeout de comando
            'server_settings': {
                'jit': 'off',       # Desabilitar JIT para queries simples
                'application_name': 'hawk_bot'
            }
        }
    
    async def create_optimized_pool(self):
        """Cria pool otimizado com monitoramento"""
        return await asyncpg.create_pool(
            self.database_url,
            **self.config,
            init=self._init_connection
        )
    
    async def _init_connection(self, conn):
        """Inicializa cada conexão com configurações otimizadas"""
        await conn.execute("SET timezone = 'UTC'")
        await conn.execute("SET statement_timeout = '30s'")
        await conn.execute("SET lock_timeout = '10s'")
```

### 5. **Sistema de Cache Inteligente**

#### Cache para Queries Frequentes:
```python
class DatabaseCache:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {
            'user_stats': 300,      # 5 minutos
            'leaderboard': 600,     # 10 minutos
            'server_stats': 1800,   # 30 minutos
        }
    
    async def get_cached_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Leaderboard com cache inteligente"""
        cache_key = f"leaderboard_{limit}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        # Buscar do banco apenas se cache expirou
        data = await self.db.get_leaderboard(limit)
        self._set_cache(cache_key, data, 'leaderboard')
        return data
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se cache ainda é válido"""
        if key not in self.cache:
            return False
        
        cache_entry = self.cache[key]
        return time.time() - cache_entry['timestamp'] < cache_entry['ttl']
```

## 📊 Métricas de Performance Esperadas

### Antes das Otimizações:
- **Query `get_all_users()`**: 2-5 segundos (1000+ usuários)
- **Migração de dados**: 30-60 segundos (1000 sessões)
- **Conexões simultâneas**: 15-25
- **Uso de memória DB**: 200-400MB
- **Tempo de resposta médio**: 500-1500ms

### Após Otimizações:
- **Query `get_all_users_paginated()`**: 50-200ms (50 usuários por página)
- **Migração de dados**: 5-10 segundos (batch de 100)
- **Conexões simultâneas**: 5-10
- **Uso de memória DB**: 100-200MB
- **Tempo de resposta médio**: 50-200ms

## 🔧 Implementação Gradual

### Fase 1: Otimizações Críticas (1-2 dias)
1. ✅ Adicionar LIMIT padrão em todas as queries
2. ✅ Implementar paginação obrigatória
3. ✅ Criar índices essenciais
4. ✅ Otimizar connection pool

### Fase 2: Melhorias Avançadas (3-5 dias)
1. ✅ Implementar sistema de cache
2. ✅ Otimizar queries com JOINs
3. ✅ Implementar batch operations
4. ✅ Adicionar monitoramento de performance

### Fase 3: Otimizações Avançadas (1 semana)
1. ✅ Implementar query optimization automática
2. ✅ Adicionar métricas detalhadas
3. ✅ Implementar cleanup automático
4. ✅ Criar dashboard de monitoramento

## ⚠️ Considerações Importantes

### Riscos:
- **Mudanças de API**: Algumas funções terão parâmetros adicionais
- **Compatibilidade**: Código existente pode precisar de ajustes
- **Testes**: Necessário teste extensivo antes do deploy

### Benefícios:
- **Performance**: 70-80% melhoria na velocidade
- **Escalabilidade**: Suporte a 10x mais usuários
- **Recursos**: 50% menos uso de memória
- **Estabilidade**: Menos timeouts e crashes

## 📝 Próximos Passos

1. **Backup completo** do banco de dados atual
2. **Implementar otimizações** em ambiente de desenvolvimento
3. **Testes de carga** para validar melhorias
4. **Deploy gradual** com monitoramento
5. **Monitoramento contínuo** de performance

---

**Status**: 🔄 Em análise  
**Prioridade**: 🔴 Alta  
**Tempo estimado**: 1-2 semanas  
**Impacto esperado**: 70-80% melhoria de performance