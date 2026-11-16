"use strict";

const EM_CONSTRUCAO = {
  logica: {
    titulo: "Decisão lógica (Computer Science)",
    texto: "Aqui você vai responder a algumas perguntas de sim ou não e receber a orientação correspondente. O módulo entra quando o grupo concluir a tabela-verdade, o mapa de Karnaugh e o circuito lógico.",
  },
  ml: {
    titulo: "Dados e estatística (Modelagem Linear)",
    texto: "Aqui vão ficar a análise estatística de uma base de dados real, com as questões já respondidas, e um chat para tirar dúvidas sobre os resultados.",
  },
  energia: {
    titulo: "Energia (Energias Renováveis)",
    texto: "Aqui você vai poder comparar energia solar com medidas de economia para reduzir a conta de luz, com cálculos, fontes e limitações.",
  },
};

const ERRO_SERVIDOR = "Não foi possível falar com o servidor. Confira sua internet e tente de novo.";
const ERRO_INTERROMPIDA = "A resposta foi interrompida antes do fim. Tente de novo.";
const MAX_HISTORICO = 20;

const historico = []; // conversa do módulo geral; existe só enquanto a página está aberta
let ocupado = false;

const mensagens = document.getElementById("mensagens");
const statusEl = document.getElementById("status");
const formulario = document.getElementById("formulario");
const campo = document.getElementById("mensagem");
const botaoEnviar = document.getElementById("enviar");

// ---------- Texto formatado ----------
// A resposta do assistente é montada só com createElement e textContent.
// Nunca usamos innerHTML, então nenhum texto recebido vira código na página.

function criar(tag, texto) {
  const el = document.createElement(tag);
  if (texto !== undefined) el.textContent = texto;
  return el;
}

function criarLink(texto, url) {
  const a = criar("a", texto);
  a.href = url;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

function formatarLinha(texto, destino) {
  const padrao = /\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<>()]*[^\s<>().,;:!?])/g;
  let fim = 0;
  let m;
  while ((m = padrao.exec(texto))) {
    destino.append(texto.slice(fim, m.index));
    if (m[1] !== undefined) destino.append(criar("strong", m[1]));
    else if (m[2] !== undefined) destino.append(criar("code", m[2]));
    else if (m[3] !== undefined) destino.append(criarLink(m[3], m[4]));
    else destino.append(criarLink(m[5], m[5]));
    fim = padrao.lastIndex;
  }
  destino.append(texto.slice(fim));
}

const EH_TITULO = /^#{1,6}\s+(.*)$/;
const EH_ITEM = /^\s*[-*•]\s+(.*)$/;
const EH_ITEM_NUMERADO = /^\s*\d+[.)]\s+(.*)$/;
const EH_LINHA_TABELA = /^\s*\|.*\|\s*$/;
const EH_SEPARADOR_TABELA = /^\s*\|[\s:|-]+\|\s*$/;

function celulas(linha) {
  return linha.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
}

function formatarTexto(texto, destino) {
  destino.replaceChildren();
  const linhas = texto.split("\n");
  let i = 0;
  while (i < linhas.length) {
    const linha = linhas[i];
    let m;
    if (!linha.trim()) {
      i++;
    } else if ((m = linha.match(EH_TITULO))) {
      const h = criar("h3");
      formatarLinha(m[1], h);
      destino.append(h);
      i++;
    } else if (EH_LINHA_TABELA.test(linha) && EH_SEPARADOR_TABELA.test(linhas[i + 1] || "")) {
      const tabela = criar("table");
      const cabecalho = tabela.createTHead().insertRow();
      for (const c of celulas(linha)) {
        const th = criar("th");
        formatarLinha(c, th);
        cabecalho.append(th);
      }
      const corpo = tabela.createTBody();
      i += 2;
      while (i < linhas.length && EH_LINHA_TABELA.test(linhas[i])) {
        const tr = corpo.insertRow();
        for (const c of celulas(linhas[i])) formatarLinha(c, tr.insertCell());
        i++;
      }
      const rolagem = criar("div");
      rolagem.className = "rolagem";
      rolagem.append(tabela);
      destino.append(rolagem);
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
        !EH_TITULO.test(linhas[i]) && !EH_ITEM.test(linhas[i]) &&
        !EH_ITEM_NUMERADO.test(linhas[i]) && !EH_LINHA_TABELA.test(linhas[i])
      ) {
        if (p.childNodes.length) p.append(criar("br"));
        formatarLinha(linhas[i], p);
        i++;
      }
      destino.append(p);
    }
  }
}

// ---------- Conversa ----------

function novaBolha(classe) {
  const bolha = criar("div");
  bolha.className = "bolha " + classe;
  mensagens.append(bolha);
  bolha.scrollIntoView({ block: "end" });
  return bolha;
}

function mostrarFontes(bolha, fontes) {
  const caixa = criar("div");
  caixa.className = "fontes";
  caixa.append(criar("strong", "Fontes consultadas:"));
  const lista = criar("ul");
  for (const f of fontes) {
    if (/^https?:\/\//.test(f.url)) lista.appendChild(criar("li")).append(criarLink(f.titulo, f.url));
  }
  caixa.append(lista);
  bolha.append(caixa);
}

async function enviar(texto) {
  ocupado = true;
  botaoEnviar.disabled = true;
  mensagens.setAttribute("aria-busy", "true");

  novaBolha("pessoa").textContent = texto;
  const bolha = novaBolha("assistente");
  const corpo = bolha.appendChild(criar("div"));
  statusEl.textContent = "Escrevendo…";

  let resposta = "";
  let erro = null;
  let terminou = false;

  function tratar(evento) {
    if (evento.tipo === "texto") {
      resposta += evento.texto;
      formatarTexto(resposta, corpo);
      statusEl.textContent = "Escrevendo…";
      bolha.scrollIntoView({ block: "end" });
    } else if (evento.tipo === "status") {
      statusEl.textContent = evento.texto;
    } else if (evento.tipo === "aviso") {
      bolha.append(Object.assign(criar("p", evento.texto), { className: "aviso-resposta" }));
    } else if (evento.tipo === "fontes") {
      mostrarFontes(bolha, evento.fontes);
    } else if (evento.tipo === "erro") {
      erro = evento.texto;
    } else if (evento.tipo === "fim") {
      terminou = true;
    }
  }

  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modulo: "geral", historico: historico.slice(-MAX_HISTORICO), mensagem: texto }),
    });
    if (!r.ok) {
      const dados = await r.json().catch(() => ({}));
      erro = dados.erro || ERRO_SERVIDOR;
    } else {
      const leitor = r.body.getReader();
      const decodificador = new TextDecoder();
      let pendente = "";
      for (;;) {
        const { value, done } = await leitor.read();
        if (done) break;
        pendente += decodificador.decode(value, { stream: true });
        let corte;
        while ((corte = pendente.indexOf("\n\n")) >= 0) {
          const bloco = pendente.slice(0, corte);
          pendente = pendente.slice(corte + 2);
          if (bloco.startsWith("data: ")) tratar(JSON.parse(bloco.slice(6)));
        }
      }
      if (!erro && !terminou) erro = ERRO_INTERROMPIDA;
    }
  } catch {
    erro = ERRO_SERVIDOR;
  }

  if (erro) {
    if (!resposta) bolha.remove();
    novaBolha("erro").textContent = erro;
  } else if (resposta) {
    historico.push({ role: "user", content: texto }, { role: "assistant", content: resposta });
  }

  statusEl.textContent = "";
  mensagens.setAttribute("aria-busy", "false");
  botaoEnviar.disabled = false;
  ocupado = false;
  campo.focus();
}

formulario.addEventListener("submit", (e) => {
  e.preventDefault();
  const texto = campo.value.trim();
  if (!texto || ocupado) return;
  campo.value = "";
  enviar(texto);
});

campo.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    formulario.requestSubmit();
  }
});

document.getElementById("nova-conversa").addEventListener("click", () => {
  if (ocupado) return;
  historico.length = 0;
  mensagens.replaceChildren();
  campo.focus();
});

// ---------- Troca de módulo ----------

const painelChat = document.getElementById("painel-chat");
const painelConstrucao = document.getElementById("painel-construcao");

for (const botao of document.querySelectorAll(".modulo")) {
  botao.addEventListener("click", () => {
    for (const b of document.querySelectorAll(".modulo")) b.removeAttribute("aria-current");
    botao.setAttribute("aria-current", "page");
    const info = EM_CONSTRUCAO[botao.dataset.modulo];
    painelChat.hidden = Boolean(info);
    painelConstrucao.hidden = !info;
    if (info) {
      document.getElementById("titulo-construcao").textContent = info.titulo;
      document.getElementById("texto-construcao").textContent = info.texto;
    }
  });
}
