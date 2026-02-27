"""API de exemplo para testar o adaptador Telegram.

Esta API é um mock mínimo que recebe o payload normalizado do adaptador e
retorna a ação `responder` para o mesmo chat.

Como usar (exemplo):

1) Instale dependências (fora do escopo do requirements.txt principal):

   - `pip install fastapi uvicorn`

2) Inicie o servidor:

   - `uvicorn examples.mock_api_fastapi:app --reload --port 8000`

3) Configure no `.env` do adaptador:

   - `API_URL=http://localhost:8000/telegram`
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Mock API Telegram", version="1.0.0")


class TelegramInbound(BaseModel):
    """Modelo do JSON que o adaptador envia para a API."""

    canal: Literal["telegram"]
    tg_user_id: str
    tg_chat_id: str
    message_id: str
    timestamp: str
    texto: str = Field(default="")
    start_payload: str | None = None


class TelegramOutbound(BaseModel):
    """Modelo do JSON que a API deve retornar para o adaptador."""

    acao: Literal["responder"]
    tg_chat_id: str
    texto: str
    reply_to_message_id: str | None = None


@app.post("/telegram", response_model=TelegramOutbound)
async def telegram_webhook(payload: TelegramInbound) -> Any:
    """Endpoint de exemplo compatível com o adaptador.

    Regras desta implementação:

    - Se vier `/start` com payload, responde confirmando o payload.
    - Caso contrário, faz eco da mensagem.

    Args:
        payload: JSON normalizado pelo adaptador.

    Returns:
        Estrutura com `acao=responder` que o adaptador entende.
    """

    if payload.start_payload:
        text = f"Start recebido com payload: {payload.start_payload}"
        reply_to = None
    else:
        text = f"Eco: {payload.texto}"
        reply_to = payload.message_id

    return TelegramOutbound(
        acao="responder",
        tg_chat_id=payload.tg_chat_id,
        texto=text,
        reply_to_message_id=reply_to,
    )
