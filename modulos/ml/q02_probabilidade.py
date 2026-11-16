"""Questão 02: probabilidades com a distribuição normal.

Variável: consumo médio de energia por residência (kWh/mês), por estado e mês.
Como rodar sozinho:  python -m modulos.ml.q02_probabilidade
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from .comum import AZUL, LARANJA, PASTA_SAIDAS, ROTULOS, TINTA, br, estilo, imagem, pct, salvar

ID = "02"
TITULO = "Probabilidade com a distribuição normal"
ARQUIVO = "q02_probabilidade.py"
ENUNCIADO = (
    "Assumindo que as variáveis numéricas escolhidas seguem uma Distribuição Normal de Probabilidade, "
    "escolher uma variável aleatória da base de dados e determinar: a) a probabilidade desta variável ser "
    "menor do que a média dos registros, classificando o evento; b) a probabilidade desta variável ser "
    "maior que a mediana dos registros, classificando o evento."
)
VARIAVEL = "consumo_medio_res_kwh"


def classificar(p: float) -> str:
    """PREMISSA: escala usual de classificação de eventos pela probabilidade."""
    if p == 0:
        return "evento impossível"
    if p == 1:
        return "evento certo"
    if abs(p - 0.5) < 0.005:
        return "evento equiprovável (tem a mesma chance de ocorrer e de não ocorrer)"
    if p < 0.5:
        return "evento pouco provável (menos de 50% de chance)"
    return "evento provável (mais de 50% de chance)"


def executar(base, pasta=PASTA_SAIDAS) -> dict:
    x = base[VARIAVEL]
    media = x.mean()
    desvio = x.std(ddof=0)
    mediana = x.median()

    p_menor_media = stats.norm.cdf(media, loc=media, scale=desvio)
    z_mediana = (mediana - media) / desvio
    p_maior_mediana = 1 - stats.norm.cdf(mediana, loc=media, scale=desvio)
    real_menor_media = (x < media).mean()
    real_maior_mediana = (x > mediana).mean()
    assimetria = stats.skew(x)

    estilo()
    figura, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(x, bins=60, density=True, color=AZUL, alpha=0.55, edgecolor="white", linewidth=0.5,
            label="Registros (estado e mês)")
    eixo = np.linspace(x.min(), x.max(), 400)
    ax.plot(eixo, stats.norm.pdf(eixo, media, desvio), color=LARANJA, linewidth=2, label="Curva normal ajustada")
    ax.axvline(media, color=TINTA, linewidth=1.5, label=f"Média: {br(media)} kWh")
    ax.axvline(mediana, color=TINTA, linewidth=1.5, linestyle="--", label=f"Mediana: {br(mediana)} kWh")
    ax.set_title("Distribuição do consumo médio por residência")
    ax.set_xlabel(ROTULOS[VARIAVEL])
    ax.set_ylabel("Densidade")
    ax.legend()
    grafico = salvar(figura, pasta, "q02_distribuicao.png")

    resposta = f"""\
**Variável escolhida:** consumo médio de energia elétrica por residência, em kWh por mês, calculado para cada estado e cada mês. É a variável mais próxima da conta de luz de uma família.

| Medida | Valor |
|---|---|
| Registros | {br(len(x), 0)} |
| Média (μ) | {br(media)} kWh |
| Desvio padrão populacional (σ) | {br(desvio)} kWh |
| Mediana | {br(mediana)} kWh |

{imagem(grafico, "Histograma do consumo médio por residência com a curva normal, a média e a mediana")}

### a) P(X < média)

Na distribuição normal a média fica exatamente no centro da curva, então:

P(X < {br(media)}) = Φ(0) = **{pct(p_menor_media)}**

Classificação: **{classificar(p_menor_media)}**.

### b) P(X > mediana)

z = (mediana − μ) ÷ σ = ({br(mediana)} − {br(media)}) ÷ {br(desvio)} = {br(z_mediana, 4)}

P(X > {br(mediana)}) = 1 − Φ({br(z_mediana, 4)}) = **{pct(p_maior_mediana)}**

Classificação: **{classificar(p_maior_mediana)}**.

### Interpretação

- Pelo modelo normal, metade dos registros fica abaixo da média. Nos dados reais, porém, {pct(real_menor_media, 1)} dos registros estão abaixo da média.
- A mediana ({br(mediana)} kWh) é {"menor" if mediana < media else "maior"} que a média ({br(media)} kWh), e a assimetria é {br(assimetria)}. Isso mostra uma distribuição {"com cauda longa à direita: alguns estados e meses têm consumo bem acima do comum, o que puxa a média para cima" if assimetria > 0 else "com cauda à esquerda"}.
- Por isso o modelo normal dá {pct(p_maior_mediana, 1)} para P(X > mediana), enquanto nos dados essa proporção é {pct(real_maior_mediana, 1)}, por definição de mediana. A suposição de normalidade, pedida no enunciado, é uma aproximação.

*Premissa: a classificação dos eventos usa a escala impossível, pouco provável, equiprovável, provável e certo, pois não tivemos acesso ao material de aula.*
"""
    return {
        "id": ID, "titulo": TITULO, "enunciado": ENUNCIADO, "arquivo": ARQUIVO,
        "graficos": [grafico],
        "valores": {
            "variavel": VARIAVEL, "n": int(len(x)), "media": media, "desvio_padrao_populacional": desvio,
            "mediana": mediana, "p_menor_que_media": p_menor_media, "z_mediana": z_mediana,
            "p_maior_que_mediana": p_maior_mediana, "proporcao_real_menor_que_media": real_menor_media,
            "proporcao_real_maior_que_mediana": real_maior_mediana, "assimetria": assimetria,
            "classificacao_a": classificar(p_menor_media), "classificacao_b": classificar(p_maior_mediana),
        },
        "resposta_md": resposta,
    }


if __name__ == "__main__":
    from .preparar_base import preparar

    print(executar(preparar())["resposta_md"])
