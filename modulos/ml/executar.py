"""Roda toda a análise de Modelagem Linear e grava os resultados.

Gera em modulos/ml/saidas/: resultados.json, os gráficos (.png) e relatorio.md.
Como rodar (na pasta do projeto, com o ambiente virtual ativado):

    python -m modulos.ml.executar
"""

import json
from pathlib import Path

from . import q02_probabilidade, q03_teste_hipotese, q04_bivariada, q05_multivariada, q06_logistica, relatorio
from .comum import BASE_CSV, PASTA_SAIDAS, br
from .preparar_base import ULTIMO_ANO, preparar

QUESTOES = [q02_probabilidade, q03_teste_hipotese, q04_bivariada, q05_multivariada, q06_logistica]

FONTE = {
    "nome": "EPE (Empresa de Pesquisa Energética). Consumo mensal de energia elétrica por classe (regiões e subsistemas)",
    "pagina": "https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/consumo-de-energia-eletrica",
    "arquivo": "https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/Documents/CONSUMO%20MENSAL%20DE%20ENERGIA%20EL%C3%89TRICA%20POR%20CLASSE.xlsx",
    "acesso": "14/11/2026",
}


def arredondar(valor):
    """Arredonda os números do JSON para que o arquivo não mude por diferenças mínimas entre computadores."""
    if isinstance(valor, float):
        return round(valor, 6)
    if isinstance(valor, dict):
        return {str(chave): arredondar(v) for chave, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [arredondar(v) for v in valor]
    if hasattr(valor, "item"):  # números do numpy
        return arredondar(valor.item())
    return valor


def descrever_base(base) -> dict:
    descricao = f"""\
- **Fonte:** {FONTE['nome']}. Arquivo baixado em {FONTE['acesso']} da página {FONTE['pagina']}
- **Recorte:** os 27 estados, mês a mês, de janeiro de 2004 a dezembro de {ULTIMO_ANO}: **{br(len(base), 0)} registros** (27 × 12 × {ULTIMO_ANO - 2003}). Os meses de 2026 ficaram de fora porque a EPE os marca como preliminares.
- **Unidade de observação:** um estado em um mês. Os dados são totais do estado, não de residências individuais.
- **Variáveis usadas:**

| Variável | Como foi calculada | Unidade |
|---|---|---|
| Consumo médio por residência | consumo residencial (MWh) × 1000 ÷ número de consumidores residenciais | kWh/mês |
| Consumo médio por estabelecimento comercial | consumo comercial (MWh) × 1000 ÷ número de consumidores comerciais | kWh/mês |
| Participação industrial | consumo industrial ÷ consumo total × 100 | % |
| Ano | ano do registro | ano |

Nenhum registro precisou ser removido: as colunas usadas não têm valores ausentes no período. Arquivos: `modulos/ml/dados/` (planilha original da EPE e a tabela organizada em `.csv`)."""
    return {"fonte": FONTE, "registros": int(len(base)), "periodo": f"01/2004 a 12/{ULTIMO_ANO}", "descricao_md": descricao}


def gerar(pasta: Path = PASTA_SAIDAS) -> dict:
    base = preparar()
    resultados = {"base": descrever_base(base), "questoes": [q.executar(base, pasta) for q in QUESTOES]}
    resultados = arredondar(resultados)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "relatorio.md").write_text(relatorio.montar(resultados), encoding="utf-8")
    return resultados


def main():
    base = preparar()
    base.to_csv(BASE_CSV, index=False, float_format="%.6f")
    resultados = gerar()
    print(f"Base: {resultados['base']['registros']} registros gravados em {BASE_CSV}")
    for q in resultados["questoes"]:
        print(f"Questão {q['id']}: {q['titulo']} — gráficos: {', '.join(q['graficos'])}")
    print(f"Resultados, gráficos e relatório gravados em {PASTA_SAIDAS}")


if __name__ == "__main__":
    main()
