-- ====================================================================
-- SCRIPT SQL PARA CRIAÇÃO DA TABELA NO SUPABASE (PostgreSQL)
-- ====================================================================
-- REGRA CRÍTICA COMPIDA:
-- Este script NÃO interage, deleta, lê ou modifica as tabelas
-- existentes ('agendamentos' e 'barbeiros_config').
-- Ele cria APENAS a nova tabela 'financas_transacoes'.
-- ====================================================================

-- Criação da tabela financas_transacoes
CREATE TABLE IF NOT EXISTS public.financas_transacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'gasto')),
    valor NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    categoria VARCHAR(100) NOT NULL DEFAULT 'Geral',
    descricao TEXT NOT NULL
);

-- Comentários na tabela e colunas no catálogo do banco de dados
COMMENT ON TABLE public.financas_transacoes IS 'Tabela para armazenamento de transações financeiras (bot Porquinho WhatsApp)';
COMMENT ON COLUMN public.financas_transacoes.id IS 'Identificador único da transação (UUID)';
COMMENT ON COLUMN public.financas_transacoes.created_at IS 'Data e hora em que a transação foi registrada';
COMMENT ON COLUMN public.financas_transacoes.tipo IS 'Tipo da transação: deve ser exatamente "entrada" ou "gasto"';
COMMENT ON COLUMN public.financas_transacoes.valor IS 'Valor monetário da transação';
COMMENT ON COLUMN public.financas_transacoes.categoria IS 'Categoria inferida da transação (ex: Almoço, Pix, Salário)';
COMMENT ON COLUMN public.financas_transacoes.descricao IS 'Descrição detalhada informada pelo usuário';

-- Criação de índice para otimizar as consultas de relatórios mensais por data
CREATE INDEX IF NOT EXISTS idx_financas_transacoes_created_at 
ON public.financas_transacoes (created_at);

-- Habilitar Row Level Security (RLS) - Boa prática de segurança no Supabase
ALTER TABLE public.financas_transacoes ENABLE ROW LEVEL SECURITY;

-- Política para permitir que o Service Role / API Backend insira e consulte dados
CREATE POLICY "Permitir acesso total à API Backend" 
ON public.financas_transacoes 
FOR ALL 
USING (true) 
WITH CHECK (true);
