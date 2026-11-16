"""Ferramentas que o chat de energia pode chamar. Elas só repassam o pedido ao código de cálculo."""

import json

from modulos.energia import calculo, dados

_UFS = sorted(dados.IRRADIACAO_POR_UF)
_LIGACOES = list(dados.CUSTO_DISPONIBILIDADE_KWH)

FERRAMENTAS_ENERGIA = [
    {
        "name": "simular_energia_solar",
        "description": (
            "Calcula geração, economia mensal, nova conta, investimento, payback e CO2 evitado de um sistema "
            "de placas solares para uma casa. Use sempre que a pessoa quiser números sobre energia solar. "
            "Se 'placas' não for informado, usa a quantidade recomendada."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consumo_kwh": {"type": "number", "description": "Consumo mensal da conta de luz, em kWh."},
                "valor_conta": {"type": "number", "description": "Valor mensal da conta de luz, em reais."},
                "uf": {"type": "string", "enum": _UFS, "description": "Sigla do estado onde fica a casa."},
                "ligacao": {
                    "type": "string",
                    "enum": _LIGACOES,
                    "description": "Tipo de ligação elétrica da casa, como aparece na conta.",
                },
                "placas": {"type": "integer", "description": "Número de placas a simular (opcional)."},
                "orcamento_total": {
                    "type": "number",
                    "description": "Valor de um orçamento recebido pela pessoa para as placas simuladas, em reais (opcional).",
                },
            },
            "required": ["consumo_kwh", "valor_conta", "uf", "ligacao"],
        },
    },
    {
        "name": "calcular_economia_eficiencia",
        "description": (
            "Calcula a economia mensal, o investimento, o payback e o CO2 evitado de medidas de eficiência: "
            "troca de lâmpadas por LED e redução do tempo de banho no chuveiro elétrico. "
            "Informe 'lampadas', 'chuveiro' ou os dois."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consumo_kwh": {"type": "number", "description": "Consumo mensal da conta de luz, em kWh."},
                "valor_conta": {"type": "number", "description": "Valor mensal da conta de luz, em reais."},
                "lampadas": {
                    "type": "object",
                    "properties": {
                        "quantidade": {"type": "integer"},
                        "potencia_atual_w": {"type": "number", "description": "Potência de cada lâmpada atual, em watts."},
                        "potencia_led_w": {"type": "number", "description": "Potência de cada lâmpada LED nova, em watts."},
                        "horas_dia": {"type": "number", "description": "Horas de uso por dia."},
                        "preco_unitario": {"type": "number", "description": "Preço de cada lâmpada LED, em reais (opcional)."},
                    },
                    "required": ["quantidade", "potencia_atual_w", "potencia_led_w", "horas_dia"],
                },
                "chuveiro": {
                    "type": "object",
                    "properties": {
                        "potencia_w": {"type": "number", "description": "Potência do chuveiro, em watts."},
                        "banhos_dia": {"type": "number", "description": "Banhos por dia na casa."},
                        "minutos_atual": {"type": "number", "description": "Duração atual de cada banho, em minutos."},
                        "minutos_novo": {"type": "number", "description": "Nova duração de cada banho, em minutos."},
                    },
                    "required": ["potencia_w", "banhos_dia", "minutos_atual", "minutos_novo"],
                },
            },
            "required": ["consumo_kwh", "valor_conta"],
        },
    },
]


def _arredondar(valor):
    if isinstance(valor, float):
        return round(valor, 2)
    if isinstance(valor, dict):
        return {chave: _arredondar(v) for chave, v in valor.items()}
    if isinstance(valor, list):
        return [_arredondar(v) for v in valor]
    return valor


def _simular_energia_solar(consumo_kwh, valor_conta, uf, ligacao, placas=None, orcamento_total=None):
    simulacao = calculo.simular_solar(consumo_kwh, valor_conta, uf, ligacao)
    if placas is None:
        placas = simulacao["placas_recomendadas"]
    if not isinstance(placas, int) or not 0 <= placas <= dados.MAX_PLACAS:
        raise calculo.EntradaInvalida(f"O número de placas precisa estar entre 0 e {dados.MAX_PLACAS}.")
    if orcamento_total and placas:
        custo = orcamento_total / (placas * simulacao["potencia_placa_w"])
        simulacao = calculo.simular_solar(consumo_kwh, valor_conta, uf, ligacao, custo_r_por_wp=custo)
    resultado = {chave: valor for chave, valor in simulacao.items() if chave != "cenarios"}
    resultado["cenario"] = simulacao["cenarios"][placas]
    resultado["origem_do_custo"] = (
        "custo de referência da EPE (valor de 2021)" if simulacao["custo_e_referencia"] else "orçamento informado pela pessoa"
    )
    return resultado


def _calcular_economia_eficiencia(consumo_kwh, valor_conta, lampadas=None, chuveiro=None):
    if not lampadas and not chuveiro:
        raise calculo.EntradaInvalida("Informe os dados das lâmpadas ou do chuveiro.")
    tarifa = calculo.tarifa_efetiva(valor_conta, consumo_kwh)
    resultado = {"tarifa": tarifa}
    if lampadas:
        resultado["lampadas"] = calculo.economia_led(tarifa=tarifa, **lampadas)
    if chuveiro:
        resultado["chuveiro"] = calculo.economia_chuveiro(tarifa=tarifa, **chuveiro)
    return resultado


_EXECUTORES = {
    "simular_energia_solar": _simular_energia_solar,
    "calcular_economia_eficiencia": _calcular_economia_eficiencia,
}


def executar(nome: str, entrada) -> tuple[str, bool]:
    """Roda uma ferramenta. Devolve o texto do resultado e se houve erro."""
    try:
        resultado = _EXECUTORES[nome](**entrada)
    except calculo.EntradaInvalida as exc:
        return str(exc), True
    except (KeyError, TypeError, ValueError):
        # Entrada fora do formato esperado: o modelo recebe o aviso e pode corrigir o pedido.
        return "Dados em formato inválido. Confira os campos obrigatórios e os tipos.", True
    resultado["fontes"] = [f"{f['dado']}: {f['valor']}. Fonte: {f['fonte']}" for f in dados.FONTES]
    resultado["limitacoes"] = dados.LIMITACOES
    return json.dumps(_arredondar(resultado), ensure_ascii=False), False
