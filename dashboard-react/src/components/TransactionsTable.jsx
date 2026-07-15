import React from 'react';
import { ListOrdered, ArrowDownRight, ArrowUpRight, Clock } from 'lucide-react';

const formatarData = (isoStr) => {
  if (!isoStr) return '---';
  try {
    const data = new Date(isoStr);
    return data.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (e) {
    return isoStr;
  }
};

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor || 0);
};

export default function TransactionsTable({ transacoes }) {
  if (!transacoes || transacoes.length === 0) {
    return (
      <div className="glass-card table-section animate-fade-in">
        <div className="section-header">
          <h2 className="section-title">
            <ListOrdered size={20} color="#38bdf8" />
            <span>Extrato de Transações</span>
          </h2>
        </div>
        <div className="empty-state">
          <Clock size={48} opacity={0.3} />
          <p>Nenhuma transação registrada para este período.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card table-section animate-fade-in">
      <div className="section-header">
        <h2 className="section-title">
          <ListOrdered size={20} color="#38bdf8" />
          <span>Extrato de Transações Recentes</span>
        </h2>
      </div>

      <div className="compact-transactions-list">
        {transacoes.map((item) => {
          const isEntrada = item.tipo === 'entrada';
          return (
            <div key={item.id || Math.random()} className="compact-transaction-item">
              <div className="transaction-item-left">
                <div className="transaction-item-title">
                  <span className={`badge-tipo-compact ${isEntrada ? 'entrada' : 'gasto'}`}>
                    {isEntrada ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                  </span>
                  <strong className="transaction-desc">{item.descricao || '---'}</strong>
                </div>
                <div className="transaction-item-meta">
                  <span className="badge-categoria-compact">{item.categoria || 'Outros'}</span>
                  <span>•</span>
                  <span className="transaction-date">
                    <Clock size={12} style={{ display: 'inline', marginRight: '3px' }} />
                    {formatarData(item.created_at)}
                  </span>
                </div>
              </div>

              <div className="transaction-item-right">
                <span className={`col-valor ${isEntrada ? 'entrada' : 'gasto'}`}>
                  {isEntrada ? '+ ' : '- '}
                  {formatarMoeda(item.valor)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
