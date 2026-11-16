"""Dados de entrada do módulo de Energia (disciplina Soluções em Energias Renováveis e Sustentáveis).

Cada número tem fonte, link e data de consulta. Premissas do grupo estão marcadas como PREMISSA.
"""

import csv
from pathlib import Path

DATA_CONSULTA = "14/11/2026"
DIAS_NO_MES = 30

# Taxa de desempenho (performance ratio): parte da energia do sol que vira eletricidade útil
# depois das perdas por temperatura, sujeira, cabos e inversor. Valor adotado pela EPE para
# sistemas instalados no local de consumo (Tabela 2 da nota técnica).
TAXA_DESEMPENHO = 0.75

# Custo inicial de um sistema fotovoltaico residencial instalado, em R$ por Wp.
# Valor de 2021 usado pela EPE (que cita a consultoria Greener). É uma referência antiga:
# quem tem um orçamento atual deve usá-lo no lugar deste número.
CUSTO_REFERENCIA_R_POR_WP = 4.90

# Despesa anual de operação e manutenção, como fração do investimento inicial (EPE).
MANUTENCAO_ANUAL = 0.01

# Vida útil do sistema, em anos (EPE).
VIDA_UTIL_ANOS = 25

# Fator médio de emissão de CO2 da geração de eletricidade no Brasil, em tCO2 por MWh.
# Último valor anual que foi possível confirmar em fonte oficial (ano de 2023).
FATOR_EMISSAO_T_POR_MWH = 0.0385

# Custo de disponibilidade: consumo mínimo cobrado na conta, em kWh, mesmo quando a energia
# gerada cobre todo o consumo. Depende do tipo de ligação da casa (ANEEL).
CUSTO_DISPONIBILIDADE_KWH = {"monofasica": 30, "bifasica": 50, "trifasica": 100}
NOMES_LIGACAO = {"monofasica": "Monofásica", "bifasica": "Bifásica", "trifasica": "Trifásica"}

# PREMISSA do grupo, não é dado oficial: potência de cada placa, em watts.
# [PENDENTE: aprovação do grupo] O usuário pode trocar pelo valor do orçamento dele.
POTENCIA_PLACA_W = 550

# Quantas placas cabem no desenho da casa fictícia. É um limite da ilustração, não um dado técnico.
MAX_PLACAS = 24


def _carregar_irradiacao() -> dict[str, dict]:
    caminho = Path(__file__).parent / "irradiacao_capitais.csv"
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return {
            linha["uf"]: {
                "uf": linha["uf"],
                "estado": linha["estado"],
                "capital": linha["capital"],
                # O arquivo do INPE está em Wh/m².dia; aqui passamos para kWh/m².dia.
                "irradiacao": int(linha["irradiacao_wh_m2_dia"]) / 1000,
            }
            for linha in csv.DictReader(arquivo)
        }


# Média anual do total diário de irradiação no plano inclinado, na capital de cada estado.
IRRADIACAO_POR_UF = _carregar_irradiacao()

FONTES = [
    {
        "dado": "Irradiação solar na capital de cada estado",
        "valor": "Média anual do total diário no plano inclinado, em kWh/m².dia",
        "fonte": "INPE. Atlas Brasileiro de Energia Solar, 2ª edição, 2017 (arquivo das sedes municipais)",
        "url": "http://labren.ccst.inpe.br/atlas_2017.html",
    },
    {
        "dado": "Taxa de desempenho do sistema solar",
        "valor": "75%",
        "fonte": "EPE. Nota Técnica DEA-SEE 014/2022, Tabela 2 (com base em Pinho e Galdino, 2014)",
        "url": "https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-689/topico-639/NT_Metodologia_4MD_PDE_2032_VF.pdf",
    },
    {
        "dado": "Custo de referência do sistema solar residencial instalado",
        "valor": "R$ 4,90 por Wp (valor de 2021)",
        "fonte": "EPE. Nota Técnica DEA-SEE 014/2022, Tabela 2 (com base em Greener, 2022)",
        "url": "https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-689/topico-639/NT_Metodologia_4MD_PDE_2032_VF.pdf",
    },
    {
        "dado": "Manutenção anual e vida útil do sistema solar",
        "valor": "1% do investimento por ano; 25 anos",
        "fonte": "EPE. Nota Técnica DEA-SEE 014/2022, Tabela 2",
        "url": "https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-689/topico-639/NT_Metodologia_4MD_PDE_2032_VF.pdf",
    },
    {
        "dado": "Custo de disponibilidade",
        "valor": "30 kWh (monofásica), 50 kWh (bifásica) ou 100 kWh (trifásica)",
        "fonte": "ANEEL. Micro e Minigeração Distribuída",
        "url": "https://www.gov.br/aneel/pt-br/assuntos/geracao-distribuida",
    },
    {
        "dado": "Fator de emissão de CO2 da eletricidade",
        "valor": "0,0385 tCO2/MWh (média de 2023)",
        "fonte": "MCTI. Fator de emissão de CO2 na geração de energia elétrica no Brasil em 2023",
        "url": "https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/noticias/2024/02/fator-de-emissao-de-co2-na-geracao-de-energia-eletrica-no-brasil-em-2023-e-o-menor-em-12-anos",
    },
    {
        "dado": "Potência de cada placa",
        "valor": "550 W (premissa do grupo, não é dado oficial; pode ser trocada)",
        "fonte": "Premissa do grupo",
        "url": "",
    },
]

LIMITACOES = [
    "Os resultados são estimativas para ajudar a decidir, não uma garantia de economia, de geração ou de custo.",
    "A tarifa usada é o valor da sua conta dividido pelo consumo. Ela inclui impostos e taxas que a energia solar não reduz, então a economia real tende a ser menor.",
    "Não entra no cálculo a cobrança pelo uso da rede sobre a energia injetada (Lei 14.300/2022), nem bandeiras tarifárias e iluminação pública.",
    "A irradiação é a da capital do estado. Outras cidades, sombras e a posição do telhado mudam o resultado.",
    "Não considera a perda de rendimento das placas com o tempo nem a troca do inversor.",
    "O custo de referência do sistema solar é de 2021. Use um orçamento atual sempre que tiver.",
    "A casa do desenho é fictícia: quantas placas cabem no seu telhado depende de avaliação técnica.",
]
