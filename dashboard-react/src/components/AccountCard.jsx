import React from 'react';
import { User, Phone, Calendar, Shield, LogOut, HelpCircle, ArrowRight } from 'lucide-react';

export default function AccountCard({ usuario, telefone, onReset }) {
  if (!usuario) return null;

  return (
    <div className="ref-account-container animate-fade-in">
      <div className="ref-account-card">
        <div className="ref-account-header">
          <div className="ref-account-avatar-large">
            <span>{usuario.nome ? usuario.nome.substring(0, 2).toUpperCase() : 'PQ'}</span>
          </div>
          <div className="ref-account-info">
            <h2>{usuario.nome || 'Usuário Porquinho'}</h2>
            <span className="ref-account-phone"><Phone size={14} /> {telefone || 'Não informado'}</span>
          </div>
          <span className="ref-account-badge"><Shield size={13} /> {usuario.plano || 'Gratuito'}</span>
        </div>

        <div className="ref-account-grid">
          <div className="ref-account-stat">
            <span className="stat-label">Início do Período</span>
            <span className="stat-val"><Calendar size={16} /> Dia {usuario.dia_inicio_mes || 1} do mês</span>
          </div>
          <div className="ref-account-stat">
            <span className="stat-label">Status do Cérebro</span>
            <span className="stat-val status-online">● Online e Conectado</span>
          </div>
        </div>

        <div className="ref-account-actions">
          <button onClick={onReset} className="ref-account-action-btn logout">
            <LogOut size={18} />
            <div>
              <strong>Trocar Número Consultado</strong>
              <span>Sair desta consulta e digitar outro WhatsApp</span>
            </div>
            <ArrowRight size={18} className="arrow" />
          </button>

          <a 
            href={`https://wa.me/${telefone ? telefone.replace(/\D/g, '') : ''}?text=ajuda`} 
            target="_blank" 
            rel="noreferrer"
            className="ref-account-action-btn help"
          >
            <HelpCircle size={18} />
            <div>
              <strong>Solicitar Ajuda no WhatsApp</strong>
              <span>Ver todos os comandos disponíveis no Cérebro</span>
            </div>
            <ArrowRight size={18} className="arrow" />
          </a>
        </div>
      </div>
    </div>
  );
}
