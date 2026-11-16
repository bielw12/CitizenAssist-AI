// Componente de chat, usado pelos módulos geral, energia e estatística.
import { criar, criarLink, formatarTexto, icone, svg } from "./formatar.js";

const ERRO_SERVIDOR = "Não foi possível falar com o servidor. Confira sua internet e tente de novo.";
const ERRO_INTERROMPIDA = "A resposta foi interrompida antes do fim. Tente de novo.";
const MAX_HISTORICO = 20;

function avatar() {
  const el = svg("svg", { viewBox: "0 0 32 32", class: "avatar marca-icone", "aria-hidden": "true" });
  el.append(svg("rect", { width: 32, height: 32, rx: 9, class: "marca-fundo" }));
  el.append(svg("path", {
    class: "marca-traco",
    d: "M9 12.5a4.5 4.5 0 0 1 4.5-4.5h5A4.5 4.5 0 0 1 23 12.5v3a4.5 4.5 0 0 1-4.5 4.5H15l-4 3.5V19.6A4.5 4.5 0 0 1 9 15.5z",
  }));
  return el;
}

/**
 * Monta um chat dentro de `visao`.
 * opcoes: { modulo, titulo, saudacao, descricao, sugestoes: [texto], rotuloCampo }
 */
export function criarChat(visao, opcoes) {
  visao.classList.add("visao-chat");
  const historico = []; // existe só enquanto a página está aberta
  let ocupado = false;
  let grudado = true; // a rolagem acompanha a resposta enquanto a pessoa não rolar para cima

  // Topo
  const topo = criar("div", null, "coluna chat-topo");
  topo.append(criar("h2", opcoes.titulo));
  const botaoNova = criar("button", "Nova conversa", "botao claro pequeno");
  botaoNova.type = "button";
  topo.append(botaoNova);

  // Área que rola
  const rolagem = criar("div", null, "chat-rolagem");
  const coluna = rolagem.appendChild(criar("div", null, "coluna"));
  const inicio = coluna.appendChild(criar("div", null, "chat-inicio"));
  inicio.append(criar("h3", opcoes.saudacao), criar("p", opcoes.descricao));
  const sugestoes = inicio.appendChild(criar("div", null, "sugestoes"));
  for (const texto of opcoes.sugestoes) {
    const b = criar("button", texto, "sugestao");
    b.type = "button";
    b.addEventListener("click", () => enviar(texto));
    sugestoes.append(b);
  }
  const privacidade = inicio.appendChild(criar("div", null, "aviso privacidade"));
  privacidade.setAttribute("role", "note");
  const p1 = privacidade.appendChild(criar("p"));
  p1.append(criar("strong", "Sou uma inteligência artificial e posso errar. "),
    "Não sou um canal oficial do governo e não confirmo a concessão de serviços ou direitos. Confira as informações importantes na fonte oficial.");
  const p2 = privacidade.appendChild(criar("p"));
  p2.append(criar("strong", "Privacidade: "),
    "não envie CPF, senhas nem dados de cartão. Sua mensagem é enviada ao serviço de inteligência artificial da Anthropic para gerar a resposta. Este site não guarda a conversa: ela some quando você fecha ou recarrega a página.");

  const mensagens = coluna.appendChild(criar("div", null, "mensagens"));
  mensagens.setAttribute("role", "log");
  mensagens.setAttribute("aria-live", "polite");
  mensagens.setAttribute("aria-label", "Conversa");

  // Base fixa: status, campo e aviso
  const base = criar("div", null, "chat-base");
  const colunaBase = base.appendChild(criar("div", null, "coluna"));
  const irFim = criar("button", "Ir para o fim", "botao claro pequeno ir-fim");
  irFim.type = "button";
  irFim.hidden = true;
  const statusEl = criar("p", "", "status");
  statusEl.setAttribute("role", "status");
  const formulario = criar("form", null, "compositor");
  const idCampo = "mensagem-" + opcoes.modulo;
  const rotulo = criar("label", opcoes.rotuloCampo || "Sua pergunta", "so-leitor");
  rotulo.htmlFor = idCampo;
  const campo = criar("textarea");
  campo.id = idCampo;
  campo.rows = 1;
  campo.maxLength = 2000;
  campo.required = true;
  campo.placeholder = "Escreva sua dúvida aqui";
  const botaoEnviar = criar("button", null, "enviar");
  botaoEnviar.type = "submit";
  botaoEnviar.setAttribute("aria-label", "Enviar mensagem");
  botaoEnviar.append(icone(["M12 19V5", "M6 11l6-6 6 6"]));
  formulario.append(rotulo, campo, botaoEnviar);
  const rodape = criar("p", "Sou uma IA e posso errar. Não sou canal oficial. Não envie CPF, senhas ou dados de cartão.", "rodape-aviso");
  colunaBase.append(irFim, statusEl, formulario, rodape);

  visao.append(topo, rolagem, base);

  // ---------- Rolagem que acompanha a conversa ----------
  function irParaFim() {
    rolagem.scrollTop = rolagem.scrollHeight;
  }
  function acompanhar() {
    if (grudado) irParaFim();
  }
  rolagem.addEventListener("scroll", () => {
    grudado = rolagem.scrollHeight - rolagem.scrollTop - rolagem.clientHeight < 80;
    irFim.hidden = grudado || !ocupado;
  });
  irFim.addEventListener("click", () => {
    grudado = true;
    irFim.hidden = true;
    irParaFim();
  });

  function ajustarAltura() {
    campo.style.height = "auto";
    campo.style.height = Math.min(campo.scrollHeight, 192) + "px";
  }

  function mostrarFontes(corpo, fontes) {
    const caixa = criar("div", null, "fontes");
    caixa.append(criar("strong", "Fontes consultadas:"));
    const lista = caixa.appendChild(criar("ul"));
    for (const f of fontes) {
      if (/^https?:\/\//.test(f.url)) lista.appendChild(criar("li")).append(criarLink(f.titulo, f.url));
    }
    corpo.append(caixa);
  }

  async function enviar(texto) {
    if (ocupado) return;
    ocupado = true;
    grudado = true;
    botaoEnviar.disabled = true;
    inicio.hidden = true;
    mensagens.setAttribute("aria-busy", "true");

    mensagens.append(criar("div", texto, "msg-pessoa"));
    const bloco = mensagens.appendChild(criar("div", null, "msg-assistente"));
    bloco.append(avatar());
    const corpo = bloco.appendChild(criar("div", null, "corpo"));
    const textoEl = corpo.appendChild(criar("div", null, "cursor"));
    statusEl.textContent = "Pensando…";
    irParaFim();

    let resposta = "";
    let erro = null;
    let terminou = false;

    function tratar(evento) {
      if (evento.tipo === "texto") {
        resposta += evento.texto;
        formatarTexto(resposta, textoEl);
        textoEl.classList.add("cursor");
        statusEl.textContent = "Escrevendo…";
      } else if (evento.tipo === "status") {
        statusEl.textContent = evento.texto;
      } else if (evento.tipo === "aviso") {
        corpo.append(criar("p", evento.texto, "aviso-resposta"));
      } else if (evento.tipo === "fontes") {
        mostrarFontes(corpo, evento.fontes);
      } else if (evento.tipo === "erro") {
        erro = evento.texto;
      } else if (evento.tipo === "fim") {
        terminou = true;
      }
      acompanhar();
    }

    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modulo: opcoes.modulo, historico: historico.slice(-MAX_HISTORICO), mensagem: texto }),
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
            const trecho = pendente.slice(0, corte);
            pendente = pendente.slice(corte + 2);
            if (trecho.startsWith("data: ")) tratar(JSON.parse(trecho.slice(6)));
          }
        }
        if (!erro && !terminou) erro = ERRO_INTERROMPIDA;
      }
    } catch {
      erro = ERRO_SERVIDOR;
    }

    textoEl.classList.remove("cursor");
    if (erro) {
      if (!resposta) bloco.remove();
      mensagens.append(criar("div", erro, "msg-erro"));
    } else if (resposta) {
      historico.push({ role: "user", content: texto }, { role: "assistant", content: resposta });
    }

    statusEl.textContent = "";
    irFim.hidden = true;
    mensagens.setAttribute("aria-busy", "false");
    botaoEnviar.disabled = false;
    ocupado = false;
    acompanhar();
    campo.focus();
  }

  formulario.addEventListener("submit", (e) => {
    e.preventDefault();
    const texto = campo.value.trim();
    if (!texto || ocupado) return;
    campo.value = "";
    ajustarAltura();
    enviar(texto);
  });
  campo.addEventListener("input", ajustarAltura);
  campo.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      formulario.requestSubmit();
    }
  });
  botaoNova.addEventListener("click", () => {
    if (ocupado) return;
    historico.length = 0;
    mensagens.replaceChildren();
    inicio.hidden = false;
    campo.focus();
  });

  return { focar: () => campo.focus() };
}
