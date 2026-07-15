import React, { useState, useEffect } from 'react';
import { Phone, Search, LogOut } from 'lucide-react';

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
        <div className="brand">
          <div>
            <h1 className="brand-title">
              Minhas Finanças
              {usuario && (
                <span className="header-username">
                  {' • '}
                  <strong style={{ color: '#38bdf8', fontWeight: 600 }}>{usuario.nome}</strong>
                </span>
              )}
            </h1>
          </div>
        </div>

        {!usuario ? (
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
        ) : (
          <div className="header-actions">
            <button onClick={onReset} className="reset-btn" title="Consultar outro número">
              <LogOut size={15} />
              <span>Trocar número</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
