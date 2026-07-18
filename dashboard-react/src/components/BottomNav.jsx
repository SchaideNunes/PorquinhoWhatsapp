import React, { useState } from 'react';
import { Activity, Wallet, Receipt, User, Plus, X, ArrowRight, Copy, Check, MessageCircle, DollarSign, Tag, Database, Loader2 } from 'lucide-react';

export default function BottomNav({ activeTab, onTabChange, usuario, telefone, onRefreshDashboard }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tipoLancamento, setTipoLancamento] = useState('gasto'); // 'gasto' ou 'entrada'
  const [valorInput, setValorInput] = useState('');
  const [descricaoInput, setDescricaoInput] = useState('');
  const [copied, setCopied] = useState(false);
  const [savingDb, setSavingDb] = useState(false);
  const [saveStatus, setSaveStatus] = useState({ type: '', msg: '' });

  // Limpa apenas números do telefone do bot (ou usa fallback padrão)
  const numeroBot = telefone ? telefone.replace(/\D/g, '') : '';
  
  // Gera comando natural em texto que o Cérebro Python reconhece perfeitamente
  const comandoGerado = `${tipoLancamento} ${valorInput || '50'} ${descricaoInput || (tipoLancamento === 'gasto' ? 'mercado' : 'salário')}`.trim();

  const handleOpenWhatsApp = () => {
    // Se tiver telefone cadastrado/consultado, tenta abrir link wa.me direto ou apenas copia
    const urlWa = `https://wa.me/${numeroBot}?text=${encodeURIComponent(comandoGerado)}`;
    if (numeroBot) {
      window.open(urlWa, '_blank');
    } else {
      handleCopy();
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(comandoGerado);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSaveDirectToDb = async () => {
    if (!valorInput || !telefone) {
      setSaveStatus({ type: 'error', msg: 'Informe um valor e certifique-se de ter um telefone consultado.' });
      return;
    }
    setSavingDb(true);
    setSaveStatus({ type: '', msg: '' });

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const resp = await fetch(`${API_BASE_URL}/api/transacao`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telefone: numeroBot || telefone,
          tipo: tipoLancamento,
          valor: valorInput,
          categoria: descricaoInput || (tipoLancamento === 'gasto' ? 'Gasto Web' : 'Entrada Web'),
          descricao: descricaoInput || (tipoLancamento === 'gasto' ? 'Gasto via Dashboard' : 'Entrada via Dashboard')
        })
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || data.message || 'Erro ao registrar transação no banco.');
      }

      setSaveStatus({ type: 'success', msg: data.message || 'Lançamento registrado com segurança!' });
      setValorInput('');
      setDescricaoInput('');
      
      // Atualiza o dashboard em tempo real após salvar
      if (onRefreshDashboard) {
        setTimeout(() => {
          onRefreshDashboard();
          setIsModalOpen(false);
          setSaveStatus({ type: '', msg: '' });
        }, 1600);
      }
    } catch (err) {
      console.error('Erro no salvamento web:', err);
      setSaveStatus({ type: 'error', msg: err.message || 'Não foi possível conectar ao Cérebro Python.' });
    } finally {
      setSavingDb(false);
    }
  };

  return (
    <>
      {/* Barra de Navegação Inferior (Inspirada no print: Activity, Budget, [+] FAB, Transactions, Accounts) */}
      <nav className="ref-bottom-nav">
        <div className="ref-nav-container">
          {/* Aba 1: Atividade (Resumo Geral) */}
          <button 
            onClick={() => onTabChange('resumo')} 
            className={`ref-nav-item ${activeTab === 'resumo' ? 'active' : ''}`}
          >
            <Activity size={20} className="nav-icon" />
            <span>Atividade</span>
          </button>

          {/* Aba 2: Orçamento / Gráficos */}
          <button 
            onClick={() => onTabChange('graficos')} 
            className={`ref-nav-item ${activeTab === 'graficos' ? 'active' : ''}`}
          >
            <Wallet size={20} className="nav-icon" />
            <span>Orçamento</span>
          </button>

          {/* Botão Central Flutuante: [+] Novo Lançamento */}
          <div className="ref-nav-fab-wrapper">
            <button 
              onClick={() => { setIsModalOpen(true); setSaveStatus({ type: '', msg: '' }); }} 
              className="ref-nav-fab"
              title="Novo Lançamento Rápido"
            >
              <Plus size={26} color="#ffffff" strokeWidth={2.8} />
            </button>
          </div>

          {/* Aba 3: Transações / Extrato */}
          <button 
            onClick={() => onTabChange('extrato')} 
            className={`ref-nav-item ${activeTab === 'extrato' ? 'active' : ''}`}
          >
            <Receipt size={20} className="nav-icon" />
            <span>Transações</span>
          </button>

          {/* Aba 4: Conta / Perfil */}
          <button 
            onClick={() => onTabChange('conta')} 
            className={`ref-nav-item ${activeTab === 'conta' ? 'active' : ''}`}
          >
            <User size={20} className="nav-icon" />
            <span>Conta</span>
          </button>
        </div>
      </nav>

      {/* Modal de Novo Lançamento Rápido no WhatsApp */}
      {isModalOpen && (
        <div className="ref-modal-overlay animate-fade-in" onClick={() => setIsModalOpen(false)}>
          <div className="ref-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="ref-modal-header">
              <div className="ref-modal-title">
                <Plus size={20} className="ref-modal-icon" />
                <span>Novo Lançamento Rápido</span>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="ref-modal-close">
                <X size={20} />
              </button>
            </div>

            <p className="ref-modal-desc">
              Escolha abaixo como deseja registrar: salve <strong>diretamente e em segurança no banco relacional</strong> com 1 clique, ou envie pela conversa do WhatsApp!
            </p>

            {saveStatus.msg && (
              <div className={`modal-alert ${saveStatus.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                <span>{saveStatus.msg}</span>
              </div>
            )}

            <div className="ref-modal-type-selector">
              <button
                type="button"
                onClick={() => setTipoLancamento('gasto')}
                className={`type-btn gasto ${tipoLancamento === 'gasto' ? 'active' : ''}`}
              >
                <span>💸 Gasto (Saída)</span>
              </button>
              <button
                type="button"
                onClick={() => setTipoLancamento('entrada')}
                className={`type-btn entrada ${tipoLancamento === 'entrada' ? 'active' : ''}`}
              >
                <span>💰 Receita (Entrada)</span>
              </button>
            </div>

            <div className="ref-modal-form">
              <div className="form-group">
                <label><DollarSign size={15} /> Valor do Lançamento (R$)</label>
                <input
                  type="text"
                  placeholder="Ex: 45,90"
                  value={valorInput}
                  onChange={(e) => setValorInput(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label><Tag size={15} /> Categoria ou Descrição</label>
                <input
                  type="text"
                  placeholder={tipoLancamento === 'gasto' ? 'Ex: Almoço no restaurante, Supermercado...' : 'Ex: Pix do cliente, Salário, Freelance...'}
                  value={descricaoInput}
                  onChange={(e) => setDescricaoInput(e.target.value)}
                />
              </div>
            </div>

            <div className="ref-modal-preview">
              <span className="preview-label">Comando Gerado para o WhatsApp:</span>
              <div className="preview-box">
                <code>{comandoGerado}</code>
                <button onClick={handleCopy} className="preview-copy-btn" title="Copiar comando">
                  {copied ? <Check size={16} color="#34d399" /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            <div className="ref-modal-actions">
              <button 
                onClick={handleSaveDirectToDb} 
                className="db-save-btn"
                disabled={savingDb}
              >
                {savingDb ? <Loader2 size={18} className="spinner-inline" /> : <Database size={18} />}
                <span>{savingDb ? 'Salvando no Banco...' : '🚀 Salvar Direto no Banco (Web)'}</span>
              </button>

              <button onClick={handleOpenWhatsApp} className="wa-send-btn">
                <MessageCircle size={18} />
                <span>{numeroBot ? '💬 Enviar pelo WhatsApp' : 'Copiar Comando'}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
