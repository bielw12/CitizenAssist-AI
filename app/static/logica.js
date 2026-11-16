// Módulo de Decisão lógica (Computer Science): entrega do grupo, simulador e relatório.
// O resultado do simulador vem do servidor (modulos/logica/cnh.py), o mesmo código testado.
import { criar, criarLink, pedir, svg } from "./formatar.js";
import { criarRelatorio } from "./ml.js";

const IMG = "/static/logica/";
let dadosCache = null;

async function dados() {
  if (!dadosCache) dadosCache = await pedir("/api/logica/dados");
  return dadosCache;
}

function figura(destino, arquivo, legenda, alt) {
  const fig = destino.appendChild(criar("figure", null, "figura"));
  const img = fig.appendChild(criar("img"));
  img.src = IMG + arquivo;
  img.alt = alt;
  fig.append(criar("figcaption", legenda));
  return fig;
}

function avisoErro(destino, mensagem) {
  destino.appendChild(criar("div", null, "aviso")).append(criar("p", mensagem));
}

// ---------- Entrega ----------

export function montarEntrega(visao) {
  const coluna = visao.appendChild(criar("div", null, "coluna larga pagina"));
  coluna.append(criar("h2", "Entrega: posso iniciar a CNH?"));
  coluna.append(criar("p", "Contribuição da disciplina Computer Science. Variáveis, tabela-verdade, mapa de Karnaugh e circuito foram feitos pelo grupo, sem uso de inteligência artificial.", "subtitulo"));

  dados().then((d) => {
    const situacao = coluna.appendChild(criar("div", null, "cartao"));
    situacao.append(criar("h3", "Situação de atendimento"));
    situacao.append(criar("p", "O módulo informa se a pessoa atende aos requisitos básicos para iniciar o processo de tirar a Carteira Nacional de Habilitação (CNH). A saída x vale 1 (apto) somente quando as quatro condições são verdadeiras."));
    const tabela = criar("table", null, "tabela");
    const cab = tabela.createTHead().insertRow();
    for (const t of ["Variável", "Pergunta", "1 significa", "0 significa"]) cab.appendChild(criar("th", t)).scope = "col";
    const corpo = tabela.createTBody();
    for (const v of d.variaveis) {
      const tr = corpo.insertRow();
      tr.appendChild(criar("th", v.nome)).scope = "row";
      for (const t of [v.pergunta, v.um, v.zero]) tr.insertCell().textContent = t;
    }
    const trx = corpo.insertRow();
    trx.appendChild(criar("th", "x (saída)")).scope = "row";
    for (const t of ["Pode iniciar o processo?", d.saida.um, d.saida.zero]) trx.insertCell().textContent = t;
    situacao.appendChild(criar("div", null, "rolagem-x")).append(tabela);

    const expressao = coluna.appendChild(criar("div", null, "cartao"));
    expressao.append(criar("h3", "Expressão booleana"));
    expressao.append(criar("p", d.expressao_do_grupo, "expressao"));
    expressao.append(criar("p", "Pela propriedade associativa, é o mesmo que " + d.expressao_simplificada + ". A simplificação completa está no relatório.", "discreto"));

    const circuito = coluna.appendChild(criar("div", null, "cartao"));
    circuito.append(criar("h3", "Circuito lógico"));
    figura(circuito, "circuito_original.png", "Circuito original feito pelo grupo no simulador logic.ly.",
      "Circuito com quatro entradas: Maior de idade, Alfabetizado, Penalmente imputável e Tem identidade. Duas portas E combinam as entradas em pares e uma terceira porta E gera a saída.");

    const lado = coluna.appendChild(criar("div", null, "lado-a-lado"));
    const mapa = lado.appendChild(criar("div", null, "cartao"));
    mapa.append(criar("h3", "Mapa de Karnaugh"));
    figura(mapa, "mapa_karnaugh.png", "Mapa feito pelo grupo. Linhas: a, b. Colunas: c, d.",
      "Mapa de Karnaugh 4 por 4 com zeros em todas as células, exceto um 1 na linha ab = 11 e coluna cd = 11.");

    const verdade = lado.appendChild(criar("div", null, "cartao"));
    verdade.append(criar("h3", "Tabela-verdade"));
    const grade = verdade.appendChild(criar("div", null, "tabela-verdade"));
    figura(grade, "tabela_verdade.png", "Original do grupo (colunas a, b, c, d e x).",
      "Tabela-verdade com as 16 combinações de a, b, c e d. A saída x é 1 apenas na última linha, 1 1 1 1.");
    const transcricao = grade.appendChild(criar("div"));
    transcricao.append(criar("p", "Transcrição da tabela do grupo", "discreto"));
    const t2 = transcricao.appendChild(criar("table", null, "tabela compacta"));
    const c2 = t2.createTHead().insertRow();
    for (const n of ["a", "b", "c", "d", "x"]) c2.appendChild(criar("th", n)).scope = "col";
    const b2 = t2.createTBody();
    for (const linha of d.tabela_do_grupo) {
      const tr = b2.insertRow();
      if (linha.x === 1) tr.className = "destaque-linha";
      for (const n of ["a", "b", "c", "d", "x"]) tr.insertCell().textContent = linha[n];
    }

    const fontes = coluna.appendChild(criar("div", null, "cartao"));
    fontes.append(criar("h3", "Regras e fontes"));
    const lista = fontes.appendChild(criar("ul", null, "fontes-lista"));
    for (const f of d.fontes) {
      const li = lista.appendChild(criar("li"));
      li.append(criar("strong", f.dado + ": "), f.texto + " ");
      li.append(criarLink(f.fonte, f.url), ".");
    }
    fontes.append(criar("p", `Consulta em ${d.data_consulta}.`, "discreto"));
  }).catch((falha) => avisoErro(coluna, falha.message));
}

// ---------- Simulador ----------

const LIGADO = "ligado";

function porta(x, y) {
  // Porta E: lado reto à esquerda e arco à direita, altura 90.
  return svg("path", { d: `M${x} ${y} h45 a45 45 0 0 1 0 90 h-45 Z`, class: "porta" });
}

function fio(pontos) {
  return svg("polyline", { points: pontos.map((p) => p.join(",")).join(" "), class: "fio" });
}

function rotuloValor(x, y) {
  return svg("text", { x, y, class: "valor", "text-anchor": "middle" });
}

function desenharCircuito(variaveis) {
  const cena = svg("svg", { viewBox: "0 0 720 400", class: "circuito", role: "img" });
  const titulo = cena.appendChild(svg("title"));
  const ys = { a: 73, b: 150, c: 263, d: 340 };
  const entradas = {};
  const fios = {};
  const valores = {};

  // Portas: E1 (a·b), E2 (c·d), E3 (saída)
  const e1 = cena.appendChild(porta(320, 60));
  const e2 = cena.appendChild(porta(320, 250));
  const e3 = cena.appendChild(porta(500, 155));
  for (const [x, y] of [[352, 110], [352, 300], [532, 205]]) {
    const t = cena.appendChild(svg("text", { x, y, class: "rotulo-porta", "text-anchor": "middle" }));
    t.textContent = "E";
  }

  // Fios das entradas até as portas da primeira camada
  const destino = { a: 80, b: 130, c: 270, d: 320 };
  for (const v of variaveis) {
    const y = ys[v.nome];
    fios[v.nome] = cena.insertBefore(fio([[176, y], [285, y], [285, destino[v.nome]], [320, destino[v.nome]]]), e1);
    valores[v.nome] = cena.appendChild(rotuloValor(230, y - 8));

    const grupo = cena.appendChild(svg("g", { class: "entrada" }));
    grupo.append(svg("rect", { x: 150, y: y - 13, width: 26, height: 26, rx: 3 }));
    const bit = grupo.appendChild(svg("text", { x: 163, y: y + 5, class: "bit", "text-anchor": "middle" }));
    const rotulo = cena.appendChild(svg("text", { x: 176, y: y - 22, class: "rotulo-entrada", "text-anchor": "end" }));
    rotulo.textContent = v.rotulo + "?";
    entradas[v.nome] = { grupo, bit };
  }

  // Saídas das portas
  fios["a·b"] = cena.insertBefore(fio([[410, 105], [460, 105], [460, 175], [500, 175]]), e1);
  fios["c·d"] = cena.insertBefore(fio([[410, 295], [460, 295], [460, 225], [500, 225]]), e1);
  fios.x = cena.insertBefore(fio([[590, 200], [632, 200]]), e1);
  valores["a·b"] = cena.appendChild(rotuloValor(435, 97));
  valores["c·d"] = cena.appendChild(rotuloValor(435, 287));
  valores.x = cena.appendChild(rotuloValor(611, 192));
  const lampada = cena.appendChild(svg("circle", { cx: 652, cy: 200, r: 20, class: "lampada" }));
  const textoLampada = cena.appendChild(svg("text", { x: 652, y: 206, class: "bit", "text-anchor": "middle" }));
  const legendaX = cena.appendChild(svg("text", { x: 652, y: 245, class: "rotulo-entrada", "text-anchor": "middle" }));
  legendaX.textContent = "x";

  return { cena, titulo, entradas, fios, valores, portas: { "a·b": e1, "c·d": e2, x: e3 }, lampada, textoLampada };
}

export function montarSimulador(visao) {
  const coluna = visao.appendChild(criar("div", null, "coluna larga pagina"));
  coluna.append(criar("h2", "Simulador: posso iniciar a CNH?"));
  coluna.append(criar("p", "Ligue ou desligue cada condição e veja o sinal percorrer o circuito projetado pelo grupo. O verde indica 1 (sim) e o cinza indica 0 (não).", "subtitulo"));

  const area = coluna.appendChild(criar("div", null, "simulador-logico"));
  const painel = area.appendChild(criar("div", null, "cartao"));
  painel.append(criar("h3", "Suas respostas"));
  const listaInterruptores = painel.appendChild(criar("div", null, "interruptores"));
  const resultado = area.appendChild(criar("div", null, "cartao resultado-logico"));
  resultado.setAttribute("aria-live", "polite");
  const desenho = coluna.appendChild(criar("div", null, "cartao"));
  const erroEl = coluna.appendChild(criar("p", null, "mensagem-erro"));
  erroEl.setAttribute("role", "alert");
  erroEl.hidden = true;

  const estado = { a: 1, b: 1, c: 1, d: 1 };
  let circuito = null;
  const botoes = {};
  let pedidoAtual = 0;

  function marcar(el, ligado) {
    el.classList.toggle(LIGADO, Boolean(ligado));
  }

  function mostrar(r) {
    for (const nome of Object.keys(estado)) {
      const v = r.entradas[nome];
      marcar(circuito.entradas[nome].grupo, v);
      circuito.entradas[nome].bit.textContent = v;
      marcar(circuito.fios[nome], v);
      marcar(circuito.valores[nome], v);
      circuito.valores[nome].textContent = v;
    }
    for (const nome of ["a·b", "c·d", "x"]) {
      const v = r.portas[nome];
      marcar(circuito.fios[nome], v);
      marcar(circuito.portas[nome], v);
      marcar(circuito.valores[nome], v);
      circuito.valores[nome].textContent = v;
    }
    marcar(circuito.lampada, r.x);
    circuito.textoLampada.textContent = r.x;
    const e = r.entradas;
    circuito.titulo.textContent = `Circuito com a=${e.a}, b=${e.b}, c=${e.c}, d=${e.d}: a·b=${r.portas["a·b"]}, c·d=${r.portas["c·d"]}, saída x=${r.x}.`;

    const conta = `x = (a·b)·(c·d) = (${e.a}·${e.b})·(${e.c}·${e.d}) = ${r.portas["a·b"]}·${r.portas["c·d"]} = ${r.x}`;
    resultado.replaceChildren(
      criar("p", r.apto ? "Apto a iniciar o processo" : "Ainda não apto", "resultado-titulo " + (r.apto ? "apto" : "nao-apto")),
      criar("p", conta, "expressao"),
      criar("p", r.orientacao),
    );
  }

  async function atualizar() {
    const numero = ++pedidoAtual;
    try {
      const r = await pedir("/api/logica/avaliar", estado);
      if (numero !== pedidoAtual) return; // chegou uma resposta mais nova
      erroEl.hidden = true;
      mostrar(r);
    } catch (falha) {
      erroEl.textContent = falha.message;
      erroEl.hidden = false;
    }
  }

  function alternar(nome) {
    estado[nome] = estado[nome] ? 0 : 1;
    botoes[nome].setAttribute("aria-checked", String(Boolean(estado[nome])));
    botoes[nome].querySelector(".estado").textContent = estado[nome] ? "Sim (1)" : "Não (0)";
    atualizar();
  }

  dados().then((d) => {
    for (const v of d.variaveis) {
      const linha = listaInterruptores.appendChild(criar("div", null, "interruptor-linha"));
      const rotulo = linha.appendChild(criar("span", `${v.nome}: ${v.pergunta}`, "interruptor-rotulo"));
      rotulo.id = "rotulo-" + v.nome;
      const botao = linha.appendChild(criar("button", null, "interruptor"));
      botao.type = "button";
      botao.setAttribute("role", "switch");
      botao.setAttribute("aria-checked", "true");
      botao.setAttribute("aria-labelledby", rotulo.id);
      botao.append(criar("span", null, "trilho-interruptor"), criar("span", "Sim (1)", "estado"));
      botao.addEventListener("click", () => alternar(v.nome));
      botoes[v.nome] = botao;
    }
    const acoes = painel.appendChild(criar("div", null, "acoes"));
    const todos = acoes.appendChild(criar("button", "Ligar todas", "botao claro pequeno"));
    todos.type = "button";
    todos.addEventListener("click", () => {
      for (const nome of Object.keys(estado)) if (!estado[nome]) alternar(nome);
    });

    circuito = desenharCircuito(d.variaveis);
    for (const v of d.variaveis) {
      circuito.entradas[v.nome].grupo.addEventListener("click", () => alternar(v.nome));
    }
    desenho.append(criar("h3", "Circuito do grupo em funcionamento"), circuito.cena,
      criar("p", "Redesenho do circuito projetado pelo grupo (veja o original em Entrega), usado apenas para animar o funcionamento. Você também pode clicar nas caixas de entrada.", "discreto"));

    const aviso = coluna.appendChild(criar("div", null, "aviso"));
    aviso.append(criar("p", "Esta é uma simulação educativa. Não é um canal oficial e não confirma nenhum direito: quem confere os requisitos é o Detran do seu estado. Suas respostas não são guardadas."));
    const limites = aviso.appendChild(criar("ul"));
    for (const texto of d.limitacoes.slice(1, 3)) limites.append(criar("li", texto));
    atualizar();
  }).catch((falha) => avisoErro(coluna, falha.message));
}

// ---------- Relatório ----------

export function montarRelatorioLogica(visao) {
  criarRelatorio(visao, "/api/logica/relatorio", "/logica/relatorio.pdf");
}
