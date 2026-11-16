"""Servidor do Citizen Assist AI: entrega a tela, o chat e os dados dos módulos."""

import json
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints

from modulos.energia import calculo
from modulos.energia import dados as energia
from modulos.logica import cnh
from modulos.logica import relatorio as relatorio_logica

from . import config
from .chat import responder

RAIZ = Path(__file__).parent.parent
PASTA_ESTATICA = Path(__file__).parent / "static"
PASTA_ML = RAIZ / "modulos" / "ml"
SAIDAS_ML = PASTA_ML / "saidas"
RELATORIO_PDF = RAIZ / "docs" / "modelagem_linear" / "relatorio.pdf"
RELATORIO_LOGICA_PDF = RAIZ / "docs" / "computer_science" / "relatorio.pdf"

app = FastAPI(title="Citizen Assist AI", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=PASTA_ESTATICA), name="static")
if SAIDAS_ML.is_dir():
    app.mount("/ml/graficos", StaticFiles(directory=SAIDAS_ML), name="graficos")

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: Texto


class PedidoChat(BaseModel):
    modulo: Literal["geral", "energia", "ml"]
    historico: list[Mensagem] = Field(default_factory=list, max_length=200)
    mensagem: Annotated[Texto, StringConstraints(max_length=config.MAX_CARACTERES_MENSAGEM)]


class PedidoSimulacao(BaseModel):
    consumo_kwh: float = Field(gt=0, le=100_000)
    valor_conta: float = Field(gt=0, le=1_000_000)
    uf: str = Field(max_length=2)
    ligacao: str = Field(max_length=20)
    potencia_placa_w: float | None = Field(None, ge=50, le=1000)
    custo_r_por_wp: float | None = Field(None, gt=0, le=100)


class Lampadas(BaseModel):
    quantidade: int = Field(ge=1, le=1000)
    potencia_atual_w: float = Field(gt=0, le=1000)
    potencia_led_w: float = Field(gt=0, le=1000)
    horas_dia: float = Field(ge=0, le=24)
    preco_unitario: float | None = Field(None, gt=0, le=10_000)


class Chuveiro(BaseModel):
    potencia_w: float = Field(gt=0, le=20_000)
    banhos_dia: float = Field(gt=0, le=50)
    minutos_atual: float = Field(gt=0, le=120)
    minutos_novo: float = Field(ge=0, le=120)


class PedidoComparacao(PedidoSimulacao):
    placas: int | None = Field(None, ge=0, le=energia.MAX_PLACAS)
    led: Lampadas | None = None
    chuveiro: Chuveiro | None = None


def erro(mensagem: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": mensagem})


# Limite simples de requisições por endereço IP, guardado só na memória do servidor.
_acessos: dict[str, deque[float]] = defaultdict(deque)


def ip_do_visitante(request: Request) -> str:
    """Endereço do visitante. Atrás de um proxy (como a Vercel), o IP real vem em X-Forwarded-For."""
    encaminhado = request.headers.get("x-forwarded-for", "")
    primeiro = encaminhado.split(",")[0].strip()
    if primeiro:
        return primeiro
    return request.client.host if request.client else "desconhecido"


def passou_do_limite(ip: str) -> bool:
    agora = time.monotonic()
    acessos = _acessos[ip]
    while acessos and agora - acessos[0] > 60:
        acessos.popleft()
    if len(acessos) >= config.LIMITE_REQUISICOES_POR_MINUTO:
        return True
    acessos.append(agora)
    return False


@app.middleware("http")
async def cabecalhos_de_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    resposta.headers["Content-Security-Policy"] = "default-src 'self'"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    return resposta


@app.exception_handler(RequestValidationError)
async def entrada_invalida(request: Request, exc: RequestValidationError):
    if request.url.path == "/api/chat":
        return erro(
            "Não entendi o pedido. Escreva uma mensagem de até "
            f"{config.MAX_CARACTERES_MENSAGEM} caracteres e tente de novo.",
            422,
        )
    return erro("Confira os valores informados: algum campo está vazio ou fora do intervalo aceito.", 422)


@app.exception_handler(calculo.EntradaInvalida)
async def calculo_invalido(request: Request, exc: calculo.EntradaInvalida):
    return erro(str(exc), 422)


@app.get("/")
async def pagina_inicial():
    return FileResponse(PASTA_ESTATICA / "index.html")


# ---------- Chat ----------


@app.post("/api/chat")
async def chat(pedido: PedidoChat, request: Request):
    ip = ip_do_visitante(request)
    if passou_do_limite(ip):
        return erro("Você enviou muitas mensagens em pouco tempo. Aguarde um minuto e tente de novo.", 429)

    # Só as mensagens mais recentes seguem para a API, e a primeira precisa ser da pessoa.
    historico = [m.model_dump() for m in pedido.historico[-config.MAX_MENSAGENS_HISTORICO :]]
    while historico and historico[0]["role"] != "user":
        historico.pop(0)

    async def eventos():
        async for evento in responder(pedido.modulo, historico, pedido.mensagem):
            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        eventos(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------- Energia ----------


@app.get("/api/energia/opcoes")
async def energia_opcoes():
    return {
        "estados": sorted(energia.IRRADIACAO_POR_UF.values(), key=lambda e: e["uf"]),
        "ligacoes": [
            {"id": chave, "nome": energia.NOMES_LIGACAO[chave], "disponibilidade_kwh": kwh}
            for chave, kwh in energia.CUSTO_DISPONIBILIDADE_KWH.items()
        ],
        "potencia_placa_w": energia.POTENCIA_PLACA_W,
        "custo_referencia_r_por_wp": energia.CUSTO_REFERENCIA_R_POR_WP,
        "max_placas": energia.MAX_PLACAS,
        "fontes": energia.FONTES,
        "limitacoes": energia.LIMITACOES,
        "data_consulta": energia.DATA_CONSULTA,
    }


@app.post("/api/energia/simular")
async def energia_simular(pedido: PedidoSimulacao):
    return calculo.simular_solar(**pedido.model_dump())


@app.post("/api/energia/comparar")
async def energia_comparar(pedido: PedidoComparacao):
    dados = pedido.model_dump()
    # Campos opcionais vazios não são enviados ao cálculo.
    for parte in ("led", "chuveiro"):
        if dados[parte]:
            dados[parte] = {chave: valor for chave, valor in dados[parte].items() if valor is not None}
    return calculo.comparar(**dados)


# ---------- Decisão lógica (Computer Science) ----------


@app.get("/api/logica/dados")
async def logica_dados():
    return {
        "variaveis": cnh.VARIAVEIS,
        "saida": cnh.SAIDA,
        "expressao_do_grupo": cnh.EXPRESSAO_DO_GRUPO,
        "expressao_simplificada": cnh.EXPRESSAO_SIMPLIFICADA,
        "tabela_do_grupo": [dict(zip(cnh.NOMES + ["x"], linha)) for linha in cnh.TABELA_DO_GRUPO],
        "fontes": cnh.FONTES,
        "limitacoes": cnh.LIMITACOES,
        "data_consulta": cnh.DATA_CONSULTA,
    }


@app.post("/api/logica/avaliar")
async def logica_avaliar(corpo: dict = Body(...)):
    for nome in cnh.NOMES:
        valor = corpo.get(nome)
        # Só os números 0 e 1 são aceitos (true/false e textos são recusados).
        if type(valor) is not int or valor not in (0, 1):
            return erro(f"Valor inválido para {nome}: use 0 (não) ou 1 (sim).", 422)
    return cnh.avaliar({nome: corpo[nome] for nome in cnh.NOMES})


@app.get("/api/logica/relatorio")
async def logica_relatorio():
    return {"markdown": relatorio_logica.montar(), "pdf": RELATORIO_LOGICA_PDF.exists()}


@app.get("/logica/relatorio.pdf")
async def logica_relatorio_pdf():
    if not RELATORIO_LOGICA_PDF.exists():
        return erro("O PDF do relatório ainda não foi gerado.", 404)
    return FileResponse(RELATORIO_LOGICA_PDF, media_type="application/pdf", filename="relatorio-computer-science.pdf")


# ---------- Estatística ----------


@app.get("/api/ml/resultados")
async def ml_resultados():
    arquivo = SAIDAS_ML / "resultados.json"
    if not arquivo.exists():
        return erro("A análise estatística ainda não foi gerada neste servidor.", 404)
    return json.loads(arquivo.read_text(encoding="utf-8"))


@app.get("/api/ml/codigo")
async def ml_codigo():
    arquivos = sorted(PASTA_ML.glob("*.py"))
    return [
        {"nome": a.name, "conteudo": a.read_text(encoding="utf-8")}
        for a in arquivos
        if a.name != "__init__.py"
    ]


@app.get("/api/ml/relatorio")
async def ml_relatorio():
    arquivo = SAIDAS_ML / "relatorio.md"
    if not arquivo.exists():
        return erro("O relatório ainda não foi gerado neste servidor.", 404)
    return {"markdown": arquivo.read_text(encoding="utf-8"), "pdf": RELATORIO_PDF.exists()}


@app.get("/ml/relatorio.pdf")
async def ml_relatorio_pdf():
    if not RELATORIO_PDF.exists():
        return erro("O PDF do relatório ainda não foi gerado.", 404)
    return FileResponse(RELATORIO_PDF, media_type="application/pdf", filename="relatorio-modelagem-linear.pdf")
