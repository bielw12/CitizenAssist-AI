"""Questão 04: análise bivariada e regressão linear simples.

X: consumo médio por estabelecimento comercial (kWh/mês).
Y: consumo médio por residência (kWh/mês).
Como rodar sozinho:  python -m modulos.ml.q04_bivariada
"""

import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats

from .comum import (AZUL, CURTOS, LARANJA, PASTA_SAIDAS, ROTULOS, br, estilo, imagem, mapa_de_calor,
                    p_valor, pct, salvar)

ID = "04"
TITULO = "Análise bivariada e regressão linear simples"
ARQUIVO = "q04_bivariada.py"
ENUNCIADO = (
    "Faça uma Análise Bivariada entre 02 variáveis quantitativas contendo: a) o gráfico de dispersão, com "
    "título e nomes nos eixos, e interprete; b) a covariância e a correlação linear de Pearson, e interprete; "
    "c) o gráfico de correlação linear de Pearson, e interprete; d) a reta da regressão linear simples (no "
    "gráfico de dispersão) e a equação; e) a verificação da adequação do modelo (R² e Teste F), e interprete; "
    "f) faça uma previsão."
)
X = "consumo_medio_com_kwh"
Y = "consumo_medio_res_kwh"
ALFA = 0.05

# Mapa divergente: laranja (negativo), cinza neutro (zero), azul-petróleo (positivo).
DIVERGENTE = LinearSegmentedColormap.from_list("divergente", ["#a85a17", "#f4f3f1", "#1f3a44"])


def forca(r: float) -> str:
    """PREMISSA: faixas usuais de intensidade da correlação."""
    intensidade = "fraca" if abs(r) < 0.3 else "moderada" if abs(r) < 0.7 else "forte"
    sentido = "positiva" if r > 0 else "negativa"
    return f"{intensidade} e {sentido}"


def executar(base, pasta=PASTA_SAIDAS) -> dict:
    x, y = base[X], base[Y]
    covariancia = np.cov(x, y, ddof=1)[0, 1]
    r, p_r = stats.pearsonr(x, y)
    modelo = sm.OLS(y, sm.add_constant(x)).fit()
    b0, b1 = modelo.params["const"], modelo.params[X]

    # Previsão: consumo comercial médio observado em 2025.
    x0 = base.loc[base["ano"] == 2025, X].mean()
    # Estados cuja média de consumo comercial é a maior da base (aparecem à direita no gráfico).
    medias_uf = base.groupby("uf")[[X, Y]].mean().sort_values(X, ascending=False)
    destaque = medias_uf.head(2)
    previsao = modelo.get_prediction(np.array([[1.0, x0]])).summary_frame(alpha=0.05).iloc[0]

    estilo()
    figura, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(x, y, s=8, color=AZUL, alpha=0.25, linewidths=0)
    ax.set_title("Consumo por residência x consumo por estabelecimento comercial")
    ax.set_xlabel(ROTULOS[X])
    ax.set_ylabel(ROTULOS[Y])
    dispersao = salvar(figura, pasta, "q04_dispersao.png")

    figura, ax = plt.subplots(figsize=(4.6, 3.8))
    matriz = base[[X, Y]].corr().rename(index=CURTOS, columns=CURTOS)
    imagem_ = mapa_de_calor(ax, matriz, DIVERGENTE, vmin=-1, vmax=1)
    figura.colorbar(imagem_, ax=ax, shrink=0.8, label="r de Pearson")
    ax.set_title("Correlação linear de Pearson")
    correlacao = salvar(figura, pasta, "q04_correlacao.png")

    figura, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(x, y, s=8, color=AZUL, alpha=0.25, linewidths=0, label="Registros (estado e mês)")
    eixo = np.linspace(x.min(), x.max(), 100)
    ax.plot(eixo, b0 + b1 * eixo, color=LARANJA, linewidth=2.5, label=f"ŷ = {br(b0)} + {br(b1, 4)}·x")
    ax.set_title("Reta de regressão linear simples")
    ax.set_xlabel(ROTULOS[X])
    ax.set_ylabel(ROTULOS[Y])
    ax.legend()
    regressao = salvar(figura, pasta, "q04_regressao.png")

    resposta = f"""\
**Variáveis:** X = consumo médio por estabelecimento comercial e Y = consumo médio por residência, ambos em kWh por mês, para cada estado e mês ({br(len(base), 0)} registros). Usamos médias por consumidor, e não totais, para não medir só o tamanho do estado: estados grandes têm muito consumo residencial e comercial ao mesmo tempo.

### a) Gráfico de dispersão

{imagem(dispersao, "Dispersão do consumo médio por residência contra o consumo médio por estabelecimento comercial")}

Os pontos sobem da esquerda para a direita: onde as lojas e escritórios consomem mais por unidade, as residências também tendem a consumir mais. A nuvem é larga, o que indica que outros fatores também influenciam o consumo das casas. À direita aparece um grupo separado, com consumo comercial alto e residencial moderado: são principalmente registros de {destaque.index[0]} e {destaque.index[1]}, os estados com maior consumo médio por estabelecimento comercial ({br(destaque.iloc[0][X], 0)} e {br(destaque.iloc[1][X], 0)} kWh), mas com consumo por residência de {br(destaque.iloc[0][Y], 0)} e {br(destaque.iloc[1][Y], 0)} kWh. Esse grupo puxa a reta para baixo do lado direito do gráfico.

### b) Covariância e correlação de Pearson

| Medida | Valor |
|---|---|
| Covariância | {br(covariancia)} kWh² |
| Correlação de Pearson (r) | {br(r, 4)} |
| Valor-p da correlação | {p_valor(p_r)} |

A covariância positiva mostra que as duas variáveis crescem juntas, mas seu valor depende das unidades e não indica a intensidade. A correlação r = {br(r, 4)} é **{forca(r)}**, e o valor-p {p_valor(p_r)} indica que ela é estatisticamente diferente de zero. Correlação não é causa: as duas variáveis provavelmente respondem a fatores comuns, como o clima quente (uso de ar-condicionado) e a renda da região.

### c) Gráfico de correlação

{imagem(correlacao, "Mapa de calor da correlação de Pearson entre as duas variáveis")}

A cor indica o sentido e a força da relação: quanto mais escura, mais forte; azul é positiva e laranja seria negativa. A diagonal vale 1 porque é cada variável comparada com ela mesma.

### d) Reta e equação da regressão linear simples

{imagem(regressao, "Dispersão com a reta de regressão linear simples")}

**ŷ = {br(b0)} + {br(b1, 4)} · x**

- Inclinação ({br(b1, 4)}): cada 100 kWh a mais no consumo médio comercial está associado a {br(b1 * 100)} kWh a mais no consumo médio por residência.
- Intercepto ({br(b0)}): é o ponto em que a reta corta o eixo Y. Não tem interpretação prática, porque não existe consumo comercial igual a zero na base.

### e) Adequação do modelo

| Medida | Valor |
|---|---|
| R² | {br(modelo.rsquared, 4)} |
| Estatística F | {br(modelo.fvalue)} |
| Valor-p do teste F | {p_valor(modelo.f_pvalue)} |

O R² indica que o consumo comercial explica **{pct(modelo.rsquared, 1)}** da variação do consumo por residência; o restante depende de outros fatores. O teste F tem valor-p {p_valor(modelo.f_pvalue)}, menor que {br(ALFA * 100, 0)}%: o modelo é estatisticamente significativo, ou seja, melhor do que usar apenas a média.

### f) Previsão

Para um estado com consumo comercial de {br(x0)} kWh por estabelecimento (média observada em 2025):

ŷ = {br(b0)} + {br(b1, 4)} × {br(x0)} = **{br(previsao['mean'])} kWh por residência por mês**

Intervalo de previsão de 95% para um estado e mês específicos: de {br(previsao['obs_ci_lower'])} a {br(previsao['obs_ci_upper'])} kWh. O intervalo é largo, coerente com o R² de {pct(modelo.rsquared, 1)}: a previsão serve como referência, não como valor exato.

*Premissa: intensidade da correlação classificada como fraca (|r| < 0,3), moderada (0,3 a 0,7) ou forte (≥ 0,7). Nível de significância de {br(ALFA * 100, 0)}% nos testes desta questão.*
"""
    return {
        "id": ID, "titulo": TITULO, "enunciado": ENUNCIADO, "arquivo": ARQUIVO,
        "graficos": [dispersao, correlacao, regressao],
        "valores": {
            "x": X, "y": Y, "n": int(len(base)), "covariancia": covariancia, "pearson_r": r, "pearson_p": p_r,
            "estados_maior_consumo_comercial": list(destaque.index),
            "intercepto": b0, "inclinacao": b1, "r2": modelo.rsquared, "f": modelo.fvalue, "f_p": modelo.f_pvalue,
            "previsao_x": x0, "previsao_y": previsao["mean"],
            "previsao_intervalo_95": [previsao["obs_ci_lower"], previsao["obs_ci_upper"]],
        },
        "resposta_md": resposta,
    }


if __name__ == "__main__":
    from .preparar_base import preparar

    print(executar(preparar())["resposta_md"])
