"""Testes das rotas de energia e do chat de energia usando as ferramentas de cálculo.

A API do Claude é substituída por um dublê: nenhum teste gasta crédito.
"""

import json
from types import SimpleNamespace as Obj

import pytest
from fastapi.testclient import TestClient

from app import chat, ferramentas, main, prompts

CASA = {"consumo_kwh": 300, "valor_conta": 285.0, "uf": "SP", "ligacao": "bifasica"}


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")
    main._acessos.clear()
    return TestClient(main.app)


def eventos(resposta):
    return [json.loads(linha[6:]) for linha in resposta.text.split("\n\n") if linha.startswith("data: ")]


# ---------- Rotas ----------


def test_opcoes_trazem_estados_ligacoes_e_fontes(cliente):
    dados = cliente.get("/api/energia/opcoes").json()
    assert len(dados["estados"]) == 27
    assert {l["id"] for l in dados["ligacoes"]} == {"monofasica", "bifasica", "trifasica"}
    assert dados["fontes"] and dados["limitacoes"]


def test_simular_devolve_os_valores_do_calculo(cliente):
    dados = cliente.post("/api/energia/simular", json=CASA).json()
    assert dados["placas_recomendadas"] == 5
    assert dados["cenarios"][5]["economia_mes"] == pytest.approx(237.50)


def test_comparar_com_led_e_chuveiro(cliente):
    corpo = {
        **CASA,
        "led": {"quantidade": 8, "potencia_atual_w": 60, "potencia_led_w": 9, "horas_dia": 5},
        "chuveiro": {"potencia_w": 5500, "banhos_dia": 4, "minutos_atual": 10, "minutos_novo": 7},
    }
    dados = cliente.post("/api/energia/comparar", json=corpo).json()
    assert dados["eficiencia"]["economia_kwh_mes"] == pytest.approx(94.2)
    # Sem preço das lâmpadas, o investimento das LED fica sem valor em vez de inventado.
    assert dados["led"]["investimento"] is None


@pytest.mark.parametrize(
    "corpo",
    [
        {**CASA, "uf": "XX"},
        {**CASA, "consumo_kwh": -5},
        {**CASA, "ligacao": ""},
    ],
)
def test_entrada_invalida_vira_mensagem_amigavel(cliente, corpo):
    resposta = cliente.post("/api/energia/simular", json=corpo)
    assert resposta.status_code == 422
    assert "erro" in resposta.json()
    assert "Traceback" not in resposta.text


def test_comparar_sem_alternativa_e_recusado(cliente):
    resposta = cliente.post("/api/energia/comparar", json=CASA)
    assert resposta.status_code == 422
    assert "lâmpadas ou do chuveiro" in resposta.json()["erro"]


# ---------- Ferramentas ----------


def test_ferramenta_solar_com_dados_validos():
    texto, erro = ferramentas.executar("simular_energia_solar", CASA)
    assert erro is False
    dados = json.loads(texto)
    assert dados["cenario"]["placas"] == 5
    assert dados["cenario"]["economia_mes"] == 237.5
    assert dados["fontes"] and dados["limitacoes"]
    assert "cenarios" not in dados


def test_ferramenta_solar_usa_o_orcamento_informado():
    texto, _ = ferramentas.executar("simular_energia_solar", {**CASA, "placas": 5, "orcamento_total": 11000})
    dados = json.loads(texto)
    assert dados["cenario"]["investimento"] == 11000
    assert dados["origem_do_custo"] == "orçamento informado pela pessoa"


def test_ferramenta_eficiencia():
    entrada = {
        "consumo_kwh": 300,
        "valor_conta": 285.0,
        "lampadas": {"quantidade": 8, "potencia_atual_w": 60, "potencia_led_w": 9, "horas_dia": 5},
    }
    texto, erro = ferramentas.executar("calcular_economia_eficiencia", entrada)
    assert erro is False
    assert json.loads(texto)["lampadas"]["economia_kwh_mes"] == 61.2


@pytest.mark.parametrize(
    "nome, entrada",
    [
        ("simular_energia_solar", {**CASA, "uf": "XX"}),
        ("simular_energia_solar", {"consumo_kwh": 300}),
        ("simular_energia_solar", {**CASA, "placas": 99}),
        ("calcular_economia_eficiencia", {"consumo_kwh": 300, "valor_conta": 285.0}),
        ("ferramenta_que_nao_existe", {}),
    ],
)
def test_ferramenta_com_entrada_invalida_devolve_erro(nome, entrada):
    texto, erro = ferramentas.executar(nome, entrada)
    assert erro is True
    assert texto


# ---------- Chat de energia ----------


def trocar_api(monkeypatch, respostas, registro):
    """Dublê da API que devolve, a cada chamada, a próxima resposta da lista."""
    fila = list(respostas)

    class Stream:
        def __init__(self, resposta):
            self.resposta = resposta

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def __aiter__(self):
            for bloco in self.resposta.content:
                yield Obj(type="content_block_start", content_block=bloco)
                if bloco.type == "text":
                    yield Obj(type="text", text=bloco.text)

        async def get_final_message(self):
            return self.resposta

    class Mensagens:
        def stream(self, **parametros):
            registro.append(json.loads(json.dumps(parametros, default=vars)))
            return Stream(fila.pop(0))

    class Cliente:
        messages = Mensagens()

        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(chat.anthropic, "AsyncAnthropic", Cliente)


def texto(t):
    return Obj(type="text", text=t, citations=None)


def test_chat_de_energia_roda_a_ferramenta_e_devolve_o_resultado(cliente, monkeypatch):
    pedido_ferramenta = Obj(type="tool_use", id="ferr_1", name="simular_energia_solar", input=CASA)
    respostas = [
        Obj(stop_reason="tool_use", content=[texto("Vou calcular."), pedido_ferramenta]),
        Obj(stop_reason="end_turn", content=[texto("A economia estimada é de R$ 237,50 por mês.")]),
    ]
    registro = []
    trocar_api(monkeypatch, respostas, registro)

    resposta = cliente.post("/api/chat", json={"modulo": "energia", "historico": [], "mensagem": "Vale a pena?"})
    recebidos = eventos(resposta)

    assert {"tipo": "status", "texto": "Fazendo as contas…"} in recebidos
    assert recebidos[-1] == {"tipo": "fim"}
    assert len(registro) == 2
    # A primeira chamada leva as ferramentas e o trecho do módulo de energia.
    assert {f["name"] for f in registro[0]["tools"]} == {"simular_energia_solar", "calcular_economia_eficiencia"}
    assert "Módulo atual: energia" in registro[0]["system"]
    # A segunda chamada devolve o resultado calculado pelo código, não pelo modelo.
    resultado = registro[1]["messages"][-1]["content"][0]
    assert resultado["type"] == "tool_result"
    assert resultado["tool_use_id"] == "ferr_1"
    assert resultado["is_error"] is False
    assert json.loads(resultado["content"])["cenario"]["economia_mes"] == 237.5


def test_chat_avisa_quando_as_etapas_acabam(cliente, monkeypatch):
    pedido_ferramenta = Obj(type="tool_use", id="ferr_1", name="simular_energia_solar", input=CASA)
    respostas = [Obj(stop_reason="tool_use", content=[pedido_ferramenta]) for _ in range(chat.MAX_ETAPAS)]
    trocar_api(monkeypatch, respostas, [])
    recebidos = eventos(cliente.post("/api/chat", json={"modulo": "energia", "historico": [], "mensagem": "Oi"}))
    assert {"tipo": "aviso", "texto": chat.AVISO_INCOMPLETA} in recebidos


def test_prompt_de_energia_restringe_o_assunto_e_traz_as_fontes():
    texto_prompt = prompts.montar_system_prompt("energia")
    assert "recuse com gentileza" in texto_prompt
    assert "Nunca calcule de cabeça" in texto_prompt
    assert "INPE" in texto_prompt and "ANEEL" in texto_prompt
