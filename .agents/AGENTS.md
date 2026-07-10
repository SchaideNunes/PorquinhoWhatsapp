# Regras do Projeto Porquinho WhatsApp

Sempre que você (IA / Agente) iniciar uma conversa ou for realizar qualquer modificação no código deste repositório:

1. **LEIA OBRIGATORIAMENTE O ARQUIVO:** `DOCUMENTACAO_E_TESTES.md` na raiz do projeto antes de propor ou executar mudanças.
2. **SIGA AS REGRAS INEGOCIÁVEIS DE NEGÓCIO:**
   - Interagir apenas com a tabela `financas_transacoes`.
   - Nunca alterar ou deletar registros durante a geração de relatórios mensais.
   - Manter compatibilidade com sinônimos e comandos case-insensitive.
   - Garantir código sem avisos de tipagem (`NoneType` ou `.get()` inseguro no Pyrefly/Pyright).
3. **EXECUTE A BATERIA DE TESTES OBRIGATÓRIOS:**
   - Antes de concluir qualquer tarefa, valide os itens listados na seção **Bateria de Testes Obrigatórios** do documento `DOCUMENTACAO_E_TESTES.md`.
4. **CONSULTE O ROADMAP:**
   - Verifique a seção de próximas atividades programadas (ex: criação do comando `HELP` / `ajuda` pelo WhatsApp, publicação 24/7 em nuvem e criação do Dashboard Financeiro Web Visual).
