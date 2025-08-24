-- ========================================
-- CONFIGURAÇÃO AUTOMÁTICA DO SUPABASE
-- HAWK ESPORTS BOT - POSTGRESQL SETUP
-- ========================================

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ========================================
-- TABELA DE USUÁRIOS
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    discriminator VARCHAR(10),
    avatar_url TEXT,
    pubg_username VARCHAR(255),
    pubg_id VARCHAR(255),
    current_rank VARCHAR(50) DEFAULT 'Unranked',
    season_points INTEGER DEFAULT 0,
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    kills INTEGER DEFAULT 0,
    damage BIGINT DEFAULT 0,
    survival_time BIGINT DEFAULT 0,
    last_match_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    badges JSONB DEFAULT '[]'::jsonb,
    achievements JSONB DEFAULT '[]'::jsonb,
    settings JSONB DEFAULT '{"notifications": true, "public_profile": true}'::jsonb
);

-- ========================================
-- TABELA DE CONFIGURAÇÕES DO BOT
-- ========================================
CREATE TABLE IF NOT EXISTS bot_settings (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    setting_key VARCHAR(255) NOT NULL,
    setting_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, setting_key)
);

-- ========================================
-- TABELA DE SESSÕES ATIVAS
-- ========================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES users(discord_id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL, -- 'checkin', 'tournament', 'minigame'
    session_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'completed', 'expired'
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELA DE RANKINGS E TEMPORADAS
-- ========================================
CREATE TABLE IF NOT EXISTS rankings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(discord_id) ON DELETE CASCADE,
    season_id VARCHAR(50) NOT NULL,
    rank_type VARCHAR(50) NOT NULL, -- 'pubg', 'checkin', 'tournament'
    current_rank VARCHAR(50),
    points INTEGER DEFAULT 0,
    position INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, season_id, rank_type)
);

-- ========================================
-- TABELA DE LOGS E AUDITORIA
-- ========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- ÍNDICES PARA PERFORMANCE
-- ========================================

-- Índices para tabela users
CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id);
CREATE INDEX IF NOT EXISTS idx_users_pubg_username ON users(pubg_username);
CREATE INDEX IF NOT EXISTS idx_users_current_rank ON users(current_rank);
CREATE INDEX IF NOT EXISTS idx_users_season_points ON users(season_points DESC);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;

-- Índices para tabela bot_settings
CREATE INDEX IF NOT EXISTS idx_bot_settings_guild ON bot_settings(guild_id);
CREATE INDEX IF NOT EXISTS idx_bot_settings_key ON bot_settings(setting_key);

-- Índices para tabela sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Índices para tabela rankings
CREATE INDEX IF NOT EXISTS idx_rankings_user_season ON rankings(user_id, season_id);
CREATE INDEX IF NOT EXISTS idx_rankings_season_type ON rankings(season_id, rank_type);
CREATE INDEX IF NOT EXISTS idx_rankings_points ON rankings(points DESC);
CREATE INDEX IF NOT EXISTS idx_rankings_position ON rankings(position);

-- Índices para tabela audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- ========================================
-- TRIGGERS PARA UPDATED_AT
-- ========================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at automaticamente
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bot_settings_updated_at BEFORE UPDATE ON bot_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- POLÍTICAS DE SEGURANÇA (RLS)
-- ========================================

-- Habilitar RLS nas tabelas principais
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rankings ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Política para permitir acesso completo ao bot (service_role)
CREATE POLICY "Bot full access" ON users FOR ALL USING (true);
CREATE POLICY "Bot full access" ON bot_settings FOR ALL USING (true);
CREATE POLICY "Bot full access" ON sessions FOR ALL USING (true);
CREATE POLICY "Bot full access" ON rankings FOR ALL USING (true);
CREATE POLICY "Bot full access" ON audit_logs FOR ALL USING (true);

-- ========================================
-- DADOS INICIAIS
-- ========================================

-- Inserir configurações padrão do bot
INSERT INTO bot_settings (guild_id, setting_key, setting_value) VALUES
(0, 'default_prefix', '"!"'),
(0, 'welcome_message', '"Bem-vindo ao Hawk Esports! 🦅"'),
(0, 'timezone', '"America/Sao_Paulo"'),
(0, 'checkin_enabled', 'true'),
(0, 'pubg_integration', 'true'),
(0, 'tournament_mode', 'false')
ON CONFLICT (guild_id, setting_key) DO NOTHING;

-- ========================================
-- VIEWS ÚTEIS
-- ========================================

-- View para ranking geral
CREATE OR REPLACE VIEW user_rankings AS
SELECT 
    u.discord_id,
    u.username,
    u.current_rank,
    u.season_points,
    u.total_matches,
    u.wins,
    u.kills,
    CASE 
        WHEN u.total_matches > 0 THEN ROUND((u.wins::DECIMAL / u.total_matches) * 100, 2)
        ELSE 0
    END as win_rate,
    CASE 
        WHEN u.total_matches > 0 THEN ROUND(u.kills::DECIMAL / u.total_matches, 2)
        ELSE 0
    END as avg_kills,
    ROW_NUMBER() OVER (ORDER BY u.season_points DESC) as position
FROM users u
WHERE u.is_active = true
ORDER BY u.season_points DESC;

-- View para estatísticas do servidor
CREATE OR REPLACE VIEW server_stats AS
SELECT 
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE is_active = true) as active_users,
    COUNT(*) FILTER (WHERE pubg_username IS NOT NULL) as pubg_linked_users,
    SUM(total_matches) as total_matches_played,
    SUM(kills) as total_kills,
    AVG(season_points) as avg_season_points
FROM users;

-- ========================================
-- FUNÇÕES ÚTEIS
-- ========================================

-- Função para limpar sessões expiradas
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions 
    WHERE status = 'active' 
    AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO audit_logs (action, details) 
    VALUES ('cleanup_expired_sessions', json_build_object('deleted_count', deleted_count));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- COMENTÁRIOS PARA DOCUMENTAÇÃO
-- ========================================

COMMENT ON TABLE users IS 'Tabela principal de usuários do Discord com dados do PUBG';
COMMENT ON TABLE bot_settings IS 'Configurações do bot por servidor';
COMMENT ON TABLE sessions IS 'Sessões ativas de usuários (check-ins, torneios, etc.)';
COMMENT ON TABLE rankings IS 'Rankings por temporada e tipo';
COMMENT ON TABLE audit_logs IS 'Logs de auditoria e ações do sistema';

COMMENT ON COLUMN users.discord_id IS 'ID único do usuário no Discord';
COMMENT ON COLUMN users.season_points IS 'Pontos da temporada atual';
COMMENT ON COLUMN users.badges IS 'Array JSON com badges conquistadas';
COMMENT ON COLUMN users.achievements IS 'Array JSON com conquistas';
COMMENT ON COLUMN users.settings IS 'Configurações personalizadas do usuário';

-- ========================================
-- FINALIZAÇÃO
-- ========================================

-- Atualizar estatísticas das tabelas
ANALYZE users;
ANALYZE bot_settings;
ANALYZE sessions;
ANALYZE rankings;
ANALYZE audit_logs;

-- Mensagem de sucesso
SELECT 'Hawk Esports Bot - Database setup completed successfully! 🦅' as status;