import React, { useState, useEffect } from 'react';
import { PiggyBank, Phone, Search, Calendar, User } from 'lucide-react';

export default function Header({ telefoneAtual, onSearch, usuario }) {
  const [inputVal, setInputVal] = useState(telefoneAtual || '');

  useEffect(() => {
    setInputVal(telefoneAtual || '');
  }, [telefoneAtual]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputVal.trim()) {
      onSearch(inputVal.trim());
    }
  };

  const getEspelhoNumero = (val) => {
    const limpo = val.replace(/\D/g, '');
    if (!limpo) {
      return {
        texto: 'Digite DDD + número (ex: 75 99999-9999)',
        status: 'dica'
      };
    }

    let numeroCompleto = limpo;
    if ((limpo.length === 10 || limpo.length === 11) && !limpo.startsWith('55')) {
      numeroCompleto = '55' + limpo;
    }

    if (numeroCompleto.startsWith('55') && numeroCompleto.length >= 4) {
      const ddd = numeroCompleto.slice(2, 4);
      const resto = numeroCompleto.slice(4);
      let formatado = `+55 (${ddd})`;
      if (resto.length > 5) {
        formatado += ` ${resto.slice(0, resto.length - 4)}-${resto.slice(resto.length - 4)}`;
      } else if (resto.length > 0) {
        formatado += ` ${resto}`;
      }
      return {
        texto: formatado,
        status: (numeroCompleto.length === 12 || numeroCompleto.length === 13) ? 'valido' : 'digitando'
      };
    }

    return {
      texto: limpo,
      status: 'digitando'
    };
  };

  const espelho = getEspelhoNumero(inputVal);

  return (
    <header className="header-wrapper animate-fade-in">
      <div className="header-top">
        <div className="brand">
          <div className="brand-icon">
            <PiggyBank size={26} color="#ffffff" />
          </div>
          <div>
            <h1 className="brand-title">Porquinho WhatsApp</h1>
            <p className="brand-subtitle">Dashboard Financeiro e Gestão em Nuvem</p>
          </div>
        </div>

        <div className="header-search-container">
          <form onSubmit={handleSubmit} className="phone-search-form">
            <div className="phone-input-wrapper">
              <Phone size={16} className="phone-input-icon" />
              <input
                type="text"
                placeholder="DDD + Número (ex: 75 99999-9999 ou 5575...)"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                className="phone-input"
              />
            </div>
            <button type="submit" className="search-btn">
              <Search size={16} />
              <span>Consultar</span>
            </button>
          </form>

          <div className="phone-mirror-box animate-fade-in">
            <span className="phone-mirror-title">
              {espelho.status === 'valido' ? '🟢 Espelho no Banco:' : '💡 Espelho do Número:'}
            </span>
            <span className={`phone-mirror-badge ${espelho.status}`}>
              {espelho.texto}
            </span>
            {espelho.status === 'dica' && (
              <span className="phone-mirror-hint">
                Pode digitar direto a partir do <strong>DDD 75</strong> ou com <strong>55</strong> (o sistema reconhece ambos!)
              </span>
            )}
            {espelho.status === 'valido' && !inputVal.replace(/\D/g, '').startsWith('55') && (
              <span className="phone-mirror-hint valid">
                ✓ Preenchemos o DDI <strong>+55</strong> automaticamente para buscar no Supabase
              </span>
            )}
          </div>
        </div>
      </div>

      {usuario && (
        <div className="user-info-bar animate-fade-in">
          <div className="user-welcome">
            <User size={18} color="#38bdf8" />
            <span>Olá, <strong>{usuario.nome}</strong></span>
            <span className="user-badge">{usuario.plano}</span>
          </div>
          <div className="user-period">
            <Calendar size={16} color="#94a3b8" />
            <span>
              Mês de Referência: <strong>{usuario.periodo?.mes_referencia}</strong> (Fechamento dia {usuario.dia_inicio_mes})
            </span>
          </div>
        </div>
      )}
    </header>
  );
}
