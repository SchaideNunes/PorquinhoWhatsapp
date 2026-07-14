import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SummaryCards from './components/SummaryCards';
import CategoryChart from './components/CategoryChart';
import TransactionsTable from './components/TransactionsTable';
import { AlertCircle, PiggyBank } from 'lucide-react';
import './App.css';

export default function App() {
  const [telefone, setTelefone] = useState('');
  const [dados, setDados] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Obtém a URL da API (suporta VITE_API_URL no ambiente Vercel ou localhost no dev)
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchDadosDashboard = async (numTelefone) => {
    if (!numTelefone) return;
    setLoading(true);
    setErrorMsg('');
    setDados(null);

    try {
      // Formata apenas números do telefone na consulta
      let numeroLimpo = numTelefone.replace(/\D/g, '');
      // Se o usuário digitou 10 ou 11 dígitos sem o DDI 55 no início (ex: DDD 75 + número), adiciona 55 automaticamente
      if ((numeroLimpo.length === 10 || numeroLimpo.length === 11) && !numeroLimpo.startsWith('55')) {
        numeroLimpo = '55' + numeroLimpo;
      }
      const resp = await fetch(`${API_BASE_URL}/api/dashboard?telefone=${numeroLimpo}`);
      
      if (!resp.ok) {
        throw new Error(`Erro na resposta do servidor: HTTP ${resp.status}`);
      }

      const json = await resp.json();

      if (json.status === 'not_found') {
        setErrorMsg(json.message || 'Número não cadastrado. Envie uma mensagem para o Porquinho no WhatsApp!');
      } else if (json.status === 'success') {
        setDados(json);
        // Atualiza a URL sem recarregar a página para facilidade de compartilhamento
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('telefone', numeroLimpo);
        window.history.pushState({}, '', newUrl);
      } else {
        setErrorMsg(json.message || 'Erro ao consultar os dados do dashboard.');
      }
    } catch (err) {
      console.error('Erro ao buscar dados:', err);
      setErrorMsg('Não foi possível conectar ao servidor backend. Verifique se o FastAPI está rodando ou se a URL da Vercel está apontando para a nuvem.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Verifica se já existe um telefone na URL (ex: /?telefone=5511999999999)
    const params = new URLSearchParams(window.location.search);
    const telParam = params.get('telefone');
    if (telParam) {
      setTelefone(telParam);
      fetchDadosDashboard(telParam);
    }
  }, []);

  const handleSearch = (numInput) => {
    setTelefone(numInput);
    fetchDadosDashboard(numInput);
  };

  return (
    <div className="app-container">
      <Header
        telefoneAtual={telefone}
        onSearch={handleSearch}
        usuario={dados?.usuario}
      />

      {errorMsg && (
        <div className="error-banner animate-fade-in">
          <AlertCircle size={22} color="#f43f5e" />
          <span>{errorMsg}</span>
        </div>
      )}

      {loading && (
        <div className="loading-container animate-fade-in">
          <div className="spinner"></div>
          <p>Buscando suas transações no Supabase em tempo real...</p>
        </div>
      )}

      {!loading && !dados && !errorMsg && (
        <div className="glass-card loading-container animate-fade-in" style={{ padding: '5rem 2rem', textAlign: 'center' }}>
          <PiggyBank size={64} color="#38bdf8" style={{ marginBottom: '0.5rem' }} />
          <h2 style={{ fontSize: '1.5rem', color: '#f8fafc', marginBottom: '0.5rem' }}>
            Consulte seu Dashboard Financeiro
          </h2>
          <p style={{ maxWidth: '500px', color: '#94a3b8' }}>
            Digite o seu número de WhatsApp no campo superior para visualizar o extrato em tempo real, saldo consolidado e o gráfico de gastos por categoria diretamente do banco relacional.
          </p>
        </div>
      )}

      {!loading && dados && (
        <>
          <SummaryCards resumo={dados.resumo} />
          
          <div className="dashboard-grid">
            <CategoryChart categorias={dados.categorias} />
            <TransactionsTable transacoes={dados.transacoes} />
          </div>
        </>
      )}
    </div>
  );
}
