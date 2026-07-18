# 🐷 PORQUINHO WHATSAPP — DOCUMENTAÇÃO OFICIAL, REGRAS DE NEGÓCIO E BATERIA DE TESTES

> **INSTRUÇÃO CRÍTICA PARA INTELIGÊNCIAS ARTIFICIAIS / AGENTES DE IA:**
> Sempre que iniciar uma nova sessão ou receber uma tarefa neste repositório, **leia este arquivo completamente** para compreender a arquitetura, as regras inegociáveis de negócio e executar/validar a **Bateria de Testes Obrigatórios** antes e depois de qualquer alteração no código.

---

## 1. VISÃO GERAL DO PROJETO E ARQUITETURA

O **Porquinho WhatsApp** é um assistente financeiro pessoal de ponta integrado diretamente ao WhatsApp por meio da **Evolution API (Baileys / QR Code)**, com backend em **Python 3 / FastAPI** e banco de dados relacional **Supabase (PostgreSQL)**.

### Stack Tecnológica & Separação de Responsabilidades (Arquitetura Modular)
O projeto adota a separação de responsabilidades em dois serviços independentes para máxima estabilidade e segurança:
1. **O "Carteiro" (Evolution API v2.3.7 - Node.js / TypeScript):**
   - Responsável exclusivamente pela conectividade bruta com o WhatsApp via QR Code (`Baileys`), criptografia de sessão e envio/recebimento de mensagens em tempo real sem depender da Meta Developers.
   - Não possui lógica de negócio ou acesso às tabelas financeiras do usuário.
2. **O "Cérebro Financeiro" (Porquinho WhatsApp - Python 3 / FastAPI):**
   - Responsável pelo processamento de linguagem natural, regras financeiras, categorização e persistência na tabela `financas_transacoes` do Supabase.
   - Recebe notificações do "Carteiro" via Webhook (`http://localhost:8000/webhook-evolution` ou URL do Render) e instrui a Evolution API a enviar respostas ao usuário.

- **Banco de Dados:** Supabase (PostgreSQL 15+) utilizando a biblioteca oficial `supabase-py` no Cérebro Python e Prisma na Evolution API.
- **Ambiente Local Autônomo (2 Cliques):** Execução local integrada via `rodar_evolution_api.bat` (porta 8080) e `rodar_porquinho.bat` (porta 8000).

---

## 2. O QUE JÁ FOI DESENVOLVIDO E CONFIGURADO

### ✅ Banco de Dados (`schema.sql` - Suporte Multi-Usuário / Multi-Tenant)
- **Tabela 1: `financas_usuarios` (Perfis e Configurações de Período Personalizado)**
  - `telefone` (VARCHAR(30), Primary Key) ➔ Identificador único do usuário no WhatsApp (Chave Estrangeira com transações).
  - `nome` (VARCHAR(100), default `'Usuário'`) ➔ Nome do usuário para atendimento intimista.
  - `plano` (VARCHAR(20), default `'gratuito'`) ➔ Plano de assinatura (`gratuito`, `premium`, `empresarial`).
  - `dia_inicio_mes` (INTEGER, default `1`) ➔ Dia em que o mês financeiro do usuário inicia e reinicia (1 a 31).
  - `dia_fechamento_cartao` (INTEGER, default `1`) ➔ Dia em que a fatura do cartão fecha para relatórios automáticos.
  - `receber_alerta_automatico` (BOOLEAN, default `true`) ➔ Se o usuário quer receber o relatório automático no dia de fechamento.
  - `created_at` e `updated_at` (TIMESTAMPTZ).
- **Tabela 2: `financas_transacoes` (Transações Isoladas por Usuário)**
  - `id` (UUID, Primary Key, gerado automaticamente).
  - `created_at` (TIMESTAMPTZ, default `NOW()`).
  - `telefone` (VARCHAR(30), Not Null, índice por tenant) ➔ Conecta a transação ao seu proprietário.
  - `tipo` (TEXT, aceita `'gasto'` ou `'entrada'`).
  - `valor` (NUMERIC(10,2), maior que zero).
  - `categoria` (TEXT).
  - `descricao` (TEXT).
- Políticas de segurança (RLS) e índices otimizados por usuário (`idx_financas_transacoes_telefone_created_at`) aplicados.

### ✅ Backend Principal (`main.py`)
- **Conexão Segura e Tipada com Supabase:** Configurada com `Optional[Client]` e validação explícita (`if supabase is None:` e guardas de tipo para evitar erros `NoneType` no Pyrefly/Pyright).
- **Recebimento de Mensagens Evolution API (`POST /webhook-evolution`):**
  - Leitura assíncrona de eventos `messages.upsert` do WhatsApp via QR Code.
  - Normalização de texto (`lower()`, `strip()`) tornando os comandos **case-insensitive**.
  - Suporte a sinônimos de entrada e saída (`gasto`, `gastei`, `saida`, `saída`, `paguei`, `entrada`, `entrei`, `recebi`, `ganhei`, `deposito`, `depósito`).
  - Rota de Webhook secundária e fallback mantida para retrocompatibilidade técnica (`POST /webhook` e `GET /webhook`).
  - **Servidor Local Evolution API v2.3.7 + Cérebro Python no Supabase Dedicado (PorquinhoWhatsapp):**
    - A Evolution API e o Cérebro Python rodam localmente no computador do usuário, 100% integrados e salvando sessões, instâncias e transações no banco dedicado **`PorquinhoWhatsapp`** na nuvem do Supabase.
    - **Como rodar o Servidor do WhatsApp (Evolution API):** Dê 2 cliques em `rodar_evolution_api.bat` (porta 8080).
    - **Como rodar o Cérebro Python do Porquinho:** Dê 2 cliques em `rodar_porquinho.bat` (porta 8000).
    - **Sem arquivos executáveis `.bat` (via terminal manual):**
      1. Evolution API: `cd evolution-api` e `node dist/main.js`
      2. Cérebro Python: `py -m uvicorn main:app --host 0.0.0.0 --port 8000`
    - Painel e Webhook local configurado: `http://localhost:8080/manager` (Webhook para `http://localhost:8000/webhook-evolution`).
- **Gestão de Perfil de Usuário (`obter_ou_criar_usuario`):**
  - Consulta o cadastro em `financas_usuarios` por `telefone`. Cria automaticamente um perfil com `dia_inicio_mes = 1` caso seja um novo usuário.
- **Registro de Transações (`inserir_transacao`):**
  - Parse inteligente de valores monetários com vírgula ou ponto (ex: `45,50` ou `45.50`).
  - Inserção na tabela `financas_transacoes` vinculada ao `telefone` do usuário.
  - Envio de recibo formatado via WhatsApp.
- **Relatório Mensal (`gerar_e_enviar_relatorio_mensal`):**
  - Consulta apenas leitura (`SELECT`) das transações filtradas estritamente por `telefone` e pelo intervalo de datas do período financeiro (`dia_inicio_mes`).
  - **Nunca altera ou exclui registros do banco.**
  - Cálculo automático de Total de Entradas, Total de Gastos e Saldo Atual com ícones dinâmicos.

---

## 3. REGRAS INEGOCIÁVEIS DO SISTEMA (PARA A IA SEGUIR)

1. **Isolamento e Escopo de Tabelas:**
   - Todas as operações financeiras e de perfis devem interagir **exclusivamente** com as tabelas do ecossistema Porquinho (`financas_transacoes` e `financas_usuarios`). Nunca crie ou altere dependências com outras tabelas sem solicitação explícita do usuário.
2. **Imutabilidade Histórica nos Relatórios:**
   - A função de relatório mensal **NUNCA** pode executar `DELETE`, `UPDATE` ou `DROP`. Ela deve apenas ler (`SELECT`) os dados do mês vigente.
3. **Robustez na Tipagem (Linter Pyrefly / Pyright):**
   - Nunca chame métodos (`.table()`, `.get()`, etc.) em variáveis que possam ser `None` ou de tipo ambíguo sem antes aplicar guardas explícitas (`if obj is not None:` ou `if isinstance(obj, dict):`).
   - Todos os dados vindos de `consulta.data` do Supabase devem ser tipados ou convertidos de forma segura (ex: `[dict(item) for item in raw_data if isinstance(item, dict)]`).
4. **Resiliência de Encoding no Windows:**
   - Mantenha sempre a configuração de `sys.stdout.reconfigure(encoding='utf-8')` no topo de `main.py` para evitar falhas em terminais Windows com codificação `cp1252`.
5. **Flexibilidade de Linguagem Natural no WhatsApp:**
   - Comandos enviados pelo usuário devem sempre ignorar maiúsculas/minúsculas e tolerar variações verbais comuns (`gastei`, `gasto`, `recebi`, `entrada`).

---

## 4. BATERIA DE TESTES OBRIGATÓRIOS (CHECKLIST DE VALIDAÇÃO)

Sempre que a IA modificar o código ou adicionar uma nova funcionalidade, **deve verificar e garantir aprovação nos seguintes testes**:

### 🔹 Teste 1: Validação de Tipagem e Sintaxe
- [ ] Verificar se o arquivo `main.py` compila sem erros de sintaxe (`python -m py_compile main.py`).
- [ ] Verificar se não há chamadas inseguras de `.get()` ou `.table()` que possam gerar alertas no Pyrefly/Pyright.

### 🔹 Teste 2: Validação do Endpoint de Healthcheck (`GET /`)
- [ ] O servidor deve responder `200 OK` na rota raiz `/` indicando o status operacional e se o Supabase está conectado.

### 🔹 Teste 3: Validação do Webhook da Evolution API (`POST /webhook-evolution`)
- [ ] Enviar payload JSON simulando o evento `messages.upsert` da Evolution API.
- [ ] O backend deve processar a mensagem sem erros e responder status `200 OK`.

### 🔹 Teste 4: Parser de Linguagem Natural (`extrair_dados_transacao`)
Garantir que os seguintes formatos sejam reconhecidos corretamente:
- [ ] `gasto 50 almoço` ➔ `{tipo: 'gasto', valor: 50.0, categoria: 'Almoço', descricao: 'almoço'}`
- [ ] `GASTEI 120,50 supermercado compra da semana` ➔ `{tipo: 'gasto', valor: 120.5, categoria: 'Supermercado'}`
- [ ] `entrada 1500 salário do mês` ➔ `{tipo: 'entrada', valor: 1500.0, categoria: 'Salário'}`
- [ ] `recebi 250 pix do cliente` ➔ `{tipo: 'entrada', valor: 250.0, categoria: 'Pix'}`

### 🔹 Teste 5: Isolamento de Relatório Mensal
- [ ] Verificar se o comando `gere o relatorio do mes` (ou variações como `relatorio`) aciona apenas consulta `SELECT` com filtros `>= inicio_mes` e `< inicio_proximo_mes`.

### 🔹 Teste 6: Validação da Rota do Dashboard Web (`GET /api/dashboard`) e Build do React
- [ ] O endpoint `GET /api/dashboard?telefone={numero}` deve realizar exclusivamente leitura (`SELECT`) na tabela `financas_transacoes` e `financas_usuarios`.
- [ ] O projeto frontend na pasta `dashboard-react` deve compilar sem erros via `npm run build` na Vercel ou localmente.

---

## 5. ROADMAP / PRÓXIMAS ATIVIDADES PROGRAMADAS

### ✅ [CONCLUÍDO] Atividade 1: Comando interativo de AJUDA / HELP pelo WhatsApp
- **Status:** Concluído com sucesso (função `enviar_mensagem_ajuda` no Cérebro e interceptação case-insensitive para `ajuda`, `help`, `menu`, `comandos`, `?`, `oi`, `olá`, etc.).
- **Objetivo:** Criar uma resposta organizada e elegante quando o usuário enviar comandos ou mensagens não reconhecidas no WhatsApp.
- **Entregáveis do Menu:**
  1. Explicação sucinta de como enviar comandos sem perder o nexo (`gasto <valor> <descrição>` ou `entrada <valor> <descrição>`).
  2. Lista das funcionalidades ativas (Gastos, Entradas, Relatório sob demanda e Ajuda).
  3. Dica de privacidade vinculando os dados ao número do WhatsApp.

### 🌐 [BLUEPRINT DE EXPANSÃO SAAS] Atividades Futuras de Expansão do Ecossistema Relacional
- **Objetivo:** Conforme o sistema crescer para milhares de usuários, criar as tabelas complementares:
  1. **`financas_orcamentos` (Limites & Alertas):** Alerta em tempo real no WhatsApp ao atingir x% do limite mensal por categoria.
  2. **`financas_recorrencias` (Parcelamentos & Assinaturas):** Lançamento automatizado em segundo plano para compras parceladas ou assinaturas recorrentes (ex: Netflix, parcela da geladeira).
  3. **`financas_categorias` (Categorias Personalizadas):** Customização pelo usuário ou pequena empresa com ícones e cores para relatórios no Dashboard Web.

### ☁️ [CONCLUÍDO - RENDER.COM] Atividade 2: Publicação e Hospedagem 24/7 na Nuvem
- **Status:** Concluído com sucesso no Render.com (URL HTTPS oficial ativa conectada ao Webhook da Evolution API).
- **Objetivo:** Publicar o backend FastAPI em uma plataforma de nuvem gratuita para que o Porquinho funcione 24 horas por dia, 7 dias por semana.
- **Entregáveis da Atividade:**
  1. ✅ Criação do arquivo `Procfile` e comando de inicialização.
  2. ✅ Configuração segura das variáveis de ambiente (`.env`) no painel do Render.
  3. ✅ Conexão da URL HTTPS definitiva do Render com a instância da Evolution API (`/webhook-evolution`).
  4. ✅ Funcionamento 24/7 autônomo.

### ✅ [CONCLUÍDO - REACT / VERCEL + FASTAPI CORS] Atividade 3: Dashboard Financeiro Web Visual (Gráficos e Extrato no Navegador)
- **Status:** Concluído com sucesso utilizando **React (Vite + React)** para deploy na **Vercel**, integrado ao backend FastAPI através da rota com CORS `GET /api/dashboard?telefone={numero}`.
- **Objetivo:** Criar uma interface web moderna, visual e responsiva com foco na versão mobile para o usuário visualizar suas finanças em gráficos e extratos.
- **Paleta de Cores & Design:** Fundo Preto Profundo (`#070a12`) com cartões em Azul Navy (`#111d3b`) em estilo Glassmorphism, limpo e profissional.
- **Entregáveis Concluídos:**
  1. ✅ Projeto React na pasta `dashboard-react/` configurado com design system e responsividade mobile-first (`Header.jsx`, `SummaryCards.jsx`, `CategoryChart.jsx`, `TransactionsTable.jsx`).
  2. ✅ Cards com resumo de Entradas, Gastos e Saldo atualizados em tempo real do Supabase com formatação `R$`.
  3. ✅ Gráfico visual com `Chart.js` (`react-chartjs-2`) demonstrando a divisão de gastos por categoria.
  4. ✅ Tabela interativa com extrato recente, rolagem horizontal otimizada para celular e badges coloridas (somente leitura na tabela `financas_transacoes`).
  5. ✅ **Barra de Navegação Inferior (`BottomNav.jsx`) e Modal Interativo via Web/WhatsApp:**
     - Navegação fluida em abas (Atividade, Orçamento, Transações e Conta).
     - Botão Central Flutuante `+` abrindo modal que permite enviar o comando pelo WhatsApp (`wa.me`) ou **salvar diretamente e com segurança no banco relacional via Web (`POST /api/transacao`)** sem sair do site, garantindo isolamento ao telefone (`obter_ou_criar_usuario`), validação blindada no Cérebro Python, envio automático do recibo no WhatsApp e atualização do dashboard em tempo real.
  6. ✅ **Como fazer o deploy na Vercel:**
     - Conecte o repositório no painel da Vercel e selecione a pasta `dashboard-react` como **Root Directory**.
     - Crie a variável de ambiente `VITE_API_URL` apontando para a URL pública do Render (ex: `https://porquinhowhatsapp.onrender.com`).
     - A Vercel executará `npm run build` e publicará o dashboard instantaneamente com SSL e CDN globais.
