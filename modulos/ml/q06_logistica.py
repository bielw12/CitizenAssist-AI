"""Questão 06: regressão logística binária.

Y (binária): 1 = consumo médio por residência acima da mediana nacional; 0 = caso contrário.
X: consumo médio por estabelecimento comercial, participação da indústria no consumo e ano.
Como rodar sozinho:  python -m modulos.ml.q06_logistica
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.colors import LinearSegmentedColormap

from .comum import CURTOS, PASTA_SAIDAS, SEMENTE, br, estilo, imagem, mapa_de_calor, p_valor, pct, salvar

ID = "06"
TITULO = "Regressão logística binária"
ARQUIVO = "q06_logistica.py"
ENUNCIADO = (
    "Faça uma Análise Multivariada entre, pelo menos, 03 variáveis quantitativas contendo: a) a equação da "
    "regressão logística binária; b) a matriz de confusão e a acurácia, interprete os resultados; c) uma "
    "classificação utilizando, pelo menos, 02 variáveis explicativas."
)
VARIAVEL_BASE = "consumo_medio_res_kwh"
XS = ["consumo_medio_com_kwh", "participacao_industrial", "ano"]
CORTE = 0.5
PROPORCAO_TREINO = 0.7
SEQUENCIAL = LinearSegmentedColormap.from_list("sequencial", ["#eef5f7", "#1f3a44"])


def executar(base, pasta=PASTA_SAIDAS) -> dict:
    limite = base[VARIAVEL_BASE].median()
    dados = base[XS].copy()
    dados["alto"] = (base[VARIAVEL_BASE] > limite).astype(int)

    treino = dados.sample(frac=PROPORCAO_TREINO, random_state=SEMENTE)
    teste = dados.drop(treino.index)
    modelo = sm.Logit(treino["alto"], sm.add_constant(treino[XS])).fit(disp=False)
    coef = modelo.params

    prob = modelo.predict(sm.add_constant(teste[XS]))
    previsto = (prob >= CORTE).astype(int)
    real = teste["alto"]
    vn = int(((previsto == 0) & (real == 0)).sum())
    fp = int(((previsto == 1) & (real == 0)).sum())
    fn = int(((previsto == 0) & (real == 1)).sum())
    vp = int(((previsto == 1) & (real == 1)).sum())
    acuracia = (vn + vp) / len(teste)
    sensibilidade = vp / (vp + fn)
    especificidade = vn / (vn + fp)
    referencia = max(real.mean(), 1 - real.mean())

    recente = base[base["ano"] == 2025]
    cenario = {"consumo_medio_com_kwh": recente["consumo_medio_com_kwh"].mean(),
               "participacao_industrial": recente["participacao_industrial"].mean(), "ano": 2025}
    logito = coef["const"] + sum(coef[v] * cenario[v] for v in XS)
    prob_cenario = 1 / (1 + np.exp(-logito))
    classe = int(prob_cenario >= CORTE)

    estilo()
    figura, ax = plt.subplots(figsize=(5.4, 4.4))
    matriz = pd.DataFrame([[vn, fp], [fn, vp]], index=["Real: não alto", "Real: alto"],
                          columns=["Previsto: não alto", "Previsto: alto"])
    mapa_de_calor(ax, matriz, SEQUENCIAL, vmin=0, vmax=max(vn, fp, fn, vp), formato=lambda v: br(v, 0))
    ax.set_title("Matriz de confusão (dados de teste)")
    grafico = salvar(figura, pasta, "q06_matriz_confusao.png")

    termos = " ".join(f"{'+' if coef[v] >= 0 else '−'} {br(abs(coef[v]), 6)}·{CURTOS[v].lower().replace(' ', '_')}" for v in XS)
    unidades = {"consumo_medio_com_kwh": (100, "100 kWh a mais no consumo comercial"),
                "participacao_industrial": (1, "1 ponto percentual a mais de participação industrial"),
                "ano": (1, "1 ano a mais")}
    chances = "\n".join(
        f"- **{CURTOS[v]}** (valor-p {p_valor(modelo.pvalues[v])}): {unidades[v][1]} "
        f"multiplica a chance de consumo alto por {br(np.exp(coef[v] * unidades[v][0]), 3)}."
        for v in XS
    )

    resposta = f"""\
**Variável resposta (binária):** "consumo alto por residência", igual a 1 quando o consumo médio por residência do estado no mês passa da mediana de todos os registros ({br(limite)} kWh) e 0 caso contrário.
**Variáveis explicativas:** consumo médio por estabelecimento comercial (kWh), participação da indústria no consumo (%) e ano.

Para medir o acerto de forma honesta, os {br(len(dados), 0)} registros foram divididos ao acaso (semente {SEMENTE}): {pct(PROPORCAO_TREINO, 0)} para ajustar o modelo ({br(len(treino), 0)} registros) e {pct(1 - PROPORCAO_TREINO, 0)} para testar ({br(len(teste), 0)} registros que o modelo não viu).

### a) Equação da regressão logística binária

P(consumo alto) = 1 ÷ (1 + e^−z), com

**z = {br(coef['const'], 4)} {termos}**

{chances}

### b) Matriz de confusão e acurácia

{imagem(grafico, "Matriz de confusão do modelo nos dados de teste")}

| | Previsto: não alto | Previsto: alto |
|---|---|---|
| **Real: não alto** | {vn} (acertos) | {fp} (falsos positivos) |
| **Real: alto** | {fn} (falsos negativos) | {vp} (acertos) |

| Medida | Valor |
|---|---|
| Acurácia | {pct(acuracia, 1)} |
| Sensibilidade (acerto entre os casos altos) | {pct(sensibilidade, 1)} |
| Especificidade (acerto entre os casos não altos) | {pct(especificidade, 1)} |
| Acurácia de quem sempre chuta a classe mais comum | {pct(referencia, 1)} |
| Pseudo R² de McFadden | {br(modelo.prsquared, 4)} |

O modelo acerta **{pct(acuracia, 1)}** dos registros de teste, {br((acuracia - referencia) * 100, 1)} pontos percentuais acima de simplesmente chutar sempre a classe mais comum ({pct(referencia, 1)}). {"Os erros se dividem de forma parecida entre falsos positivos e falsos negativos" if abs(fp - fn) <= 0.2 * max(fp, fn) else ("Erra mais classificando como alto o que não é (falsos positivos)" if fp > fn else "Erra mais deixando de reconhecer casos altos (falsos negativos)")}.

### c) Classificação de um novo caso

Cenário com as médias de 2025: consumo comercial de {br(cenario['consumo_medio_com_kwh'])} kWh, participação industrial de {br(cenario['participacao_industrial'])}% e ano 2025.

z = {br(logito, 4)} e P(consumo alto) = **{pct(prob_cenario, 1)}**. Com o corte em {br(CORTE * 100, 0)}%, o caso é classificado como **{"consumo alto por residência" if classe else "consumo não alto por residência"}**.

*Premissas: a variável binária foi definida pela mediana, para dividir a base em dois grupos de tamanho parecido; o corte de classificação é {br(CORTE * 100, 0)}%; a divisão treino/teste ({pct(PROPORCAO_TREINO, 0)}/{pct(1 - PROPORCAO_TREINO, 0)}) é aleatória por registro, então um mesmo estado aparece nos dois grupos em meses diferentes.*
"""
    return {
        "id": ID, "titulo": TITULO, "enunciado": ENUNCIADO, "arquivo": ARQUIVO,
        "graficos": [grafico],
        "valores": {
            "limite_mediana": limite, "x": XS, "n_treino": int(len(treino)), "n_teste": int(len(teste)),
            "coeficientes": coef.to_dict(), "p_valores": modelo.pvalues.to_dict(),
            "matriz_confusao": {"vn": vn, "fp": fp, "fn": fn, "vp": vp}, "acuracia": acuracia,
            "sensibilidade": sensibilidade, "especificidade": especificidade, "acuracia_referencia": referencia,
            "pseudo_r2": modelo.prsquared, "cenario": cenario, "probabilidade_cenario": prob_cenario,
            "classe_cenario": classe,
        },
        "resposta_md": resposta,
    }


if __name__ == "__main__":
    from .preparar_base import preparar

    print(executar(preparar())["resposta_md"])
