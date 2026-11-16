"""Questão 07: monta o relatório estatístico (relatorio.md) somente a partir de resultados.json.

Nenhum número é digitado aqui: todos vêm dos resultados calculados pelos scripts das questões.
É chamado por executar.py. Para gerar o PDF, abra a seção "Relatório" do sistema e use
"Imprimir ou salvar como PDF".
"""

from .comum import br, pct


def _questao(resultados, numero):
    return next(q for q in resultados["questoes"] if q["id"] == numero)


def montar(resultados: dict) -> str:
    q2, q3, q4, q5, q6 = (_questao(resultados, n)["valores"] for n in ("02", "03", "04", "05", "06"))
    teste_a, teste_b = q3["testes"]
    base = resultados["base"]

    tendencia = []
    for t in (teste_a, teste_b):
        periodo = f"{t['anos'][0]}–{t['anos'][1]}"
        if t["rejeita_h0"]:
            tendencia.append(f"em {periodo} a média da amostra foi {br(t['media_amostral'])} kWh, "
                             f"significativamente {'menor' if t['cauda'] == 'esquerda' else 'maior'} que a referência")
        else:
            tendencia.append(f"em {periodo} a média da amostra foi {br(t['media_amostral'])} kWh, "
                             "sem diferença significativa em relação à referência")
    crescimento = teste_a["rejeita_h0"] and teste_b["rejeita_h0"]

    secoes_questoes = "\n\n".join(
        f"## Questão {q['id']}: {q['titulo']}\n\n*Enunciado: {q['enunciado']}*\n\n{q['resposta_md']}"
        for q in resultados["questoes"]
    )

    return f"""\
# Relatório estatístico: consumo de energia elétrica nas residências brasileiras

**Global Solution GS26_2 — Citizen Assist AI** · Disciplina Modelagem Linear para Aprendizado de Máquina · Ciência da Computação, turma 1CC

**Integrantes:** [PENDENTE: nome completo e número de matrícula de cada integrante]

**Base de dados:** {base['fonte']['nome']}, acesso em {base['fonte']['acesso']}.

## Sumário executivo

- Entre {base['periodo']}, uma residência brasileira consumiu em média **{br(q2['media'])} kWh por mês** (média dos estados e meses), com mediana de {br(q2['mediana'])} kWh. A distribuição é assimétrica: alguns estados consomem bem acima do comum.
- O consumo por residência **{"cresceu ao longo do tempo" if crescimento else "teve resultados mistos ao longo do tempo"}**: {tendencia[0]}; {tendencia[1]}.
- Onde o comércio consome mais por estabelecimento, as residências também consomem mais (r = {br(q4['pearson_r'], 2)}). Sozinha, essa variável explica {pct(q4['r2'], 1)} da variação do consumo das residências.
- Somando a participação da indústria e o ano, o modelo de regressão múltipla explica **{pct(q5['r2'], 1)}** da variação e estima {br(q5['previsao_y'])} kWh por residência para o cenário médio de 2025.
- A regressão logística identifica estados e meses de consumo residencial alto com **{pct(q6['acuracia'], 1)} de acerto** em dados que o modelo não viu, contra {pct(q6['acuracia_referencia'], 1)} de um chute simples.

## 1. Contexto e objetivo

O Citizen Assist AI é um assistente digital que ajuda o cidadão a se informar sobre o dia a dia, incluindo a conta de luz. Para orientar uma família, é útil saber qual é o consumo típico de uma residência no Brasil, como ele muda com o tempo e o que está associado a consumos mais altos.

**Objetivo:** descrever e modelar o consumo médio de energia elétrica por residência nos estados brasileiros, com dados oficiais, para gerar valores de referência e insights que apoiem as orientações de energia do assistente.

## 2. Base de dados

{base['descricao_md']}

## 3. Metodologia

- **Ferramentas:** Python, com pandas (organização dos dados), SciPy (probabilidades e testes), statsmodels (regressões) e matplotlib (gráficos). Cada questão tem um arquivo `.py` próprio em `modulos/ml/`.
- **Reprodutibilidade:** os sorteios usam semente fixa. Rodar `python -m modulos.ml.executar` gera de novo os mesmos resultados, gráficos e este relatório.
- **Níveis de significância:** 6% e 9% nos testes da questão 03, como pede o enunciado, e 5% nas demais.
- **Premissas adotadas** (o material de aula não estava disponível): escala de classificação dos eventos na questão 02; origem das amostras na questão 03 (sorteadas de um período); faixas de intensidade da correlação; definição da variável binária pela mediana e corte de 50% na questão 06. Cada premissa está indicada na questão correspondente.

{secoes_questoes}

## Insights e recomendações para o Citizen Assist AI

1. **Valor de referência para o cidadão.** O consumo típico de uma residência fica em torno de {br(q2['mediana'], 0)} kWh por mês (mediana dos estados e meses). O assistente pode usar esse valor para ajudar a pessoa a entender se a conta dela está acima ou abaixo do comum, lembrando que o valor varia muito entre estados.
2. **O consumo das casas tende a subir.** A comparação entre o início e o fim da série mostra consumo maior nos anos recentes. Medidas de eficiência, como as do módulo de Energia (lâmpadas LED e banho mais curto), ganham importância.
3. **Fatores regionais pesam.** A relação com o consumo comercial e com o perfil industrial do estado indica que clima e economia local influenciam o consumo das casas. Orientações por estado são mais úteis do que uma média nacional única.
4. **Modelos como apoio, não como garantia.** Os modelos explicam parte da variação ({pct(q5['r2'], 1)} na regressão múltipla) e erram em alguns casos (acurácia de {pct(q6['acuracia'], 1)}). As estimativas devem ser apresentadas ao cidadão com intervalos e limitações.

## Limitações

- Os dados são médias por estado e mês, não medições de residências individuais. As conclusões valem para médias estaduais e não devem ser aplicadas diretamente a uma casa.
- Correlação não é causalidade. Variáveis importantes, como temperatura, renda e número de moradores, não estão na base.
- A suposição de distribuição normal, pedida no enunciado, é uma aproximação: a variável é assimétrica.
- Registros do mesmo estado em meses seguidos não são independentes, o que torna os valores-p mais otimistas do que seriam com dados independentes.
- Previsões para anos fora do período de 2004 a {base['periodo'][-4:]} são extrapolação.

## Como reproduzir

1. Instale as bibliotecas: `pip install -r requirements-analise.txt`
2. Rode, na pasta do projeto: `python -m modulos.ml.executar`
3. Os resultados ficam em `modulos/ml/saidas/` e aparecem na seção "Dados e estatística" do sistema.

## Referências

- {base['fonte']['nome']}. Disponível em: {base['fonte']['pagina']}. Acesso em: {base['fonte']['acesso']}.
- Bibliotecas Python: pandas, NumPy, SciPy, statsmodels e matplotlib (documentação oficial de cada projeto).
"""
