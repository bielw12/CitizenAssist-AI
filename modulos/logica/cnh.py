"""Módulo de decisão lógica: apto ou não para iniciar o processo de tirar a CNH.

Contribuição da disciplina Computer Science. A modelagem (variáveis, expressão, tabela-verdade,
mapa de Karnaugh e circuito) foi feita pelo grupo, sem IA. Este arquivo implementa a lógica do
grupo e a valida contra a tabela-verdade do grupo em todas as combinações.

Programa de terminal:  python -m modulos.logica.cnh
"""

from itertools import product

DATA_CONSULTA = "15/11/2026"

# Variáveis do grupo e o significado de cada valor.
VARIAVEIS = [
    {"nome": "a", "pergunta": "É maior de idade?", "rotulo": "Maior de idade",
     "um": "tem 18 anos ou mais", "zero": "tem menos de 18 anos", "falta": "ter 18 anos ou mais"},
    {"nome": "b", "pergunta": "É alfabetizado (sabe ler e escrever)?", "rotulo": "Alfabetizado",
     "um": "sabe ler e escrever", "zero": "não sabe ler e escrever", "falta": "saber ler e escrever"},
    {"nome": "c", "pergunta": "É penalmente imputável?", "rotulo": "Penalmente imputável",
     "um": "pode responder criminalmente pelos próprios atos", "zero": "não é penalmente imputável",
     "falta": "ser penalmente imputável"},
    {"nome": "d", "pergunta": "Tem documento de identidade?", "rotulo": "Tem identidade",
     "um": "tem documento de identidade", "zero": "não tem documento de identidade",
     "falta": "ter um documento de identidade"},
]
NOMES = [v["nome"] for v in VARIAVEIS]
SAIDA = {"nome": "x", "um": "apto a iniciar o processo de habilitação", "zero": "ainda não apto"}

EXPRESSAO_DO_GRUPO = "x = (a·b)·(c·d)"
EXPRESSAO_SIMPLIFICADA = "x = a·b·c·d"
FORMA_CANONICA = "x = Σm(15) = a·b·c·d"

# Transcrição da tabela-verdade feita pelo grupo (imagem tabela_verdade.png), na ordem a, b, c, d, x.
TABELA_DO_GRUPO = [
    (0, 0, 0, 0, 0), (0, 0, 0, 1, 0), (0, 0, 1, 0, 0), (0, 0, 1, 1, 0),
    (0, 1, 0, 0, 0), (0, 1, 0, 1, 0), (0, 1, 1, 0, 0), (0, 1, 1, 1, 0),
    (1, 0, 0, 0, 0), (1, 0, 0, 1, 0), (1, 0, 1, 0, 0), (1, 0, 1, 1, 0),
    (1, 1, 0, 0, 0), (1, 1, 0, 1, 0), (1, 1, 1, 0, 0), (1, 1, 1, 1, 1),
]

FONTES = [
    {
        "dado": "Requisitos para o processo de formação de condutores",
        "texto": "Art. 17: ser penalmente imputável; saber ler e escrever; possuir documento de identificação "
                 "reconhecido por lei; e estar inscrito no CPF.",
        "fonte": "Resolução CONTRAN nº 1.020, de 1º de dezembro de 2025 (Diário Oficial da União de 09/12/2025)",
        "url": "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao10202025.pdf/@@display-file/file",
    },
    {
        "dado": "Base legal da habilitação",
        "texto": "Art. 140 do Código de Trânsito Brasileiro (Lei nº 9.503/1997), regulamentado pela resolução acima.",
        "fonte": "Lei nº 9.503, de 23 de setembro de 1997",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm",
    },
    {
        "dado": "Idade da imputabilidade penal",
        "texto": "Art. 228: são penalmente inimputáveis os menores de 18 anos.",
        "fonte": "Constituição Federal de 1988",
        "url": "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
    },
]

LIMITACOES = [
    "É uma orientação simplificada, não uma decisão oficial: quem confere os requisitos é o Detran do seu estado.",
    "O resultado indica só se a pessoa pode iniciar o processo. Depois ainda há avaliação psicológica, exame médico e as provas.",
    "A Resolução CONTRAN nº 1.020/2025 também exige inscrição no CPF, que não faz parte do modelo do grupo.",
    "\"Maior de idade\" e \"penalmente imputável\" se sobrepõem: quem tem menos de 18 anos nunca é penalmente imputável. "
    "O grupo manteve as duas variáveis para deixar a regra mais clara para o cidadão.",
    "O sistema não guarda as respostas e não pede nenhum dado pessoal.",
]


class EntradaInvalida(ValueError):
    """Valor que não é 0 nem 1. A mensagem é mostrada ao usuário."""


def regra_do_grupo(a: int, b: int, c: int, d: int) -> int:
    """Expressão exatamente como o grupo escreveu: (a·b)·(c·d)."""
    return (a & b) & (c & d)


def expressao_simplificada(a: int, b: int, c: int, d: int) -> int:
    """a·b·c·d (propriedade associativa)."""
    return a & b & c & d


def para_bit(valor) -> int:
    """Aceita 0/1, True/False ou textos como "1", "0", "s", "sim", "n", "não". Recusa o resto."""
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, int) and valor in (0, 1):
        return valor
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in ("1", "s", "sim"):
            return 1
        if texto in ("0", "n", "nao", "não"):
            return 0
    raise EntradaInvalida(f"Resposta inválida: {valor!r}. Use 1 (sim) ou 0 (não).")


def avaliar(entradas: dict) -> dict:
    """Calcula a saída pelo circuito do grupo, com as saídas de cada porta, e a orientação ao cidadão."""
    faltando = [n for n in NOMES if n not in entradas]
    if faltando:
        raise EntradaInvalida(f"Falta responder: {', '.join(faltando)}.")
    a, b, c, d = (para_bit(entradas[n]) for n in NOMES)
    porta_ab = a & b
    porta_cd = c & d
    x = porta_ab & porta_cd
    pendentes = [v["falta"] for v in VARIAVEIS if not {"a": a, "b": b, "c": c, "d": d}[v["nome"]]]
    if x:
        orientacao = ("Pelas respostas, você atende aos requisitos desta simulação para iniciar o processo de "
                      "habilitação. Procure o Detran do seu estado para confirmar e seguir as próximas etapas.")
    else:
        orientacao = ("Pelas respostas, ainda não é possível iniciar o processo. Falta: "
                      + "; ".join(pendentes) + ".")
    return {
        "entradas": {"a": a, "b": b, "c": c, "d": d},
        "portas": {"a·b": porta_ab, "c·d": porta_cd, "x": x},
        "x": x,
        "apto": bool(x),
        "pendentes": pendentes,
        "orientacao": orientacao,
    }


def todas_as_combinacoes() -> list[dict]:
    """As 16 combinações, comparando tabela do grupo, regra do grupo, expressão simplificada e execução."""
    linhas = []
    for (a, b, c, d), linha_do_grupo in zip(product((0, 1), repeat=4), TABELA_DO_GRUPO):
        assert linha_do_grupo[:4] == (a, b, c, d), "A transcrição da tabela do grupo está fora de ordem."
        executado = avaliar({"a": a, "b": b, "c": c, "d": d})["x"]
        linhas.append({
            "a": a, "b": b, "c": c, "d": d,
            "tabela_do_grupo": linha_do_grupo[4],
            "regra_do_grupo": regra_do_grupo(a, b, c, d),
            "simplificada": expressao_simplificada(a, b, c, d),
            "executado": executado,
        })
    return linhas


def main(entrada=input, saida=print):
    saida("Citizen Assist AI — Posso iniciar o processo de tirar a CNH?")
    saida("Simulação educativa. Não é canal oficial e não guarda suas respostas.")
    saida("Responda com s (sim) ou n (não).\n")
    respostas = {}
    for variavel in VARIAVEIS:
        while True:
            try:
                respostas[variavel["nome"]] = para_bit(entrada(f"{variavel['pergunta']} "))
                break
            except EntradaInvalida:
                saida("Não entendi. Responda com s (sim) ou n (não).")
    resultado = avaliar(respostas)
    saida(f"\nSaída x = {resultado['x']}: {SAIDA['um'] if resultado['x'] else SAIDA['zero']}.")
    saida(resultado["orientacao"])
    return resultado


if __name__ == "__main__":
    main()
