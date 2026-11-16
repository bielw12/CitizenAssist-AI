"""Questão 05: análise multivariada e regressão linear múltipla.

Y: consumo médio por residência (kWh/mês).
X: consumo médio por estabelecimento comercial, participação da indústria no consumo e ano.
Como rodar sozinho:  python -m modulos.ml.q05_multivariada
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .comum import AZUL, CURTOS, PASTA_SAIDAS, br, estilo, imagem, mapa_de_calor, p_valor, pct, salvar
from .q04_bivariada import DIVERGENTE

ID = "05"
TITULO = "Análise multivariada e regressão linear múltipla"
ARQUIVO = "q05_multivariada.py"
ENUNCIADO = (
    "Faça uma Análise Multivariada entre, pelo menos, 03 variáveis quantitativas contendo: a) o gráfico de "
    "dispersão, e interprete; b) a matriz de covariância e a matriz de correlação linear de Pearson, e "
    "interprete; c) o gráfico de correlação linear de Pearson, e interprete; d) a equação da regressão "
    "linear múltipla; e) a verificação da adequação do modelo (R² e Teste F), e interprete; f) faça uma "
    "previsão utilizando, pelo menos, 02 variáveis explicativas."
)
Y = "consumo_medio_res_kwh"
XS = ["consumo_medio_com_kwh", "participacao_industrial", "ano"]
UNIDADES = {"consumo_medio_com_kwh": "kWh", "participacao_industrial": "ponto percentual", "ano": "ano"}


def tabela_md(matriz: pd.DataFrame, casas: int) -> str:
    nomes = [CURTOS[c] for c in matriz.columns]
    linhas = ["| | " + " | ".join(nomes) + " |", "|---|" + "---|" * len(nomes)]
    for indice, linha in matriz.iterrows():
        linhas.append(f"| **{CURTOS[indice]}** | " + " | ".join(br(v, casas) for v in linha) + " |")
    return "\n".join(linhas)


def executar(base, pasta=PASTA_SAIDAS) -> dict:
    variaveis = [Y] + XS
    dados = base[variaveis]
    covariancias = dados.cov()
    correlacoes = dados.corr()
    modelo = sm.OLS(base[Y], sm.add_constant(base[XS])).fit()
    simples = sm.OLS(base[Y], sm.add_constant(base[XS[0]])).fit()

    recente = base[base["ano"] == 2025]
    cenario = {"consumo_medio_com_kwh": recente["consumo_medio_com_kwh"].mean(),
               "participacao_industrial": recente["participacao_industrial"].mean(), "ano": 2025}
    entrada = np.array([[1.0] + [cenario[v] for v in XS]])
    previsao = modelo.get_prediction(entrada).summary_frame(alpha=0.05).iloc[0]

    estilo()
    eixos = pd.plotting.scatter_matrix(
        dados.rename(columns=CURTOS), figsize=(9, 9), s=4, alpha=0.2, color=AZUL, diagonal="hist",
        hist_kwds={"color": AZUL, "alpha": 0.6, "bins": 30, "edgecolor": "white"},
    )
    for ax in eixos.ravel():
        ax.grid(False)
        ax.xaxis.label.set_size(8)
        ax.yaxis.label.set_size(8)
        ax.tick_params(labelsize=7)
    figura = eixos[0, 0].get_figure()
    figura.suptitle("Matriz de dispersão das quatro variáveis", fontweight="bold")
    dispersao = salvar(figura, pasta, "q05_dispersao.png")

    figura, ax = plt.subplots(figsize=(6.4, 5.2))
    imagem_ = mapa_de_calor(ax, correlacoes.rename(index=CURTOS, columns=CURTOS), DIVERGENTE, vmin=-1, vmax=1)
    figura.colorbar(imagem_, ax=ax, shrink=0.8, label="r de Pearson")
    ax.set_title("Matriz de correlação de Pearson")
    correlacao = salvar(figura, pasta, "q05_correlacao.png")

    r = correlacoes[Y]
    coef = modelo.params
    termos = " ".join(f"{'+' if coef[v] >= 0 else '−'} {br(abs(coef[v]), 4)}·{CURTOS[v].lower().replace(' ', '_')}" for v in XS)
    interpretacoes = "\n".join(
        f"- **{CURTOS[v]}** ({br(coef[v], 4)}; valor-p {p_valor(modelo.pvalues[v])}): mantidas as outras variáveis "
        f"constantes, cada 1 {UNIDADES[v]} a mais está associado a {br(abs(coef[v]), 4)} kWh "
        f"{'a mais' if coef[v] >= 0 else 'a menos'} no consumo por residência."
        for v in XS
    )

    resposta = f"""\
**Variáveis:** consumo médio por residência (Y), consumo médio por estabelecimento comercial, participação da indústria no consumo total do estado (%) e ano. A participação industrial indica o perfil econômico do estado; o ano capta a tendência ao longo do tempo.

### a) Gráfico de dispersão

{imagem(dispersao, "Matriz de dispersão entre as quatro variáveis, com histogramas na diagonal")}

Cada quadro cruza duas variáveis. O consumo por residência sobe junto com o consumo comercial e com o ano, e tende a cair quando a indústria tem participação maior no consumo do estado. A nuvem do ano forma colunas porque cada ano tem 324 registros (27 estados × 12 meses).

### b) Matrizes de covariância e de correlação

Covariância (unidades diferentes por variável, por isso só o sinal é comparável):

{tabela_md(covariancias, 2)}

Correlação de Pearson:

{tabela_md(correlacoes, 4)}

Em relação ao consumo por residência, a correlação é de {br(r['consumo_medio_com_kwh'], 2)} com o consumo comercial, {br(r['participacao_industrial'], 2)} com a participação industrial e {br(r['ano'], 2)} com o ano. Entre as variáveis explicativas, as correlações são baixas (no máximo {br(correlacoes.loc[XS, XS].where(~np.eye(3, dtype=bool)).abs().max().max(), 2)} em valor absoluto), o que reduz o risco de uma variável repetir a informação da outra no modelo.

### c) Gráfico de correlação

{imagem(correlacao, "Mapa de calor da matriz de correlação de Pearson")}

Azul indica relação positiva e laranja, negativa; quanto mais escura a cor, mais forte a relação. O quadro confirma a tabela: o consumo comercial é a variável mais ligada ao consumo por residência.

### d) Equação da regressão linear múltipla

**ŷ = {br(coef['const'], 4)} {termos}**

{interpretacoes}

O intercepto ({br(coef['const'], 2)}) é grande porque a variável ano vale cerca de 2.000; ele não tem interpretação prática isolada.

### e) Adequação do modelo

| Medida | Valor |
|---|---|
| R² | {br(modelo.rsquared, 4)} |
| R² ajustado | {br(modelo.rsquared_adj, 4)} |
| Estatística F | {br(modelo.fvalue)} |
| Valor-p do teste F | {p_valor(modelo.f_pvalue)} |
| R² da regressão simples (só consumo comercial) | {br(simples.rsquared, 4)} |

O modelo explica **{pct(modelo.rsquared, 1)}** da variação do consumo por residência, contra {pct(simples.rsquared, 1)} da regressão simples da questão 04. O teste F (valor-p {p_valor(modelo.f_pvalue)}) indica que o conjunto das variáveis é estatisticamente significativo. Ainda assim, parte da variação continua sem explicação, provavelmente por fatores que não estão na base, como temperatura e renda.

### f) Previsão

Cenário com as médias de 2025: consumo comercial de {br(cenario['consumo_medio_com_kwh'])} kWh por estabelecimento, participação industrial de {br(cenario['participacao_industrial'])}% e ano 2025.

ŷ = **{br(previsao['mean'])} kWh por residência por mês**

Intervalo de previsão de 95%: de {br(previsao['obs_ci_lower'])} a {br(previsao['obs_ci_upper'])} kWh. Usar o modelo para anos futuros seria extrapolação e exige cuidado.
"""
    return {
        "id": ID, "titulo": TITULO, "enunciado": ENUNCIADO, "arquivo": ARQUIVO,
        "graficos": [dispersao, correlacao],
        "valores": {
            "y": Y, "x": XS, "n": int(len(base)),
            "covariancias": covariancias.to_dict(), "correlacoes": correlacoes.to_dict(),
            "coeficientes": coef.to_dict(), "p_valores": modelo.pvalues.to_dict(),
            "r2": modelo.rsquared, "r2_ajustado": modelo.rsquared_adj, "f": modelo.fvalue, "f_p": modelo.f_pvalue,
            "r2_simples": simples.rsquared, "cenario": cenario, "previsao_y": previsao["mean"],
            "previsao_intervalo_95": [previsao["obs_ci_lower"], previsao["obs_ci_upper"]],
        },
        "resposta_md": resposta,
    }


if __name__ == "__main__":
    from .preparar_base import preparar

    print(executar(preparar())["resposta_md"])
