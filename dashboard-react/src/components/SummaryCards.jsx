import React from 'react';
import { TrendingUp, TrendingDown, Wallet } from 'lucide-react';

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor || 0);
};

export default function SummaryCards({ resumo }) {
  if (!resumo) return null;

  const { entradas = 0, gastos = 0, saldo = 0 } = resumo;

  return (
    <div className="cards-grid animate-fade-in">
      <div className="summary-card glass-card">
        <div className="card-header">
          <span className="card-title">Entradas no Período</span>
          <div className="card-icon emerald">
            <TrendingUp size={20} />
          </div>
        </div>
        <div className="card-value emerald">
          {formatarMoeda(entradas)}
        </div>
        <div className="card-footer">
          Receitas registradas pelo WhatsApp
        </div>
      </div>

      <div className="summary-card glass-card">
        <div className="card-header">
          <span className="card-title">Gastos no Período</span>
          <div className="card-icon rose">
            <TrendingDown size={20} />
          </div>
        </div>
        <div className="card-value rose">
          {formatarMoeda(gastos)}
        </div>
        <div className="card-footer">
          Despesas e saídas acumuladas
        </div>
      </div>

      <div className="summary-card glass-card">
        <div className="card-header">
          <span className="card-title">Saldo Atual do Mês</span>
          <div className="card-icon cyan">
            <Wallet size={20} />
          </div>
        </div>
        <div className="card-value cyan" style={{ color: saldo < 0 ? 'var(--rose)' : 'var(--cyan)' }}>
          {formatarMoeda(saldo)}
        </div>
        <div className="card-footer">
          Diferença entre entradas e gastos
        </div>
      </div>
    </div>
  );
}
