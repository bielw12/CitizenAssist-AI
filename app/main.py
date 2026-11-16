"""Servidor do Citizen Assist AI: entrega a tela e a rota do chat."""

import json
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints

from . import config
from .chat import responder

PASTA_ESTATICA = Path(__file__).parent / "static"

app = FastAPI(title="Citizen Assist AI", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=PASTA_ESTATICA), name="static")

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: Texto


class PedidoChat(BaseModel):
    modulo: Literal["geral"]
    historico: list[Mensagem] = Field(default_factory=list, max_length=200)
    mensagem: Annotated[Texto, StringConstraints(max_length=config.MAX_CARACTERES_MENSAGEM)]


# Limite simples de requisições por endereço IP, guardado só na memória do servidor.
_acessos: dict[str, deque[float]] = defaultdict(deque)


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
    return JSONResponse(
        status_code=422,
        content={
            "erro": "Não entendi o pedido. Escreva uma mensagem de até "
            f"{config.MAX_CARACTERES_MENSAGEM} caracteres e tente de novo."
        },
    )


@app.get("/")
async def pagina_inicial():
    return FileResponse(PASTA_ESTATICA / "index.html")


@app.post("/api/chat")
async def chat(pedido: PedidoChat, request: Request):
    ip = request.client.host if request.client else "desconhecido"
    if passou_do_limite(ip):
        return JSONResponse(
            status_code=429,
            content={"erro": "Você enviou muitas mensagens em pouco tempo. Aguarde um minuto e tente de novo."},
        )

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
