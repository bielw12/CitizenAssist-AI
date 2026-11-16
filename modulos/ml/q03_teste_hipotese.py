"""Questão 03: teste de hipótese para a média (teste z, desvio padrão populacional conhecido).

Variável: consumo médio de energia por residência (kWh/mês).
Pergunta de negócio: o consumo por residência mudou ao longo do tempo?
Como rodar sozinho:  python -m modulos.ml.q03_teste_hipotese
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from .comum import AZUL, LARANJA, PASTA_SAIDAS, SEMENTE, TINTA, br, estilo, imagem, p_valor, salvar

ID = "03"
TITULO = "Teste de hipótese para a média"
ARQUIVO = "q03_teste_hipotese.py"
ENUNCIADO = (
    "Assumindo distribuição normal, escolher uma variável e realizar um teste de hipótese para a média: "
    "a) a média amostral é menor do que a média populacional de referência, a 6% de significância, amostra "
    "de tamanho 20; b) a média amostral é maior do que a média populacional de referência, a 9% de "
    "significância, amostra de tamanho 25. Em ambos, o desvio padrão de referência é o desvio padrão "
    "populacional dos dados."
)
VARIAVEL = "consumo_medio_res_kwh"

# PREMISSA: cada amostra é sorteada (com semente fixa) de um período, para responder se o consumo
# por residência daquele período era diferente da média de todo o período de 2004 a 2025.
TESTES = [
    {"item": "a", "n": 20, "alfa": 0.06, "cauda": "esquerda", "anos": (2004, 2005)},
    {"item": "b", "n": 25, "alfa": 0.09, "cauda": "direita", "anos": (2024, 2025)},
]


def testar(base, mu0, sigma, item, n, alfa, cauda, anos):
    grupo = base[base["ano"].between(*anos)]
    amostra = grupo.sample(n=n, random_state=SEMENTE)
    media = amostra[VARIAVEL].mean()
    erro_padrao = sigma / np.sqrt(n)
    z = (media - mu0) / erro_padrao
    if cauda == "esquerda":
        z_critico = stats.norm.ppf(alfa)
        p = stats.norm.cdf(z)
        rejeita = z < z_critico
    else:
        z_critico = stats.norm.ppf(1 - alfa)
        p = 1 - stats.norm.cdf(z)
        rejeita = z > z_critico
    return {
        "item": item, "n": n, "alfa": alfa, "cauda": cauda, "anos": list(anos),
        "media_amostral": media, "erro_padrao": erro_padrao, "z": z, "z_critico": z_critico,
        "p_valor": p, "rejeita_h0": bool(rejeita),
        "amostra": [
            {"uf": r.uf, "ano": int(r.ano), "mes": int(r.mes), "valor": round(float(getattr(r, VARIAVEL)), 2)}
            for r in amostra.itertuples()
        ],
    }


def texto_teste(t, mu0, sigma):
    sinal = "<" if t["cauda"] == "esquerda" else ">"
    palavra = "menor" if t["cauda"] == "esquerda" else "maior"
    periodo = f"{t['anos'][0]} e {t['anos'][1]}"
    regiao = f"z {'<' if t['cauda'] == 'esquerda' else '>'} {br(t['z_critico'], 4)}"
    lista = "; ".join(f"{a['uf']} {a['mes']:02d}/{a['ano']}: {br(a['valor'], 1)}" for a in t["amostra"])
    if t["rejeita_h0"]:
        decisao = f"Como z = {br(t['z'], 4)} está na região de rejeição ({regiao}), **rejeitamos H₀**."
        conclusao = (f"Ao nível de {br(t['alfa'] * 100, 0)}% de significância, há evidência de que o consumo médio por "
                     f"residência entre {periodo} era {palavra} que a média de referência de {br(mu0)} kWh.")
    else:
        decisao = f"Como z = {br(t['z'], 4)} não está na região de rejeição ({regiao}), **não rejeitamos H₀**."
        conclusao = (f"Ao nível de {br(t['alfa'] * 100, 0)}% de significância, a amostra não traz evidência suficiente "
                     f"de que o consumo médio por residência entre {periodo} fosse {palavra} que {br(mu0)} kWh.")
    return f"""\
### {t['item']}) Média amostral {palavra} que a de referência (α = {br(t['alfa'] * 100, 0)}%, n = {t['n']})

Amostra: {t['n']} registros sorteados entre os meses de {periodo}.

- H₀: μ = {br(mu0)} kWh
- H₁: μ {sinal} {br(mu0)} kWh (teste unilateral à {t['cauda']})

| Etapa | Valor |
|---|---|
| Média amostral (x̄) | {br(t['media_amostral'])} kWh |
| Erro padrão (σ ÷ √n) | {br(sigma, 2)} ÷ √{t['n']} = {br(t['erro_padrao'], 4)} |
| Estatística z = (x̄ − μ) ÷ (σ ÷ √n) | {br(t['z'], 4)} |
| Valor crítico | {br(t['z_critico'], 4)} |
| Valor-p | {p_valor(t['p_valor'])} |

{decisao}

**Conclusão:** {conclusao}

Registros sorteados (estado, mês/ano: kWh): {lista}.
"""


def executar(base, pasta=PASTA_SAIDAS) -> dict:
    x = base[VARIAVEL]
    mu0 = x.mean()
    sigma = x.std(ddof=0)
    resultados = [testar(base, mu0, sigma, **config) for config in TESTES]

    estilo()
    figura, eixos = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    z_eixo = np.linspace(-4, 4, 400)
    for ax, t in zip(eixos, resultados):
        ax.plot(z_eixo, stats.norm.pdf(z_eixo), color=TINTA, linewidth=1.5)
        regiao = z_eixo <= t["z_critico"] if t["cauda"] == "esquerda" else z_eixo >= t["z_critico"]
        ax.fill_between(z_eixo[regiao], stats.norm.pdf(z_eixo[regiao]), color=LARANJA, alpha=0.45,
                        label=f"Região de rejeição (α = {br(t['alfa'] * 100, 0)}%)")
        z_visivel = float(np.clip(t["z"], -3.9, 3.9))
        ax.axvline(z_visivel, color=AZUL, linewidth=2, label=f"z calculado = {br(t['z'], 2)}")
        ax.set_title(f"{t['item']}) n = {t['n']}, amostra de {t['anos'][0]} e {t['anos'][1]}")
        ax.set_xlabel("z")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    eixos[0].set_ylabel("Densidade (normal padrão)")
    grafico = salvar(figura, pasta, "q03_teste_z.png")

    resposta = f"""\
**Variável:** consumo médio por residência (kWh/mês). **Pergunta:** o consumo por residência no início e no fim da série era diferente da média de 2004 a 2025?

Valores de referência (todos os {br(len(x), 0)} registros): média populacional μ = **{br(mu0)} kWh** e desvio padrão populacional σ = **{br(sigma)} kWh**. Como σ é conhecido, usamos o teste z.

{imagem(grafico, "Curvas normais padrão com as regiões de rejeição e os valores de z calculados")}

{texto_teste(resultados[0], mu0, sigma)}

{texto_teste(resultados[1], mu0, sigma)}

*Premissa: a amostra de cada item foi sorteada, com semente fixa ({SEMENTE}), entre os registros de um período (2004–2005 no item a, 2024–2025 no item b). O enunciado não define de onde vem a amostra; escolhemos períodos para que o teste responda a uma pergunta útil sobre a evolução do consumo.*
"""
    return {
        "id": ID, "titulo": TITULO, "enunciado": ENUNCIADO, "arquivo": ARQUIVO,
        "graficos": [grafico],
        "valores": {"variavel": VARIAVEL, "media_referencia": mu0, "desvio_padrao_populacional": sigma, "testes": resultados},
        "resposta_md": resposta,
    }


if __name__ == "__main__":
    from .preparar_base import preparar

    print(executar(preparar())["resposta_md"])
