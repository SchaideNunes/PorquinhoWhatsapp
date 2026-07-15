import React from 'react';
import { 
  ListOrdered, ArrowDownRight, ArrowUpRight, Clock, 
  Utensils, Dumbbell, Car, ShoppingBag, DollarSign, Home, Zap, HeartPulse, Sparkles 
} from 'lucide-react';

const formatarData = (isoStr) => {
  if (!isoStr) return '---';
  try {
    const data = new Date(isoStr);
    return data.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
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

// Escolhe um ícone elegante de acordo com o nome da categoria
const getCategoryIcon = (categoria, isEntrada) => {
  if (isEntrada) return <DollarSign size={20} />;
  const catLower = (categoria || '').toLowerCase();
  if (catLower.includes('almoço') || catLower.includes('jantar') || catLower.includes('comida') || catLower.includes('restaurante')) {
    return <Utensils size={19} />;
  }
  if (catLower.includes('academia') || catLower.includes('treino') || catLower.includes('esporte')) {
    return <Dumbbell size={19} />;
  }
  if (catLower.includes('gasolina') || catLower.includes('carro') || catLower.includes('uber') || catLower.includes('transporte')) {
    return <Car size={19} />;
  }
  if (catLower.includes('mercado') || catLower.includes('compras') || catLower.includes('loja')) {
    return <ShoppingBag size={19} />;
  }
  if (catLower.includes('casa') || catLower.includes('aluguel') || catLower.includes('luz') || catLower.includes('água')) {
    return <Home size={19} />;
  }
  if (catLower.includes('saúde') || catLower.includes('médico') || catLower.includes('farmácia')) {
    return <HeartPulse size={19} />;
  }
  return <Sparkles size={19} />;
};

const formatarTextoCapitalizado = (str) => {
  if (!str) return '---';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export default function TransactionsTable({ transacoes }) {
  if (!transacoes || transacoes.length === 0) {
    return (
      <div className="glass-card table-section animate-fade-in">
        <div className="ref-tx-header">
          <h2 className="ref-tx-main-title">Últimas Transações</h2>
        </div>
        <div className="empty-state">
          <Clock size={48} opacity={0.3} />
          <p>Nenhuma transação registrada para este período.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card table-section animate-fade-in" style={{ padding: '1.5rem 1.75rem' }}>
      <div className="ref-tx-header">
        <h2 className="ref-tx-main-title">Últimas Transações</h2>
        <span className="ref-tx-showall">Ver todas ({transacoes.length}) ›</span>
      </div>

      <div className="ref-tx-list-rows">
        {transacoes.map((item, index) => {
          const isEntrada = item.tipo === 'entrada';
          const tituloPrincipal = item.descricao ? formatarTextoCapitalizado(item.descricao) : (item.categoria || 'Transação');
          const subtitulo = item.categoria ? formatarTextoCapitalizado(item.categoria) : 'Geral';

          return (
            <div key={item.id || index} className="ref-tx-row">
              <div className="ref-tx-row-left">
                <div className={`ref-tx-avatar ${isEntrada ? 'entrada' : 'gasto'}`}>
                  {getCategoryIcon(item.categoria, isEntrada)}
                </div>
                <div className="ref-tx-info">
                  <span className="ref-tx-title">{tituloPrincipal}</span>
                  <span className="ref-tx-subtitle">{subtitulo}</span>
                </div>
              </div>

              <div className="ref-tx-row-right">
                <span className={`col-valor ${isEntrada ? 'entrada' : 'gasto'}`}>
                  {isEntrada ? '+ ' : '- '}
                  {formatarMoeda(item.valor)}
                </span>
                <span className="ref-tx-account-label">
                  {isEntrada ? 'Entrada' : 'Gasto'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
