# Energia no Citizen Assist AI — análise e justificativas

Contribuição da disciplina **Soluções em Energias Renováveis e Sustentáveis**.

Integrantes: [PENDENTE: nome completo e RM de cada integrante]

## 1. Público e necessidade energética

- **Público:** famílias de todo o Brasil que querem pagar menos na conta de luz e não têm formação técnica.
- **Necessidade:** saber se vale a pena investir em energia solar ou se medidas simples de economia já resolvem, com números da própria conta de luz e linguagem acessível.
- **Como o assistente ajuda:** a pessoa informa o consumo (kWh), o valor da conta, o estado e o tipo de ligação. O sistema calcula e compara as alternativas, mostra as fontes e explica os limites da estimativa.

## 2. Alternativas comparadas

| Alternativa | Tipo | O que muda |
|---|---|---|
| Energia solar fotovoltaica | Fornecimento, **renovável** | Gera parte da energia da casa no telhado |
| Troca de lâmpadas por LED | Economia (eficiência) | Menor potência para a mesma iluminação |
| Banho mais curto no chuveiro elétrico | Economia (hábito) | Menos tempo do aparelho de maior potência ligado |
| Eficiência + solar juntas | Combinação | Reduz o consumo e depois dimensiona as placas para o que sobra |

Todas são comparadas para **a mesma casa** e para **o mesmo período de 12 meses**.

## 3. Dados utilizados

Consulta em 14/11/2026. Os arquivos e o código estão em `modulos/energia/`.

| Dado | Valor | Unidade | Origem |
|---|---|---|---|
| Irradiação na capital de cada estado | 4,327 (Manaus) a 5,775 (Fortaleza) | kWh/m²·dia, média anual no plano inclinado | INPE, Atlas Brasileiro de Energia Solar, 2ª ed., 2017 |
| Taxa de desempenho do sistema | 75% | — | EPE, Nota Técnica DEA-SEE 014/2022, Tabela 2 |
| Custo do sistema solar residencial instalado | 4,90 | R$/Wp (valor de 2021) | EPE, Nota Técnica DEA-SEE 014/2022, Tabela 2 (cita Greener, 2022) |
| Manutenção anual | 1% do investimento | R$/ano | EPE, Nota Técnica DEA-SEE 014/2022, Tabela 2 |
| Vida útil | 25 | anos | EPE, Nota Técnica DEA-SEE 014/2022, Tabela 2 |
| Custo de disponibilidade | 30 / 50 / 100 | kWh (mono / bi / trifásica) | ANEEL, página de Micro e Minigeração Distribuída |
| Fator de emissão de CO2 da eletricidade | 0,0385 | tCO2/MWh (média de 2023) | MCTI, notícia de fevereiro de 2024 |
| Potência de cada placa | 550 | W | **Premissa do grupo** [PENDENTE: aprovação do grupo] |
| Dados de lâmpadas e chuveiro | informados pelo usuário | W, horas, minutos | Lidos no produto ou na embalagem |

**Dados estimados:** a potência da placa é uma premissa. O custo por Wp é de 2021 e está desatualizado; por isso o simulador aceita o valor de um orçamento real. O fator de emissão de 2024 em diante não foi encontrado em fonte oficial durante a consulta; usamos o último valor anual confirmado (2023).

O arquivo do INPE traz Porto Alegre com o estado errado (Rio Grande do Norte). O script `extrair_irradiacao.py` associa capital e estado pelo nome da cidade e corrige isso.

## 4. Fórmulas

| Grandeza | Fórmula |
|---|---|
| Tarifa média | valor da conta ÷ consumo |
| Geração de uma placa por mês | potência (kW) × irradiação (kWh/m²·dia) × 30 × taxa de desempenho |
| Energia que reduz a conta | menor valor entre a geração e (consumo − custo de disponibilidade) |
| Economia por mês | energia que reduz a conta × tarifa média |
| Investimento | placas × potência (W) × custo por Wp |
| Retorno (payback simples) | investimento ÷ (economia em 12 meses − manutenção anual) |
| CO2 evitado por ano | energia que reduz a conta × 12 ÷ 1000 × fator de emissão |
| Economia com LED | lâmpadas × (potência atual − potência LED) × horas por dia × 30 |
| Economia no chuveiro | potência × (minutos antes − minutos depois) ÷ 60 × banhos por dia × 30 |

A irradiação em kWh/m²·dia equivale ao número de "horas de sol pleno" por dia, por isso multiplica diretamente a potência da placa.

## 5. Exemplo calculado à mão

Casa em São Paulo, consumo de 300 kWh, conta de R$ 285,00, ligação bifásica.

1. Tarifa média: 285 ÷ 300 = **R$ 0,95 por kWh**.
2. Geração de uma placa: 0,55 kW × 4,671 × 30 × 0,75 = **57,80 kWh por mês**.
3. Energia que pode reduzir a conta: 300 − 50 = **250 kWh** (os 50 kWh do mínimo bifásico sempre são cobrados).
4. Placas necessárias: 250 ÷ 57,80 = 4,33, ou seja, **5 placas**.
5. Com 5 placas, a geração é 289,02 kWh, mas só 250 kWh reduzem a conta. Economia: 250 × 0,95 = **R$ 237,50 por mês**. Nova conta: **R$ 47,50**.
6. Investimento: 5 × 550 W × R$ 4,90 = **R$ 13.475,00**. Manutenção: 1% = R$ 134,75 por ano.
7. Retorno: 13.475 ÷ (237,50 × 12 − 134,75) = 13.475 ÷ 2.715,25 = **4,96 anos**.
8. CO2 evitado: 250 × 12 ÷ 1000 × 0,0385 = 0,1155 t = **115,5 kg por ano**.

Mesma casa, medidas de eficiência:

- **LED:** 8 lâmpadas de 60 W trocadas por LED de 9 W, 5 horas por dia: 8 × 51 W × 5 h × 30 = **61,2 kWh por mês**, ou R$ 58,14. Com LED a R$ 10,00, investimento de R$ 80,00 e retorno em 1,4 meses.
- **Chuveiro:** 5.500 W, 4 banhos por dia, de 10 para 7 minutos: 5,5 kW × 3/60 h × 4 × 30 = **33 kWh por mês**, ou R$ 31,35, sem investimento.
- **As duas juntas:** a eficiência reduz o consumo para 205,8 kWh. Sobram 155,8 kWh para abater, e **3 placas** bastam em vez de 5. O investimento total cai para R$ 8.165,00, com a mesma economia de R$ 237,50 por mês.

Todos esses números são conferidos automaticamente em `tests/test_energia.py`.

## 6. Recomendações e justificativas

| Critério | Solar | LED | Chuveiro |
|---|---|---|---|
| Custo | Alto (milhares de reais) | Baixo | Nenhum |
| Economia | A maior, até o limite do custo de disponibilidade | Média, depende das horas de uso | Média, depende do hábito |
| Viabilidade | Exige telhado adequado, profissional habilitado e pedido à distribuidora | Imediata | Imediata, depende das pessoas |
| Impacto ambiental | O maior CO2 evitado | Menor | Menor |

**Recomendação do assistente:** começar pelas medidas de eficiência, que custam pouco e se pagam em meses, e depois dimensionar o sistema solar para o consumo já reduzido. Assim o investimento em placas é menor para a mesma economia.

**Observação sobre o impacto ambiental:** a eletricidade do Brasil já tem baixa emissão de CO2 por ser majoritariamente renovável. Por isso o CO2 evitado por uma casa é pequeno em números absolutos, e o principal ganho para a família é financeiro.

## 7. Integração ao assistente

| Onde | O que faz |
|---|---|
| Simulador solar | Desenho 2D em que as placas entram uma a uma no telhado, com economia, nova conta, retorno e CO2 a cada placa |
| Comparar alternativas | Tabela lado a lado para a mesma casa e 12 meses, com viabilidade e limites |
| Chat de energia | Responde só sobre energia e chama as mesmas funções de cálculo como ferramentas, para que os números venham do código e não do modelo |

Código: `modulos/energia/calculo.py` (cálculos), `app/ferramentas.py` (ferramentas do chat), `app/static/energia.js` (telas).

## 8. Limitações

- Os resultados são estimativas, não garantias de economia, geração ou custo.
- A tarifa média inclui impostos e taxas que a energia solar não reduz; a economia real tende a ser menor.
- Não entra no cálculo a cobrança pelo uso da rede sobre a energia injetada (Lei 14.300/2022), nem bandeiras tarifárias e iluminação pública.
- A irradiação é a da capital do estado; outras cidades, sombras e a posição do telhado mudam o resultado.
- Não considera a perda de rendimento das placas com o tempo nem a troca do inversor.
- O custo de referência é de 2021.
- A casa do desenho é fictícia.

## 9. Testes com usuários

Os registros ficam em [`testes_com_usuarios.md`](testes_com_usuarios.md). [PENDENTE: realização dos testes pelo grupo]
