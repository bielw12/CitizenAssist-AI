"""Cálculos do módulo de Energia. Funções puras: recebem números e devolvem números.

O simulador da tela e o chat de energia usam estas mesmas funções, para que todo valor
mostrado ao usuário venha daqui e não do modelo de linguagem.
"""

import math

from . import dados


class EntradaInvalida(ValueError):
    """Dados informados que não permitem fazer a conta. A mensagem é mostrada ao usuário."""


def tarifa_efetiva(valor_conta: float, consumo_kwh: float) -> float:
    """Preço médio pago por kWh, em R$: valor da conta dividido pelo consumo."""
    if consumo_kwh <= 0 or valor_conta <= 0:
        raise EntradaInvalida("O consumo e o valor da conta precisam ser maiores que zero.")
    return valor_conta / consumo_kwh


def geracao_mensal_por_placa(
    irradiacao_kwh_m2_dia: float,
    potencia_placa_w: float = dados.POTENCIA_PLACA_W,
    taxa_desempenho: float = dados.TAXA_DESEMPENHO,
) -> float:
    """Energia que uma placa gera por mês, em kWh.

    potência (kW) x irradiação (kWh/m².dia, que equivale a horas de sol pleno) x 30 dias x taxa de desempenho
    """
    return potencia_placa_w / 1000 * irradiacao_kwh_m2_dia * dados.DIAS_NO_MES * taxa_desempenho


def _cenario(placas, consumo_kwh, valor_conta, tarifa, por_placa, disponibilidade, potencia_placa_w, custo_r_por_wp):
    geracao = placas * por_placa
    compensavel = max(consumo_kwh - disponibilidade, 0)
    aproveitada = min(geracao, compensavel)
    economia_mes = aproveitada * tarifa
    investimento = placas * potencia_placa_w * custo_r_por_wp
    economia_ano_liquida = economia_mes * 12 - investimento * dados.MANUTENCAO_ANUAL
    payback = investimento / economia_ano_liquida if placas and economia_ano_liquida > 0 else None
    return {
        "placas": placas,
        "potencia_kwp": placas * potencia_placa_w / 1000,
        "geracao_kwh_mes": geracao,
        "aproveitada_kwh_mes": aproveitada,
        "economia_mes": economia_mes,
        "economia_ano": economia_mes * 12,
        "nova_conta": valor_conta - economia_mes,
        "investimento": investimento,
        "manutencao_ano": investimento * dados.MANUTENCAO_ANUAL,
        "payback_anos": payback,
        # kWh por ano -> MWh -> toneladas de CO2 -> kg
        "co2_evitado_kg_ano": aproveitada * 12 / 1000 * dados.FATOR_EMISSAO_T_POR_MWH * 1000,
    }


def simular_solar(
    consumo_kwh: float,
    valor_conta: float,
    uf: str,
    ligacao: str,
    potencia_placa_w: float | None = None,
    custo_r_por_wp: float | None = None,
) -> dict:
    """Simula de 0 até MAX_PLACAS placas para uma casa e indica a quantidade recomendada."""
    if uf not in dados.IRRADIACAO_POR_UF:
        raise EntradaInvalida("Estado não reconhecido. Use a sigla, como SP ou BA.")
    if ligacao not in dados.CUSTO_DISPONIBILIDADE_KWH:
        raise EntradaInvalida("Tipo de ligação não reconhecido. Use monofasica, bifasica ou trifasica.")
    potencia_placa_w = potencia_placa_w or dados.POTENCIA_PLACA_W
    custo_r_por_wp = custo_r_por_wp or dados.CUSTO_REFERENCIA_R_POR_WP
    if potencia_placa_w <= 0 or custo_r_por_wp <= 0:
        raise EntradaInvalida("A potência da placa e o custo precisam ser maiores que zero.")

    local = dados.IRRADIACAO_POR_UF[uf]
    tarifa = tarifa_efetiva(valor_conta, consumo_kwh)
    por_placa = geracao_mensal_por_placa(local["irradiacao"], potencia_placa_w)
    disponibilidade = dados.CUSTO_DISPONIBILIDADE_KWH[ligacao]
    compensavel = max(consumo_kwh - disponibilidade, 0)

    # Menor número de placas que gera toda a energia que pode ser abatida da conta.
    necessarias = math.ceil(compensavel / por_placa) if compensavel > 0 else 0
    recomendadas = min(necessarias, dados.MAX_PLACAS)

    cenarios = [
        _cenario(n, consumo_kwh, valor_conta, tarifa, por_placa, disponibilidade, potencia_placa_w, custo_r_por_wp)
        for n in range(dados.MAX_PLACAS + 1)
    ]
    return {
        "uf": uf,
        "capital": local["capital"],
        "irradiacao_kwh_m2_dia": local["irradiacao"],
        "ligacao": ligacao,
        "consumo_kwh": consumo_kwh,
        "valor_conta": valor_conta,
        "tarifa": tarifa,
        "disponibilidade_kwh": disponibilidade,
        "potencia_placa_w": potencia_placa_w,
        "custo_r_por_wp": custo_r_por_wp,
        "custo_e_referencia": custo_r_por_wp == dados.CUSTO_REFERENCIA_R_POR_WP,
        "geracao_por_placa_kwh_mes": por_placa,
        "placas_necessarias": necessarias,
        "placas_recomendadas": recomendadas,
        "max_placas": dados.MAX_PLACAS,
        "vida_util_anos": dados.VIDA_UTIL_ANOS,
        "cenarios": cenarios,
    }


def economia_led(
    quantidade: int,
    potencia_atual_w: float,
    potencia_led_w: float,
    horas_dia: float,
    tarifa: float,
    preco_unitario: float | None = None,
) -> dict:
    """Economia mensal ao trocar lâmpadas por LED: diferença de potência x horas de uso x 30 dias."""
    if quantidade < 0 or horas_dia < 0 or horas_dia > 24:
        raise EntradaInvalida("Confira a quantidade de lâmpadas e as horas de uso por dia (de 0 a 24).")
    if potencia_led_w >= potencia_atual_w:
        raise EntradaInvalida("A potência da lâmpada LED precisa ser menor que a da lâmpada atual.")
    kwh = quantidade * (potencia_atual_w - potencia_led_w) / 1000 * horas_dia * dados.DIAS_NO_MES
    investimento = quantidade * preco_unitario if preco_unitario else None
    return _resultado_eficiencia(kwh, tarifa, investimento)


def economia_chuveiro(potencia_w: float, banhos_dia: float, minutos_atual: float, minutos_novo: float, tarifa: float) -> dict:
    """Economia mensal ao reduzir o tempo de banho: potência x tempo economizado x banhos x 30 dias."""
    if potencia_w <= 0 or banhos_dia < 0 or minutos_atual <= 0 or minutos_novo < 0:
        raise EntradaInvalida("Confira a potência do chuveiro, os banhos por dia e os minutos de banho.")
    if minutos_novo >= minutos_atual:
        raise EntradaInvalida("O novo tempo de banho precisa ser menor que o tempo atual.")
    kwh = potencia_w / 1000 * (minutos_atual - minutos_novo) / 60 * banhos_dia * dados.DIAS_NO_MES
    return _resultado_eficiencia(kwh, tarifa, 0.0)


def _resultado_eficiencia(kwh_mes: float, tarifa: float, investimento: float | None) -> dict:
    economia_mes = kwh_mes * tarifa
    payback = investimento / economia_mes if investimento and economia_mes > 0 else (0.0 if investimento == 0 else None)
    return {
        "economia_kwh_mes": kwh_mes,
        "economia_mes": economia_mes,
        "economia_ano": economia_mes * 12,
        "investimento": investimento,
        "payback_meses": payback,
        "co2_evitado_kg_ano": kwh_mes * 12 / 1000 * dados.FATOR_EMISSAO_T_POR_MWH * 1000,
    }


def comparar(
    consumo_kwh: float,
    valor_conta: float,
    uf: str,
    ligacao: str,
    placas: int | None = None,
    potencia_placa_w: float | None = None,
    custo_r_por_wp: float | None = None,
    led: dict | None = None,
    chuveiro: dict | None = None,
) -> dict:
    """Compara, para a mesma casa e para 12 meses, a energia solar com as medidas de eficiência."""
    if not led and not chuveiro:
        raise EntradaInvalida("Informe os dados das lâmpadas ou do chuveiro para comparar.")
    simulacao = simular_solar(consumo_kwh, valor_conta, uf, ligacao, potencia_placa_w, custo_r_por_wp)
    tarifa = simulacao["tarifa"]
    if placas is None:
        placas = simulacao["placas_recomendadas"]
    if not 0 <= placas <= dados.MAX_PLACAS:
        raise EntradaInvalida(f"O número de placas precisa estar entre 0 e {dados.MAX_PLACAS}.")
    solar = simulacao["cenarios"][placas]

    resultado_led = economia_led(tarifa=tarifa, **led) if led else None
    resultado_chuveiro = economia_chuveiro(tarifa=tarifa, **chuveiro) if chuveiro else None
    partes = [r for r in (resultado_led, resultado_chuveiro) if r]
    kwh_eficiencia = sum(r["economia_kwh_mes"] for r in partes)
    if kwh_eficiencia >= consumo_kwh:
        raise EntradaInvalida(
            "Os dados informados dariam uma economia maior que todo o consumo da casa. Confira os valores."
        )
    investimentos = [r["investimento"] for r in partes]
    investimento = None if any(i is None for i in investimentos) else sum(investimentos)
    eficiencia = _resultado_eficiencia(kwh_eficiencia, tarifa, investimento)

    # As duas juntas: primeiro reduz o consumo, depois dimensiona as placas para o que sobrou.
    consumo_reduzido = consumo_kwh - kwh_eficiencia
    simulacao_reduzida = simular_solar(
        consumo_reduzido, consumo_reduzido * tarifa, uf, ligacao, potencia_placa_w, custo_r_por_wp
    )
    solar_reduzido = simulacao_reduzida["cenarios"][simulacao_reduzida["placas_recomendadas"]]

    return {
        "tarifa": tarifa,
        "capital": simulacao["capital"],
        "solar": solar,
        "led": resultado_led,
        "chuveiro": resultado_chuveiro,
        "eficiencia": eficiencia,
        "juntas": {
            "consumo_reduzido_kwh": consumo_reduzido,
            "placas": solar_reduzido["placas"],
            "economia_mes": eficiencia["economia_mes"] + solar_reduzido["economia_mes"],
            "economia_ano": eficiencia["economia_ano"] + solar_reduzido["economia_ano"],
            "investimento": None if investimento is None else investimento + solar_reduzido["investimento"],
            "investimento_solar": solar_reduzido["investimento"],
            "co2_evitado_kg_ano": eficiencia["co2_evitado_kg_ano"] + solar_reduzido["co2_evitado_kg_ano"],
        },
    }
