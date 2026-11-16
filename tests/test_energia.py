"""Testes dos cálculos de energia, conferidos contra um exemplo feito à mão.

Exemplo: casa em São Paulo (irradiação 4,671 kWh/m².dia), consumo de 300 kWh,
conta de R$ 285,00, ligação bifásica (50 kWh), placas de 550 W e taxa de desempenho 0,75.

  tarifa             = 285 / 300                     = 0,95 R$/kWh
  geração por placa  = 0,55 x 4,671 x 30 x 0,75      = 57,803625 kWh/mês
  energia abatível   = 300 - 50                      = 250 kWh
  placas necessárias = 250 / 57,803625 = 4,33        -> 5 placas
  4 placas: geração 231,2145 kWh; economia 231,2145 x 0,95 = R$ 219,65; nova conta R$ 65,35
  5 placas: geração 289,0181 kWh; só 250 kWh abatem; economia R$ 237,50; nova conta R$ 47,50
  investimento (5)   = 5 x 550 Wp x R$ 4,90          = R$ 13.475,00
  manutenção         = 1% de 13.475                  = R$ 134,75 por ano
  payback            = 13.475 / (237,50 x 12 - 134,75) = 13.475 / 2.715,25 = 4,96 anos
  CO2 evitado        = 250 x 12 / 1000 x 0,0385      = 0,1155 t = 115,5 kg por ano
"""

import pytest

from modulos.energia import calculo, dados

CASA = dict(consumo_kwh=300, valor_conta=285.0, uf="SP", ligacao="bifasica")


def test_dados_das_27_capitais():
    assert len(dados.IRRADIACAO_POR_UF) == 27
    assert dados.IRRADIACAO_POR_UF["SP"]["capital"] == "São Paulo"
    assert dados.IRRADIACAO_POR_UF["SP"]["irradiacao"] == pytest.approx(4.671)
    assert dados.IRRADIACAO_POR_UF["RS"]["capital"] == "Porto Alegre"
    assert all(3 < local["irradiacao"] < 7 for local in dados.IRRADIACAO_POR_UF.values())


def test_tarifa_e_geracao_por_placa():
    assert calculo.tarifa_efetiva(285.0, 300) == pytest.approx(0.95)
    assert calculo.geracao_mensal_por_placa(4.671, 550, 0.75) == pytest.approx(57.803625)


def test_simulacao_do_exemplo_feito_a_mao():
    s = calculo.simular_solar(**CASA)
    assert s["tarifa"] == pytest.approx(0.95)
    assert s["disponibilidade_kwh"] == 50
    assert s["placas_necessarias"] == 5
    assert s["placas_recomendadas"] == 5
    assert len(s["cenarios"]) == dados.MAX_PLACAS + 1

    sem_placas = s["cenarios"][0]
    assert sem_placas["economia_mes"] == 0
    assert sem_placas["nova_conta"] == pytest.approx(285.0)
    assert sem_placas["payback_anos"] is None

    quatro = s["cenarios"][4]
    assert quatro["geracao_kwh_mes"] == pytest.approx(231.2145)
    assert quatro["economia_mes"] == pytest.approx(219.653775)
    assert quatro["nova_conta"] == pytest.approx(65.346225)

    cinco = s["cenarios"][5]
    assert cinco["geracao_kwh_mes"] == pytest.approx(289.018125)
    assert cinco["aproveitada_kwh_mes"] == pytest.approx(250)
    assert cinco["economia_mes"] == pytest.approx(237.50)
    assert cinco["nova_conta"] == pytest.approx(47.50)
    assert cinco["investimento"] == pytest.approx(13475.0)
    assert cinco["manutencao_ano"] == pytest.approx(134.75)
    assert cinco["payback_anos"] == pytest.approx(13475 / 2715.25)
    assert cinco["co2_evitado_kg_ano"] == pytest.approx(115.5)


def test_placas_a_mais_nao_aumentam_a_economia():
    cenarios = calculo.simular_solar(**CASA)["cenarios"]
    assert cenarios[10]["economia_mes"] == pytest.approx(cenarios[5]["economia_mes"])
    assert cenarios[10]["payback_anos"] > cenarios[5]["payback_anos"]


def test_consumo_abaixo_do_minimo_nao_gera_economia():
    s = calculo.simular_solar(consumo_kwh=40, valor_conta=40.0, uf="SP", ligacao="bifasica")
    assert s["placas_recomendadas"] == 0
    assert s["cenarios"][3]["economia_mes"] == 0


def test_orcamento_do_usuario_substitui_o_custo_de_referencia():
    s = calculo.simular_solar(**CASA, custo_r_por_wp=3.0)
    assert s["custo_e_referencia"] is False
    assert s["cenarios"][5]["investimento"] == pytest.approx(5 * 550 * 3.0)


def test_led_e_chuveiro_feitos_a_mao():
    # 8 lâmpadas de 60 W trocadas por LED de 9 W, 5 h por dia: 8 x 51 W x 5 h x 30 = 61,2 kWh
    led = calculo.economia_led(8, 60, 9, 5, tarifa=0.95, preco_unitario=10.0)
    assert led["economia_kwh_mes"] == pytest.approx(61.2)
    assert led["economia_mes"] == pytest.approx(58.14)
    assert led["investimento"] == pytest.approx(80.0)
    assert led["payback_meses"] == pytest.approx(80 / 58.14)
    # Chuveiro de 5.500 W, 4 banhos por dia, de 10 para 7 minutos: 5,5 kW x 3/60 h x 4 x 30 = 33 kWh
    chuveiro = calculo.economia_chuveiro(5500, 4, 10, 7, tarifa=0.95)
    assert chuveiro["economia_kwh_mes"] == pytest.approx(33.0)
    assert chuveiro["economia_mes"] == pytest.approx(31.35)
    assert chuveiro["investimento"] == 0
    assert chuveiro["payback_meses"] == 0


def test_comparacao_para_a_mesma_casa():
    c = calculo.comparar(
        **CASA,
        led=dict(quantidade=8, potencia_atual_w=60, potencia_led_w=9, horas_dia=5, preco_unitario=10.0),
        chuveiro=dict(potencia_w=5500, banhos_dia=4, minutos_atual=10, minutos_novo=7),
    )
    assert c["solar"]["placas"] == 5
    assert c["eficiencia"]["economia_kwh_mes"] == pytest.approx(94.2)
    assert c["eficiencia"]["economia_mes"] == pytest.approx(89.49)
    assert c["eficiencia"]["investimento"] == pytest.approx(80.0)
    # Com o consumo reduzido para 205,8 kWh, sobram 155,8 kWh para abater: 3 placas bastam.
    assert c["juntas"]["consumo_reduzido_kwh"] == pytest.approx(205.8)
    assert c["juntas"]["placas"] == 3
    assert c["juntas"]["economia_mes"] == pytest.approx(89.49 + 155.8 * 0.95)


@pytest.mark.parametrize(
    "argumentos",
    [
        dict(consumo_kwh=0, valor_conta=100, uf="SP", ligacao="bifasica"),
        dict(consumo_kwh=300, valor_conta=285, uf="XX", ligacao="bifasica"),
        dict(consumo_kwh=300, valor_conta=285, uf="SP", ligacao="quadrifasica"),
    ],
)
def test_entradas_invalidas_geram_mensagem(argumentos):
    with pytest.raises(calculo.EntradaInvalida):
        calculo.simular_solar(**argumentos)


def test_eficiencia_impossivel_e_recusada():
    with pytest.raises(calculo.EntradaInvalida):
        calculo.economia_led(8, 9, 60, 5, tarifa=0.95)
    with pytest.raises(calculo.EntradaInvalida):
        calculo.comparar(**CASA, led=dict(quantidade=500, potencia_atual_w=100, potencia_led_w=9, horas_dia=24))
