"""Conversa com a API do Claude: resposta em streaming, fontes e erros amigáveis."""

import logging
from collections.abc import AsyncIterator

import anthropic

from . import config
from .prompts import montar_system_prompt

log = logging.getLogger("citizen_assist")

MSG_SEM_CHAVE = (
    "O assistente ainda não foi configurado: falta a chave da API. "
    "Se você é responsável pelo projeto, siga o passo de configuração do arquivo .env no README."
)
MSG_CHAVE_INVALIDA = (
    "O assistente não conseguiu se conectar porque a chave da API é inválida ou foi desativada. "
    "Se você é responsável pelo projeto, confira a chave no arquivo .env."
)
MSG_SEM_PERMISSAO = (
    "A chave da API não tem permissão para este pedido. "
    "Se você é responsável pelo projeto, confira no console da Anthropic o acesso ao modelo e à busca na web."
)
MSG_MODELO = (
    "O modelo configurado não foi encontrado. "
    "Se você é responsável pelo projeto, confira o valor de CLAUDE_MODEL no arquivo .env."
)
MSG_SEM_CREDITO = (
    "O assistente está indisponível porque a conta da API está sem crédito ou com problema de pagamento."
)
MSG_LIMITE = "Muitas pessoas estão usando o assistente agora. Aguarde um minuto e tente de novo."
MSG_TEMPO = "A resposta demorou demais e foi interrompida. Tente de novo em instantes."
MSG_CONEXAO = "Não foi possível falar com o serviço de inteligência artificial. Confira a internet e tente de novo."
MSG_INSTAVEL = "O serviço de inteligência artificial está instável no momento. Tente de novo em alguns minutos."
MSG_GENERICA = "Não foi possível responder agora. Tente de novo em instantes."
AVISO_RECUSA = "O assistente não pôde responder a esse pedido. Tente reformular a pergunta."
AVISO_CORTE = "A resposta ficou longa e foi cortada. Peça para continuar, se precisar."

MAX_CONTINUACOES = 3  # vezes que retomamos uma busca na web pausada pela API


def mensagem_de_erro(exc: Exception) -> str:
    """Traduz um erro da API em uma mensagem que qualquer pessoa entende."""
    if isinstance(exc, anthropic.AuthenticationError):
        return MSG_CHAVE_INVALIDA
    if isinstance(exc, anthropic.PermissionDeniedError):
        return MSG_SEM_PERMISSAO
    if isinstance(exc, anthropic.NotFoundError):
        return MSG_MODELO
    if isinstance(exc, anthropic.RateLimitError):
        return MSG_LIMITE
    if isinstance(exc, anthropic.APITimeoutError):
        return MSG_TEMPO
    if isinstance(exc, anthropic.APIConnectionError):
        return MSG_CONEXAO
    if isinstance(exc, anthropic.APIStatusError):
        if exc.status_code == 402:
            return MSG_SEM_CREDITO
        if exc.status_code >= 500:
            return MSG_INSTAVEL
    return MSG_GENERICA


def ferramentas_do_modulo(modulo: str) -> list[dict]:
    if modulo == "geral" and config.BUSCA_WEB:
        busca = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": config.BUSCA_WEB_MAX_USOS,
        }
        if config.BUSCA_WEB_DOMINIOS:
            busca["allowed_domains"] = config.BUSCA_WEB_DOMINIOS
        return [busca]
    return []


def fontes_citadas(conteudo) -> list[dict]:
    """Extrai as páginas da web que o modelo citou na resposta."""
    fontes = []
    for bloco in conteudo:
        if bloco.type != "text":
            continue
        for citacao in getattr(bloco, "citations", None) or []:
            if citacao.type == "web_search_result_location":
                fontes.append({"titulo": citacao.title or citacao.url, "url": citacao.url})
    return fontes


async def responder(modulo: str, historico: list[dict], mensagem: str) -> AsyncIterator[dict]:
    """Gera os eventos da resposta: texto aos poucos, status, fontes, avisos e erros."""
    if not config.chave_configurada():
        yield {"tipo": "erro", "texto": MSG_SEM_CHAVE}
        return

    mensagens = historico + [{"role": "user", "content": mensagem}]
    parametros = {
        "model": config.MODELO,
        "max_tokens": config.MAX_TOKENS,
        "system": montar_system_prompt(modulo),
    }
    ferramentas = ferramentas_do_modulo(modulo)
    if ferramentas:
        parametros["tools"] = ferramentas

    fontes: list[dict] = []
    try:
        async with anthropic.AsyncAnthropic(timeout=90.0) as cliente:
            for _ in range(MAX_CONTINUACOES + 1):
                async with cliente.messages.stream(messages=mensagens, **parametros) as stream:
                    async for evento in stream:
                        if evento.type == "text":
                            yield {"tipo": "texto", "texto": evento.text}
                        elif (
                            evento.type == "content_block_start"
                            and evento.content_block.type == "server_tool_use"
                        ):
                            yield {"tipo": "status", "texto": "Pesquisando em fontes oficiais…"}
                    final = await stream.get_final_message()
                fontes += fontes_citadas(final.content)
                if final.stop_reason != "pause_turn":
                    break
                # A API pausou uma busca longa: reenviamos a resposta parcial para ela continuar.
                mensagens = mensagens + [{"role": "assistant", "content": final.content}]
    except Exception as exc:  # noqa: BLE001 - qualquer falha vira mensagem amigável
        # Registramos só o tipo do erro: nada do que a pessoa escreveu vai para o log.
        log.warning("Falha na chamada à API: %s", type(exc).__name__)
        yield {"tipo": "erro", "texto": mensagem_de_erro(exc)}
        return

    if final.stop_reason == "refusal":
        yield {"tipo": "aviso", "texto": AVISO_RECUSA}
    elif final.stop_reason == "max_tokens":
        yield {"tipo": "aviso", "texto": AVISO_CORTE}

    unicas = list({f["url"]: f for f in fontes}.values())
    if unicas:
        yield {"tipo": "fontes", "fontes": unicas}
    yield {"tipo": "fim"}
