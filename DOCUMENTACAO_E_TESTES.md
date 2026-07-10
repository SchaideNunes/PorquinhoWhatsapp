# 🐷 PORQUINHO WHATSAPP — DOCUMENTAÇÃO OFICIAL, REGRAS DE NEGÓCIO E BATERIA DE TESTES

> **INSTRUÇÃO CRÍTICA PARA INTELIGÊNCIAS ARTIFICIAIS / AGENTES DE IA:**
> Sempre que iniciar uma nova sessão ou receber uma tarefa neste repositório, **leia este arquivo completamente** para compreender a arquitetura, as regras inegociáveis de negócio e executar/validar a **Bateria de Testes Obrigatórios** antes e depois de qualquer alteração no código.

---

## 1. VISÃO GERAL DO PROJETO E ARQUITETURA

O **Porquinho WhatsApp** é um assistente financeiro pessoal de ponta integrado diretamente ao WhatsApp por meio da **API Oficial da Meta (Cloud API)**, com backend em **Python 3 / FastAPI** e banco de dados relacional **Supabase (PostgreSQL)**.

### Stack Tecnológica
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Httpx (comunicação assíncrona com a Meta Cloud API).
- **Banco de Dados:** Supabase (PostgreSQL 15+) utilizando a biblioteca oficial `supabase-py`.
- **Canal do Usuário:** WhatsApp via Meta Cloud API (Webhook para recebimento + Graph API para envio).
- **Ambiente de Teste Local:** Túnel HTTPS via Cloudflare (`cloudflared`) ou SSH (`localhost.run`/`pinggy`).

---

## 2. O QUE JÁ FOI DESENVOLVIDO E CONFIGURADO

### ✅ Banco de Dados (`schema.sql`)
- Tabela criada e configurada: **`financas_transacoes`**
- Colunas:
  - `id` (UUID, Primary Key, gerado automaticamente)
  - `tipo` (TEXT, aceita `'gasto'` ou `'entrada'`)
  - `valor` (NUMERIC(10,2), maior que zero)
  - `categoria` (TEXT)
  - `descricao` (TEXT)
  - `created_at` (TIMESTAMPTZ, default `NOW()`)
- Políticas de segurança e índices otimizados aplicados.

### ✅ Backend Principal (`main.py`)
- **Conexão Segura e Tipada com Supabase:** Configurada com `Optional[Client]` e validação explícita (`if supabase is None:` e guardas de tipo para evitar erros `NoneType` no Pyrefly/Pyright).
- **Verificação de Webhook (`GET /webhook`):** Validação oficial do `hub.verify_token` (`schaide123`) respondendo com o `hub.challenge` para a Meta Cloud API.
- **Recebimento de Mensagens (`POST /webhook`):**
  - Leitura segura e tipada de estruturas JSON aninhadas da Meta.
  - Normalização de texto (`lower()`, `strip()`) tornando os comandos **case-insensitive**.
  - Suporte a sinônimos de entrada e saída (`gasto`, `gastei`, `saida`, `saída`, `paguei`, `entrada`, `entrei`, `recebi`, `ganhei`, `deposito`, `depósito`).
- **Registro de Transações (`inserir_transacao`):**
  - Parse inteligente de valores monetários com vírgula ou ponto (ex: `45,50` ou `45.50`).
  - Inserção na tabela `financas_transacoes`.
  - Envio de recibo formatado via WhatsApp.
- **Relatório Mensal (`gerar_e_enviar_relatorio_mensal`):**
  - Consulta apenas leitura (`SELECT`) das transações do mês e ano correntes.
  - **Nunca altera ou exclui registros do banco.**
  - Cálculo automático de Total de Entradas, Total de Gastos e Saldo Atual com ícones dinâmicos.

---

## 3. REGRAS INEGOCIÁVEIS DO SISTEMA (PARA A IA SEGUIR)

1. **Isolamento de Tabelas:**
   - Todas as operações financeiras devem interagir **exclusivamente** com a tabela `financas_transacoes`. Nunca crie dependências com outras tabelas sem solicitação explícita do usuário.
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

### 🔹 Teste 3: Validação do Webhook da Meta (`GET /webhook`)
- [ ] Enviar requisição simulando a Meta:
  `GET /webhook?hub.mode=subscribe&hub.verify_token=schaide123&hub.challenge=115599`
- [ ] O backend deve retornar status `200 OK` com o corpo em texto plano contendo exatamente `115599`.

### 🔹 Teste 4: Parser de Linguagem Natural (`extrair_dados_transacao`)
Garantir que os seguintes formatos sejam reconhecidos corretamente:
- [ ] `gasto 50 almoço` ➔ `{tipo: 'gasto', valor: 50.0, categoria: 'Almoço', descricao: 'almoço'}`
- [ ] `GASTEI 120,50 supermercado compra da semana` ➔ `{tipo: 'gasto', valor: 120.5, categoria: 'Supermercado'}`
- [ ] `entrada 1500 salário do mês` ➔ `{tipo: 'entrada', valor: 1500.0, categoria: 'Salário'}`
- [ ] `recebi 250 pix do cliente` ➔ `{tipo: 'entrada', valor: 250.0, categoria: 'Pix'}`

### 🔹 Teste 5: Isolamento de Relatório Mensal
- [ ] Verificar se o comando `gere o relatorio do mes` (ou variações como `relatorio`) aciona apenas consulta `SELECT` com filtros `>= inicio_mes` e `< inicio_proximo_mes`.

---

## 5. ROADMAP / PRÓXIMAS ATIVIDADES PROGRAMADAS

### 🚀 Atividade 1: Comando interativo de AJUDA / HELP pelo WhatsApp
- **Objetivo:** Criar um comando interativo (`ajuda`, `help`, `comandos`, `menu` ou `?`) que o usuário possa enviar no WhatsApp para receber um guia rápido e bonito com todos os comandos disponíveis do Porquinho.
- **O que deverá incluir no Menu de Ajuda:**
  1. Como registrar gastos (exemplos práticos com `gasto` e `gastei`).
  2. Como registrar entradas/ganhos (exemplos práticos com `entrada` e `recebi`).
  3. Como consultar o saldo e o relatório do mês (`gere o relatorio do mes`).
  4. Dicas de categorias automáticas.

### ☁️ [CONCLUÍDO - RENDER.COM] Atividade 2: Publicação e Hospedagem 24/7 na Nuvem
- **Status:** Concluído com sucesso no Render.com (URL oficial conectada com Webhook da Meta e Token Permanente).
- **Objetivo:** Publicar o backend FastAPI em uma plataforma de nuvem gratuita para que o Porquinho funcione 24 horas por dia, 7 dias por semana.
- **Entregáveis da Atividade:**
  1. ✅ Criação do arquivo `Procfile` e comando de inicialização.
  2. ✅ Configuração segura das variáveis de ambiente (`.env`) no painel do Render.
  3. ✅ Substituição da URL do túnel temporário pela URL HTTPS oficial definitiva (`porquinhowhatsapp.onrender.com/webhook`).
  4. ✅ Funcionamento 24/7 autônomo.

### 📊 Atividade 3: Dashboard Financeiro Web Visual (Gráficos e Extrato no Navegador)
- **Objetivo:** Criar uma interface web moderna, visual e responsiva servida pelo próprio FastAPI (ex: `/dashboard`) para o usuário visualizar suas finanças em gráficos e extratos.
- **Entregáveis da Atividade:**
  1. Página HTML + Vanilla CSS com design moderno (Modo Escuro premium / Glassmorphism / Cores vibrantes).
  2. Cards com resumo de Entradas, Gastos e Saldo em tempo real.
  3. Gráfico visual (ex: Chart.js) mostrando a divisão de gastos por categoria.
  4. Tabela interativa com histórico recente de transações (somente leitura na tabela `financas_transacoes`).
