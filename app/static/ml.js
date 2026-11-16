// Módulo de Estatística: questões respondidas, código e relatório.
// Tudo vem dos arquivos gerados por modulos/ml/executar.py; aqui só mostramos.
import { criar, formatarTexto, pedir } from "./formatar.js";

let arquivoEscolhido = null; // arquivo de código pedido pelo atalho de uma questão

function cabecalho(visao, titulo, subtitulo, larga) {
  const coluna = visao.appendChild(criar("div", null, "coluna pagina" + (larga ? " larga" : "")));
  coluna.append(criar("h2", titulo), criar("p", subtitulo, "subtitulo"));
  return coluna;
}

function mostrarErro(destino, mensagem) {
  const caixa = destino.appendChild(criar("div", null, "aviso"));
  caixa.append(criar("p", mensagem));
}

export function montarQuestoes(visao) {
  const coluna = cabecalho(visao, "Questões respondidas",
    "Análise estatística do consumo de energia elétrica no Brasil, com dados oficiais da EPE. Disciplina Modelagem Linear para Aprendizado de Máquina.");
  const carregando = coluna.appendChild(criar("p", "Carregando a análise…", "discreto"));

  pedir("/api/ml/resultados").then((dados) => {
    carregando.remove();
    const base = coluna.appendChild(criar("div", null, "cartao"));
    base.append(criar("h3", "Base de dados"));
    formatarTexto(dados.base.descricao_md, base.appendChild(criar("div")));

    for (const q of dados.questoes) {
      const cartao = coluna.appendChild(criar("article", null, "cartao questao"));
      cartao.id = "questao-" + q.id;
      cartao.append(criar("h3", `Questão ${q.id}: ${q.titulo}`));
      cartao.append(criar("p", q.enunciado, "enunciado"));
      formatarTexto(q.resposta_md, cartao.appendChild(criar("div")), 4);
      const acoes = cartao.appendChild(criar("div", null, "acoes"));
      const verCodigo = acoes.appendChild(criar("a", "Ver o código desta questão", "botao claro pequeno"));
      verCodigo.href = "#/ml/codigo";
      verCodigo.addEventListener("click", () => { arquivoEscolhido = q.arquivo; });
    }
  }).catch((falha) => {
    carregando.remove();
    mostrarErro(coluna, falha.message);
  });
}

export function montarCodigo(visao) {
  const coluna = cabecalho(visao, "Código",
    "Os arquivos Python da análise, exatamente como estão no repositório.", true);
  const lista = coluna.appendChild(criar("div", null, "arquivos"));
  lista.setAttribute("role", "group");
  lista.setAttribute("aria-label", "Arquivos");
  const titulo = coluna.appendChild(criar("p", "", "discreto"));
  const codigo = coluna.appendChild(criar("pre", null, "codigo"));
  codigo.tabIndex = 0;
  codigo.setAttribute("aria-label", "Código do arquivo escolhido");
  let arquivos = [];
  const botoes = {};

  function escolher(nome) {
    const arquivo = arquivos.find((a) => a.nome === nome) || arquivos[0];
    if (!arquivo) return;
    for (const [n, b] of Object.entries(botoes)) b.setAttribute("aria-pressed", String(n === arquivo.nome));
    titulo.textContent = `modulos/ml/${arquivo.nome} · ${arquivo.conteudo.split("\n").length} linhas`;
    codigo.textContent = arquivo.conteudo;
    codigo.scrollTop = 0;
  }

  pedir("/api/ml/codigo").then((dados) => {
    arquivos = dados;
    if (!arquivos.length) {
      mostrarErro(coluna, "Nenhum arquivo de código encontrado.");
      return;
    }
    for (const a of arquivos) {
      const b = lista.appendChild(criar("button", a.nome));
      b.type = "button";
      b.addEventListener("click", () => escolher(a.nome));
      botoes[a.nome] = b;
    }
    escolher(arquivoEscolhido);
  }).catch((falha) => mostrarErro(coluna, falha.message));

  return {
    aoMostrar() {
      if (arquivoEscolhido && arquivos.length) escolher(arquivoEscolhido);
      arquivoEscolhido = null;
    },
  };
}

export function montarRelatorio(visao) {
  const coluna = visao.appendChild(criar("div", null, "coluna pagina"));
  const acoes = coluna.appendChild(criar("div", null, "acoes nao-imprimir"));
  const corpo = coluna.appendChild(criar("article"));
  corpo.append(criar("p", "Carregando o relatório…", "discreto"));

  pedir("/api/ml/relatorio").then((dados) => {
    formatarTexto(dados.markdown, corpo, 2);
    if (dados.pdf) {
      const baixar = acoes.appendChild(criar("a", "Baixar o relatório em PDF", "botao"));
      baixar.href = "/ml/relatorio.pdf";
      baixar.setAttribute("download", "");
    }
    const imprimir = acoes.appendChild(criar("button", "Imprimir ou salvar como PDF", "botao claro"));
    imprimir.type = "button";
    imprimir.addEventListener("click", () => window.print());
  }).catch((falha) => {
    corpo.replaceChildren();
    mostrarErro(corpo, falha.message);
  });
}
