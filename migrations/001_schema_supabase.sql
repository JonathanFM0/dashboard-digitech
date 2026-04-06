-- ============================================================
-- MANUAL DE INSTALAÇÃO - ESTÁGIO 1
-- Painel de Desempenho 360º - Digitech
-- ============================================================
-- 
-- OBJETIVO: Migrar do sistema baseado em arquivos Excel/Git
-- para um banco de dados PostgreSQL (Supabase) mantendo o
-- sistema ativo durante a transição.
--
-- ARQUITETURA "TROCAR A RODA DO CAMINHÃO ANDANDO":
-- 1. O sistema continua lendo arquivos locais como fallback
-- 2. Novo upload salva no Supabase E no Git (dupla escrita)
-- 3. Leitura prioriza Supabase, fallback para arquivos
-- 4. Migração gradual dos dados históricos
-- ============================================================

-- ============================================================
-- PASSO 1: CONFIGURAR SUPABASE (GRATUITO)
-- ============================================================
-- 1. Acesse https://supabase.com e crie conta gratuita
-- 2. Crie novo projeto: "Digitech-Painel"
-- 3. Aguarde provisionamento (~2 minutos)
-- 4. Vá em Settings > API e copie:
--    - Project URL (ex: https://xxxxx.supabase.co)
--    - anon/public key
--    - service_role key (para operações admin)
-- 5. Vá em SQL Editor e execute este script inteiro
-- ============================================================

-- ============================================================
-- TABELA: turmas
-- ============================================================
CREATE TABLE IF NOT EXISTS turmas (
    id SERIAL PRIMARY KEY,
    id_turma VARCHAR(50) UNIQUE NOT NULL,
    nome_turma VARCHAR(200) NOT NULL,
    turno VARCHAR(20),
    vagas_ocupadas INTEGER DEFAULT 0,
    mes_ano VARCHAR(7) NOT NULL, -- Formato: "2026-01"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_turmas_mes ON turmas(mes_ano);
CREATE INDEX idx_turmas_id ON turmas(id_turma);

-- ============================================================
-- TABELA: ocupacao
-- ============================================================
CREATE TABLE IF NOT EXISTS ocupacao (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    ambiente VARCHAR(200) NOT NULL,
    percentual_ocupacao DECIMAL(5,2),
    turno VARCHAR(20),
    mes_ano VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ocupacao_data ON ocupacao(data);
CREATE INDEX idx_ocupacao_ambiente ON ocupacao(ambiente);
CREATE INDEX idx_ocupacao_mes ON ocupacao(mes_ano);

-- ============================================================
-- TABELA: nao_regencia
-- ============================================================
CREATE TABLE IF NOT EXISTS nao_regencia (
    id SERIAL PRIMARY KEY,
    id_instrutor VARCHAR(50),
    instrutor VARCHAR(200) NOT NULL,
    data_inicio DATE,
    data_fim DATE,
    horas_nao_regencia DECIMAL(10,2) DEFAULT 0,
    tipo_atividade VARCHAR(100),
    mes_ano VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_nao_regencia_instrutor ON nao_regencia(instrutor);
CREATE INDEX idx_nao_regencia_datas ON nao_regencia(data_inicio, data_fim);
CREATE INDEX idx_nao_regencia_mes ON nao_regencia(mes_ano);

-- ============================================================
-- TABELA: instrutores
-- ============================================================
CREATE TABLE IF NOT EXISTS instrutores (
    id SERIAL PRIMARY KEY,
    id_instrutor VARCHAR(50) UNIQUE,
    nome_completo VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instrutores_nome ON instrutores(nome_completo);

-- ============================================================
-- TABELA: disciplinas
-- ============================================================
CREATE TABLE IF NOT EXISTS disciplinas (
    id SERIAL PRIMARY KEY,
    id_turma VARCHAR(50) NOT NULL,
    nome_disciplina VARCHAR(200) NOT NULL,
    carga_horaria DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'NÃO INICIADO',
    mes_ano VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_disciplinas_turma FOREIGN KEY (id_turma) 
        REFERENCES turmas(id_turma) ON DELETE CASCADE
);

CREATE INDEX idx_disciplinas_turma ON disciplinas(id_turma);
CREATE INDEX idx_disciplinas_status ON disciplinas(status);
CREATE INDEX idx_disciplinas_mes ON disciplinas(mes_ano);

-- ============================================================
-- TABELA: ambientes
-- ============================================================
CREATE TABLE IF NOT EXISTS ambientes (
    id SERIAL PRIMARY KEY,
    nome_ambiente VARCHAR(200) UNIQUE NOT NULL,
    tipo VARCHAR(50),
    virtual BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ambientes_nome ON ambientes(nome_ambiente);

-- ============================================================
-- TABELA: faltas
-- ============================================================
CREATE TABLE IF NOT EXISTS faltas (
    id SERIAL PRIMARY KEY,
    data_falta DATE NOT NULL,
    instrutor VARCHAR(200) NOT NULL,
    motivo TEXT,
    mes_ano VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_faltas_data ON faltas(data_falta);
CREATE INDEX idx_faltas_instrutor ON faltas(instrutor);
CREATE INDEX idx_faltas_mes ON faltas(mes_ano);

-- ============================================================
-- TABELA: parametros
-- ============================================================
CREATE TABLE IF NOT EXISTS parametros (
    id SERIAL PRIMARY KEY,
    parametro VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELA: calendario (NOVA - para agenda de eventos)
-- ============================================================
CREATE TABLE IF NOT EXISTS calendario (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    tipo_dia VARCHAR(50) NOT NULL, -- Feriado, Recesso, Evento, Visita, Reunião
    descricao TEXT,
    mes_ano VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_calendario_data ON calendario(data);
CREATE INDEX idx_calendario_tipo ON calendario(tipo_dia);
CREATE INDEX idx_calendario_mes ON calendario(mes_ano);

-- ============================================================
-- TABELA: metas_ha (para metas manuais de Hora-Aluno)
-- ============================================================
CREATE TABLE IF NOT EXISTS metas_ha (
    id SERIAL PRIMARY KEY,
    turma_id VARCHAR(50), -- NULL = meta global
    meta_manual DECIMAL(15,2),
    mes_ano VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(turma_id, mes_ano)
);

CREATE INDEX idx_metas_ha_turma ON metas_ha(turma_id);
CREATE INDEX idx_metas_ha_mes ON metas_ha(mes_ano);

-- ============================================================
-- TABELA: auditoria_upload (LOG de quem subiu o quê)
-- ============================================================
CREATE TABLE IF NOT EXISTS auditoria_upload (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(100),
    nome_arquivo VARCHAR(255),
    mes_ano VARCHAR(7),
    registros_inseridos INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'SUCESSO', -- SUCESSO, PARCIAL, ERRO
    erro_mensagem TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_auditoria_usuario ON auditoria_upload(usuario);
CREATE INDEX idx_auditoria_data ON auditoria_upload(created_at);

-- ============================================================
-- FUNÇÃO: Atualizar updated_at automaticamente
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger nas tabelas com updated_at
CREATE TRIGGER update_turmas_updated_at BEFORE UPDATE ON turmas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_metas_ha_updated_at BEFORE UPDATE ON metas_ha
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parametros_updated_at BEFORE UPDATE ON parametros
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- DADOS INICIAIS: Parâmetros padrão
-- ============================================================
INSERT INTO parametros (parametro, valor) VALUES
    ('versao_sistema', '2.0.0-banco'),
    ('data_migracao', NOW()::text),
    ('modo_operacao', 'hibrido') -- híbrido = usa DB + fallback arquivos
ON CONFLICT (parametro) DO NOTHING;

-- ============================================================
-- VISÃO: Consolidado mensal para consultas rápidas
-- ============================================================
CREATE OR REPLACE VIEW vw_consolidado_mensal AS
SELECT 
    o.mes_ano,
    COUNT(DISTINCT o.ambiente) as qtd_ambientes,
    AVG(o.percentual_ocupacao) as ocupacao_media,
    COUNT(DISTINCT t.id_turma) as qtd_turmas,
    SUM(t.vagas_ocupadas) as total_alunos,
    COUNT(DISTINCT nr.instrutor) as qtd_instrutores_ativos,
    SUM(nr.horas_nao_regencia) as total_horas_nao_regencia,
    COUNT(f.id) as qtd_faltas
FROM ocupacao o
LEFT JOIN turmas t ON o.mes_ano = t.mes_ano
LEFT JOIN nao_regencia nr ON o.mes_ano = nr.mes_ano
LEFT JOIN faltas f ON o.mes_ano = f.mes_ano
GROUP BY o.mes_ano
ORDER BY o.mes_ano DESC;

-- ============================================================
-- FIM DO SCRIPT DE BANCO DE DADOS
-- ============================================================
-- PRÓXIMOS PASSOS:
-- 1. Execute este script no SQL Editor do Supabase
-- 2. Copie as credenciais para .streamlit/secrets.toml
-- 3. Execute migrate.py para migrar dados históricos
-- 4. O app.py já está preparado para modo híbrido
-- ============================================================
