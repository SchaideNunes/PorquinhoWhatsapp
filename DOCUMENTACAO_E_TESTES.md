# 🐷 PORQUINHO WHATSAPP — DOCUMENTAÇÃO OFICIAL, REGRAS DE ENGENHARIA, DESIGN, SEGURANÇA E BATERIA DE TESTES

> **Documento de Governança Técnica & Regras Inegociáveis de Desenvolvimento**  
> Este arquivo estabelece o padrão de excelência técnica, arquitetural, visual, de segurança e de testes para o ecossistema do **Porquinho WhatsApp**.  
> **INSTRUÇÃO CRÍTICA PARA DESENVOLVEDORES / AGENTES DE IA:** Sempre que iniciar uma nova sessão ou receber uma tarefa neste repositório, **leia este arquivo completamente** para compreender a arquitetura, as regras inegociáveis de negócio e executar/validar a **Bateria de Testes Obrigatórios** antes e depois de qualquer alteração no código.

---

## 🏛️ 1. VISÃO GERAL DO PROJETO E ARQUITETURA

O **Porquinho WhatsApp** é um assistente financeiro pessoal de ponta integrado diretamente ao WhatsApp por meio da **Evolution API (Baileys / QR Code)**, com backend em **Python 3 / FastAPI** e banco de dados relacional **Supabase (PostgreSQL)**, acompanhado de um **Dashboard Web Visual em React (Vite)** publicado na **Vercel**.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           ARQUITETURA DO ECOSSISTEMA                             │
│                                                                                  │
│   📱 WhatsApp Usuário  ◄──►  📬 "O Carteiro" (Evolution API v2.3.7 / Node.js)    │
│                                        │ Webhook (POST /webhook-evolution)       │
│                                        ▼                                         │
│   💻 Dashboard Web     ◄──►  🧠 "O Cérebro" (Porquinho - FastAPI / Python 3)    │
│      (React / Vite)   CORS / REST      │ supabase-py                             │
│                                        ▼                                         │
│                              🗄️ Supabase Cloud (PostgreSQL 15+)                  │
│                                 • financas_usuarios                              │
│                                 • financas_transacoes                            │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 🧩 Separação de Responsabilidades (Arquitetura Modular)
1. **O "Carteiro" (Evolution API v2.3.7 - Node.js / TypeScript):**
   - Responsável exclusivamente pela conectividade bruta com o WhatsApp via QR Code (`Baileys`), criptografia de sessão e envio/recebimento de mensagens em tempo real sem depender da Meta Developers.
   - Não possui lógica de negócio ou acesso às tabelas financeiras do usuário.
2. **O "Cérebro Financeiro" (Porquinho WhatsApp - Python 3 / FastAPI):**
   - Responsável pelo processamento de linguagem natural, regras financeiras, categorização, normalização do 9º dígito de telefone e persistência na tabela `financas_transacoes` do Supabase.
   - Recebe notificações do "Carteiro" via Webhook (`http://localhost:8000/webhook-evolution` ou URL do Render) e instrui a Evolution API a enviar respostas ao usuário.
3. **O "Dashboard Web" (React / Vite + Tailwind CSS / Vanilla CSS):**
   - Interface visual moderna, responsiva e mobile-first para o usuário consultar extratos, gráficos por categoria, resumos de saldo e lançar transações diretamente pelo navegador.
   - Comunica-se com o backend FastAPI via endpoints REST com CORS habilitado.

---

## 🚀 2. O QUE JÁ FOI DESENVOLVIDO, TESTADO E CONFIGURADO

### ✅ 1. Banco de Dados Relacional (`schema.sql` - Supabase / PostgreSQL)
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
- **Políticas e Performance:** RLS ativo e índices otimizados por usuário (`idx_financas_transacoes_telefone_created_at`).

### ✅ 2. Backend Principal (`main.py` - FastAPI)
- **Conexão Segura e Tipada com Supabase:** Configurada com `Optional[Client]` e validação explícita (`if supabase is None:` e guardas de tipo para evitar erros `NoneType` no Pyrefly/Pyright).
- **Tratamento Inteligente do 9º Dígito (`gerar_variacoes_telefone`):**
  - Gera variações com e sem DDI 55 e com/sem o 9º dígito (ex.: `5575991503949`, `557591503949`, `75991503949`), eliminando problemas de divergência entre o WhatsApp e o cadastro do usuário.
- **Recebimento de Mensagens Evolution API (`POST /webhook-evolution`):**
  - Leitura assíncrona de eventos `messages.upsert` do WhatsApp via QR Code.
  - Normalização de texto (`lower()`, `strip()`) tornando os comandos **case-insensitive**.
  - Suporte a sinônimos de entrada e saída (`gasto`, `gastei`, `saida`, `saída`, `paguei`, `entrada`, `entrei`, `recebi`, `ganhei`, `deposito`, `depósito`).
  - Atualização automática do nome do usuário via `pushName` do WhatsApp.
- **Parser de Linguagem Natural (`extrair_dados_transacao`):**
  - Identificação de valores monetários com vírgula ou ponto (ex: `45,50` ou `45.50`).
  - Extração inteligente de categorias (`Alimentação`, `Supermercado`, `Transporte`, `Salário`, `Pix`, etc.).
- **Gestão de Perfil de Usuário (`obter_ou_criar_usuario`):**
  - Consulta o cadastro em `financas_usuarios` por `telefone`. Cria automaticamente um perfil caso seja um novo usuário.
- **Registro de Transações (`inserir_transacao`):**
  - Inserção na tabela `financas_transacoes` vinculada ao `telefone` do usuário.
  - Envio de recibo formatado em tempo real via WhatsApp com confirmação de saldo.
- **Relatório Mensal Sob Demanda (`gerar_e_enviar_relatorio_mensal`):**
  - Consulta apenas leitura (`SELECT`) das transações filtradas estritamente por `telefone` e pelo intervalo de datas do período financeiro (`dia_inicio_mes`).
  - **Nunca altera ou exclui registros do banco.**
  - Cálculo automático de Total de Entradas, Total de Gastos e Saldo Atual com ícones dinâmicos.
- **Comando de Ajuda Interativo (`enviar_mensagem_ajuda`):**
  - Menu completo acionado por `ajuda`, `help`, `menu`, `comandos`, `?`, `oi`, `olá` ou mensagens não reconhecidas.
  - Informa comandos, link direto para o dashboard web e orientações de uso.
- **Rotas de API REST com CORS:**
  - `GET /` ➔ Healthcheck e status de conectividade do banco.
  - `GET /api/dashboard?telefone={numero}` ➔ Retorna resumo consolidado, lista de categorias e transações do mês vigente (somente leitura).
  - `POST /api/transacao` ➔ Endpoint seguro para lançamento direto via Web, com validação de payload, inserção no Supabase e envio de comprovante no WhatsApp.
  - `PUT /api/usuario/nome` ➔ Atualização do nome de exibição do usuário.

### ✅ 3. Dashboard Web Visual (`dashboard-react` - React / Vite)
- **Design System Premium:** Fundo Preto Profundo (`#070a12`) com cartões em Azul Navy (`#111d3b`) em estilo Glassmorphism, limpo e profissional.
- **Componentes Construídos:**
  - `Header.jsx`: Identificação do usuário, status de conexão e botão para alternar telefone/sair.
  - `SummaryCards.jsx`: Cards com resumo de Entradas, Gastos e Saldo atualizados em tempo real com formatação monetária em `R$`.
  - `CategoryChart.jsx`: Gráfico interativo com `Chart.js` (`react-chartjs-2`) demonstrando os gastos por categoria.
  - `TransactionsTable.jsx`: Extrato recente com badges coloridas por tipo de movimentação.
  - `BottomNav.jsx`: Barra de navegação inferior com abas (Atividade, Orçamento, Transações e Conta) e botão flutuante `+` para abertura de modal.
  - `AccountCard.jsx`: Edição rápida do perfil e nome do usuário.
- **Modal Interativo Web / WhatsApp:** Permite registrar transação diretamente pela Web (chamando `POST /api/transacao`) ou gerar link pronto para o WhatsApp (`wa.me`).

---

## 🚨 3. METODOLOGIA DE DESENVOLVIMENTO: TDD ESTRITO & FLUXO INCREMENTAL

> [!IMPORTANT]
> **O desenvolvimento é guiado por testes (Test-Driven Development) e construído de forma incremental (feature por feature).**  
> Nenhum código de funcionalidade é considerado concluído sem que seus respectivos testes automatizados passem com 100% de sucesso.

### 🔄 Ciclo Red-Green-Refactor Obrigatório:
1. 🔴 **Fase RED (Teste Primeiro):** Escrever primeiro o teste unitário/integração que define o comportamento esperado do componente, função ou endpoint. Executar o teste e garantir que ele **falhe propositalmente**.
2. 🟢 **Fase GREEN (Código Mínimo):** Implementar o código estritamente necessário para fazer o teste passar.
3. 🔵 **Fase REFACTOR (Refatoração Limpa):** Melhorar a estrutura, legibilidade, tipagem e performance do código, garantindo que 100% da suíte de testes permaneça verde.
4. ⏩ **Avanço Incremental:** Concluir e testar uma funcionalidade por completo antes de iniciar a próxima. Nunca crie múltiplos módulos interdependentes sem validar a base.

### 🧪 Tipos de Testes Exigidos:
- **Testes Unitários:** Validação de regras de negócio puras, utilitários, cálculos, máscaras de formulário, parser de texto e formatadores de dados.
- **Testes de Integração:** Validação de rotas de API, webhooks, contratos de payload e persistência no Supabase.
- **Testes de Concorrência e Race Conditions:** Validação de integridade em transações simultâneas e consistência de saldo.
- **Testes de Resiliência & Edge Cases:** Cenários de dados vazios, inputs maliciosos, telefones com variações de dígitos, serviços externos indisponíveis e limites de caracteres.

---

## 🔒 4. SEGURANÇA & PROTEÇÃO DE DADOS (SECURITY BY DESIGN)

> [!CAUTION]
> **Segurança não é um adendo final; ela é nativa do código desde a primeira linha.**

### 🔑 1. Gestão de Segredos & Variáveis de Ambiente
- **Proibido Commitar Segredos:** `.env`, chaves de API, credenciais do Supabase, tokens JWT e certificados NUNCA devem ser versionados no Git.
- **`.gitignore` Rigoroso:** Manter configurado para ignorar `.env`, `.env.local`, `node_modules/`, `.venv/`, `__pycache__/`, logs e arquivos temporários.
- **Template `.env.example`:** Sempre manter um arquivo `.env.example` documentado com todas as chaves exigidas pela aplicação (com valores fictícios e descritivos).
- **Isolamento entre Ambientes:** Nunca conectar ou modificar bancos de dados de produção ou de outros projetos sem autorização expressa.

### 🛡️ 2. Prevenção de Injeções (SQL / NoSQL / XSS)
- **Consultas Parametrizadas:** Proibida qualquer interpolação ou concatenação de strings em queries SQL. Utilizar estritamente os métodos parametrizados do cliente oficial (`supabase-py`).
- **Sanitização de Entradas:** Sanitizar e validar todos os inputs do usuário para neutralizar scripts maliciosos (XSS) e injeções de HTML.
- **Validação de Schemas:** Utilizar validação explícita de tipos, tamanhos e formatos antes de processar qualquer requisição no FastAPI e React.

### 🔐 3. Autenticação, Autorização & Isolamento Multi-Tenant
- **Row Level Security (RLS) / Multi-Tenant:** Garantir que consultas filtrem estritamente os registros pertencentes ao telefone do usuário autenticado.
- **Isolamento por Telefone:** Toda leitura ou escrita na tabela `financas_transacoes` deve incluir obrigatoriamente a cláusula de filtro do telefone do usuário (`.in_("telefone", variacoes)` ou `.eq("telefone", telefone)`).

### 🌐 4. Proteção HTTP & Infraestrutura
- **Rate Limiting:** Implementar proteção contra abuso em rotas públicas críticas e webhooks.
- **CORS Estrito:** Configurar políticas de CORS liberando apenas as origens confiáveis necessárias (Vercel, localhost).

---

## 🎨 5. DIRETRIZES DE DESIGN, UI/UX & FRONTEND DE ALTO PADRÃO

> [!NOTE]
> **A interface deve impressionar pela sofisticação, autenticidade e acabamento refinado.**  
> Designs amadores, templates genéricos ou com "cara de IA" (efeitos artificiais e poluídos) não são aceitos. O produto deve transmitir a sensação de software artesanal de elite (padrão Linear, Apple, Stripe).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ESTÉTICA & EXPERIÊNCIA                          │
│                                                                        │
│  ✨ Visual Premium      🔤 Tipografia Curada     ⚡ Animações Vivas    │
│  Dark/Glassmorphism     Google Fonts Modernas    Transições Suaves     │
│                                                                        │
│  🚫 Padrão Anti-IA      📱 100% Mobile-First     🛡️ Validação Reativa  │
│  Sem Efeitos Exagerados 320px a Ultrawide        Micro-UX & Feedback   │
└────────────────────────────────────────────────────────────────────────┘
```

### 🚫 1. Padrão Anti-IA: Design Autêntico, Humano e Sem Clichês
Para garantir que a interface não aparente ser um "template gerado por IA genérico", siga estas regras rígidas:
- **Sem Exageros e Poluição Visual:** Proibido o uso indiscriminado de gradientes roxo/magenta fluorescentes caóticos, neons artificiais, borrões excessivos ("auroras") espalhados sem propósito ou múltiplos efeitos brigando por atenção.
- **Hovers Sutis & Elegantes:** Nada de cartões pulando na tela (`scale-110`, giros ou saltos bruscos). Utilize micro-interações discretas:
  - Variações leves de borda (`border-white/10` para `border-white/25`);
  - Elevação sutil (`translate-y-[-2px]`);
  - Transições suaves de opacidade e cor de fundo com timing natural (150ms a 250ms com curva `ease-out`).
- **Animações com Propósito (Dar Vida sem Poluir):** Toda animação deve servir para enriquecer a experiência do usuário (ex: guiar a leitura, indicar carregamento ou responder a uma ação), nunca apenas "para se mexer".

### 💎 2. Paleta de Cores e Estética Visual
- **Paletas Curadas:** Fundo Preto Profundo (`#070a12` / `#000000`), cartões em Azul Navy Translúcido (`#111d3b` / `rgba(17, 29, 59, 0.7)`), acentos em Verde Esmeralda (`#10b981` para entradas) e Vermelho Coral (`#ef4444` para gastos).
- **Glassmorphism Elegante:** Fundos translúcidos (`backdrop-blur-md`), bordas sutis com gradientes suaves (`border border-white/10`) e sombras com elevação natural (`box-shadow` refinada).
- **Hierarquia Visual:** Contraste nítido entre títulos, subtítulos, valores em destaque e textos de apoio.

### 🔤 3. Tipografia Moderna
- **Fontes de Alta Qualidade:** Utilizar tipografias modernas do Google Fonts (ex: `Inter`, `Outfit`, `Plus Jakarta Sans`) em substituição às fontes padrão do navegador.
- **Escala Modular:** Definir pesos e tamanhos com proporções consistentes para títulos (`h1`, `h2`, `h3`) e corpo de texto.

### 📱 4. Responsividade & Mobile-First
- **Adaptação Completa:** Layout totalmente fluido garantindo usabilidade impecável de 320px (smartphones compactos) até monitores ultrawide.
- **Áreas de Toque Adequadas:** Botões e elementos clicáveis com dimensões mínimas de 44x44px para facilitar o toque no mobile.
- **Máscaras Estritas de Entrada:** Formatação automática em tempo real para campos como WhatsApp `(XX) XXXXX-XXXX` e moeda (`R$ 0,00`).

---

## 🏛️ 6. ARQUITETURA DE SOFTWARE, QUALIDADE DE CÓDIGO & REGRAS INEGOCIÁVEIS DO SISTEMA

### 📐 1. Separação de Responsabilidades (Clean Architecture / DDD)
- **Rotas / Controllers:** Apenas recebem requisições, validam schemas e retornam códigos HTTP adequados.
- **Services / Camada de Negócio:** Contêm as regras da aplicação, orquestração e fluxos lógicos independentes de framework.
- **Repositories / Acesso a Dados:** Realizam a comunicação direta com o banco de dados Supabase.
- **Schemas / DTOs:** Modelos de contrato tipados e imutáveis.

### 🛡️ 2. Regras Inegociáveis do Sistema (Para a IA Seguir)
1. **Isolamento e Escopo de Tabelas:**
   - Todas as operações financeiras e de perfis devem interagir **exclusivamente** com as tabelas do ecossistema Porquinho (`financas_transacoes` e `financas_usuarios`). Nunca crie ou altere dependências com outras tabelas sem solicitação explícita do usuário.
2. **Imutabilidade Histórica nos Relatórios:**
   - A função de relatório mensal e os endpoints de dashboard **NUNCA** podem executar `DELETE`, `UPDATE` ou `DROP`. Devem estritamente realizar leitura (`SELECT`) dos dados do mês vigente.
3. **Robustez na Tipagem (Linter Pyrefly / Pyright):**
   - Nunca invoque métodos (`.table()`, `.get()`, etc.) em variáveis sem antes validar a existência do objeto (`if supabase is None:`, `if obj is not None:` ou `if isinstance(obj, dict):`).
   - Todos os dados vindos de `consulta.data` do Supabase devem ser tipados ou convertidos de forma segura (`[dict(item) for item in raw_data if isinstance(item, dict)]`).
4. **Resiliência de Encoding no Windows:**
   - Mantenha sempre a configuração de `sys.stdout.reconfigure(encoding='utf-8')` no topo de `main.py` para evitar falhas em terminais Windows com codificação `cp1252`.
5. **Flexibilidade de Linguagem Natural no WhatsApp:**
   - Comandos enviados pelo usuário devem sempre ignorar maiúsculas/minúsculas e tolerar variações verbais comuns (`gastei`, `gasto`, `recebi`, `entrada`, `paguei`).

### ⚠️ 3. Tratamento Resiliente de Erros & Códigos HTTP
- Respostas HTTP semânticas: `200 OK` / `201 Created` para sucessos, `400 Bad Request` / `422 Unprocessable Entity` para validações, `401 Unauthorized` / `403 Forbidden` para autenticação, `404 Not Found` para ausência de registros e `500 Internal Server Error` com logs estruturados.

---

## 🗄️ 7. GESTÃO DE DADOS, CONCORRÊNCIA & BANCO DE DADOS

1. **Integridade de Dados & Chaves Estrangeiras:** Definição correta de Primary Keys (UUID nas transações, VARCHAR no telefone do usuário), Foreign Keys e índices de busca frequente.
2. **Controle Atômico de Concorrência:** Garantir que inserções simultâneas não corrompam a consistência dos dados do usuário.
3. **Scripts de Migrations & Seeds:**
   - Manter sempre os arquivos `schema.sql` (estrutura de tabelas e índices) e seeds atualizados na raiz do repositório.

---

## 🔀 8. CONTROLE DE VERSÃO & CONVENTIONAL COMMITS

> [!TIP]
> **Commits frequentes e atômicos após cada funcionalidade concluída e testada.**  
> Evite commits gigantescos. Faça commits atômicos conforme cada componente, endpoint ou correção atinge o estado verde no TDD.

### 📝 Padrão Conventional Commits:
| Prefixo | Finalidade | Exemplo |
| :--- | :--- | :--- |
| `feat:` | Nova funcionalidade ou recurso para o usuário | `feat: implement direct transaction creation via dashboard modal` |
| `test:` | Adição, ajuste ou refatoração de testes automatizados | `test: add tests for brazilian phone 9th digit variations` |
| `fix:` | Correção de bug ou comportamento inesperado | `fix: resolve type safety issue on supabase query data extraction` |
| `refactor:` | Refatoração de código sem alteração de comportamento | `refactor: extract phone number parser into standalone utility` |
| `perf:` | Otimização de performance ou tempo de carregamento | `perf: add composite index on financas_transacoes user and date` |
| `style:` | Ajustes puramente visuais, CSS, formatação ou micro-animações | `style: polish glassmorphism styles and card hover effects` |
| `docs:` | Alteração ou adição de documentação e regras | `docs: consolidate engineering guidelines and testing rules` |
| `chore:` | Ajustes em dependências, scripts de build ou configs de CI/CD | `chore: update vite and react dependencies in dashboard` |

---

## 🧪 9. BATERIA DE TESTES OBRIGATÓRIOS (CHECKLIST DE VALIDAÇÃO)

Sempre que a IA modificar o código ou adicionar uma nova funcionalidade, **deve verificar e garantir aprovação nos seguintes testes**:

### 🔹 Teste 1: Validação de Tipagem e Sintaxe
- [ ] O arquivo `main.py` compila sem erros de sintaxe (`python -m py_compile main.py`).
- [ ] Nenhuma chamada insegura de `.get()` ou `.table()` que possa gerar alertas no Pyrefly/Pyright.

### 🔹 Teste 2: Validação do Endpoint de Healthcheck (`GET /`)
- [ ] O servidor responde `200 OK` na rota raiz `/` indicando status operacional e conexão com o Supabase.

### 🔹 Teste 3: Validação do Webhook da Evolution API (`POST /webhook-evolution`)
- [ ] Enviar payload JSON simulando o evento `messages.upsert` da Evolution API.
- [ ] O backend processa a mensagem sem erros e responde status `200 OK`.

### 🔹 Teste 4: Parser de Linguagem Natural (`extrair_dados_transacao`)
Garantir que os seguintes formatos sejam reconhecidos com 100% de precisão:
- [ ] `gasto 50 almoço` ➔ `{tipo: 'gasto', valor: 50.0, categoria: 'Almoço', descricao: 'almoço'}`
- [ ] `GASTEI 120,50 supermercado compra da semana` ➔ `{tipo: 'gasto', valor: 120.5, categoria: 'Supermercado'}`
- [ ] `entrada 1500 salário do mês` ➔ `{tipo: 'entrada', valor: 1500.0, categoria: 'Salário'}`
- [ ] `recebi 250 pix do cliente` ➔ `{tipo: 'entrada', valor: 250.0, categoria: 'Pix'}`

### 🔹 Teste 5: Normalização do 9º Dígito de Telefone (`gerar_variacoes_telefone`)
- [ ] Telefone `5575991503949` deve gerar variações: `5575991503949`, `557591503949`, `75991503949`, `7591503949`.
- [ ] Telefone digitado sem DDI `75991503949` deve encontrar o perfil cadastrado com DDI `5575991503949`.

### 🔹 Teste 6: Isolamento de Relatório Mensal
- [ ] O comando `relatorio` aciona exclusivamente consulta `SELECT` com filtros `>= inicio_mes` e `< inicio_proximo_mes` para o telefone do usuário.

### 🔹 Teste 7: Validação da Rota do Dashboard Web (`GET /api/dashboard`) e Build do React
- [ ] O endpoint `GET /api/dashboard?telefone={numero}` realiza exclusivamente leitura (`SELECT`) nas tabelas `financas_transacoes` e `financas_usuarios`.
- [ ] O projeto frontend na pasta `dashboard-react` compila sem erros via `npm run build` na Vercel ou localmente.

---

## 🛠️ 10. GUIA DE EXECUÇÃO LOCAL E EM PRODUÇÃO (COMANDOS ÚTEIS)

### 💻 1. Execução Local dos Serviços (Ambiente de Desenvolvimento)
- **Opção 1 (Scripts de 2 Cliques no Windows):**
  - WhatsApp Server (Evolution API): Executar `rodar_evolution_api.bat` (porta 8080).
  - Cérebro Python (Porquinho FastAPI): Executar `rodar_porquinho.bat` (porta 8000).
- **Opção 2 (Via Terminal Manual):**
  ```powershell
  # 1. Iniciar Evolution API
  cd evolution-api
  node dist/main.js

  # 2. Iniciar Cérebro FastAPI (em outro terminal)
  py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

  # 3. Iniciar Dashboard React (em outro terminal)
  cd dashboard-react
  npm run dev
  ```

### ☁️ 2. Execução em Produção (Nuvem 24/7)
- **Backend FastAPI (Render.com):**
  - Configurado via `Procfile` (`web: uvicorn main:app --host 0.0.0.0 --port $PORT`).
  - Webhook da Evolution API apontado para: `https://<seu-app-no-render>.onrender.com/webhook-evolution`.
- **Frontend Dashboard (Vercel):**
  - Root Directory: `dashboard-react`.
  - Variável de ambiente: `VITE_API_URL` configurada com a URL do Render.

---

## 🗺️ 11. ROADMAP / PRÓXIMAS ATIVIDADES PROGRAMADAS

### ✅ Entregas Concluídas
1. ✅ **Comando interativo de AJUDA / HELP pelo WhatsApp:** Resposta organizada e elegante com instruções e link do dashboard.
2. ✅ **Publicação e Hospedagem 24/7 na Nuvem (Render.com):** Backend FastAPI rodando 24/7 com SSL e integração contínua.
3. ✅ **Dashboard Financeiro Web Visual (React / Vite + Vercel):** Interface web com resumo, gráficos Chart.js, extrato e modal de lançamento direto.
4. ✅ **Suporte a Variações do 9º Dígito:** Resolução definitiva de incompatibilidades de números com ou sem DDI/9º dígito.

### 🌐 [BLUEPRINT DE EXPANSÃO SAAS] Próximas Atividades de Expansão
1. **`financas_orcamentos` (Limites & Alertas por Categoria):**
   - Criação da tabela de metas e orçamentos mensais por usuário.
   - Envio de alerta automático no WhatsApp quando o usuário atingir 80% ou 100% do teto estipulado para uma categoria (ex.: Alimentação, Lazer).
2. **`financas_recorrencias` (Parcelamentos & Assinaturas Automáticas):**
   - Tabela para lançamentos programados e recorrentes (ex.: Netflix, Spotify, parcela de cartão 3/10).
   - Cron/Worker agendado para registrar as transações no dia configurado.
3. **`financas_categorias` (Categorias Customizáveis):**
   - Permitir que o usuário adicione ou edite suas próprias categorias personalizadas com cores e ícones customizados no Dashboard Web.
4. **Exportação de Relatórios em PDF / Excel:**
   - Geração de extrato financeiro consolidado em `.pdf` e planilha `.xlsx` enviado diretamente no WhatsApp do usuário ou para download no Dashboard Web.
