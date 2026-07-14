-- ====================================================================
-- SCRIPT SQL PARA CRIAÇÃO DAS TABELAS NO SUPABASE (PostgreSQL)
-- ====================================================================
-- REGRA CRÍTICA COMPRIDA:
-- Este script interage apenas com as tabelas do ecossistema financeiro
-- ('financas_transacoes' e 'financas_usuarios').
-- ====================================================================

-- 1. Criação da tabela financas_usuarios (Multi-tenant e Configurações de Período)
CREATE TABLE IF NOT EXISTS public.financas_usuarios (
    telefone VARCHAR(30) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL DEFAULT 'Usuário',
    plano VARCHAR(20) NOT NULL DEFAULT 'gratuito' CHECK (plano IN ('gratuito', 'premium', 'empresarial')),
    dia_inicio_mes INTEGER NOT NULL DEFAULT 1 CHECK (dia_inicio_mes BETWEEN 1 AND 31),
    dia_fechamento_cartao INTEGER NOT NULL DEFAULT 1 CHECK (dia_fechamento_cartao BETWEEN 1 AND 31),
    receber_alerta_automatico BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.financas_usuarios IS 'Tabela de perfis e configurações de período dos usuários do Porquinho WhatsApp';
COMMENT ON COLUMN public.financas_usuarios.telefone IS 'Número de WhatsApp (Chave Primária e identificador do tenant)';
COMMENT ON COLUMN public.financas_usuarios.nome IS 'Nome ou apelido do usuário para atendimento intimista';
COMMENT ON COLUMN public.financas_usuarios.plano IS 'Plano de assinatura: gratuito, premium ou empresarial';
COMMENT ON COLUMN public.financas_usuarios.dia_inicio_mes IS 'Dia do mês em que o período financeiro do usuário inicia e reinicia (1 a 31)';
COMMENT ON COLUMN public.financas_usuarios.dia_fechamento_cartao IS 'Dia de fechamento do cartão do usuário para envio de relatórios/alertas';
COMMENT ON COLUMN public.financas_usuarios.receber_alerta_automatico IS 'Se o usuário deseja receber o relatório automaticamente no WhatsApp no dia de fechamento';

ALTER TABLE public.financas_usuarios ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir acesso total à API Backend para usuarios" 
ON public.financas_usuarios 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- 2. Criação da tabela financas_transacoes
CREATE TABLE IF NOT EXISTS public.financas_transacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    telefone VARCHAR(30) NOT NULL DEFAULT 'desconhecido',
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'gasto')),
    valor NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    categoria VARCHAR(100) NOT NULL DEFAULT 'Geral',
    descricao TEXT NOT NULL
);

-- Caso a tabela já exista (atualização/migração multi-usuário), garante a adição da coluna telefone:
ALTER TABLE public.financas_transacoes ADD COLUMN IF NOT EXISTS telefone VARCHAR(30) NOT NULL DEFAULT 'desconhecido';

-- Comentários na tabela e colunas no catálogo do banco de dados
COMMENT ON TABLE public.financas_transacoes IS 'Tabela para armazenamento de transações financeiras multi-usuário (bot Porquinho WhatsApp)';
COMMENT ON COLUMN public.financas_transacoes.id IS 'Identificador único da transação (UUID)';
COMMENT ON COLUMN public.financas_transacoes.created_at IS 'Data e hora em que a transação foi registrada';
COMMENT ON COLUMN public.financas_transacoes.telefone IS 'Número de WhatsApp do usuário proprietário da transação';
COMMENT ON COLUMN public.financas_transacoes.tipo IS 'Tipo da transação: deve ser exatamente "entrada" ou "gasto"';
COMMENT ON COLUMN public.financas_transacoes.valor IS 'Valor monetário da transação';
COMMENT ON COLUMN public.financas_transacoes.categoria IS 'Categoria inferida da transação (ex: Almoço, Pix, Salário)';
COMMENT ON COLUMN public.financas_transacoes.descricao IS 'Descrição detalhada informada pelo usuário';

-- Criação de índices para otimizar as consultas de relatórios mensais por usuário e data
CREATE INDEX IF NOT EXISTS idx_financas_transacoes_created_at 
ON public.financas_transacoes (created_at);

CREATE INDEX IF NOT EXISTS idx_financas_transacoes_telefone_created_at 
ON public.financas_transacoes (telefone, created_at);

-- Habilitar Row Level Security (RLS) - Boa prática de segurança no Supabase
ALTER TABLE public.financas_transacoes ENABLE ROW LEVEL SECURITY;

-- Política para permitir que o Service Role / API Backend insira e consulte dados
CREATE POLICY "Permitir acesso total à API Backend" 
ON public.financas_transacoes 
FOR ALL 
USING (true) 
WITH CHECK (true);
