"""Extrai a irradiação das 27 capitais do arquivo do Atlas Brasileiro de Energia Solar (INPE).

Como usar:
    python -m modulos.energia.extrair_irradiacao caminho/para/tilted_latitude_means_sedes-munic.csv

O arquivo de entrada vem de http://labren.ccst.inpe.br/atlas_2017.html
("TILTED_LATITUDE_sedes-munic_(csv).zip"). Ele traz, para cada sede municipal, a média
anual do total diário da irradiação no plano inclinado na latitude, em Wh/m².dia.

A coluna STATE do arquivo original tem um erro (Porto Alegre aparece como Rio Grande do
Norte), por isso a sigla do estado é definida aqui pelo nome da capital.
"""

import csv
import sys
from pathlib import Path

CAPITAIS = {
    "Rio Branco": ("AC", "Acre"), "Maceió": ("AL", "Alagoas"), "Macapá": ("AP", "Amapá"),
    "Manaus": ("AM", "Amazonas"), "Salvador": ("BA", "Bahia"), "Fortaleza": ("CE", "Ceará"),
    "Brasília": ("DF", "Distrito Federal"), "Vitória": ("ES", "Espírito Santo"), "Goiânia": ("GO", "Goiás"),
    "São Luís": ("MA", "Maranhão"), "Cuiabá": ("MT", "Mato Grosso"), "Campo Grande": ("MS", "Mato Grosso do Sul"),
    "Belo Horizonte": ("MG", "Minas Gerais"), "Belém": ("PA", "Pará"), "João Pessoa": ("PB", "Paraíba"),
    "Curitiba": ("PR", "Paraná"), "Recife": ("PE", "Pernambuco"), "Teresina": ("PI", "Piauí"),
    "Rio de Janeiro": ("RJ", "Rio de Janeiro"), "Natal": ("RN", "Rio Grande do Norte"),
    "Porto Alegre": ("RS", "Rio Grande do Sul"), "Porto Velho": ("RO", "Rondônia"), "Boa Vista": ("RR", "Roraima"),
    "Florianópolis": ("SC", "Santa Catarina"), "São Paulo": ("SP", "São Paulo"), "Aracaju": ("SE", "Sergipe"),
    "Palmas": ("TO", "Tocantins"),
}

SAIDA = Path(__file__).parent / "irradiacao_capitais.csv"


def extrair(entrada: str) -> list[dict]:
    linhas = []
    with open(entrada, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo, delimiter=";"):
            if linha["CLASS"] in ("Capital Estadual", "Capital Federal"):
                uf, estado = CAPITAIS[linha["NAME"]]
                linhas.append({
                    "uf": uf,
                    "estado": estado,
                    "capital": linha["NAME"],
                    "irradiacao_wh_m2_dia": int(linha["ANNUAL"]),
                })
    if len(linhas) != 27:
        raise SystemExit(f"Esperava 27 capitais, encontrei {len(linhas)}.")
    return sorted(linhas, key=lambda l: l["estado"])


if __name__ == "__main__":
    capitais = extrair(sys.argv[1])
    with open(SAIDA, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(capitais[0]))
        escritor.writeheader()
        escritor.writerows(capitais)
    print(f"{len(capitais)} capitais gravadas em {SAIDA}")
