"""Testes do MVP. Nenhum deles gasta crédito: a API do Claude é substituída por um dublê."""

import json

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient

from app import chat, config, main


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")
    main._acessos.clear()
    return TestClient(main.app)


def eventos(resposta):
    return [json.loads(linha[6:]) for linha in resposta.text.split("\n\n") if linha.startswith("data: ")]


def perguntar(cliente, mensagem="Olá", historico=None):
    return cliente.post("/api/chat", json={"modulo": "geral", "historico": historico or [], "mensagem": mensagem})


def erro_da_api(classe, status):
    pedido = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return classe("erro", response=httpx2.Response(status, request=pedido), body=None)


def trocar_api(monkeypatch, falha=None, textos=(), stop_reason="end_turn", registro=None):
    """Substitui o cliente da Anthropic por um dublê que devolve textos fixos ou levanta um erro."""

    class Evento:
        type = "text"

        def __init__(self, texto):
            self.text = texto

    class Final:
        content = []

        def __init__(self):
            self.stop_reason = stop_reason

    class Stream:
        async def __aenter__(self):
            if falha:
                raise falha
            return self

        async def __aexit__(self, *args):
            return False

        async def __aiter__(self):
            for texto in textos:
                yield Evento(texto)

        async def get_final_message(self):
            return Final()

    class Mensagens:
        def stream(self, **parametros):
            if registro is not None:
                registro.append(parametros)
            return Stream()

    class Cliente:
        messages = Mensagens()

        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(chat.anthropic, "AsyncAnthropic", Cliente)


def test_pagina_inicial_abre(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "Citizen Assist AI" in resposta.text
    # Os avisos de IA e de privacidade são montados pelo chat.js em todos os chats.
    chat_js = cliente.get("/static/chat.js").text
    assert "posso errar" in chat_js
    assert "não envie CPF" in chat_js


def test_resposta_chega_em_pedacos(cliente, monkeypatch):
    registro = []
    trocar_api(monkeypatch, textos=["Olá, ", "tudo bem?"], registro=registro)
    recebidos = eventos(perguntar(cliente))
    assert [e["texto"] for e in recebidos if e["tipo"] == "texto"] == ["Olá, ", "tudo bem?"]
    assert recebidos[-1] == {"tipo": "fim"}
    assert registro[0]["model"] == config.MODELO
    assert "Citizen Assist AI" in registro[0]["system"]


def test_chave_ausente_gera_mensagem_amigavel(cliente, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    recebidos = eventos(perguntar(cliente))
    assert recebidos == [{"tipo": "erro", "texto": chat.MSG_SEM_CHAVE}]


@pytest.mark.parametrize(
    "falha, mensagem",
    [
        (erro_da_api(anthropic.AuthenticationError, 401), chat.MSG_CHAVE_INVALIDA),
        (erro_da_api(anthropic.PermissionDeniedError, 403), chat.MSG_SEM_PERMISSAO),
        (erro_da_api(anthropic.NotFoundError, 404), chat.MSG_MODELO),
        (erro_da_api(anthropic.RateLimitError, 429), chat.MSG_LIMITE),
        (erro_da_api(anthropic.APIStatusError, 402), chat.MSG_SEM_CREDITO),
        (erro_da_api(anthropic.InternalServerError, 529), chat.MSG_INSTAVEL),
        (erro_da_api(anthropic.BadRequestError, 400), chat.MSG_GENERICA),
        (anthropic.APITimeoutError(httpx2.Request("POST", "https://api.anthropic.com")), chat.MSG_TEMPO),
        (anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com")), chat.MSG_CONEXAO),
        (RuntimeError("detalhe interno que não pode aparecer"), chat.MSG_GENERICA),
    ],
)
def test_falhas_da_api_viram_mensagens_amigaveis(cliente, monkeypatch, falha, mensagem):
    trocar_api(monkeypatch, falha=falha)
    resposta = perguntar(cliente)
    assert eventos(resposta) == [{"tipo": "erro", "texto": mensagem}]
    assert "Traceback" not in resposta.text
    assert "detalhe interno" not in resposta.text


def test_resposta_recusada_ou_cortada_gera_aviso(cliente, monkeypatch):
    trocar_api(monkeypatch, stop_reason="refusal")
    assert {"tipo": "aviso", "texto": chat.AVISO_RECUSA} in eventos(perguntar(cliente))
    trocar_api(monkeypatch, textos=["texto"], stop_reason="max_tokens")
    assert {"tipo": "aviso", "texto": chat.AVISO_CORTE} in eventos(perguntar(cliente))


@pytest.mark.parametrize("mensagem", ["", "   ", "a" * (config.MAX_CARACTERES_MENSAGEM + 1)])
def test_mensagem_invalida_e_recusada(cliente, mensagem):
    resposta = perguntar(cliente, mensagem)
    assert resposta.status_code == 422
    assert "Não entendi o pedido" in resposta.json()["erro"]


def test_modulo_desconhecido_e_recusado(cliente):
    resposta = cliente.post("/api/chat", json={"modulo": "outro", "historico": [], "mensagem": "Olá"})
    assert resposta.status_code == 422


def test_limite_de_requisicoes_por_minuto(cliente, monkeypatch):
    trocar_api(monkeypatch, textos=["ok"])
    for _ in range(config.LIMITE_REQUISICOES_POR_MINUTO):
        assert perguntar(cliente).status_code == 200
    bloqueada = perguntar(cliente)
    assert bloqueada.status_code == 429
    assert "muitas mensagens" in bloqueada.json()["erro"]


def test_historico_e_cortado_e_comeca_pela_pessoa(cliente, monkeypatch):
    registro = []
    trocar_api(monkeypatch, textos=["ok"], registro=registro)
    longo = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"mensagem {i}"}
        for i in range(config.MAX_MENSAGENS_HISTORICO + 5)
    ]
    perguntar(cliente, "pergunta nova", longo)
    enviadas = registro[0]["messages"]
    assert len(enviadas) <= config.MAX_MENSAGENS_HISTORICO + 1
    assert enviadas[0]["role"] == "user"
    assert enviadas[-1] == {"role": "user", "content": "pergunta nova"}


def test_busca_na_web_so_em_dominios_configurados(monkeypatch):
    monkeypatch.setattr(config, "BUSCA_WEB", True)
    monkeypatch.setattr(config, "BUSCA_WEB_DOMINIOS", ["gov.br"])
    (busca,) = chat.ferramentas_do_modulo("geral")
    assert busca["max_uses"] == config.BUSCA_WEB_MAX_USOS
    assert busca["allowed_domains"] == ["gov.br"]
    monkeypatch.setattr(config, "BUSCA_WEB", False)
    assert chat.ferramentas_do_modulo("geral") == []
