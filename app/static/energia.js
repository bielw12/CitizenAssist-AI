// Módulo de Energia: simulador solar 2D e comparação de alternativas.
// Todos os números vêm do servidor (modulos/energia/calculo.py); aqui só mostramos.
import { criar, criarLink, formatoNumero, formatoReais, icone, pedir, svg } from "./formatar.js";

const reais = (v) => formatoReais.format(v);
const numero = (v, casas = 0) => formatoNumero(casas).format(v);
const plural = (n, um, varios) => `${numero(n)} ${n === 1 ? um : varios}`;

// Dados da casa informados no simulador, reaproveitados na comparação.
let casa = null;
let opcoes = null;

async function carregarOpcoes() {
  if (!opcoes) opcoes = await pedir("/api/energia/opcoes");
  return opcoes;
}

function campo(rotulo, atributos, ajuda) {
  const div = criar("div", null, "campo");
  const label = div.appendChild(criar("label", rotulo));
  const entrada = div.appendChild(criar(atributos.opcoes ? "select" : "input"));
  for (const [nome, valor] of Object.entries(atributos)) {
    if (nome === "opcoes") {
      for (const [v, texto] of valor) {
        const o = entrada.appendChild(criar("option", texto));
        o.value = v;
      }
    } else entrada.setAttribute(nome, valor);
  }
  label.htmlFor = entrada.id;
  if (ajuda) {
    const dica = div.appendChild(criar("span", ajuda, "ajuda"));
    dica.id = entrada.id + "-ajuda";
    entrada.setAttribute("aria-describedby", dica.id);
  }
  return { div, entrada };
}

const valorNumerico = (entrada) => (entrada.value.trim() === "" ? null : Number(entrada.value.replace(",", ".")));

function textoPayback(anos, vidaUtil) {
  if (anos === null) return "Não se paga com esses valores";
  const texto = `${numero(anos, 1)} anos`;
  return anos > vidaUtil ? `${texto} (mais que a vida útil de ${vidaUtil} anos)` : texto;
}

function listaFontes(destino, dados) {
  const cartao = destino.appendChild(criar("div", null, "cartao"));
  cartao.append(criar("h3", "De onde vêm os números"));
  const lista = cartao.appendChild(criar("ul", null, "fontes-lista"));
  for (const f of dados.fontes) {
    const li = lista.appendChild(criar("li"));
    li.append(criar("strong", f.dado + ": "), f.valor + ". ");
    if (f.url) li.append(criarLink(f.fonte, f.url));
    else li.append(f.fonte);
    li.append(".");
  }
  cartao.append(criar("p", `Fontes consultadas em ${dados.data_consulta}.`, "discreto"));
  cartao.append(criar("h3", "Limites desta estimativa"));
  const limites = cartao.appendChild(criar("ul", null, "fontes-lista"));
  for (const texto of dados.limitacoes) limites.append(criar("li", texto));
}

// ---------- Desenho da casa ----------

const TELHADO = { topoEsq: 150, topoDir: 490, baseEsq: 80, baseDir: 560, yTopo: 70, yBase: 200 };
const COLUNAS = 8;

function pontoNoTelhado(u, v) {
  const esq = TELHADO.topoEsq + (TELHADO.baseEsq - TELHADO.topoEsq) * v;
  const dir = TELHADO.topoDir + (TELHADO.baseDir - TELHADO.topoDir) * v;
  return [esq + (dir - esq) * u, TELHADO.yTopo + (TELHADO.yBase - TELHADO.yTopo) * v];
}

function desenharCena(maxPlacas) {
  const cena = svg("svg", { viewBox: "0 0 640 380", class: "cena", role: "img" });
  const titulo = cena.appendChild(svg("title"));
  cena.append(svg("rect", { class: "ceu", width: 640, height: 380 }));
  for (let i = 0; i < 8; i++) {
    const a = (i * Math.PI) / 4;
    cena.append(svg("line", {
      class: "raio",
      x1: 585 + Math.cos(a) * 38, y1: 58 + Math.sin(a) * 38,
      x2: 585 + Math.cos(a) * 50, y2: 58 + Math.sin(a) * 50,
    }));
  }
  cena.append(svg("circle", { class: "sol", cx: 585, cy: 58, r: 28 }));
  cena.append(svg("rect", { class: "chao", y: 330, width: 640, height: 50 }));
  cena.append(svg("rect", { class: "parede", x: 110, y: 200, width: 420, height: 130 }));
  cena.append(svg("rect", { class: "porta", x: 292, y: 250, width: 56, height: 80, rx: 3 }));
  cena.append(svg("rect", { class: "janela", x: 160, y: 235, width: 72, height: 54, rx: 3 }));
  cena.append(svg("rect", { class: "janela", x: 408, y: 235, width: 72, height: 54, rx: 3 }));
  const t = TELHADO;
  cena.append(svg("polygon", {
    class: "telhado",
    points: `${t.topoEsq},${t.yTopo} ${t.topoDir},${t.yTopo} ${t.baseDir},${t.yBase} ${t.baseEsq},${t.yBase}`,
  }));

  const linhas = Math.ceil(maxPlacas / COLUNAS);
  const placas = [];
  for (let i = 0; i < maxPlacas; i++) {
    const coluna = i % COLUNAS;
    const linha = Math.floor(i / COLUNAS);
    const u0 = 0.05 + (coluna / COLUNAS) * 0.9 + 0.008;
    const u1 = 0.05 + ((coluna + 1) / COLUNAS) * 0.9 - 0.008;
    const v0 = 0.1 + (linha / linhas) * 0.8 + 0.02;
    const v1 = 0.1 + ((linha + 1) / linhas) * 0.8 - 0.02;
    const pontos = [pontoNoTelhado(u0, v0), pontoNoTelhado(u1, v0), pontoNoTelhado(u1, v1), pontoNoTelhado(u0, v1)]
      .map((p) => p.map((n) => n.toFixed(1)).join(",")).join(" ");
    cena.append(svg("polygon", { class: "vaga", points: pontos }));
    placas.push(cena.appendChild(svg("polygon", { class: "placa", points: pontos })));
  }
  return { cena, placas, titulo };
}

// ---------- Simulador ----------

export function montarSimulador(visao) {
  const coluna = visao.appendChild(criar("div", null, "coluna larga pagina"));
  coluna.append(criar("h2", "Simulador solar"));
  coluna.append(criar("p", "Informe os dados da sua conta de luz e veja, placa por placa, quanto a energia solar pode economizar na sua casa.", "subtitulo"));

  const cartaoForm = coluna.appendChild(criar("form", null, "cartao"));
  cartaoForm.noValidate = true;
  cartaoForm.append(criar("h3", "Sua conta de luz"));
  const campos = cartaoForm.appendChild(criar("div", null, "campos"));
  const consumo = campo("Consumo no mês (kWh)", { id: "sim-consumo", type: "text", inputmode: "decimal", required: "", autocomplete: "off" }, "Aparece na conta como consumo em kWh.");
  const valor = campo("Valor da conta (R$)", { id: "sim-valor", type: "text", inputmode: "decimal", required: "", autocomplete: "off" }, "Total pago no mês.");
  const estado = campo("Estado", { id: "sim-uf", opcoes: [["", "Carregando…"]] }, "O cálculo usa o sol da capital.");
  const ligacao = campo("Tipo de ligação", { id: "sim-ligacao", opcoes: [["", "Carregando…"]] }, "Aparece na conta: monofásica, bifásica ou trifásica.");
  campos.append(consumo.div, valor.div, estado.div, ligacao.div);

  const avancado = cartaoForm.appendChild(criar("details", null, "avancado"));
  avancado.append(criar("summary", "Tenho um orçamento ou quero mudar a potência da placa"));
  const camposAv = avancado.appendChild(criar("div", null, "campos"));
  const potencia = campo("Potência de cada placa (W)", { id: "sim-potencia", type: "text", inputmode: "decimal", autocomplete: "off" }, "Premissa do grupo: 550 W. Troque pelo valor do seu orçamento.");
  const orcamento = campo("Valor do orçamento (R$)", { id: "sim-orcamento", type: "text", inputmode: "decimal", autocomplete: "off" }, "Opcional. Substitui o custo de referência de 2021.");
  const placasOrc = campo("Placas no orçamento", { id: "sim-placas-orc", type: "text", inputmode: "numeric", autocomplete: "off" }, "Quantas placas o orçamento inclui.");
  camposAv.append(potencia.div, orcamento.div, placasOrc.div);

  const acoes = cartaoForm.appendChild(criar("div", null, "acoes"));
  const botaoSimular = acoes.appendChild(criar("button", "Simular", "botao"));
  botaoSimular.type = "submit";
  const erroEl = coluna.appendChild(criar("p", null, "mensagem-erro"));
  erroEl.setAttribute("role", "alert");
  erroEl.hidden = true;

  // Resultado
  const resultado = coluna.appendChild(criar("div", null, "simulador"));
  resultado.hidden = true;
  const cartaoCena = resultado.appendChild(criar("div", null, "cartao"));
  const cartaoNumeros = resultado.appendChild(criar("div", null, "cartao"));
  const rodapeFontes = coluna.appendChild(criar("div"));

  let simulacao = null;
  let placasEl = [];
  let tituloCena = null;
  let atual = 0;
  let temporizador = null;

  const controles = criar("div", null, "controles");
  const botaoTocar = controles.appendChild(criar("button", null, "botao claro pequeno"));
  botaoTocar.type = "button";
  const rotuloFaixa = controles.appendChild(criar("label", "Placas", "so-leitor"));
  rotuloFaixa.htmlFor = "sim-faixa";
  const faixa = controles.appendChild(criar("input"));
  faixa.type = "range";
  faixa.id = "sim-faixa";
  faixa.min = 0;
  faixa.step = 1;
  const contagem = controles.appendChild(criar("strong"));
  const botaoRecomendado = controles.appendChild(criar("button", "Usar o recomendado", "botao claro pequeno"));
  botaoRecomendado.type = "button";

  const indicadores = criar("div", null, "indicadores");
  const ind = {};
  for (const [chave, nome, principal] of [
    ["economia", "Economia por mês", true],
    ["placas", "Placas no telhado"],
    ["geracao", "Geração por mês"],
    ["conta", "Nova conta estimada"],
    ["payback", "Retorno do investimento"],
    ["investimento", "Investimento estimado"],
    ["co2", "CO2 evitado por ano"],
  ]) {
    const caixa = indicadores.appendChild(criar("div", null, "indicador" + (principal ? " principal" : "")));
    caixa.append(criar("span", nome, "nome"));
    ind[chave] = caixa.appendChild(criar("span", "", "valor"));
  }
  const barras = criar("div", null, "barras");
  const barra = {};
  for (const [chave, nome] of [["antes", "Conta hoje"], ["depois", "Conta com as placas"]]) {
    const b = barras.appendChild(criar("div", null, "barra " + chave));
    const legenda = b.appendChild(criar("div", null, "legenda"));
    legenda.append(criar("span", nome));
    const valorEl = legenda.appendChild(criar("strong"));
    const preenchimento = b.appendChild(criar("div", null, "trilho")).appendChild(criar("div", null, "preenchimento"));
    barra[chave] = { valorEl, preenchimento };
  }
  const resumo = criar("p", "", "discreto");
  const anuncio = criar("p", "", "so-leitor");
  anuncio.setAttribute("role", "status");

  function rotuloTocar(tocando) {
    botaoTocar.replaceChildren(
      icone(tocando ? ["M9 6v12", "M15 6v12"] : ["M8 5.5v13l10-6.5z"]),
      tocando ? "Pausar" : "Ver as placas entrando",
    );
  }

  function mostrar(n, anunciar) {
    atual = n;
    const c = simulacao.cenarios[n];
    placasEl.forEach((p, i) => p.classList.toggle("ativa", i < n));
    faixa.value = n;
    contagem.textContent = plural(n, "placa", "placas");
    ind.economia.textContent = reais(c.economia_mes);
    ind.placas.textContent = `${numero(n)} (${numero(c.potencia_kwp, 2)} kWp)`;
    ind.geracao.textContent = `${numero(c.geracao_kwh_mes)} kWh`;
    ind.conta.textContent = reais(c.nova_conta);
    ind.payback.textContent = n ? textoPayback(c.payback_anos, simulacao.vida_util_anos) : "—";
    ind.investimento.textContent = n ? reais(c.investimento) : "—";
    ind.co2.textContent = `${numero(c.co2_evitado_kg_ano)} kg`;
    barra.antes.valorEl.textContent = reais(simulacao.valor_conta);
    barra.antes.preenchimento.style.width = "100%";
    barra.depois.valorEl.textContent = reais(c.nova_conta);
    barra.depois.preenchimento.style.width = Math.max((c.nova_conta / simulacao.valor_conta) * 100, 0) + "%";
    const frase = `Com ${plural(n, "placa", "placas")}: economia de ${reais(c.economia_mes)} por mês e conta estimada de ${reais(c.nova_conta)}.`;
    tituloCena.textContent = `Casa fictícia com ${plural(n, "placa solar", "placas solares")} no telhado.`;
    if (anunciar) anuncio.textContent = frase;
    if (casa) casa.placas = n;
  }

  function parar() {
    clearInterval(temporizador);
    temporizador = null;
    rotuloTocar(false);
  }

  function tocar() {
    const alvo = simulacao.placas_recomendadas;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches || alvo === 0) {
      mostrar(alvo, true);
      return;
    }
    mostrar(0, false);
    rotuloTocar(true);
    temporizador = setInterval(() => {
      if (atual >= alvo) {
        parar();
        mostrar(alvo, true);
      } else mostrar(atual + 1, false);
    }, 450);
  }

  botaoTocar.addEventListener("click", () => (temporizador ? parar() : tocar()));
  faixa.addEventListener("input", () => {
    parar();
    mostrar(Number(faixa.value), true);
  });
  botaoRecomendado.addEventListener("click", () => {
    parar();
    mostrar(simulacao.placas_recomendadas, true);
  });

  function exibir(s) {
    simulacao = s;
    parar();
    const desenho = desenharCena(s.max_placas);
    placasEl = desenho.placas;
    tituloCena = desenho.titulo;
    faixa.max = s.max_placas;
    cartaoCena.replaceChildren(desenho.cena, controles, anuncio,
      criar("p", "Desenho ilustrativo: quantas placas cabem no seu telhado depende de avaliação técnica.", "discreto"));

    const textoResumo = [];
    textoResumo.push(`Em ${s.capital}, cada placa de ${numero(s.potencia_placa_w)} W gera cerca de ${numero(s.geracao_por_placa_kwh_mes, 1)} kWh por mês.`);
    textoResumo.push(`Sua tarifa média é ${reais(s.tarifa)} por kWh.`);
    if (s.placas_necessarias === 0) {
      textoResumo.push(`Seu consumo já está no mínimo cobrado na conta (${numero(s.disponibilidade_kwh)} kWh), então as placas não reduziriam o valor pago.`);
    } else {
      textoResumo.push(`A conta nunca fica abaixo do mínimo de ${numero(s.disponibilidade_kwh)} kWh, por isso o recomendado são ${plural(s.placas_recomendadas, "placa", "placas")}: mais que isso não aumenta a economia.`);
      if (s.placas_necessarias > s.max_placas) {
        textoResumo.push(`Para cobrir todo o consumo seriam necessárias ${numero(s.placas_necessarias)} placas; o desenho mostra até ${numero(s.max_placas)}.`);
      }
    }
    textoResumo.push(s.custo_e_referencia
      ? `O investimento usa o custo de referência da EPE, de ${reais(s.custo_r_por_wp)} por Wp (valor de 2021).`
      : `O investimento usa o seu orçamento, que equivale a ${reais(s.custo_r_por_wp)} por Wp.`);
    resumo.textContent = textoResumo.join(" ");

    const ligacaoComparar = criar("a", "Comparar com LED e chuveiro", "botao claro pequeno");
    ligacaoComparar.href = "#/energia/comparar";
    cartaoNumeros.replaceChildren(criar("h3", "Resultado estimado"), indicadores, barras, resumo, ligacaoComparar);
    resultado.hidden = false;
    tocar();
    resultado.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  cartaoForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    erroEl.hidden = true;
    const corpo = {
      consumo_kwh: valorNumerico(consumo.entrada),
      valor_conta: valorNumerico(valor.entrada),
      uf: estado.entrada.value,
      ligacao: ligacao.entrada.value,
    };
    const w = valorNumerico(potencia.entrada);
    const orc = valorNumerico(orcamento.entrada);
    const nOrc = valorNumerico(placasOrc.entrada);
    try {
      if (!corpo.consumo_kwh || !corpo.valor_conta || !corpo.uf || !corpo.ligacao) {
        throw new Error("Preencha o consumo, o valor da conta, o estado e o tipo de ligação.");
      }
      if (w) corpo.potencia_placa_w = w;
      if (orc || nOrc) {
        if (!orc || !nOrc) throw new Error("Para usar um orçamento, informe o valor e o número de placas dele.");
        corpo.custo_r_por_wp = orc / (nOrc * (w || opcoes.potencia_placa_w));
      }
      botaoSimular.disabled = true;
      const s = await pedir("/api/energia/simular", corpo);
      casa = { ...corpo, placas: s.placas_recomendadas };
      exibir(s);
    } catch (falha) {
      erroEl.textContent = falha.message;
      erroEl.hidden = false;
    } finally {
      botaoSimular.disabled = false;
    }
  });

  carregarOpcoes().then((dados) => {
    estado.entrada.replaceChildren();
    for (const [v, texto] of [["", "Escolha o estado"], ...dados.estados.map((e) => [e.uf, `${e.estado} (${e.uf})`])]) {
      estado.entrada.appendChild(criar("option", texto)).value = v;
    }
    ligacao.entrada.replaceChildren();
    for (const [v, texto] of [["", "Escolha o tipo"], ...dados.ligacoes.map((l) => [l.id, l.nome])]) {
      ligacao.entrada.appendChild(criar("option", texto)).value = v;
    }
    potencia.entrada.placeholder = String(dados.potencia_placa_w);
    listaFontes(rodapeFontes, dados);
  }).catch((falha) => {
    erroEl.textContent = falha.message;
    erroEl.hidden = false;
  });
}

// ---------- Comparação de alternativas ----------

const QUALITATIVO = {
  solar: {
    viabilidade: "Exige telhado com espaço e sem sombra, avaliação de um profissional habilitado e pedido de conexão à distribuidora.",
    limites: "A conta não zera: fica o mínimo da ligação. Parte da energia injetada na rede paga pelo uso da rede (Lei 14.300/2022), o que não entrou nesta conta.",
  },
  led: {
    viabilidade: "Simples: basta trocar as lâmpadas. Não depende de obra nem de autorização.",
    limites: "A economia depende das horas de uso informadas. Lâmpadas pouco usadas quase não mudam a conta.",
  },
  chuveiro: {
    viabilidade: "Não tem custo, mas depende de todos na casa manterem o novo hábito.",
    limites: "A potência real varia com a posição do chuveiro (verão ou inverno).",
  },
  eficiencia: {
    viabilidade: "Pode começar hoje, com pouco ou nenhum investimento.",
    limites: "Há um teto: só se economiza a energia que hoje é desperdiçada.",
  },
  juntas: {
    viabilidade: "Reduzir o consumo antes diminui o tamanho e o custo do sistema solar necessário.",
    limites: "Somam-se os limites das duas alternativas.",
  },
};

function textoRetornoMeses(r) {
  if (r.payback_meses === 0) return "Imediato (sem investimento)";
  if (r.payback_meses === null) return r.investimento === null ? "Informe o preço para calcular" : "Não se paga com esses valores";
  return r.payback_meses < 24 ? `${numero(r.payback_meses, 1)} meses` : `${numero(r.payback_meses / 12, 1)} anos`;
}

export function montarComparacao(visao) {
  const coluna = visao.appendChild(criar("div", null, "coluna larga pagina"));
  coluna.append(criar("h2", "Comparar alternativas"));
  coluna.append(criar("p", "Compare a energia solar com medidas de economia, para a mesma casa e para o mesmo período de 12 meses.", "subtitulo"));

  const semCasa = coluna.appendChild(criar("div", null, "aviso"));
  const pSem = semCasa.appendChild(criar("p", "Primeiro informe os dados da sua conta de luz no "));
  const atalho = pSem.appendChild(criar("a", "Simulador solar"));
  atalho.href = "#/energia/simulador";
  pSem.append(". A comparação usa a mesma casa.");

  const conteudo = coluna.appendChild(criar("div"));
  const resumoCasa = conteudo.appendChild(criar("p", "", "discreto"));
  const formulario = conteudo.appendChild(criar("form", null, "cartao"));
  formulario.noValidate = true;
  const entrada = (id) => ({ id, type: "text", inputmode: "decimal", autocomplete: "off" });

  formulario.append(criar("h3", "Troca por lâmpadas LED"));
  const camposLed = formulario.appendChild(criar("div", null, "campos"));
  const led = {
    quantidade: campo("Quantas lâmpadas vai trocar", entrada("cmp-led-qtd")),
    potencia_atual_w: campo("Potência de cada lâmpada atual (W)", entrada("cmp-led-atual"), "Vem escrita na lâmpada."),
    potencia_led_w: campo("Potência de cada LED nova (W)", entrada("cmp-led-nova"), "Vem escrita na embalagem."),
    horas_dia: campo("Horas de uso por dia", entrada("cmp-led-horas")),
    preco_unitario: campo("Preço de cada LED (R$)", entrada("cmp-led-preco"), "Opcional. Usado para o retorno."),
  };
  camposLed.append(...Object.values(led).map((c) => c.div));

  const tituloChuveiro = formulario.appendChild(criar("h3", "Banho mais curto no chuveiro elétrico"));
  tituloChuveiro.style.marginTop = "1.25rem";
  const camposChuveiro = formulario.appendChild(criar("div", null, "campos"));
  const chuveiro = {
    potencia_w: campo("Potência do chuveiro (W)", entrada("cmp-chu-pot"), "Vem escrita no aparelho."),
    banhos_dia: campo("Banhos por dia na casa", entrada("cmp-chu-banhos")),
    minutos_atual: campo("Minutos por banho hoje", entrada("cmp-chu-atual")),
    minutos_novo: campo("Minutos por banho depois", entrada("cmp-chu-novo")),
  };
  camposChuveiro.append(...Object.values(chuveiro).map((c) => c.div));
  formulario.append(criar("p", "Preencha um dos grupos ou os dois.", "discreto"));

  const acoes = formulario.appendChild(criar("div", null, "acoes"));
  const botao = acoes.appendChild(criar("button", "Comparar", "botao"));
  botao.type = "submit";
  const erroEl = conteudo.appendChild(criar("p", null, "mensagem-erro"));
  erroEl.setAttribute("role", "alert");
  erroEl.hidden = true;
  const resultado = conteudo.appendChild(criar("div"));
  resultado.setAttribute("aria-live", "polite");

  function lerGrupo(grupo, opcionais = []) {
    const valores = {};
    let preenchidos = 0;
    for (const [nome, c] of Object.entries(grupo)) {
      const v = valorNumerico(c.entrada);
      if (v !== null) {
        valores[nome] = v;
        if (!opcionais.includes(nome)) preenchidos++;
      }
    }
    const obrigatorios = Object.keys(grupo).length - opcionais.length;
    if (preenchidos === 0) return null;
    if (preenchidos < obrigatorios || Object.values(valores).some(Number.isNaN)) {
      throw new Error("Preencha com números todos os campos do grupo que você quer comparar.");
    }
    return valores;
  }

  function exibir(c) {
    const colunas = [["Energia solar", `${plural(c.solar.placas, "placa", "placas")}`, "solar"]];
    if (c.led) colunas.push(["Lâmpadas LED", "", "led"]);
    if (c.chuveiro) colunas.push(["Chuveiro", "banho mais curto", "chuveiro"]);
    if (c.led && c.chuveiro) colunas.push(["Eficiência", "LED + chuveiro", "eficiencia"]);
    colunas.push(["As duas juntas", `eficiência + ${plural(c.juntas.placas, "placa", "placas")}`, "juntas"]);

    const dadosDe = { solar: c.solar, led: c.led, chuveiro: c.chuveiro, eficiencia: c.eficiencia, juntas: c.juntas };
    const investimento = (chave) => {
      const v = dadosDe[chave].investimento;
      return v === null || v === undefined ? "Não informado" : reais(v);
    };
    const retorno = (chave) => {
      if (chave === "solar") return c.solar.placas ? textoPayback(c.solar.payback_anos, 25) : "—";
      if (chave === "juntas") return "Veja cada alternativa";
      return textoRetornoMeses(dadosDe[chave]);
    };
    const linhas = [
      ["Investimento", investimento],
      ["Economia por mês", (k) => reais(dadosDe[k].economia_mes)],
      ["Economia em 12 meses", (k) => reais(dadosDe[k].economia_ano)],
      ["Retorno do investimento", retorno],
      ["CO2 evitado em 12 meses", (k) => `${numero(dadosDe[k].co2_evitado_kg_ano, 1)} kg`],
      ["Viabilidade", (k) => QUALITATIVO[k].viabilidade],
      ["Limites", (k) => QUALITATIVO[k].limites],
    ];

    const tabela = criar("table", null, "tabela");
    const cabecalho = tabela.createTHead().insertRow();
    cabecalho.append(criar("th", ""));
    for (const [nome, detalhe] of colunas) {
      const th = cabecalho.appendChild(criar("th", nome));
      th.scope = "col";
      if (detalhe) th.append(criar("br"), criar("span", detalhe, "discreto"));
    }
    const corpo = tabela.createTBody();
    for (const [nome, valorDe] of linhas) {
      const tr = corpo.insertRow();
      const th = tr.appendChild(criar("th", nome));
      th.scope = "row";
      for (const [, , chave] of colunas) tr.insertCell().textContent = valorDe(chave);
    }

    // Frases de resumo calculadas a partir dos números acima.
    const frases = [];
    const eficiencia = c.eficiencia;
    frases.push(c.solar.economia_mes > eficiencia.economia_mes
      ? `A energia solar dá a maior economia mensal (${reais(c.solar.economia_mes)} contra ${reais(eficiencia.economia_mes)} das medidas de eficiência), mas pede o maior investimento (${reais(c.solar.investimento)}).`
      : `As medidas de eficiência economizam ${reais(eficiencia.economia_mes)} por mês, mais que as placas simuladas (${reais(c.solar.economia_mes)}), e com investimento muito menor.`);
    if (c.juntas.placas < c.solar.placas) {
      frases.push(`Fazendo antes as medidas de eficiência, o consumo cai para ${numero(c.juntas.consumo_reduzido_kwh)} kWh e ${plural(c.juntas.placas, "placa passa", "placas passam")} a bastar, em vez de ${numero(c.solar.placas)}. O investimento em solar cai para ${reais(c.juntas.investimento_solar)}.`);
    }
    frases.push("São estimativas para ajudar na decisão, não garantias. A instalação de placas exige avaliação de um profissional habilitado.");

    const cartao = criar("div", null, "cartao");
    cartao.append(criar("h3", "Resultado da comparação"));
    cartao.appendChild(criar("div", null, "rolagem-x")).append(tabela);
    for (const f of frases) cartao.append(criar("p", f, "resumo-comparacao"));
    resultado.replaceChildren(cartao);
    cartao.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  formulario.addEventListener("submit", async (e) => {
    e.preventDefault();
    erroEl.hidden = true;
    try {
      const corpo = { ...casa, led: lerGrupo(led, ["preco_unitario"]), chuveiro: lerGrupo(chuveiro) };
      if (!corpo.led && !corpo.chuveiro) throw new Error("Preencha os dados das lâmpadas, do chuveiro ou dos dois.");
      botao.disabled = true;
      exibir(await pedir("/api/energia/comparar", corpo));
    } catch (falha) {
      erroEl.textContent = falha.message;
      erroEl.hidden = false;
    } finally {
      botao.disabled = false;
    }
  });

  let fontesMontadas = false;
  function aoMostrar() {
    semCasa.hidden = Boolean(casa);
    conteudo.hidden = !casa;
    if (casa) {
      resumoCasa.textContent = `Casa do simulador: ${numero(casa.consumo_kwh)} kWh por mês, conta de ${reais(casa.valor_conta)}, estado ${casa.uf}, ${plural(casa.placas, "placa", "placas")} na simulação.`;
    }
    if (!fontesMontadas) {
      fontesMontadas = true;
      carregarOpcoes().then((dados) => listaFontes(coluna, dados)).catch(() => {});
    }
  }
  aoMostrar();
  return { aoMostrar };
}
