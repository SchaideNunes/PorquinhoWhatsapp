import React from 'react';
import { TrendingUp, TrendingDown, Wallet, Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react';

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor || 0);
};

export default function SummaryCards({ resumo }) {
  if (!resumo) return null;

  const { entradas = 0, gastos = 0, saldo = 0 } = resumo;
  const isPositivo = saldo >= 0;

  return (
    <div className="ref-summary-container animate-fade-in">
      {/* Hero Card - Saldo Disponível (Estilo My Budget) */}
      <div className="ref-hero-balance glass-card">
        <div className="ref-hero-top">
          <div className="ref-hero-label">
            <Wallet size={18} color="#38bdf8" />
            <span>Saldo Atual do Mês</span>
          </div>
          <div className={`ref-hero-pill ${isPositivo ? 'positivo' : 'negativo'}`}>
            {isPositivo ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
            <span>{isPositivo ? 'Saldo positivo' : 'Atenção aos gastos'}</span>
          </div>
        </div>
        <div className="ref-hero-value" style={{ color: isPositivo ? '#f8fafc' : 'var(--rose)' }}>
          {formatarMoeda(saldo)}
        </div>
        <p className="ref-hero-hint">
          Balanço geral em tempo real calculado diretamente das suas mensagens no WhatsApp
        </p>
      </div>

      {/* Sub Cards - Entradas e Gastos */}
      <div className="ref-subcards-grid">
        <div className="summary-card glass-card">
          <div className="card-header">
            <span className="card-title">Entradas (Receitas)</span>
            <div className="card-icon emerald">
              <TrendingUp size={20} />
            </div>
          </div>
          <div className="card-value emerald">
            {formatarMoeda(entradas)}
          </div>
          <div className="card-footer">
            Total recebido e registrado no período
          </div>
        </div>

        <div className="summary-card glass-card">
          <div className="card-header">
            <span className="card-title">Gastos (Despesas)</span>
            <div className="card-icon rose">
              <TrendingDown size={20} />
            </div>
          </div>
          <div className="card-value rose">
            {formatarMoeda(gastos)}
          </div>
          <div className="card-footer">
            Total gasto e categorizado
          </div>
        </div>
      </div>
    </div>
  );
}
