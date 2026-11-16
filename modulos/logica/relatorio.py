"""Relatório técnico de Computer Science (IA permitida pelo enunciado apenas para o relatório).

A tabela de resultados dos testes é calculada pelo código a cada geração, nunca digitada.
"""

from . import cnh

IMG = "/static/logica/"


def _tabela_variaveis() -> str:
    linhas = ["| Variável | Pergunta | 1 significa | 0 significa |", "|---|---|---|---|"]
    linhas += [f"| **{v['nome']}** | {v['pergunta']} | {v['um']} | {v['zero']} |" for v in cnh.VARIAVEIS]
    linhas.append(f"| **x** (saída) | Pode iniciar o processo? | {cnh.SAIDA['um']} | {cnh.SAIDA['zero']} |")
    return "\n".join(linhas)


def _tabela_testes(linhas) -> str:
    cabecalho = ["| a | b | c | d | Tabela do grupo | (a·b)·(c·d) | a·b·c·d | Programa | Iguais? |",
                 "|---|---|---|---|---|---|---|---|---|"]
    corpo = []
    for l in linhas:
        iguais = l["tabela_do_grupo"] == l["regra_do_grupo"] == l["simplificada"] == l["executado"]
        corpo.append(f"| {l['a']} | {l['b']} | {l['c']} | {l['d']} | {l['tabela_do_grupo']} | {l['regra_do_grupo']} "
                     f"| {l['simplificada']} | {l['executado']} | {'sim' if iguais else '**NÃO**'} |")
    return "\n".join(cabecalho + corpo)


def montar() -> str:
    linhas = cnh.todas_as_combinacoes()
    todas_iguais = all(l["tabela_do_grupo"] == l["regra_do_grupo"] == l["simplificada"] == l["executado"] for l in linhas)
    mintermos = [i for i, l in enumerate(linhas) if l["tabela_do_grupo"] == 1]
    fontes = "\n".join(f"- {f['fonte']}. {f['texto']} Disponível em: {f['url']}. Acesso em: {cnh.DATA_CONSULTA}."
                       for f in cnh.FONTES)
    limitacoes = "\n".join(f"- {texto}" for texto in cnh.LIMITACOES)

    return f"""\
# Relatório técnico: módulo de decisão lógica para iniciar a CNH

**Global Solution GS26_2 — Citizen Assist AI** · Disciplina Computer Science · Ciência da Computação, turma 1CC

**Integrantes:** [PENDENTE: nome completo e RM de cada integrante]

**Autoria:** variáveis, regras, tabela-verdade, mapa de Karnaugh e circuito lógico foram feitos pelo grupo, sem uso de inteligência artificial. A inteligência artificial foi usada apenas na redação deste relatório e na programação do simulador, como permitido pelo enunciado. [PENDENTE: confirmar com o professor o uso de IA no código do simulador]

## 1. Descrição do problema

Muitas pessoas não sabem se já podem começar o processo para tirar a Carteira Nacional de Habilitação (CNH). O Citizen Assist AI oferece uma orientação rápida: a pessoa responde a quatro perguntas de sim ou não e o assistente indica se ela atende aos requisitos básicos para iniciar o processo e, se não atender, o que falta.

**Situação de atendimento escolhida:** orientação sobre os requisitos para iniciar o processo de habilitação.

## 2. Variáveis, regras e referências

{_tabela_variaveis()}

**Regra:** a pessoa está apta (x = 1) somente quando as quatro condições são verdadeiras ao mesmo tempo.

**Referências (consulta em {cnh.DATA_CONSULTA}):**

{fontes}

O texto da Resolução CONTRAN nº 1.020/2025 foi conferido no arquivo oficial do Diário Oficial da União publicado no portal do Ministério dos Transportes. Os textos do Código de Trânsito e da Constituição foram conferidos em cópias de sites jurídicos; os links acima são os oficiais, do Planalto.

## 3. Tabela-verdade

Tabela feita pelo grupo (ordem das colunas: a, b, c, d e x):

![Tabela-verdade feita pelo grupo]({IMG}tabela_verdade.png)

A transcrição dessa tabela, linha a linha, está na seção 9, ao lado dos resultados do programa.

## 4. Expressão booleana

- **Expressão do grupo:** {cnh.EXPRESSAO_DO_GRUPO}
- **Forma canônica (soma de mintermos):** a saída vale 1 apenas no mintermo {mintermos[0]}, a última linha da tabela (a = b = c = d = 1). Logo, {cnh.FORMA_CANONICA}.
- **Forma canônica (produto de maxtermos):** a saída vale 0 nas outras 15 linhas, então x = ΠM(0, 1, 2, …, 14). Como só há um mintermo, a soma de mintermos é a forma mais curta e foi a adotada.

## 5. Simplificação por álgebra booleana

| Passo | Expressão | Propriedade usada |
|---|---|---|
| 1 | x = (a·b)·(c·d) | expressão do grupo |
| 2 | x = a·b·c·d | associativa do produto: (a·b)·(c·d) = a·b·c·d |

A expressão já está na forma mínima: é um único produto com as quatro variáveis, sem termos repetidos nem complementos para eliminar. Não há como retirar nenhuma variável, porque cada uma, sozinha, pode tornar x igual a 0.

**Teoremas de De Morgan:** não foram necessários. Eles servem para transformar complementos de somas ou de produtos, e a expressão do grupo não tem nenhum complemento. O enunciado pede essa transformação somente se necessária.

## 6. Mapa de Karnaugh

Mapa feito pelo grupo (linhas: a, b; colunas: c, d):

![Mapa de Karnaugh feito pelo grupo]({IMG}mapa_karnaugh.png)

- **Agrupamento:** há um único 1, na célula a = 1, b = 1, c = 1, d = 1. Ele não tem nenhum 1 vizinho, então forma um grupo de uma célula só.
- **Termo do grupo:** a célula fixa as quatro variáveis em 1, o que dá a·b·c·d.
- **Comparação com a álgebra:** o resultado do mapa (x = a·b·c·d) é igual ao da simplificação algébrica da seção 5.

## 7. Circuitos lógicos

**Circuito original (feito pelo grupo no simulador logic.ly):** três portas E (AND) de 2 entradas, uma para a·b, uma para c·d e uma que junta as duas.

![Circuito lógico original feito pelo grupo]({IMG}circuito_original.png)

**Circuito simplificado:** uma porta E de 4 entradas, ligada diretamente a a, b, c e d.

[PENDENTE: imagem do circuito simplificado, desenhada pelo grupo no logic.ly ou no LogicCircuit]

**Comparação de portas (mesmo critério de representação):**

| Critério | Original | Simplificado |
|---|---|---|
| Número de portas | 3 portas E de 2 entradas | 1 porta E de 4 entradas |
| Total de portas | 3 | 1 |
| Equivalente em portas E de 2 entradas | 3 | 3 (uma porta de 4 entradas equivale a 3 portas de 2 entradas) |
| Níveis de portas entre entrada e saída | 2 | 1 |

O circuito simplificado usa menos componentes e tem um nível só. Contando apenas portas de 2 entradas, os dois são equivalentes, o que confirma que a expressão do grupo já era mínima e a simplificação apenas reorganiza o produto.

## 8. Implementação

A lógica foi implementada em Python, em `modulos/logica/cnh.py`, e aparece no sistema em **Decisão lógica → Simulador**.

- **Programa de terminal:** `python -m modulos.logica.cnh` faz as quatro perguntas, aceita s/n ou 1/0 e mostra a saída e a orientação.
- **Simulador na tela:** quatro interruptores ligam e desligam as entradas. O desenho do circuito do grupo mostra o valor (0 ou 1) de cada fio e de cada porta, e a lâmpada de saída acende quando x = 1. Cada resultado vem do mesmo código Python.
- **Entradas inválidas:** qualquer resposta diferente de sim/não ou 1/0 é recusada com uma mensagem clara (no terminal, a pergunta é repetida; no sistema, aparece um aviso).
- **Orientação compreensível:** além de x, o sistema explica em português o que falta para a pessoa ficar apta.

## 9. Testes: equivalência em todas as combinações

O teste automático (`tests/test_logica.py`) compara, nas 16 combinações, a tabela-verdade do grupo, a expressão original do grupo, a expressão simplificada e o resultado executado pelo programa. A tabela abaixo é gerada pelo próprio código a cada vez que o relatório é montado.

{_tabela_testes(linhas)}

**Resultado:** {"as quatro representações coincidem nas 16 combinações." if todas_iguais else "há divergência entre as representações; veja as linhas marcadas."}

## 10. Prints da simulação

- Prints do simulador do sistema: ver a seção "Decisão lógica → Simulador" e os arquivos em `docs/computer_science/`.
- [PENDENTE: prints da simulação no logic.ly ou no LogicCircuit, feitos pelo grupo]

## 11. Instruções de execução

1. Siga a instalação descrita no `README.md` do repositório.
2. Programa de terminal: `python -m modulos.logica.cnh`
3. Sistema completo: `uvicorn app.main:app --port 8000` e abra http://127.0.0.1:8000, em "Decisão lógica".
4. Testes: `python -m pytest tests/test_logica.py`

## 12. Limitações, privacidade e uso responsável

{limitacoes}
- O Citizen Assist AI é um protótipo acadêmico. Não é um canal oficial e não confirma a concessão de serviços ou direitos.
"""
