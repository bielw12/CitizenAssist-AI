# Relatório estatístico: consumo de energia elétrica nas residências brasileiras

**Global Solution GS26_2 — Citizen Assist AI** · Disciplina Modelagem Linear para Aprendizado de Máquina · Ciência da Computação, turma 1CC

**Integrantes:** [PENDENTE: nome completo e número de matrícula de cada integrante]

**Base de dados:** EPE (Empresa de Pesquisa Energética). Consumo mensal de energia elétrica por classe (regiões e subsistemas), acesso em 14/11/2026.

## Sumário executivo

- Entre 01/2004 a 12/2025, uma residência brasileira consumiu em média **164,59 kWh por mês** (média dos estados e meses), com mediana de 157,07 kWh. A distribuição é assimétrica: alguns estados consomem bem acima do comum.
- O consumo por residência **cresceu ao longo do tempo**: em 2004–2005 a média da amostra foi 136,40 kWh, significativamente menor que a referência; em 2024–2025 a média da amostra foi 190,71 kWh, significativamente maior que a referência.
- Onde o comércio consome mais por estabelecimento, as residências também consomem mais (r = 0,68). Sozinha, essa variável explica 46,0% da variação do consumo das residências.
- Somando a participação da indústria e o ano, o modelo de regressão múltipla explica **58,3%** da variação e estima 193,26 kWh por residência para o cenário médio de 2025.
- A regressão logística identifica estados e meses de consumo residencial alto com **85,4% de acerto** em dados que o modelo não viu, contra 50,6% de um chute simples.

## 1. Contexto e objetivo

O Citizen Assist AI é um assistente digital que ajuda o cidadão a se informar sobre o dia a dia, incluindo a conta de luz. Para orientar uma família, é útil saber qual é o consumo típico de uma residência no Brasil, como ele muda com o tempo e o que está associado a consumos mais altos.

**Objetivo:** descrever e modelar o consumo médio de energia elétrica por residência nos estados brasileiros, com dados oficiais, para gerar valores de referência e insights que apoiem as orientações de energia do assistente.

## 2. Base de dados

- **Fonte:** EPE (Empresa de Pesquisa Energética). Consumo mensal de energia elétrica por classe (regiões e subsistemas). Arquivo baixado em 14/11/2026 da página https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/consumo-de-energia-eletrica
- **Recorte:** os 27 estados, mês a mês, de janeiro de 2004 a dezembro de 2025: **7.128 registros** (27 × 12 × 22). Os meses de 2026 ficaram de fora porque a EPE os marca como preliminares.
- **Unidade de observação:** um estado em um mês. Os dados são totais do estado, não de residências individuais.
- **Variáveis usadas:**

| Variável | Como foi calculada | Unidade |
|---|---|---|
| Consumo médio por residência | consumo residencial (MWh) × 1000 ÷ número de consumidores residenciais | kWh/mês |
| Consumo médio por estabelecimento comercial | consumo comercial (MWh) × 1000 ÷ número de consumidores comerciais | kWh/mês |
| Participação industrial | consumo industrial ÷ consumo total × 100 | % |
| Ano | ano do registro | ano |

Nenhum registro precisou ser removido: as colunas usadas não têm valores ausentes no período. Arquivos: `modulos/ml/dados/` (planilha original da EPE e a tabela organizada em `.csv`).

## 3. Metodologia

- **Ferramentas:** Python, com pandas (organização dos dados), SciPy (probabilidades e testes), statsmodels (regressões) e matplotlib (gráficos). Cada questão tem um arquivo `.py` próprio em `modulos/ml/`.
- **Reprodutibilidade:** os sorteios usam semente fixa. Rodar `python -m modulos.ml.executar` gera de novo os mesmos resultados, gráficos e este relatório.
- **Níveis de significância:** 6% e 9% nos testes da questão 03, como pede o enunciado, e 5% nas demais.
- **Premissas adotadas** (o material de aula não estava disponível): escala de classificação dos eventos na questão 02; origem das amostras na questão 03 (sorteadas de um período); faixas de intensidade da correlação; definição da variável binária pela mediana e corte de 50% na questão 06. Cada premissa está indicada na questão correspondente.

## Questão 02: Probabilidade com a distribuição normal

*Enunciado: Assumindo que as variáveis numéricas escolhidas seguem uma Distribuição Normal de Probabilidade, escolher uma variável aleatória da base de dados e determinar: a) a probabilidade desta variável ser menor do que a média dos registros, classificando o evento; b) a probabilidade desta variável ser maior que a mediana dos registros, classificando o evento.*

**Variável escolhida:** consumo médio de energia elétrica por residência, em kWh por mês, calculado para cada estado e cada mês. É a variável mais próxima da conta de luz de uma família.

| Medida | Valor |
|---|---|
| Registros | 7.128 |
| Média (μ) | 164,59 kWh |
| Desvio padrão populacional (σ) | 52,39 kWh |
| Mediana | 157,07 kWh |

![Histograma do consumo médio por residência com a curva normal, a média e a mediana](/ml/graficos/q02_distribuicao.png)

### a) P(X < média)

Na distribuição normal a média fica exatamente no centro da curva, então:

P(X < 164,59) = Φ(0) = **50,00%**

Classificação: **evento equiprovável (tem a mesma chance de ocorrer e de não ocorrer)**.

### b) P(X > mediana)

z = (mediana − μ) ÷ σ = (157,07 − 164,59) ÷ 52,39 = -0,1436

P(X > 157,07) = 1 − Φ(-0,1436) = **55,71%**

Classificação: **evento provável (mais de 50% de chance)**.

### Interpretação

- Pelo modelo normal, metade dos registros fica abaixo da média. Nos dados reais, porém, 55,7% dos registros estão abaixo da média.
- A mediana (157,07 kWh) é menor que a média (164,59 kWh), e a assimetria é 0,95. Isso mostra uma distribuição com cauda longa à direita: alguns estados e meses têm consumo bem acima do comum, o que puxa a média para cima.
- Por isso o modelo normal dá 55,7% para P(X > mediana), enquanto nos dados essa proporção é 50,0%, por definição de mediana. A suposição de normalidade, pedida no enunciado, é uma aproximação.

*Premissa: a classificação dos eventos usa a escala impossível, pouco provável, equiprovável, provável e certo, pois não tivemos acesso ao material de aula.*


## Questão 03: Teste de hipótese para a média

*Enunciado: Assumindo distribuição normal, escolher uma variável e realizar um teste de hipótese para a média: a) a média amostral é menor do que a média populacional de referência, a 6% de significância, amostra de tamanho 20; b) a média amostral é maior do que a média populacional de referência, a 9% de significância, amostra de tamanho 25. Em ambos, o desvio padrão de referência é o desvio padrão populacional dos dados.*

**Variável:** consumo médio por residência (kWh/mês). **Pergunta:** o consumo por residência no início e no fim da série era diferente da média de 2004 a 2025?

Valores de referência (todos os 7.128 registros): média populacional μ = **164,59 kWh** e desvio padrão populacional σ = **52,39 kWh**. Como σ é conhecido, usamos o teste z.

![Curvas normais padrão com as regiões de rejeição e os valores de z calculados](/ml/graficos/q03_teste_z.png)

### a) Média amostral menor que a de referência (α = 6%, n = 20)

Amostra: 20 registros sorteados entre os meses de 2004 e 2005.

- H₀: μ = 164,59 kWh
- H₁: μ < 164,59 kWh (teste unilateral à esquerda)

| Etapa | Valor |
|---|---|
| Média amostral (x̄) | 136,40 kWh |
| Erro padrão (σ ÷ √n) | 52,39 ÷ √20 = 11,7139 |
| Estatística z = (x̄ − μ) ÷ (σ ÷ √n) | -2,4065 |
| Valor crítico | -1,5548 |
| Valor-p | 0,0081 |

Como z = -2,4065 está na região de rejeição (z < -1,5548), **rejeitamos H₀**.

**Conclusão:** Ao nível de 6% de significância, há evidência de que o consumo médio por residência entre 2004 e 2005 era menor que a média de referência de 164,59 kWh.

Registros sorteados (estado, mês/ano: kWh): RN 08/2005: 104,7; RJ 05/2004: 165,0; DF 06/2004: 188,6; RN 09/2005: 104,8; MA 03/2005: 86,6; RJ 06/2004: 145,7; GO 03/2004: 123,4; SE 06/2004: 90,2; SE 10/2005: 97,5; PB 11/2004: 86,7; MT 02/2004: 166,1; PB 08/2004: 78,8; AM 07/2004: 161,7; CE 03/2005: 97,1; MS 10/2004: 151,2; RR 03/2005: 205,9; SC 01/2004: 192,4; PI 05/2005: 85,2; DF 03/2005: 193,3; DF 06/2005: 203,2.


### b) Média amostral maior que a de referência (α = 9%, n = 25)

Amostra: 25 registros sorteados entre os meses de 2024 e 2025.

- H₀: μ = 164,59 kWh
- H₁: μ > 164,59 kWh (teste unilateral à direita)

| Etapa | Valor |
|---|---|
| Média amostral (x̄) | 190,71 kWh |
| Erro padrão (σ ÷ √n) | 52,39 ÷ √25 = 10,4772 |
| Estatística z = (x̄ − μ) ÷ (σ ÷ √n) | 2,4931 |
| Valor crítico | 1,3408 |
| Valor-p | 0,0063 |

Como z = 2,4931 está na região de rejeição (z > 1,3408), **rejeitamos H₀**.

**Conclusão:** Ao nível de 9% de significância, há evidência de que o consumo médio por residência entre 2024 e 2025 era maior que a média de referência de 164,59 kWh.

Registros sorteados (estado, mês/ano: kWh): RN 08/2025: 130,5; RJ 05/2024: 178,7; DF 06/2024: 207,4; RN 09/2025: 128,3; MA 03/2025: 149,2; RJ 06/2024: 153,1; GO 03/2024: 207,2; SE 06/2024: 137,9; SE 10/2025: 132,6; PB 11/2024: 145,7; MT 02/2024: 247,2; PB 08/2024: 135,9; AM 07/2024: 259,6; CE 03/2025: 132,8; MS 10/2024: 225,3; RR 03/2025: 335,8; SC 01/2024: 292,1; PI 05/2025: 159,3; DF 03/2025: 219,9; DF 06/2025: 188,2; RO 05/2025: 291,7; PE 07/2025: 118,2; RO 01/2025: 262,6; DF 01/2024: 199,4; AL 10/2024: 129,1.


*Premissa: a amostra de cada item foi sorteada, com semente fixa (2026), entre os registros de um período (2004–2005 no item a, 2024–2025 no item b). O enunciado não define de onde vem a amostra; escolhemos períodos para que o teste responda a uma pergunta útil sobre a evolução do consumo.*


## Questão 04: Análise bivariada e regressão linear simples

*Enunciado: Faça uma Análise Bivariada entre 02 variáveis quantitativas contendo: a) o gráfico de dispersão, com título e nomes nos eixos, e interprete; b) a covariância e a correlação linear de Pearson, e interprete; c) o gráfico de correlação linear de Pearson, e interprete; d) a reta da regressão linear simples (no gráfico de dispersão) e a equação; e) a verificação da adequação do modelo (R² e Teste F), e interprete; f) faça uma previsão.*

**Variáveis:** X = consumo médio por estabelecimento comercial e Y = consumo médio por residência, ambos em kWh por mês, para cada estado e mês (7.128 registros). Usamos médias por consumidor, e não totais, para não medir só o tamanho do estado: estados grandes têm muito consumo residencial e comercial ao mesmo tempo.

### a) Gráfico de dispersão

![Dispersão do consumo médio por residência contra o consumo médio por estabelecimento comercial](/ml/graficos/q04_dispersao.png)

Os pontos sobem da esquerda para a direita: onde as lojas e escritórios consomem mais por unidade, as residências também tendem a consumir mais. A nuvem é larga, o que indica que outros fatores também influenciam o consumo das casas. À direita aparece um grupo separado, com consumo comercial alto e residencial moderado: são principalmente registros de SP e RJ, os estados com maior consumo médio por estabelecimento comercial (1.980 e 1.718 kWh), mas com consumo por residência de 197 e 167 kWh. Esse grupo puxa a reta para baixo do lado direito do gráfico.

### b) Covariância e correlação de Pearson

| Medida | Valor |
|---|---|
| Covariância | 12.940,29 kWh² |
| Correlação de Pearson (r) | 0,6782 |
| Valor-p da correlação | menor que 0,0001 |

A covariância positiva mostra que as duas variáveis crescem juntas, mas seu valor depende das unidades e não indica a intensidade. A correlação r = 0,6782 é **moderada e positiva**, e o valor-p menor que 0,0001 indica que ela é estatisticamente diferente de zero. Correlação não é causa: as duas variáveis provavelmente respondem a fatores comuns, como o clima quente (uso de ar-condicionado) e a renda da região.

### c) Gráfico de correlação

![Mapa de calor da correlação de Pearson entre as duas variáveis](/ml/graficos/q04_correlacao.png)

A cor indica o sentido e a força da relação: quanto mais escura, mais forte; azul é positiva e laranja seria negativa. A diagonal vale 1 porque é cada variável comparada com ela mesma.

### d) Reta e equação da regressão linear simples

![Dispersão com a reta de regressão linear simples](/ml/graficos/q04_regressao.png)

**ŷ = 58,42 + 0,0975 · x**

- Inclinação (0,0975): cada 100 kWh a mais no consumo médio comercial está associado a 9,75 kWh a mais no consumo médio por residência.
- Intercepto (58,42): é o ponto em que a reta corta o eixo Y. Não tem interpretação prática, porque não existe consumo comercial igual a zero na base.

### e) Adequação do modelo

| Medida | Valor |
|---|---|
| R² | 0,4599 |
| Estatística F | 6.067,91 |
| Valor-p do teste F | menor que 0,0001 |

O R² indica que o consumo comercial explica **46,0%** da variação do consumo por residência; o restante depende de outros fatores. O teste F tem valor-p menor que 0,0001, menor que 5%: o modelo é estatisticamente significativo, ou seja, melhor do que usar apenas a média.

### f) Previsão

Para um estado com consumo comercial de 1.313,52 kWh por estabelecimento (média observada em 2025):

ŷ = 58,42 + 0,0975 × 1.313,52 = **186,55 kWh por residência por mês**

Intervalo de previsão de 95% para um estado e mês específicos: de 111,06 a 262,03 kWh. O intervalo é largo, coerente com o R² de 46,0%: a previsão serve como referência, não como valor exato.

*Premissa: intensidade da correlação classificada como fraca (|r| < 0,3), moderada (0,3 a 0,7) ou forte (≥ 0,7). Nível de significância de 5% nos testes desta questão.*


## Questão 05: Análise multivariada e regressão linear múltipla

*Enunciado: Faça uma Análise Multivariada entre, pelo menos, 03 variáveis quantitativas contendo: a) o gráfico de dispersão, e interprete; b) a matriz de covariância e a matriz de correlação linear de Pearson, e interprete; c) o gráfico de correlação linear de Pearson, e interprete; d) a equação da regressão linear múltipla; e) a verificação da adequação do modelo (R² e Teste F), e interprete; f) faça uma previsão utilizando, pelo menos, 02 variáveis explicativas.*

**Variáveis:** consumo médio por residência (Y), consumo médio por estabelecimento comercial, participação da indústria no consumo total do estado (%) e ano. A participação industrial indica o perfil econômico do estado; o ano capta a tendência ao longo do tempo.

### a) Gráfico de dispersão

![Matriz de dispersão entre as quatro variáveis, com histogramas na diagonal](/ml/graficos/q05_dispersao.png)

Cada quadro cruza duas variáveis. O consumo por residência sobe junto com o consumo comercial e com o ano, e tende a cair quando a indústria tem participação maior no consumo do estado. A nuvem do ano forma colunas porque cada ano tem 324 registros (27 estados × 12 meses).

### b) Matrizes de covariância e de correlação

Covariância (unidades diferentes por variável, por isso só o sinal é comparável):

| | Consumo residencial | Consumo comercial | Participação industrial | Ano |
|---|---|---|---|---|
| **Consumo residencial** | 2.744,70 | 12.940,29 | -407,03 | 111,85 |
| **Consumo comercial** | 12.940,29 | 132.656,44 | -1.072,66 | 786,52 |
| **Participação industrial** | -407,03 | -1.072,66 | 288,17 | -21,95 |
| **Ano** | 111,85 | 786,52 | -21,95 | 40,26 |

Correlação de Pearson:

| | Consumo residencial | Consumo comercial | Participação industrial | Ano |
|---|---|---|---|---|
| **Consumo residencial** | 1,0000 | 0,6782 | -0,4577 | 0,3365 |
| **Consumo comercial** | 0,6782 | 1,0000 | -0,1735 | 0,3404 |
| **Participação industrial** | -0,4577 | -0,1735 | 1,0000 | -0,2038 |
| **Ano** | 0,3365 | 0,3404 | -0,2038 | 1,0000 |

Em relação ao consumo por residência, a correlação é de 0,68 com o consumo comercial, -0,46 com a participação industrial e 0,34 com o ano. Entre as variáveis explicativas, as correlações são baixas (no máximo 0,34 em valor absoluto), o que reduz o risco de uma variável repetir a informação da outra no modelo.

### c) Gráfico de correlação

![Mapa de calor da matriz de correlação de Pearson](/ml/graficos/q05_correlacao.png)

Azul indica relação positiva e laranja, negativa; quanto mais escura a cor, mais forte a relação. O quadro confirma a tabela: o consumo comercial é a variável mais ligada ao consumo por residência.

### d) Equação da regressão linear múltipla

**ŷ = -957,1819 + 0,0859·consumo_comercial − 1,0526·participação_industrial + 0,5259·ano**

- **Consumo comercial** (0,0859; valor-p menor que 0,0001): mantidas as outras variáveis constantes, cada 1 kWh a mais está associado a 0,0859 kWh a mais no consumo por residência.
- **Participação industrial** (-1,0526; valor-p menor que 0,0001): mantidas as outras variáveis constantes, cada 1 ponto percentual a mais está associado a 1,0526 kWh a menos no consumo por residência.
- **Ano** (0,5259; valor-p menor que 0,0001): mantidas as outras variáveis constantes, cada 1 ano a mais está associado a 0,5259 kWh a mais no consumo por residência.

O intercepto (-957,18) é grande porque a variável ano vale cerca de 2.000; ele não tem interpretação prática isolada.

### e) Adequação do modelo

| Medida | Valor |
|---|---|
| R² | 0,5826 |
| R² ajustado | 0,5824 |
| Estatística F | 3.314,49 |
| Valor-p do teste F | menor que 0,0001 |
| R² da regressão simples (só consumo comercial) | 0,4599 |

O modelo explica **58,3%** da variação do consumo por residência, contra 46,0% da regressão simples da questão 04. O teste F (valor-p menor que 0,0001) indica que o conjunto das variáveis é estatisticamente significativo. Ainda assim, parte da variação continua sem explicação, provavelmente por fatores que não estão na base, como temperatura e renda.

### f) Previsão

Cenário com as médias de 2025: consumo comercial de 1.313,52 kWh por estabelecimento, participação industrial de 26,06% e ano 2025.

ŷ = **193,26 kWh por residência por mês**

Intervalo de previsão de 95%: de 126,88 a 259,65 kWh. Usar o modelo para anos futuros seria extrapolação e exige cuidado.


## Questão 06: Regressão logística binária

*Enunciado: Faça uma Análise Multivariada entre, pelo menos, 03 variáveis quantitativas contendo: a) a equação da regressão logística binária; b) a matriz de confusão e a acurácia, interprete os resultados; c) uma classificação utilizando, pelo menos, 02 variáveis explicativas.*

**Variável resposta (binária):** "consumo alto por residência", igual a 1 quando o consumo médio por residência do estado no mês passa da mediana de todos os registros (157,07 kWh) e 0 caso contrário.
**Variáveis explicativas:** consumo médio por estabelecimento comercial (kWh), participação da indústria no consumo (%) e ano.

Para medir o acerto de forma honesta, os 7.128 registros foram divididos ao acaso (semente 2026): 70% para ajustar o modelo (4.990 registros) e 30% para testar (2.138 registros que o modelo não viu).

### a) Equação da regressão logística binária

P(consumo alto) = 1 ÷ (1 + e^−z), com

**z = 83,4706 + 0,007900·consumo_comercial − 0,051762·participação_industrial − 0,044806·ano**

- **Consumo comercial** (valor-p menor que 0,0001): 100 kWh a mais no consumo comercial multiplica a chance de consumo alto por 2,203.
- **Participação industrial** (valor-p menor que 0,0001): 1 ponto percentual a mais de participação industrial multiplica a chance de consumo alto por 0,950.
- **Ano** (valor-p menor que 0,0001): 1 ano a mais multiplica a chance de consumo alto por 0,956.

### b) Matriz de confusão e acurácia

![Matriz de confusão do modelo nos dados de teste](/ml/graficos/q06_matriz_confusao.png)

| | Previsto: não alto | Previsto: alto |
|---|---|---|
| **Real: não alto** | 920 (acertos) | 162 (falsos positivos) |
| **Real: alto** | 151 (falsos negativos) | 905 (acertos) |

| Medida | Valor |
|---|---|
| Acurácia | 85,4% |
| Sensibilidade (acerto entre os casos altos) | 85,7% |
| Especificidade (acerto entre os casos não altos) | 85,0% |
| Acurácia de quem sempre chuta a classe mais comum | 50,6% |
| Pseudo R² de McFadden | 0,4700 |

O modelo acerta **85,4%** dos registros de teste, 34,8 pontos percentuais acima de simplesmente chutar sempre a classe mais comum (50,6%). Os erros se dividem de forma parecida entre falsos positivos e falsos negativos.

### c) Classificação de um novo caso

Cenário com as médias de 2025: consumo comercial de 1.313,52 kWh, participação industrial de 26,06% e ano 2025.

z = 1,7655 e P(consumo alto) = **85,4%**. Com o corte em 50%, o caso é classificado como **consumo alto por residência**.

*Premissas: a variável binária foi definida pela mediana, para dividir a base em dois grupos de tamanho parecido; o corte de classificação é 50%; a divisão treino/teste (70%/30%) é aleatória por registro, então um mesmo estado aparece nos dois grupos em meses diferentes.*


## Insights e recomendações para o Citizen Assist AI

1. **Valor de referência para o cidadão.** O consumo típico de uma residência fica em torno de 157 kWh por mês (mediana dos estados e meses). O assistente pode usar esse valor para ajudar a pessoa a entender se a conta dela está acima ou abaixo do comum, lembrando que o valor varia muito entre estados.
2. **O consumo das casas tende a subir.** A comparação entre o início e o fim da série mostra consumo maior nos anos recentes. Medidas de eficiência, como as do módulo de Energia (lâmpadas LED e banho mais curto), ganham importância.
3. **Fatores regionais pesam.** A relação com o consumo comercial e com o perfil industrial do estado indica que clima e economia local influenciam o consumo das casas. Orientações por estado são mais úteis do que uma média nacional única.
4. **Modelos como apoio, não como garantia.** Os modelos explicam parte da variação (58,3% na regressão múltipla) e erram em alguns casos (acurácia de 85,4%). As estimativas devem ser apresentadas ao cidadão com intervalos e limitações.

## Limitações

- Os dados são médias por estado e mês, não medições de residências individuais. As conclusões valem para médias estaduais e não devem ser aplicadas diretamente a uma casa.
- Correlação não é causalidade. Variáveis importantes, como temperatura, renda e número de moradores, não estão na base.
- A suposição de distribuição normal, pedida no enunciado, é uma aproximação: a variável é assimétrica.
- Registros do mesmo estado em meses seguidos não são independentes, o que torna os valores-p mais otimistas do que seriam com dados independentes.
- Previsões para anos fora do período de 2004 a 2025 são extrapolação.

## Como reproduzir

1. Instale as bibliotecas: `pip install -r requirements-analise.txt`
2. Rode, na pasta do projeto: `python -m modulos.ml.executar`
3. Os resultados ficam em `modulos/ml/saidas/` e aparecem na seção "Dados e estatística" do sistema.

## Referências

- EPE (Empresa de Pesquisa Energética). Consumo mensal de energia elétrica por classe (regiões e subsistemas). Disponível em: https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/consumo-de-energia-eletrica. Acesso em: 14/11/2026.
- Bibliotecas Python: pandas, NumPy, SciPy, statsmodels e matplotlib (documentação oficial de cada projeto).
