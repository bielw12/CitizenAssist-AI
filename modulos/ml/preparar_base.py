"""Transforma a planilha oficial da EPE em uma tabela com uma linha por estado e mês.

Entrada: dados/epe_consumo_mensal_por_classe.xlsx (EPE, "Consumo mensal de energia elétrica por classe").
Saída:   dados/base_consumo_uf_mensal.csv

Período usado: janeiro de 2004 a dezembro de 2025. Os meses de 2026 ficam de fora porque a
EPE os marca como preliminares (2026*).

Como rodar sozinho:  python -m modulos.ml.preparar_base
"""

import pandas as pd

from .comum import BASE_CSV, PLANILHA

ULTIMO_ANO = 2025

# Coluna da tabela final -> aba da planilha da EPE
ABAS = {
    "consumo_total_mwh": "CONSUMO POR UF",
    "consumo_residencial_mwh": "CONSUMO RESIDENCIAL POR UF",
    "consumo_industrial_mwh": "CONSUMO INDUSTRIAL POR UF",
    "consumo_comercial_mwh": "CONSUMO COMERCIAL POR UF",
    "consumidores_residenciais": "CONSUMIDORES RES. POR UF",
    "consumidores_comerciais": "CONSUMIDORES COMERCIAIS POR UF",
}

SIGLAS = {
    "Rondonia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR", "Para": "PA", "Amapa": "AP",
    "Tocantins": "TO", "Maranhao": "MA", "Piaui": "PI", "Ceara": "CE", "Rio Grande do Norte": "RN",
    "Paraiba": "PB", "Pernambuco": "PE", "Alagoas": "AL", "Sergipe": "SE", "Bahia": "BA",
    "Minas Gerais": "MG", "Espirito Santo": "ES", "Rio de Janeiro": "RJ", "Sao Paulo": "SP",
    "Parana": "PR", "Santa Catarina": "SC", "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS",
    "Mato Grosso": "MT", "Goias": "GO", "Distrito Federal": "DF",
}
MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]


def ler_aba(aba: str, nome: str) -> pd.Series:
    """Lê uma aba "POR UF": linha 5 tem o ano, linha 6 o mês e as linhas 8 a 34 os 27 estados."""
    planilha = pd.read_excel(PLANILHA, sheet_name=aba, header=None)
    anos = planilha.iloc[4, 1:].astype(str).str.replace("*", "", regex=False).astype(int)
    meses = planilha.iloc[5, 1:].map(lambda m: MESES.index(m) + 1)
    valores = planilha.iloc[7:34, 1:].apply(pd.to_numeric)
    valores.index = planilha.iloc[7:34, 0].map(SIGLAS)
    valores.columns = pd.MultiIndex.from_arrays([anos.values, meses.values], names=["ano", "mes"])
    return valores.stack(["ano", "mes"], future_stack=True).rename(nome)


def preparar() -> pd.DataFrame:
    base = pd.concat([ler_aba(aba, nome) for nome, aba in ABAS.items()], axis=1)
    base.index.names = ["uf", "ano", "mes"]
    base = base.reset_index()
    base = base[base["ano"] <= ULTIMO_ANO].sort_values(["ano", "mes", "uf"]).reset_index(drop=True)
    if base.isna().any().any() or len(base) != 27 * 12 * (ULTIMO_ANO - 2004 + 1):
        raise SystemExit("A planilha não tem o formato esperado. Confira se o arquivo é o da EPE.")

    # Variáveis derivadas (MWh x 1000 = kWh)
    base["consumo_medio_res_kwh"] = base["consumo_residencial_mwh"] * 1000 / base["consumidores_residenciais"]
    base["consumo_medio_com_kwh"] = base["consumo_comercial_mwh"] * 1000 / base["consumidores_comerciais"]
    base["participacao_industrial"] = base["consumo_industrial_mwh"] / base["consumo_total_mwh"] * 100
    return base


def main():
    base = preparar()
    BASE_CSV.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(BASE_CSV, index=False, float_format="%.6f")
    print(f"{len(base)} linhas gravadas em {BASE_CSV}")


if __name__ == "__main__":
    main()
