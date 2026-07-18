import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor || 0);
};

export default function SummaryCards({ resumo }) {
  if (!resumo) return null;

  const { entradas = 0, gastos = 0, saldo = 0 } = resumo;
  
  // Calcula porcentagem gasta em relação às entradas
  const percentualGasto = entradas > 0 
    ? Math.min(Math.round((gastos / entradas) * 100), 100) 
    : (gastos > 0 ? 100 : 0);
    
  const isPositivo = saldo >= 0;

  return (
    <div className="ref-budget-summary-card glass-card animate-fade-in">
      {/* Top 3 colunas inspiradas no print: Budgeted / Spent / Left */}
      <div className="ref-budget-cols">
        <div className="ref-budget-col">
          <span className="ref-budget-label">Entradas</span>
          <span className="ref-budget-val budgeted">{formatarMoeda(entradas)}</span>
        </div>

        <div className="ref-budget-col">
          <span className="ref-budget-label">Gastos</span>
          <span className="ref-budget-val spent">{formatarMoeda(gastos)}</span>
        </div>

        <div className="ref-budget-col">
          <span className="ref-budget-label">Saldo</span>
          <span className={`ref-budget-val left ${isPositivo ? 'positivo' : 'negativo'}`}>{formatarMoeda(saldo)}</span>
        </div>
      </div>

      {/* Barra de Progresso Horizontal (Budget Track Bar) */}
      <div className="ref-budget-progress-bg">
        <div 
          className={`ref-budget-progress-bar ${!isPositivo ? 'overflow' : ''}`}
          style={{ width: `${percentualGasto}%` }}
        />
      </div>

      {/* Status Footer com Check (✓ You are on track!) */}
      <div className={`ref-budget-status ${isPositivo ? 'on-track' : 'alert'}`}>
        {isPositivo ? (
          <>
            <CheckCircle2 size={16} className="status-icon" />
            <span>Saldo positivo e gastos dentro do orçamento!</span>
          </>
        ) : (
          <>
            <AlertTriangle size={16} className="status-icon" />
            <span>Atenção: seus gastos superaram as entradas neste período!</span>
          </>
        )}
      </div>
    </div>
  );
}

