import os
import sys
import re
import json
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
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
GRUPO_PERMITIDO = os.getenv("GRUPO_PERMITIDO", "").strip()

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

# Configuração de CORS para permitir que o Dashboard Web (React na Vercel ou local) acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        descricao = partes[2].strip().rstrip(".!?;")
        # A categoria será a primeira palavra da descrição capitalizada sem pontuação final
        categoria = descricao.split()[0].capitalize().rstrip(".!?;")
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
        type_webhook = payload.get("typeWebhook", "")
        print(f"[GREEN API WEBHOOK RECEBIDO] Tipo: {type_webhook}")
        
        if type_webhook in ["incomingMessageReceived", "outgoingMessageReceived", "outgoingAPIMessageReceived"]:
            sender_data = payload.get("senderData", {})
            chat_id = str(sender_data.get("chatId", sender_data.get("sender", "")))
            chat_name = str(sender_data.get("chatName", "")).strip()

            # =========================================================================
            # BLINDAGEM TOTAL DE SEGURANÇA (TOTAL LOCKDOWN)
            # =========================================================================
            # Se GRUPO_PERMITIDO estiver configurado (ex: 'Finanças'), o bot NUNCA
            # processa nem responde conversas privadas (@c.us) nem outros grupos.
            # SÓ PROCESSA e RESPONDE dentro do grupo (@g.us) autorizado.
            if GRUPO_PERMITIDO:
                if "@g.us" not in chat_id:
                    print(f"[SEGURANÇA BLINDADA] Conversa privada '{chat_id}' ignorada. Permitido apenas o grupo '{GRUPO_PERMITIDO}'.")
                    return Response(status_code=status.HTTP_200_OK)

                import unicodedata
                def remover_acentos(txt: str) -> str:
                    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn').lower()
                
                nome_recebido_limpo = remover_acentos(chat_name)
                nome_permitido_limpo = remover_acentos(GRUPO_PERMITIDO)

                if nome_permitido_limpo not in nome_recebido_limpo and nome_recebido_limpo not in nome_permitido_limpo:
                    print(f"[SEGURANÇA BLINDADA] Grupo '{chat_name}' ignorado. Permitido apenas: '{GRUPO_PERMITIDO}'.")
                    return Response(status_code=status.HTTP_200_OK)

            texto = payload.get("messageData", {}).get("textMessageData", {}).get("textMessage", "").strip()
            if not texto:
                texto = payload.get("messageData", {}).get("extendedTextMessageData", {}).get("text", "").strip()
            
            print(f"[GREEN API MENSAGEM] ChatID: {chat_id} | Grupo: {chat_name} | Texto: {texto}")
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
            push_name = str(data.get("pushName", "")).strip()
            
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
                    await processar_mensagem_usuario(numero_remetente, corpo_texto, push_name)
    except Exception as e:
        print(f"[ERRO] Erro ao processar payload da Evolution API: {e}")

    return Response(status_code=status.HTTP_200_OK)


@app.post("/webhook")
async def receber_mensagens_whatsapp(request: Request):
    """
    Endpoint POST para receber notificações e mensagens da Meta Cloud API (Webhook).
    Processa estruturas aninhadas com tipagem segura e envia para o processador principal.
    """
    try:
        dados = await request.json()
        print(f"[META API] Webhook recebido: {json.dumps(dados, indent=2)}")

        entry_list = dados.get("entry", [])
        if isinstance(entry_list, list):
            for entry in entry_list:
                if not isinstance(entry, dict):
                    continue
                changes_list = entry.get("changes", [])
                if isinstance(changes_list, list):
                    for change in changes_list:
                        if not isinstance(change, dict):
                            continue
                        value = change.get("value", {})
                        if not isinstance(value, dict):
                            continue
                        messages_list = value.get("messages", [])
                        if isinstance(messages_list, list):
                            for msg in messages_list:
                                if not isinstance(msg, dict):
                                    continue
                                if msg.get("type") == "text":
                                    text_obj = msg.get("text", {})
                                    if isinstance(text_obj, dict):
                                        texto_mensagem = text_obj.get("body", "")
                                        numero_remetente = msg.get("from", "")

                                        if texto_mensagem and numero_remetente:
                                            print(f"[META API] Mensagem de {numero_remetente}: {texto_mensagem}")
                                            await processar_mensagem_usuario(numero_remetente, texto_mensagem)

        return {"status": "success", "message": "Webhook processado com sucesso"}

    except Exception as e:
        print(f"[ERRO] Falha ao processar Webhook da Meta: {e}")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------------------
# 5. LÓGICA DE NEGÓCIO (INSERÇÃO E RELATÓRIO SOB DEMANDA)
# -----------------------------------------------------------------------------------------

async def processar_mensagem_usuario(numero: str, texto: str, push_name: str = ""):
    """
    Roteador lógico das mensagens recebidas:
    0. Permite trocar o nome de tratamento ("meu nome é ...").
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

    # Garante/recupera o perfil no banco de dados, capturando o pushName do WhatsApp se o nome for padrão
    await obter_ou_criar_usuario(numero, push_name)

    texto_normalizado = re.sub(r'\s+', ' ', texto.lower().strip())
    
    # -------------------------------------------------------------------------------------
    # CASO 0: COMANDO PARA TROCAR / ATUALIZAR NOME DO USUÁRIO
    # -------------------------------------------------------------------------------------
    match_nome = re.match(r"^(?:meu\s+nome\s+é|trocar\s+nome\s+para|mudar\s+nome\s+para|alterar\s+nome\s+para|me\s+chame\s+de|nome)\s+(.+)$", texto_normalizado)
    if match_nome:
        novo_nome = match_nome.group(1).strip().title()
        if len(novo_nome) >= 2 and novo_nome.lower() not in ["ajuda", "menu", "relatorio", "gasto", "entrada"]:
            try:
                variacoes = gerar_variacoes_telefone(numero)
                supabase.table("financas_usuarios").update({"nome": novo_nome}).in_("telefone", variacoes).execute()
                await enviar_mensagem_whatsapp(
                    numero,
                    f"✅ *Nome atualizado com sucesso!*\n\nA partir de agora chamarei você de *{novo_nome}*. 🐷"
                )
            except Exception as e_nome:
                await enviar_mensagem_whatsapp(
                    numero,
                    f"❌ Erro ao atualizar o nome no banco de dados: {e_nome}"
                )
            return

    # -------------------------------------------------------------------------------------
    # CASO 1: RELATÓRIO SOB DEMANDA
    # -------------------------------------------------------------------------------------
    if texto_normalizado in ["gere o relatorio do mes", "gere o relatório do mês", "relatorio", "relatório"]:
        await gerar_e_enviar_relatorio_mensal(numero)
        return

    # -------------------------------------------------------------------------------------
    # CASO 1.5: COMANDOS EXPLICITOS DE AJUDA / SAUDAÇÃO
    # -------------------------------------------------------------------------------------
    if texto_normalizado in ["ajuda", "help", "menu", "comandos", "?", "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite"]:
        await enviar_mensagem_ajuda(numero)
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
                "Para registrar sem perder o nexo, diga se é entrada ou saída, o valor e a descrição após:\n\n"
                "*Exemplos simples:*\n"
                "🟢 `Entrada 1500 Salario.`\n"
                "🔴 `Gastei 250 academia.`"
            )
            await enviar_mensagem_whatsapp(numero, mensagem_erro)
            return
            
        await inserir_transacao(numero, dados_transacao)
        return

    # -------------------------------------------------------------------------------------
    # CASO 3: COMANDO NÃO RECONHECIDO (FALLBACK PARA AJUDA)
    # -------------------------------------------------------------------------------------
    await enviar_mensagem_ajuda(numero)


async def enviar_mensagem_ajuda(numero: str):
    """
    Envia uma mensagem de ajuda simplificada explicando como o bot funciona e listando suas funcionalidades.
    """
    msg_ajuda = (
        "🐷 *Olá! Sou o Porquinho, seu Cérebro Financeiro no WhatsApp!*\n\n"
        "💡 *COMO EU FUNCIONO:*\n"
        "Para eu registrar suas contas sem perder o nexo, basta dizer se é *entrada* ou *saída*, o *valor* e a *descrição* logo após.\n\n"
        "📋 *EXEMPLOS SIMPLES:*\n"
        "🟢 *Entrada:* `Entrada 1500 Salario.`\n"
        "🔴 *Saída:* `Gastei 250 academia.`\n\n"
        "⚙️ *FUNCIONALIDADES E COMANDOS:*\n\n"
        "• *Registrar Entrada/Ganho:*\n"
        "Use palavras como: `entrada`, `recebi` ou `ganhei`\n"
        "👉 _Exemplo:_ `Entrada 1500 Salario.`\n\n"
        "• *Registrar Saída/Gasto:*\n"
        "Use palavras como: `gastei`, `gasto`, `saida` ou `paguei`\n"
        "👉 _Exemplo:_ `Gastei 250 academia.`\n\n"
        "• *Relatório e Saldo do Mês:*\n"
        "Consulta o resumo financeiro atual.\n"
        "👉 _Exemplo:_ `relatorio` ou `gere o relatorio do mes`\n\n"
        "• *Trocar seu Nome:*\n"
        "Atualiza o nome pelo qual eu chamo você.\n"
        "👉 _Exemplo:_ `meu nome é Carlos` ou `trocar nome para Ana`\n\n"
        "• *Ajuda e Menu:*\n"
        "Exibe esta lista a qualquer momento.\n"
        "👉 _Exemplo:_ `ajuda` ou `menu`\n\n"
        "_Dica: Seus dados são 100% privados e vinculados exclusivamente ao seu WhatsApp!_"
    )
    await enviar_mensagem_whatsapp(numero, msg_ajuda)


def gerar_variacoes_telefone(numero: str) -> list[str]:
    """
    Gera as variações do número de telefone para resolver o problema do 9º dígito no Brasil
    e números digitados com ou sem o DDI (55), garantindo que o usuário seja encontrado em qualquer formato.
    """
    limpo = re.sub(r"\D", "", numero.strip())
    if not limpo:
        return [numero]

    variacoes = set([limpo])

    # 1. Garante versão com DDI 55
    if (len(limpo) == 10 or len(limpo) == 11) and not limpo.startswith("55"):
        num_ddi = "55" + limpo
        variacoes.add(num_ddi)
    else:
        num_ddi = limpo

    # 2. Variações do 9º dígito para números com DDI 55
    if num_ddi.startswith("55"):
        # Se tem 13 dígitos (ex: 55 75 9 91503949), gera também a versão de 12 dígitos sem o 9º
        if len(num_ddi) == 13 and num_ddi[4] == "9":
            sem_nono = num_ddi[:4] + num_ddi[5:]
            variacoes.add(sem_nono)
            variacoes.add(sem_nono[2:])  # sem DDI
        # Se tem 12 dígitos (ex: 55 75 91503949), gera também a versão de 13 dígitos com o 9º
        elif len(num_ddi) == 12:
            com_nono = num_ddi[:4] + "9" + num_ddi[4:]
            variacoes.add(com_nono)
            variacoes.add(com_nono[2:])  # sem DDI

    return list(variacoes)


async def obter_ou_criar_usuario(numero: str, push_name: str = "") -> Dict[str, Any]:
    """
    Busca o perfil do usuário na tabela 'financas_usuarios' pelo número de WhatsApp.
    Se não existir, cria automaticamente. Se existir e o nome for 'Usuário' (padrão) e recebermos um pushName real, atualiza o nome no banco.
    """
    if supabase is None:
        return {"telefone": numero, "nome": push_name.title() if push_name and push_name.strip() else "Usuário", "plano": "gratuito", "dia_inicio_mes": 1, "dia_fechamento_cartao": 1, "receber_alerta_automatico": True}

    try:
        variacoes = gerar_variacoes_telefone(numero)
        consulta = supabase.table("financas_usuarios").select("*").in_("telefone", variacoes).execute()
        raw_data = consulta.data or []
        if raw_data and isinstance(raw_data[0], dict):
            user_dict = dict(raw_data[0])
            # Se o nome no banco ainda é "Usuário" e o WhatsApp enviou um pushName real, atualiza no banco
            if push_name and push_name.strip() and push_name.title() not in ["Usuário", "Usuario"] and user_dict.get("nome", "") in ["Usuário", "Usuario", ""]:
                try:
                    supabase.table("financas_usuarios").update({"nome": push_name.title()}).in_("telefone", variacoes).execute()
                    user_dict["nome"] = push_name.title()
                except Exception as e_up:
                    print(f"[AVISO] Não foi possível atualizar o push_name do usuário: {e_up}")
            return user_dict
        
        # Cria novo perfil se ainda não existir
        nome_inicial = push_name.title() if push_name and push_name.strip() and push_name.title() not in ["Usuário", "Usuario"] else "Usuário"
        novo_usuario = {
            "telefone": numero,
            "nome": nome_inicial,
            "plano": "gratuito",
            "dia_inicio_mes": 1,
            "dia_fechamento_cartao": 1,
            "receber_alerta_automatico": True
        }
        supabase.table("financas_usuarios").insert(novo_usuario).execute()
        return novo_usuario
    except Exception as e:
        print(f"[ERRO] Erro ao obter/criar usuário no Supabase: {e}")
        return {"telefone": numero, "nome": push_name.title() if push_name and push_name.strip() else "Usuário", "plano": "gratuito", "dia_inicio_mes": 1, "dia_fechamento_cartao": 1, "receber_alerta_automatico": True}


async def inserir_transacao(numero: str, dados: Dict[str, Any]):
    """
    Insere o registro APENAS na tabela 'financas_transacoes' e garante que o usuário exista em 'financas_usuarios'.
    Envia confirmação via WhatsApp/Meta API após a inserção.
    """
    if supabase is None:
        await enviar_mensagem_whatsapp(numero, "❌ Erro: Conexão com o banco de dados Supabase não configurada.")
        return

    try:
        # Garante ou recupera perfil do usuário no banco (com suporte a variações do 9º dígito)
        usuario = await obter_ou_criar_usuario(numero)
        telefone_real = str(usuario.get("telefone", numero))

        # Monta o payload para inserção no Supabase com suporte multi-usuário (isolado por telefone)
        novo_registro = {
            "telefone": telefone_real,
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
    Busca no Supabase apenas as transações do período financeiro do usuário (`numero`),
    respeitando a configuração personalizada `dia_inicio_mes` da tabela `financas_usuarios`.
    NÃO deleta, altera ou apaga nenhum dado do banco.
    Soma entradas, subtrai saídas e envia mensagem formatada com o saldo atual via WhatsApp.
    """
    if supabase is None:
        await enviar_mensagem_whatsapp(numero, "❌ Erro: Conexão com o banco de dados Supabase não configurada.")
        return

    try:
        usuario = await obter_ou_criar_usuario(numero)
        val_dia = usuario.get("dia_inicio_mes", 1)
        try:
            dia_inicio = int(val_dia) if isinstance(val_dia, (int, str, float)) else 1
        except (ValueError, TypeError):
            dia_inicio = 1
        
        agora = datetime.now()
        ano_atual = agora.year
        mes_atual = agora.month
        
        # Define os limites de data/hora respeitando o dia de fechamento personalizado do usuário
        if dia_inicio == 1:
            inicio_mes_dt = datetime(ano_atual, mes_atual, 1, 0, 0, 0)
            if mes_atual == 12:
                inicio_proximo_mes_dt = datetime(ano_atual + 1, 1, 1, 0, 0, 0)
            else:
                inicio_proximo_mes_dt = datetime(ano_atual, mes_atual + 1, 1, 0, 0, 0)
        else:
            if agora.day < dia_inicio:
                # Mês financeiro iniciou no mês anterior
                if mes_atual == 1:
                    inicio_mes_dt = datetime(ano_atual - 1, 12, dia_inicio, 0, 0, 0)
                else:
                    inicio_mes_dt = datetime(ano_atual, mes_atual - 1, dia_inicio, 0, 0, 0)
                inicio_proximo_mes_dt = datetime(ano_atual, mes_atual, dia_inicio, 0, 0, 0)
            else:
                # Mês financeiro iniciou no mês atual
                inicio_mes_dt = datetime(ano_atual, mes_atual, dia_inicio, 0, 0, 0)
                if mes_atual == 12:
                    inicio_proximo_mes_dt = datetime(ano_atual + 1, 1, dia_inicio, 0, 0, 0)
                else:
                    inicio_proximo_mes_dt = datetime(ano_atual, mes_atual + 1, dia_inicio, 0, 0, 0)

        inicio_mes = inicio_mes_dt.isoformat()
        inicio_proximo_mes = inicio_proximo_mes_dt.isoformat()

        variacoes = gerar_variacoes_telefone(numero)

        # Consulta APENAS leitura (SELECT) na tabela financas_transacoes filtrada por usuário e período
        consulta = (
            supabase.table("financas_transacoes")
            .select("tipo, valor, created_at")
            .in_("telefone", variacoes)
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
# 6. ROTA DA API DO DASHBOARD WEB (GET /api/dashboard)
# -----------------------------------------------------------------------------------------
@app.get("/api/dashboard")
async def obter_dados_dashboard(telefone: Optional[str] = None):
    """
    Endpoint GET para fornecer dados consolidados e transações em tempo real
    para o Dashboard Web React (somente leitura na tabela financas_transacoes).
    """
    if not telefone:
        return {"status": "error", "message": "Parâmetro 'telefone' é obrigatório."}

    # Normaliza o número do telefone removendo caracteres não numéricos
    numero = re.sub(r"\D", "", telefone.strip())
    if not numero:
        return {"status": "error", "message": "Número de telefone inválido."}

    if supabase is None:
        raise HTTPException(status_code=500, detail="Banco de dados Supabase não conectado.")

    try:
        variacoes = gerar_variacoes_telefone(numero)
        # Consulta o usuário para obter configurações de período financeiro e dados de perfil
        consulta_user = (
            supabase.table("financas_usuarios")
            .select("telefone, nome, plano, dia_inicio_mes")
            .in_("telefone", variacoes)
            .execute()
        )
        user_raw = consulta_user.data or []
        usuarios: list[dict[str, Any]] = [dict(u) for u in user_raw if isinstance(u, dict)]
        
        if not usuarios:
            return {
                "status": "not_found",
                "message": "Número não encontrado. Envie uma mensagem para o Porquinho no WhatsApp para iniciar!"
            }

        usuario_data: dict[str, Any] = usuarios[0]
        nome = str(usuario_data.get("nome", "Usuário"))
        plano = str(usuario_data.get("plano", "gratuito"))
        val_dia = usuario_data.get("dia_inicio_mes", 1)
        try:
            dia_inicio = int(val_dia) if isinstance(val_dia, (int, str, float)) else 1
        except (ValueError, TypeError):
            dia_inicio = 1

        # Calcula as datas de início e fim do período financeiro atual do usuário
        agora = datetime.now()
        ano_atual = agora.year
        mes_atual = agora.month

        if dia_inicio == 1:
            inicio_mes_dt = datetime(ano_atual, mes_atual, 1, 0, 0, 0)
            if mes_atual == 12:
                inicio_proximo_mes_dt = datetime(ano_atual + 1, 1, 1, 0, 0, 0)
            else:
                inicio_proximo_mes_dt = datetime(ano_atual, mes_atual + 1, 1, 0, 0, 0)
        else:
            if agora.day < dia_inicio:
                if mes_atual == 1:
                    inicio_mes_dt = datetime(ano_atual - 1, 12, dia_inicio, 0, 0, 0)
                else:
                    inicio_mes_dt = datetime(ano_atual, mes_atual - 1, dia_inicio, 0, 0, 0)
                inicio_proximo_mes_dt = datetime(ano_atual, mes_atual, dia_inicio, 0, 0, 0)
            else:
                inicio_mes_dt = datetime(ano_atual, mes_atual, dia_inicio, 0, 0, 0)
                if mes_atual == 12:
                    inicio_proximo_mes_dt = datetime(ano_atual + 1, 1, dia_inicio, 0, 0, 0)
                else:
                    inicio_proximo_mes_dt = datetime(ano_atual, mes_atual + 1, dia_inicio, 0, 0, 0)

        inicio_mes = inicio_mes_dt.isoformat()
        inicio_proximo_mes = inicio_proximo_mes_dt.isoformat()

        # Consulta APENAS leitura (SELECT) na tabela financas_transacoes considerando todas as variações do número
        consulta_transacoes = (
            supabase.table("financas_transacoes")
            .select("id, created_at, tipo, valor, categoria, descricao")
            .in_("telefone", variacoes)
            .gte("created_at", inicio_mes)
            .lt("created_at", inicio_proximo_mes)
            .order("created_at", desc=True)
            .execute()
        )
        
        raw_data = consulta_transacoes.data or []
        transacoes: list[dict[str, Any]] = [dict(item) for item in raw_data if isinstance(item, dict)]

        total_entradas = 0.0
        total_gastos = 0.0
        categorias_map: dict[str, float] = {}

        lista_formatada: list[dict[str, Any]] = []
        for t in transacoes:
            try:
                valor = float(t.get("valor", 0.0))
            except (ValueError, TypeError):
                valor = 0.0

            tipo = str(t.get("tipo", "")).lower()
            if tipo == "entrada":
                total_entradas += valor
            elif tipo == "gasto":
                total_gastos += valor
                cat = str(t.get("categoria") or "Outros").strip()
                if not cat:
                    cat = "Outros"
                categorias_map[cat] = categorias_map.get(cat, 0.0) + valor

            lista_formatada.append({
                "id": str(t.get("id", "")),
                "created_at": str(t.get("created_at", "")),
                "tipo": tipo,
                "valor": round(valor, 2),
                "categoria": str(t.get("categoria", "Outros")),
                "descricao": str(t.get("descricao", ""))
            })

        saldo_atual = total_entradas - total_gastos

        return {
            "status": "success",
            "usuario": {
                "telefone": numero,
                "nome": nome,
                "plano": plano,
                "dia_inicio_mes": dia_inicio,
                "periodo": {
                    "inicio": inicio_mes,
                    "fim": inicio_proximo_mes,
                    "mes_referencia": f"{mes_atual:02d}/{ano_atual}"
                }
            },
            "resumo": {
                "entradas": round(total_entradas, 2),
                "gastos": round(total_gastos, 2),
                "saldo": round(saldo_atual, 2)
            },
            "categorias": [
                {"categoria": k, "valor": round(v, 2)}
                for k, v in sorted(categorias_map.items(), key=lambda x: x[1], reverse=True)
            ],
            "transacoes": lista_formatada
        }

    except Exception as e:
        print(f"[ERRO] Erro na rota /api/dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar dados do dashboard.")


@app.put("/api/usuario/nome")
async def atualizar_nome_usuario(payload: Dict[str, Any]):
    """
    Endpoint para atualizar o nome do usuário na tabela 'financas_usuarios' pelo telefone via API (Dashboard).
    """
    if supabase is None:
        raise HTTPException(status_code=503, detail="Serviço indisponível. Supabase não conectado.")

    telefone = payload.get("telefone", "")
    novo_nome = payload.get("nome", "").strip().title()

    if not telefone or not novo_nome or len(novo_nome) < 2:
        raise HTTPException(status_code=400, detail="Parâmetros inválidos: telefone e nome (mínimo 2 caracteres) são obrigatórios.")

    try:
        variacoes = gerar_variacoes_telefone(str(telefone))
        resposta = supabase.table("financas_usuarios").update({"nome": novo_nome}).in_("telefone", variacoes).execute()
        return {"status": "success", "message": f"Nome atualizado com sucesso para: {novo_nome}", "data": resposta.data}
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar nome via API: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar o nome do usuário.")


# -----------------------------------------------------------------------------------------
# 7. ROTA DE SAÚDE DA API (HEALTHCHECK)
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
