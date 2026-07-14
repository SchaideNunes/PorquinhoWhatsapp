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
          <p>Nenhuma transação registrada para este período no Supabase.</p>
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

      <div className="table-responsive">
        <table className="transactions-table">
          <thead>
            <tr>
              <th>Data / Hora</th>
              <th>Tipo</th>
              <th>Categoria</th>
              <th>Descrição</th>
              <th style={{ textAlign: 'right' }}>Valor</th>
            </tr>
          </thead>
          <tbody>
            {transacoes.map((item) => {
              const isEntrada = item.tipo === 'entrada';
              return (
                <tr key={item.id || Math.random()}>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)' }}>
                      <Clock size={14} />
                      {formatarData(item.created_at)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge-tipo ${isEntrada ? 'entrada' : 'gasto'}`}>
                      {isEntrada ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      {isEntrada ? 'Entrada' : 'Gasto'}
                    </span>
                  </td>
                  <td>
                    <span className="badge-categoria">{item.categoria || 'Outros'}</span>
                  </td>
                  <td style={{ color: 'var(--text-primary)', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.descricao || '---'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`col-valor ${isEntrada ? 'entrada' : 'gasto'}`}>
                      {isEntrada ? '+ ' : '- '}
                      {formatarMoeda(item.valor)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
