# Porquinho WhatsApp - Bot Financeiro Pessoal

> 📘 **Atenção (IAs e Desenvolvedores):** Consulte o arquivo [DOCUMENTACAO_E_TESTES.md](file:///d:/Trabalho/Porquinho%20Whatsapp/DOCUMENTACAO_E_TESTES.md) para ver a arquitetura completa, regras inegociáveis de negócio, bateria de testes obrigatórios e roadmap de próximas atividades.

Backend de automação para controle financeiro pessoal integrado ao WhatsApp utilizando a **API Oficial da Meta (Cloud API)** e banco de dados **Supabase (PostgreSQL)**.

---

## Stack Tecnológica
* **Linguagem:** Python 3 + FastAPI
* **Servidor Web:** Uvicorn (Assíncrono)
* **WhatsApp:** Meta Cloud API (Webhooks & Graph API)
* **Banco de Dados:** Supabase (PostgreSQL / `supabase-py`)

---

## Funcionalidades
1. **Verificação de Webhook:** Autenticação automática via `GET /webhook` compatível com o desafio (`hub.challenge`) da Meta Developers.
2. **Registro de Gastos:** Identificação automática de comandos que iniciam com `gasto` (ex: `gasto 50 almoço`). O bot extrai o valor, categoriza e salva no banco de dados.
3. **Registro de Entradas:** Identificação automática de comandos que iniciam com `entrada` (ex: `entrada 100 pix`).
4. **Relatório Mensal Sob Demanda:** Comando exclusivo (`gere o relatorio do mes`) que calcula o total de ganhos e gastos do mês vigente no Supabase em tempo real sem alterar os dados, retornando o saldo atualizado com formatação monetária brasileira (R$).
5. **Segurança e Isolamento:** Código desenhado estritamente para operar apenas na tabela `financas_transacoes`, preservando quaisquer outras tabelas existentes no banco.

---

## Como Configurar

### 1. Banco de Dados (Supabase)
Abra o **SQL Editor** no painel do seu projeto no Supabase e execute o conteúdo do arquivo `schema.sql` para criar a tabela `financas_transacoes` com as políticas de segurança.

### 2. Variáveis de Ambiente
Copie o arquivo de exemplo e preencha as suas credenciais:
```bash
cp .env.example .env
```
*(Nota: O arquivo `.env` é ignorado pelo Git por segurança).*

### 3. Instalação das Dependências
Instale as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

### 4. Executando o Servidor
Inicie o servidor local com recarregamento automático:
```bash
uvicorn main:app --reload --port 8000
```
O webhook estará disponível em `http://localhost:8000/webhook`. Para testes com a Meta, utilize um túnel como **ngrok** (`ngrok http 8000`) ou **Cloudflare Tunnels**.
