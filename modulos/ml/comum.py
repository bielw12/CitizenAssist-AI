"""Funções e constantes usadas por todos os scripts da análise de Modelagem Linear."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera arquivos de imagem sem abrir janela
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PASTA = Path(__file__).parent
PLANILHA = PASTA / "dados" / "epe_consumo_mensal_por_classe.xlsx"
BASE_CSV = PASTA / "dados" / "base_consumo_uf_mensal.csv"
PASTA_SAIDAS = PASTA / "saidas"

SEMENTE = 2026  # semente fixa: os sorteios dão sempre o mesmo resultado

# Cores dos gráficos (validadas para contraste e daltonismo; derivadas da identidade visual).
AZUL = "#00809f"
LARANJA = "#c96d1e"
TINTA = "#26221e"
TINTA_SUAVE = "#6b635b"
GRADE = "#e4ddd2"

# Nomes das variáveis usados em gráficos e tabelas.
ROTULOS = {
    "consumo_medio_res_kwh": "Consumo médio por residência (kWh/mês)",
    "consumo_medio_com_kwh": "Consumo médio por estabelecimento comercial (kWh/mês)",
    "participacao_industrial": "Participação da indústria no consumo (%)",
    "ano": "Ano",
}
CURTOS = {
    "consumo_medio_res_kwh": "Consumo residencial",
    "consumo_medio_com_kwh": "Consumo comercial",
    "participacao_industrial": "Participação industrial",
    "ano": "Ano",
}


def carregar_base() -> pd.DataFrame:
    return pd.read_csv(BASE_CSV)


def br(valor: float, casas: int = 2) -> str:
    """Número no formato brasileiro: 1.234,56."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor: float, casas: int = 2) -> str:
    return br(valor * 100, casas) + "%"


def p_valor(p: float) -> str:
    return "menor que 0,0001" if p < 0.0001 else br(p, 4)


def imagem(arquivo: str, legenda: str) -> str:
    """Trecho de texto que mostra um gráfico na tela e no relatório."""
    return f"![{legenda}](/ml/graficos/{arquivo})"


def estilo():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GRADE,
        "axes.labelcolor": TINTA,
        "axes.titlecolor": TINTA,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.color": GRADE,
        "grid.linewidth": 0.6,
        "xtick.color": TINTA_SUAVE,
        "ytick.color": TINTA_SUAVE,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def salvar(figura, pasta: Path, arquivo: str) -> str:
    pasta.mkdir(parents=True, exist_ok=True)
    # Sem metadados de data: o mesmo dado gera sempre o mesmo arquivo.
    figura.savefig(pasta / arquivo, metadata={"Software": None})
    plt.close(figura)
    return arquivo


def mapa_de_calor(ax, matriz: pd.DataFrame, cmap, vmin=None, vmax=None, formato=lambda v: br(v, 2)):
    """Desenha uma matriz com os valores escritos em cada célula."""
    imagem_ = ax.imshow(matriz.values, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(matriz.columns)), matriz.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(matriz.index)), matriz.index)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    norma = imagem_.norm
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz.values[i, j]
            intensidade = abs(norma(valor) - 0.5) * 2 if vmin is not None and vmin < 0 else norma(valor)
            cor = "white" if intensidade > 0.6 else TINTA
            ax.text(j, i, formato(valor), ha="center", va="center", color=cor, fontsize=10)
    return imagem_
