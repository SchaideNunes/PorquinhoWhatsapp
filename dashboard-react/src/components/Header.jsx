import React, { useState, useEffect } from 'react';
import { Phone, Search, LogOut, ChevronLeft, ChevronRight, User } from 'lucide-react';

const getInitials = (nome) => {
  if (!nome) return 'U';
  const partes = nome.trim().split(' ');
  if (partes.length === 1) return partes[0].substring(0, 2).toUpperCase();
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
};

export default function Header({ telefoneAtual, onSearch, usuario, onReset }) {
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
        {!usuario ? (
          <>
            <div className="brand">
              <div className="ref-user-avatar default">
                <User size={22} color="#ffffff" />
              </div>
              <div>
                <h1 className="brand-title">Minhas Finanças</h1>
                <span className="ref-header-sub">Digite seu WhatsApp para acessar</span>
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
          </>
        ) : (
          <div className="ref-header-container">
            {/* Esquerda: Foto/Avatar + Minhas Finanças e Subtítulo */}
            <div className="ref-header-left">
              <div className="ref-user-avatar">
                <span>{getInitials(usuario.nome)}</span>
              </div>
              <div className="ref-header-titles">
                <h1 className="ref-header-maintitle">Minhas Finanças</h1>
                <span className="ref-header-sub">{usuario.nome}</span>
              </div>
            </div>

            {/* Direita: Pílula de Período (< Mês >) + Botão de Trocar */}
            <div className="ref-header-right">
              <div className="ref-period-pill">
                <ChevronLeft size={16} className="ref-arrow" />
                <span>{usuario.periodo?.mes_referencia || 'Mês Atual'}</span>
                <ChevronRight size={16} className="ref-arrow" />
              </div>

              <button onClick={onReset} className="reset-btn" title="Consultar outro número">
                <LogOut size={15} />
                <span>Trocar</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
