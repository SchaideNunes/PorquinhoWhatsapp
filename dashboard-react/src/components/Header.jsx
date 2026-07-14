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

        <form onSubmit={handleSubmit} className="phone-search-form">
          <div className="phone-input-wrapper">
            <Phone size={16} className="phone-input-icon" />
            <input
              type="text"
              placeholder="Ex: 75 991503949"
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
