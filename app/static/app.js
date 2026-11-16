// Navegação: barra lateral retrátil e troca de seções pelo endereço (#/modulo/secao).
import { criar } from "./formatar.js";
import { criarChat } from "./chat.js";
import { montarSimulador, montarComparacao } from "./energia.js";
import { montarQuestoes, montarCodigo, montarRelatorio } from "./ml.js";

function paginaSimples(visao, titulo, montarCorpo) {
  const coluna = visao.appendChild(criar("div", null, "coluna pagina"));
  coluna.append(criar("h2", titulo));
  montarCorpo(coluna);
}

const ROTAS = {
  "geral/chat": {
    modulo: "Dúvidas gerais", secao: "Chat de cidadania",
    montar: (v) => criarChat(v, {
      modulo: "geral",
      titulo: "Chat de cidadania",
      saudacao: "Como posso ajudar hoje?",
      descricao: "Tire dúvidas sobre serviços públicos, documentos, direitos e contas. Eu procuro em fontes oficiais e mostro de onde veio a informação.",
      sugestoes: [
        "Quais documentos preciso para tirar a carteira de identidade?",
        "Como pedir a segunda via da certidão de nascimento?",
        "O que é o CadÚnico e quem pode se inscrever?",
      ],
    }),
  },
  "logica/inicio": {
    modulo: "Decisão lógica", secao: "Em construção",
    montar: (v) => paginaSimples(v, "Decisão lógica", (c) => {
      c.append(criar("p", "Contribuição da disciplina Computer Science.", "subtitulo"));
      const cartao = c.appendChild(criar("div", null, "cartao"));
      cartao.append(criar("span", "Em construção", "etiqueta"));
      cartao.append(criar("p", "Aqui você vai responder a algumas perguntas de sim ou não e receber a orientação correspondente. O módulo entra quando o grupo concluir, sem uso de IA, a tabela-verdade, o mapa de Karnaugh e o circuito lógico."));
    }),
  },
  "ml/questoes": { modulo: "Dados e estatística", secao: "Questões respondidas", montar: montarQuestoes },
  "ml/codigo": { modulo: "Dados e estatística", secao: "Código", montar: montarCodigo },
  "ml/relatorio": { modulo: "Dados e estatística", secao: "Relatório", montar: montarRelatorio },
  "ml/chat": {
    modulo: "Dados e estatística", secao: "Chat de dúvidas",
    montar: (v) => criarChat(v, {
      modulo: "ml",
      titulo: "Chat de dúvidas sobre a análise",
      saudacao: "Dúvidas sobre a análise?",
      descricao: "Pergunte sobre as questões respondidas e o relatório de Modelagem Linear. Eu explico os resultados e os conceitos usados, sem inventar números.",
      sugestoes: [
        "O que significa o R² encontrado na regressão?",
        "Como interpretar a matriz de confusão?",
        "Qual a diferença entre correlação e causalidade nesta análise?",
      ],
    }),
  },
  "energia/simulador": { modulo: "Energia", secao: "Simulador solar", montar: montarSimulador },
  "energia/comparar": { modulo: "Energia", secao: "Comparar alternativas", montar: montarComparacao },
  "energia/chat": {
    modulo: "Energia", secao: "Chat de energia",
    montar: (v) => criarChat(v, {
      modulo: "energia",
      titulo: "Chat de energia",
      saudacao: "Vamos falar da sua conta de luz?",
      descricao: "Respondo só sobre energia: consumo, economia, energia solar e eficiência. Se você me passar os dados da sua conta, eu faço as contas e mostro as fontes e os limites da estimativa.",
      sugestoes: [
        "Vale a pena colocar placas solares na minha casa?",
        "Quanto eu economizo trocando minhas lâmpadas por LED?",
        "O que é o custo de disponibilidade na conta de luz?",
      ],
    }),
  },
  "sobre/inicio": {
    modulo: "Sobre e privacidade", secao: "",
    montar: (v) => paginaSimples(v, "Sobre e privacidade", (c) => {
      c.append(criar("p", "Protótipo acadêmico da Global Solution GS26_2 (Ciência da Computação, turma 1CC).", "subtitulo"));
      const itens = [
        ["O que é", "O Citizen Assist AI é um assistente de inteligência artificial que ajuda pessoas a se informarem sobre cidadania, energia e análise de dados. Ele usa o modelo Claude, da Anthropic."],
        ["O que ele não é", "Não é um canal oficial do governo, não representa nenhum órgão público e não confirma a concessão de serviços, benefícios ou direitos. Também não substitui profissionais das áreas jurídica, de saúde, financeira ou de engenharia."],
        ["Ele pode errar", "Respostas de inteligência artificial podem conter erros ou estar desatualizadas. Confira as informações importantes na fonte oficial indicada. As simulações de energia são estimativas, não garantias."],
        ["Privacidade", "Não envie CPF, senhas, dados de cartão nem outras informações sensíveis. As mensagens do chat são enviadas ao serviço da Anthropic para gerar a resposta. Este site não tem login, não guarda as conversas e não registra o conteúdo das mensagens: a conversa some quando você fecha ou recarrega a página."],
        ["Emergências", "Em caso de risco à vida, ligue 190 (Polícia Militar), 192 (SAMU) ou 193 (Corpo de Bombeiros)."],
      ];
      for (const [titulo, texto] of itens) {
        const cartao = c.appendChild(criar("div", null, "cartao"));
        cartao.append(criar("h3", titulo), criar("p", texto));
      }
    }),
  },
};

const ROTA_PADRAO = "geral/chat";
const app = document.getElementById("app");
const conteudo = document.getElementById("conteudo");
const trilha = document.getElementById("trilha");
const visoes = {};

function rotaAtual() {
  const rota = location.hash.replace(/^#\/?/, "");
  return ROTAS[rota] ? rota : ROTA_PADRAO;
}

function navegar() {
  const rota = rotaAtual();
  const info = ROTAS[rota];
  if (!visoes[rota]) {
    const visao = criar("section", null, "visao");
    visao.hidden = true;
    conteudo.append(visao);
    visoes[rota] = { visao, api: info.montar(visao) };
  }
  for (const [nome, v] of Object.entries(visoes)) v.visao.hidden = nome !== rota;
  visoes[rota].api?.aoMostrar?.();

  // Marca o item atual na barra lateral.
  const modulo = rota.split("/")[0];
  for (const a of document.querySelectorAll(".secoes a")) {
    if (a.getAttribute("href") === "#/" + rota) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
  for (const g of document.querySelectorAll(".grupo")) g.classList.toggle("ativo", g.dataset.modulo === modulo);
  document.querySelector(".lateral-rodape .grupo-titulo").classList.toggle("ativo", modulo === "sobre");

  trilha.replaceChildren(criar("strong", info.modulo), info.secao ? " · " + info.secao : "");
  document.title = (info.secao || info.modulo) + " · Citizen Assist AI";
  fecharMenu();
}

// ---------- Barra lateral ----------
const botaoAlternar = document.getElementById("alternar-lateral");
const botaoMenu = document.getElementById("abrir-menu");
const fundoMenu = document.getElementById("fundo-menu");

function definirRecolhida(recolhida) {
  app.classList.toggle("recolhida", recolhida);
  botaoAlternar.setAttribute("aria-expanded", String(!recolhida));
  botaoAlternar.setAttribute("aria-label", recolhida ? "Expandir barra lateral" : "Recolher barra lateral");
  try { localStorage.setItem("lateral-recolhida", recolhida ? "1" : "0"); } catch { /* sem armazenamento */ }
}

function fecharMenu() {
  app.classList.remove("menu-aberto");
  fundoMenu.hidden = true;
  botaoMenu.setAttribute("aria-expanded", "false");
}

botaoAlternar.addEventListener("click", () => definirRecolhida(!app.classList.contains("recolhida")));
botaoMenu.addEventListener("click", () => {
  app.classList.add("menu-aberto");
  fundoMenu.hidden = false;
  botaoMenu.setAttribute("aria-expanded", "true");
  document.querySelector(".marca").focus();
});
fundoMenu.addEventListener("click", fecharMenu);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && app.classList.contains("menu-aberto")) {
    fecharMenu();
    botaoMenu.focus();
  }
});

let recolhidaSalva = false;
try { recolhidaSalva = localStorage.getItem("lateral-recolhida") === "1"; } catch { /* sem armazenamento */ }
definirRecolhida(recolhidaSalva);

window.addEventListener("hashchange", () => {
  navegar();
  conteudo.focus();
});
navegar();
