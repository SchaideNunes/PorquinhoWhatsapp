# =========================================================================================
# BOT FINANCEIRO WHATSAPP "PORQUINHO" - BACKEND FASTAPI
# =========================================================================================
# Desenvolvido por: Desenvolvedor Python Sênior Especialista em Automação e Webhooks
# Stack: Python, FastAPI, Supabase (PostgreSQL), Meta Cloud API (WhatsApp)
# =========================================================================================

import os
import sys
import re
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from supabase import create_client, Client

# Garante suporte a UTF-8 no console do Windows para não falhar no cp1252
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -----------------------------------------------------------------------------------------
# 1. CARREGAMENTO DE VARIÁVEIS DE AMBIENTE E CONFIGURAÇÕES DE SEGURANÇA
# -----------------------------------------------------------------------------------------
# Carrega as variáveis do arquivo .env para o sistema operacional
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "").strip()
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "").strip()
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "").strip()
META_API_VERSION = os.getenv("META_API_VERSION", "v19.0").strip()

# Configurações para Evolution API (WhatsApp Não-Oficial via QR Code)
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "").strip().rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "").strip()
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "").strip()

# Configurações para Green API (WhatsApp QR Code Cloud Gratuito)
GREEN_API_ID = os.getenv("GREEN_API_ID", "").strip()
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN", "").strip()

# Validação inicial básica
if not SUPABASE_URL or not SUPABASE_KEY:
    print("[AVISO] As credenciais do Supabase não foram preenchidas no arquivo .env.")

# -----------------------------------------------------------------------------------------
# 2. INICIALIZAÇÃO DO BANCO DE DADOS (SUPABASE) E APP FASTAPI
# -----------------------------------------------------------------------------------------
# Inicializa o cliente oficial do Supabase
# REGRA CRÍTICA COMPRIDA: O cliente será utilizado APENAS na tabela 'financas_transacoes'.
# Nunca acessará, modificará ou lerá 'agendamentos' ou 'barbeiros_config'.
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Conexão com o Supabase estabelecida com sucesso!")
    except Exception as e:
        print(f"[ERRO] Erro ao inicializar cliente Supabase: {e}")

# Criação da instância do aplicativo FastAPI
app = FastAPI(
    title="Porquinho WhatsApp Bot - API",
    description="Backend para automação financeira pessoal via WhatsApp e Supabase.",
    version="1.0.0"
)

# -----------------------------------------------------------------------------------------
# 3. FUNÇÕES AUXILIARES (FORMATAÇÃO, ENVIO DE MENSAGENS WHATSAPP, PARSER)
# -----------------------------------------------------------------------------------------

def formatar_moeda(valor: float) -> str:
    """
    Formata um valor float para o formato monetário brasileiro (R$ X.XXX,XX).
    Sem depender de configurações de locale do sistema operacional.
    """
    valor_formatado = f"{valor:,.2f}"
    return f"R$ {valor_formatado}".replace(",", "X").replace(".", ",").replace("X", ".")


async def enviar_mensagem_whatsapp(numero_destino: str, texto_mensagem: str) -> bool:
    """
    Envia uma mensagem de texto.
    Prioriza a Evolution API (WhatsApp Não-Oficial via QR Code) se configurada.
    Caso contrário, utiliza a API Oficial da Meta (Cloud API).
    """
    # 1. Envio via Green API (Grátis QR Code Cloud)
    if GREEN_API_ID and GREEN_API_TOKEN:
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
        chat_id = f"{numero_destino}@c.us" if "@" not in numero_destino else numero_destino
        payload = {"chatId": chat_id, "message": texto_mensagem}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                if response.status_code in [200, 201]:
                    print(f"[OK] Mensagem enviada via Green API para {numero_destino}.")
                    return True
                else:
                    print(f"[ERRO] Erro ao enviar via Green API ({response.status_code}): {response.text}")
            except Exception as e:
                print(f"[ERRO] Exceção na Green API: {e}")

    # 2. Envio via Evolution API
    if EVOLUTION_API_URL and EVOLUTION_API_KEY and EVOLUTION_INSTANCE:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "number": numero_destino,
            "text": texto_mensagem
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)
                if response.status_code in [200, 201]:
                    print(f"[OK] Mensagem enviada via Evolution API para {numero_destino}.")
                    return True
                else:
                    print(f"[ERRO] Erro ao enviar via Evolution API ({response.status_code}): {response.text}")
                    return False
            except Exception as e:
                print(f"[ERRO] Exceção ao conectar com Evolution API: {e}")
                return False

    # 2. Envio via Meta Cloud API (Fallback)
    if not META_ACCESS_TOKEN or not META_PHONE_NUMBER_ID:
        print("[AVISO] Tokens da Meta API não configurados no .env.")
        return False

    url = f"https://graph.facebook.com/{META_API_VERSION}/{META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {
            "body": texto_mensagem
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code in [200, 201]:
                print(f"[OK] Mensagem enviada com sucesso via Meta API para {numero_destino}.")
                return True
            else:
                print(f"[ERRO] Erro ao enviar mensagem da Meta API ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"[ERRO] Exceção ao tentar conectar com a Meta API: {e}")
            return False


def extrair_dados_transacao(texto_mensagem: str):
    """
    Analisa a mensagem de texto para extrair o tipo (gasto/entrada), valor e descrição.
    Suporta formatos como:
      - "gasto 50 almoço"
      - "gasto 50,50 almoço no restaurante"
      - "entrada 100 pix do cliente"
    """
    texto = texto_mensagem.strip()
    
    # Divide o texto em no máximo 3 partes: [comando, valor, descricao_completa]
    partes = texto.split(maxsplit=2)
    
    if len(partes) < 2:
        return None
        
    tipo_raw = partes[0].lower()
    
    sinonimos_gasto = ["gasto", "gastei", "gastar", "saida", "saída", "paguei"]
    sinonimos_entrada = ["entrada", "entrei", "recebi", "ganhei", "deposito", "depósito"]
    
    if tipo_raw in sinonimos_gasto:
        tipo = "gasto"
    elif tipo_raw in sinonimos_entrada:
        tipo = "entrada"
    else:
        return None
        
    # Tratamento do valor monetário (substitui vírgula por ponto para conversão)
    valor_str = partes[1].replace(".", "").replace(",", ".") if "," in partes[1] and "." in partes[1] else partes[1].replace(",", ".")
    try:
        valor = float(valor_str)
        if valor <= 0:
            return None
    except ValueError:
        return None
        
    # Identificação da descrição e inferência simples de categoria
    if len(partes) == 3:
        descricao = partes[2].strip()
        # A categoria será a primeira palavra da descrição capitalizada (ex: "Almoço", "Pix")
        categoria = descricao.split()[0].capitalize()
    else:
        descricao = "Não informado"
        categoria = "Geral"
        
    return {
        "tipo": tipo,
        "valor": valor,
        "categoria": categoria,
        "descricao": descricao
    }

# -----------------------------------------------------------------------------------------
# 4. ROTAS DO WEBHOOK (VERIFICAÇÃO E RECEBIMENTO DE MENSAGENS)
# -----------------------------------------------------------------------------------------

@app.get("/webhook", response_class=PlainTextResponse)
async def verificar_webhook_meta(request: Request):
    """
    ROTA GET /webhook:
    Exigida pelo painel da Meta Developers para validação e autorização do endpoint.
    Verifica o token e retorna o 'hub.challenge' em formato texto puro.
    """
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")

    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        print("[OK] Webhook verificado com sucesso pela Meta!")
        return PlainTextResponse(content=str(hub_challenge), status_code=200)
    
    print("[ERRO] Falha de verificação do Webhook: Token inválido.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Token de verificação inválido ou modo incorreto."
    )


@app.post("/webhook-green")
async def receber_mensagens_green(request: Request):
    """
    ROTA POST /webhook-green:
    Recebe eventos de mensagens recebidas da Green API (WhatsApp via QR Code em Nuvem).
    """
    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=status.HTTP_200_OK)

    try:
        if payload.get("typeWebhook") == "incomingMessageReceived":
            sender_data = payload.get("senderData", {})
            # Se for grupo, chatId termina em @g.us; se for individual, @c.us
            chat_id = sender_data.get("chatId", sender_data.get("sender", ""))
            texto = payload.get("messageData", {}).get("textMessageData", {}).get("textMessage", "").strip()
            if not texto:
                texto = payload.get("messageData", {}).get("extendedTextMessageData", {}).get("text", "").strip()
            if texto and chat_id:
                await processar_mensagem_usuario(chat_id, texto)
    except Exception as e:
        print(f"[ERRO] Erro no webhook Green API: {e}")

    return Response(status_code=status.HTTP_200_OK)


@app.post("/webhook-evolution")
async def receber_mensagens_evolution(request: Request):
    """
    ROTA POST /webhook-evolution:
    Recebe o payload assíncrono de eventos e mensagens da Evolution API (WhatsApp via QR Code).
    Processa mensagens de texto e responde no mesmo chat/grupo.
    """
    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=status.HTTP_200_OK)

    try:
        event = payload.get("event", "")
        if event in ["messages.upsert", "MESSAGES_UPSERT"]:
            data = payload.get("data", {})
            key = data.get("key", {})
            remote_jid = str(key.get("remoteJid", ""))
            
            # Ignora status/stories (@broadcast)
            if "broadcast" not in remote_jid:
                numero_remetente = remote_jid.split("@")[0]
                
                msg_obj = data.get("message", {})
                corpo_texto = ""
                if isinstance(msg_obj, dict):
                    if "conversation" in msg_obj:
                        corpo_texto = str(msg_obj.get("conversation", ""))
                    elif "extendedTextMessage" in msg_obj:
                        corpo_texto = str(msg_obj.get("extendedTextMessage", {}).get("text", ""))
                
                corpo_texto = corpo_texto.strip()
                if corpo_texto:
                    await processar_mensagem_usuario(numero_remetente, corpo_texto)
    except Exception as e:
        print(f"[ERRO] Erro ao processar payload da Evolution API: {e}")

    return Response(status_code=status.HTTP_200_OK)


@app.post("/webhook")
async def receber_mensagens_whatsapp(request: Request):
    """
    ROTA POST /webhook:
    Recebe o payload assíncrono de eventos e mensagens do WhatsApp (Meta Cloud API).
    Processa mensagens de texto, aplica a lógica de finanças e responde ao usuário.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload JSON inválido.")

    try:
        if isinstance(payload, dict):
            entry_list = payload.get("entry", [])
            if isinstance(entry_list, list):
                for entry in entry_list:
                    if isinstance(entry, dict):
                        changes_list = entry.get("changes", [])
                        if isinstance(changes_list, list):
                            for change in changes_list:
                                if isinstance(change, dict):
                                    value = change.get("value", {})
                                    if isinstance(value, dict):
                                        messages = value.get("messages", [])
                                        if isinstance(messages, list):
                                            for message in messages:
                                                if isinstance(message, dict) and message.get("type") == "text":
                                                    numero_remetente = str(message.get("from", ""))
                                                    corpo_texto = str(message.get("text", {}).get("body", "")).strip()
                                                    await processar_mensagem_usuario(numero_remetente, corpo_texto)
    except Exception as e:
        print(f"[ERRO] Erro ao processar payload do WhatsApp: {e}")

    # Sempre retorne 200 OK rapidamente para a Meta API não reenviar a notificação
    return Response(status_code=status.HTTP_200_OK)


# -----------------------------------------------------------------------------------------
# 5. LÓGICA DE NEGÓCIO (INSERÇÃO E RELATÓRIO SOB DEMANDA)
# -----------------------------------------------------------------------------------------

async def processar_mensagem_usuario(numero: str, texto: str):
    """
    Roteador lógico das mensagens recebidas:
    1. Verifica se é pedido de relatório ("gere o relatorio do mes").
    2. Verifica se é comando de transação ("gasto ..." ou "entrada ...").
    3. Responde com mensagem de ajuda caso não entenda.
    """
    if not supabase:
        await enviar_mensagem_whatsapp(
            numero, 
            "⚠️ *Erro no Sistema:* O banco de dados Supabase não está conectado."
        )
        return

    texto_normalizado = re.sub(r'\s+', ' ', texto.lower().strip())
    
    # -------------------------------------------------------------------------------------
    # CASO 1: RELATÓRIO SOB DEMANDA
    # -------------------------------------------------------------------------------------
    if texto_normalizado in ["gere o relatorio do mes", "gere o relatório do mês", "relatorio", "relatório"]:
        await gerar_e_enviar_relatorio_mensal(numero)
        return

    # -------------------------------------------------------------------------------------
    # CASO 2: INSERÇÃO DE GASTO OU ENTRADA
    # -------------------------------------------------------------------------------------
    primeira_palavra = texto_normalizado.split()[0] if texto_normalizado.split() else ""
    gatilhos_transacao = [
        "gasto", "gastei", "gastar", "saida", "saída", "paguei",
        "entrada", "entrei", "recebi", "ganhei", "deposito", "depósito"
    ]
    if primeira_palavra in gatilhos_transacao:
        dados_transacao = extrair_dados_transacao(texto)
        
        if not dados_transacao:
            mensagem_erro = (
                "❌ *Formato inválido!*\n\n"
                "Para registrar, utilize o padrão:\n"
                "👉 `gasto <valor> <descrição>`\n"
                "👉 `entrada <valor> <descrição>`\n\n"
                "*Exemplos:*\n"
                "• `gasto 50 almoço`\n"
                "• `gasto 120,50 mercado`\n"
                "• `entrada 100 pix`"
            )
            await enviar_mensagem_whatsapp(numero, mensagem_erro)
            return
            
        await inserir_transacao(numero, dados_transacao)
        return

    # -------------------------------------------------------------------------------------
    # CASO 3: COMANDO NÃO RECONHECIDO (AJUDA)
    # -------------------------------------------------------------------------------------
    mensagem_ajuda = (
        "🐷 *Olá! Sou o Porquinho, seu bot financeiro pessoal!*\n\n"
        "Aqui está o que você pode me pedir:\n\n"
        "🔴 *Registrar Saída/Gasto:*\n"
        "`gasto 50 almoço`\n\n"
        "🟢 *Registrar Entrada/Ganho:*\n"
        "`entrada 100 pix`\n\n"
        "📊 *Ver Relatório Mensal:*\n"
        "`gere o relatorio do mes`"
    )
    await enviar_mensagem_whatsapp(numero, mensagem_ajuda)


async def inserir_transacao(numero: str, dados: Dict[str, Any]):
    """
    Insere o registro APENAS na tabela 'financas_transacoes'.
    Cumpre estritamente a regra de não interagir com outras tabelas.
    Envia confirmação via Meta API após a inserção.
    """
    if supabase is None:
        await enviar_mensagem_whatsapp(numero, "❌ Erro: Conexão com o banco de dados Supabase não configurada.")
        return

    try:
        # Monta o payload para inserção no Supabase
        novo_registro = {
            "tipo": dados["tipo"],
            "valor": dados["valor"],
            "categoria": dados["categoria"],
            "descricao": dados["descricao"]
            # created_at e id são gerados automaticamente pelo Supabase/PostgreSQL
        }
        
        # Executa o INSERT no Supabase
        resposta_db = supabase.table("financas_transacoes").insert(novo_registro).execute()
        
        if resposta_db.data:
            icon_tipo = "🔴" if dados["tipo"] == "gasto" else "🟢"
            tipo_formatado = "Gasto" if dados["tipo"] == "gasto" else "Entrada"
            adicionado_str = "adicionado" if dados["tipo"] == "gasto" else "adicionada"
            
            msg_sucesso = (
                f"✅ *{tipo_formatado} de {formatar_moeda(dados['valor'])} {adicionado_str} com sucesso!*\n\n"
                f"{icon_tipo} *Tipo:* {tipo_formatado}\n"
                f"💵 *Valor:* {formatar_moeda(dados['valor'])}\n"
                f"🏷️ *Categoria:* {dados['categoria']}\n"
                f"📝 *Descrição:* {dados['descricao']}"
            )
            await enviar_mensagem_whatsapp(numero, msg_sucesso)
        else:
            await enviar_mensagem_whatsapp(numero, "❌ Erro ao salvar transação no banco de dados.")
            
    except Exception as e:
        print(f"[ERRO] Erro no Supabase durante INSERT em financas_transacoes: {e}")
        await enviar_mensagem_whatsapp(numero, "❌ Erro interno ao tentar registrar sua transação no banco.")


async def gerar_e_enviar_relatorio_mensal(numero: str):
    """
    Busca no Supabase apenas as transações do mês e ano atuais.
    NÃO deleta, altera ou apaga nenhum dado do banco.
    Soma entradas, subtrai saídas e envia mensagem formatada com o saldo atual via WhatsApp.
    """
    if supabase is None:
        await enviar_mensagem_whatsapp(numero, "❌ Erro: Conexão com o banco de dados Supabase não configurada.")
        return

    try:
        agora = datetime.now()
        ano_atual = agora.year
        mes_atual = agora.month
        
        # Define os limites de data/hora para a consulta do mês atual no Supabase
        inicio_mes = datetime(ano_atual, mes_atual, 1, 0, 0, 0).isoformat()
        if mes_atual == 12:
            inicio_proximo_mes = datetime(ano_atual + 1, 1, 1, 0, 0, 0).isoformat()
        else:
            inicio_proximo_mes = datetime(ano_atual, mes_atual + 1, 1, 0, 0, 0).isoformat()

        # Consulta APENAS leitura (SELECT) na tabela financas_transacoes filtrada por data
        consulta = (
            supabase.table("financas_transacoes")
            .select("tipo, valor, created_at")
            .gte("created_at", inicio_mes)
            .lt("created_at", inicio_proximo_mes)
            .execute()
        )
        
        raw_data = consulta.data or []
        transacoes: list[dict[str, Any]] = [dict(item) for item in raw_data if isinstance(item, dict)]
        
        total_entradas = 0.0
        total_gastos = 0.0
        
        for t in transacoes:
            valor = float(t.get("valor", 0.0))
            if t.get("tipo") == "entrada":
                total_entradas += valor
            elif t.get("tipo") == "gasto":
                total_gastos += valor
                
        saldo_atual = total_entradas - total_gastos
        
        # Define ícone do saldo (positivo ou negativo)
        icon_saldo = "🟢" if saldo_atual >= 0 else "🔴"
        meses_nomes = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        nome_mes = meses_nomes[mes_atual - 1]
        
        msg_relatorio = (
            f"📊 *Relatório do Mês de {nome_mes}/{ano_atual}*\n"
            f"───────────────────\n\n"
            f"🟢 *Total de Entradas:* {formatar_moeda(total_entradas)}\n"
            f"🔴 *Total de Gastos:* {formatar_moeda(total_gastos)}\n"
            f"───────────────────\n"
            f"{icon_saldo} *Saldo Atual:* {formatar_moeda(saldo_atual)}\n\n"
            f"_Resumo gerado sem alterar nenhum registro do sistema!_"
        )
        
        await enviar_mensagem_whatsapp(numero, msg_relatorio)
        
    except Exception as e:
        print(f"[ERRO] Erro ao gerar relatório mensal no Supabase: {e}")
        await enviar_mensagem_whatsapp(numero, "❌ Erro ao calcular o relatório mensal.")


# -----------------------------------------------------------------------------------------
# 6. ROTA DE SAÚDE DA API (HEALTHCHECK)
# -----------------------------------------------------------------------------------------
@app.get("/")
async def health_check():
    """Rota raiz simples para teste de status do servidor."""
    return {
        "status": "online",
        "bot": "Porquinho WhatsApp Bot",
        "database_connected": supabase is not None
    }

# =========================================================================================
# PARA RODAR LOCALMENTE: uvicorn main:app --reload --port 8000
# =========================================================================================
