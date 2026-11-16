"""Testes do módulo de Estatística: a análise é reproduzível e a tela recebe os arquivos gerados."""

import json
import re

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("pandas", reason="instale requirements-analise.txt para rodar a análise")
pytest.importorskip("statsmodels", reason="instale requirements-analise.txt para rodar a análise")

from app import main  # noqa: E402
from modulos.ml import comum, executar  # noqa: E402

SALVOS = comum.PASTA_SAIDAS / "resultados.json"


@pytest.fixture(scope="module")
def gerado(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("saidas")
    executar.gerar(pasta)
    return pasta


def test_rodar_de_novo_gera_os_mesmos_resultados(gerado):
    novo = json.loads((gerado / "resultados.json").read_text(encoding="utf-8"))
    salvo = json.loads(SALVOS.read_text(encoding="utf-8"))
    assert novo == salvo


def test_relatorio_gerado_e_o_mesmo_que_esta_no_repositorio(gerado):
    novo = (gerado / "relatorio.md").read_text(encoding="utf-8")
    salvo = (comum.PASTA_SAIDAS / "relatorio.md").read_text(encoding="utf-8")
    assert novo == salvo


def test_todas_as_questoes_e_graficos_existem(gerado):
    resultados = json.loads((gerado / "resultados.json").read_text(encoding="utf-8"))
    assert [q["id"] for q in resultados["questoes"]] == ["02", "03", "04", "05", "06"]
    for q in resultados["questoes"]:
        for grafico in q["graficos"]:
            assert (gerado / grafico).exists()
            assert f"/ml/graficos/{grafico}" in q["resposta_md"]


def test_base_tem_27_estados_e_22_anos():
    base = executar.preparar()
    assert len(base) == 27 * 12 * 22
    assert base["uf"].nunique() == 27
    assert base["ano"].min() == 2004 and base["ano"].max() == 2025


def test_valores_do_enunciado():
    testes = json.loads(SALVOS.read_text(encoding="utf-8"))["questoes"][1]["valores"]["testes"]
    assert [(t["n"], t["alfa"], t["cauda"]) for t in testes] == [(20, 0.06, "esquerda"), (25, 0.09, "direita")]


def test_relatorio_nao_tem_numero_fora_dos_resultados():
    """Os números do sumário executivo precisam aparecer nos resultados (formatados em pt-BR)."""
    resultados = json.loads(SALVOS.read_text(encoding="utf-8"))
    relatorio = (comum.PASTA_SAIDAS / "relatorio.md").read_text(encoding="utf-8")
    sumario = relatorio.split("## Sumário executivo")[1].split("## 1.")[0]
    q = {item["id"]: item["valores"] for item in resultados["questoes"]}
    esperados = [comum.br(q["02"]["media"]), comum.br(q["02"]["mediana"]), comum.pct(q["05"]["r2"], 1),
                 comum.pct(q["06"]["acuracia"], 1), comum.br(q["04"]["pearson_r"], 2)]
    for numero in esperados:
        assert numero in sumario
    assert re.search(r"\[PENDENTE", relatorio)


def test_chat_de_estatistica_recebe_o_relatorio():
    from app import prompts

    texto = prompts.montar_system_prompt("ml")
    assert "<relatorio>" in texto
    assert "Nunca invente nem recalcule resultados" in texto
    resultados = json.loads(SALVOS.read_text(encoding="utf-8"))
    assert comum.pct(resultados["questoes"][4]["valores"]["acuracia"], 1) in texto


def test_rotas_do_modulo():
    cliente = TestClient(main.app)
    assert len(cliente.get("/api/ml/resultados").json()["questoes"]) == 5
    nomes = [a["nome"] for a in cliente.get("/api/ml/codigo").json()]
    assert "q04_bivariada.py" in nomes and "__init__.py" not in nomes
    assert cliente.get("/api/ml/relatorio").json()["markdown"].startswith("# Relatório")
    assert cliente.get("/ml/graficos/q04_regressao.png").headers["content-type"] == "image/png"
