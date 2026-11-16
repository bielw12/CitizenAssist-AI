"""Ponto de entrada para a Vercel (e para `uvicorn index:app`): reaproveita o app de app/main.py."""

from app.main import app  # noqa: F401
