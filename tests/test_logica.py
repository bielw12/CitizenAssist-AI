"""Testes do módulo de Decisão lógica (Computer Science).

Validam, nas 16 combinações, a equivalência entre a tabela-verdade do grupo, a expressão
original do grupo, a expressão simplificada e o resultado executado (programa e rota da API).
"""

from itertools import product

import pytest
from fastapi.testclient import TestClient

from app import main
from modulos.logica import cnh, relatorio

COMBINACOES = list(product((0, 1), repeat=4))


@pytest.fixture
def cliente():
    return TestClient(main.app)


def test_tabela_do_grupo_tem_as_16_combinacoes_em_ordem():
    assert [linha[:4] for linha in cnh.TABELA_DO_GRUPO] == COMBINACOES


@pytest.mark.parametrize("linha", cnh.TABELA_DO_GRUPO)
def test_equivalencia_em_todas_as_combinacoes(linha, cliente):
    a, b, c, d, x_do_grupo = linha
    entradas = {"a": a, "b": b, "c": c, "d": d}
    assert cnh.regra_do_grupo(a, b, c, d) == x_do_grupo
    assert cnh.expressao_simplificada(a, b, c, d) == x_do_grupo
    assert cnh.avaliar(entradas)["x"] == x_do_grupo
    assert cliente.post("/api/logica/avaliar", json=entradas).json()["x"] == x_do_grupo


def test_portas_intermediarias_do_circuito():
    r = cnh.avaliar({"a": 1, "b": 1, "c": 1, "d": 0})
    assert r["portas"] == {"a·b": 1, "c·d": 0, "x": 0}
    assert r["apto"] is False


def test_orientacao_lista_o_que_falta():
    r = cnh.avaliar({"a": 1, "b": 0, "c": 1, "d": 0})
    assert r["pendentes"] == ["saber ler e escrever", "ter um documento de identidade"]
    assert "saber ler e escrever" in r["orientacao"]
    apto = cnh.avaliar({"a": 1, "b": 1, "c": 1, "d": 1})
    assert apto["apto"] is True and apto["pendentes"] == []
    assert "Detran" in apto["orientacao"]


@pytest.mark.parametrize(
    "corpo",
    [
        {"a": 2, "b": 1, "c": 1, "d": 1},
        {"a": "sim", "b": 1, "c": 1, "d": 1},
        {"a": True, "b": 1, "c": 1, "d": 1},
        {"a": 1, "b": 1, "c": 1},
        {"a": None, "b": 1, "c": 1, "d": 1},
    ],
)
def test_rota_recusa_entradas_invalidas(cliente, corpo):
    resposta = cliente.post("/api/logica/avaliar", json=corpo)
    assert resposta.status_code == 422
    assert "use 0 (não) ou 1 (sim)" in resposta.json()["erro"]


def test_rota_recusa_corpo_que_nao_e_objeto(cliente):
    resposta = cliente.post("/api/logica/avaliar", json=[1, 1, 1, 1])
    assert resposta.status_code == 422
    assert "erro" in resposta.json()


@pytest.mark.parametrize("valor", ["talvez", "2", "", 5, None, 1.5])
def test_conversao_recusa_valores_invalidos(valor):
    with pytest.raises(cnh.EntradaInvalida):
        cnh.para_bit(valor)


@pytest.mark.parametrize("valor, bit", [("s", 1), ("Sim", 1), ("1", 1), (" n ", 0), ("não", 0), ("0", 0), (True, 1), (0, 0)])
def test_conversao_aceita_respostas_validas(valor, bit):
    assert cnh.para_bit(valor) == bit


def test_programa_de_terminal_pede_de_novo_quando_a_resposta_e_invalida():
    respostas = iter(["talvez", "s", "s", "x", "s", "n"])
    mensagens = []
    resultado = cnh.main(entrada=lambda pergunta: next(respostas), saida=mensagens.append)
    assert resultado["entradas"] == {"a": 1, "b": 1, "c": 1, "d": 0}
    assert sum("Não entendi" in m for m in mensagens) == 2
    assert any("ter um documento de identidade" in m for m in mensagens)


def test_relatorio_tem_as_16_linhas_de_teste_e_as_fontes(cliente):
    texto = relatorio.montar()
    for a, b, c, d in COMBINACOES:
        assert f"| {a} | {b} | {c} | {d} |" in texto
    assert "as quatro representações coincidem nas 16 combinações" in texto
    assert "Resolução CONTRAN nº 1.020" in texto
    assert "[PENDENTE: imagem do circuito simplificado" in texto
    assert cliente.get("/api/logica/relatorio").json()["markdown"] == texto


def test_imagens_do_grupo_e_dados_da_entrega(cliente):
    for nome in ("circuito_original.png", "mapa_karnaugh.png", "tabela_verdade.png"):
        assert cliente.get(f"/static/logica/{nome}").headers["content-type"] == "image/png"
    dados = cliente.get("/api/logica/dados").json()
    assert len(dados["tabela_do_grupo"]) == 16
    assert dados["expressao_do_grupo"] == "x = (a·b)·(c·d)"
