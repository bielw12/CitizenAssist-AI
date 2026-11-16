// Texto formatado seguro: tudo é montado com createElement e textContent.
// Nunca usamos innerHTML, então nenhum texto recebido vira código na página.

export function criar(tag, texto, classe) {
  const el = document.createElement(tag);
  if (texto !== undefined && texto !== null) el.textContent = texto;
  if (classe) el.className = classe;
  return el;
}

export function criarLink(texto, url) {
  const a = criar("a", texto);
  a.href = url;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

// Imagens só podem vir da pasta de gráficos do próprio sistema.
const IMAGEM_PERMITIDA = /^\/ml\/graficos\/[\w.-]+\.png$/;

const PADRAO_LINHA =
  /!\[([^\]]*)\]\(([^)\s]+)\)|\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<>()]*[^\s<>().,;:!?])|\*([^*\s][^*]*?)\*/g;

export function formatarLinha(texto, destino) {
  let fim = 0;
  let m;
  PADRAO_LINHA.lastIndex = 0;
  while ((m = PADRAO_LINHA.exec(texto))) {
    destino.append(texto.slice(fim, m.index));
    if (m[2] !== undefined) {
      if (IMAGEM_PERMITIDA.test(m[2])) {
        const img = criar("img");
        img.src = m[2];
        img.alt = m[1];
        destino.append(img);
      } else {
        destino.append(m[0]);
      }
    } else if (m[3] !== undefined) destino.append(criar("strong", m[3]));
    else if (m[4] !== undefined) destino.append(criar("code", m[4]));
    else if (m[5] !== undefined) destino.append(criarLink(m[5], m[6]));
    else if (m[7] !== undefined) destino.append(criarLink(m[7], m[7]));
    else destino.append(criar("em", m[8]));
    fim = PADRAO_LINHA.lastIndex;
  }
  destino.append(texto.slice(fim));
}

const EH_TITULO = /^(#{1,6})\s+(.*)$/;
const EH_ITEM = /^\s*[-*•]\s+(.*)$/;
const EH_ITEM_NUMERADO = /^\s*\d+[.)]\s+(.*)$/;
const EH_LINHA_TABELA = /^\s*\|.*\|\s*$/;
const EH_SEPARADOR_TABELA = /^\s*\|[\s:|-]+\|\s*$/;
const EH_CERCA = /^\s*```/;
const EH_REGUA = /^\s*(-{3,}|\*{3,})\s*$/;

function celulas(linha) {
  return linha.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
}

// tituloBase: nível do título de um "#" (2 no relatório, 3 nas respostas do chat).
export function formatarTexto(texto, destino, tituloBase = 3) {
  destino.replaceChildren();
  destino.classList.add("texto");
  const linhas = texto.split("\n");
  let i = 0;
  while (i < linhas.length) {
    const linha = linhas[i];
    let m;
    if (!linha.trim()) {
      i++;
    } else if (EH_CERCA.test(linha)) {
      const codigo = [];
      i++;
      while (i < linhas.length && !EH_CERCA.test(linhas[i])) codigo.push(linhas[i++]);
      i++;
      destino.appendChild(criar("pre")).append(criar("code", codigo.join("\n")));
    } else if (EH_REGUA.test(linha)) {
      destino.append(criar("hr"));
      i++;
    } else if ((m = linha.match(EH_TITULO))) {
      const nivel = Math.min(tituloBase + m[1].length - 1, 4);
      formatarLinha(m[2], destino.appendChild(criar("h" + nivel)));
      i++;
    } else if (EH_LINHA_TABELA.test(linha) && EH_SEPARADOR_TABELA.test(linhas[i + 1] || "")) {
      const tabela = criar("table");
      const cabecalho = tabela.createTHead().insertRow();
      for (const c of celulas(linha)) formatarLinha(c, cabecalho.appendChild(criar("th")));
      const corpo = tabela.createTBody();
      i += 2;
      while (i < linhas.length && EH_LINHA_TABELA.test(linhas[i])) {
        const tr = corpo.insertRow();
        for (const c of celulas(linhas[i])) formatarLinha(c, tr.insertCell());
        i++;
      }
      destino.appendChild(criar("div", null, "rolagem-x")).append(tabela);
    } else if (EH_ITEM.test(linha) || EH_ITEM_NUMERADO.test(linha)) {
      const padrao = EH_ITEM.test(linha) ? EH_ITEM : EH_ITEM_NUMERADO;
      const lista = criar(padrao === EH_ITEM ? "ul" : "ol");
      while (i < linhas.length && (m = linhas[i].match(padrao))) {
        formatarLinha(m[1], lista.appendChild(criar("li")));
        i++;
      }
      destino.append(lista);
    } else {
      const p = criar("p");
      while (
        i < linhas.length && linhas[i].trim() &&
        !EH_TITULO.test(linhas[i]) && !EH_ITEM.test(linhas[i]) && !EH_ITEM_NUMERADO.test(linhas[i]) &&
        !EH_LINHA_TABELA.test(linhas[i]) && !EH_CERCA.test(linhas[i]) && !EH_REGUA.test(linhas[i])
      ) {
        if (p.childNodes.length) p.append(criar("br"));
        formatarLinha(linhas[i], p);
        i++;
      }
      destino.append(p);
    }
  }
}

// Ícones próprios, desenhados com elementos SVG (sem innerHTML).
const NS = "http://www.w3.org/2000/svg";
export function svg(tag, atributos = {}) {
  const el = document.createElementNS(NS, tag);
  for (const [nome, valor] of Object.entries(atributos)) el.setAttribute(nome, valor);
  return el;
}

export function icone(caminhos, classe) {
  const el = svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" });
  if (classe) el.setAttribute("class", classe);
  for (const d of caminhos) el.append(svg("path", { d }));
  return el;
}

export const formatoReais = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
export const formatoNumero = (casas = 0) =>
  new Intl.NumberFormat("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

// Chamada às rotas do próprio servidor, com mensagem de erro amigável.
export async function pedir(url, corpo) {
  let resposta;
  try {
    resposta = await fetch(url, corpo === undefined ? {} : {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
  } catch {
    throw new Error("Não foi possível falar com o servidor. Confira sua internet e tente de novo.");
  }
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(dados.erro || "Não foi possível concluir o pedido. Tente de novo.");
  return dados;
}
