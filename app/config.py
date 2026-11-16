"""Configurações lidas do arquivo .env (veja .env.example)."""

import os

from dotenv import load_dotenv

load_dotenv()

MODELO = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8000"))

MAX_CARACTERES_MENSAGEM = int(os.getenv("MAX_CARACTERES_MENSAGEM", "2000"))
MAX_MENSAGENS_HISTORICO = int(os.getenv("MAX_MENSAGENS_HISTORICO", "20"))
LIMITE_REQUISICOES_POR_MINUTO = int(os.getenv("LIMITE_REQUISICOES_POR_MINUTO", "10"))

BUSCA_WEB = os.getenv("BUSCA_WEB", "1") == "1"
BUSCA_WEB_MAX_USOS = int(os.getenv("BUSCA_WEB_MAX_USOS", "3"))
BUSCA_WEB_DOMINIOS = [
    d.strip()
    for d in os.getenv("BUSCA_WEB_DOMINIOS", "gov.br,jus.br,leg.br,mp.br,def.br").split(",")
    if d.strip()
]


def chave_configurada() -> bool:
    """Diz se existe uma chave de API. Lida a cada chamada para facilitar os testes."""
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
