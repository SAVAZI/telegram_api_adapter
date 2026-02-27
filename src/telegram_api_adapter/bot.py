"""Bot do Telegram.

Aqui ficam a criação da Application do `python-telegram-bot` e os handlers básicos.
A ideia é manter este módulo pequeno e delegar integrações para adapters em `adapters/`.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from telegram.constants import ChatType
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

from telegram_api_adapter.config import Settings


logger = logging.getLogger("telegram_api_adapter")


def _is_private_message(update: Update) -> bool:
    """Verifica se o update representa uma mensagem em chat privado.

    Args:
        update: Update recebido do Telegram.

    Returns:
        `True` se for uma mensagem em chat privado; caso contrário, `False`.
    """

    if update.message is None:
        return False

    if update.effective_chat is None:
        return False

    return update.effective_chat.type == ChatType.PRIVATE


def _normalize_update(update: Update, start_payload: str | None) -> dict[str, Any]:
    """Normaliza a mensagem recebida para o JSON esperado pela API.

    Formato produzido:
    {
      canal: "telegram",
      tg_user_id: str(update.effective_user.id),
      tg_chat_id: str(update.effective_chat.id),
      message_id: str(update.message.message_id),
      timestamp: update.message.date.isoformat(),
      texto: update.message.text or "",
      start_payload: argumento do /start ou null
    }

    Args:
        update: Update recebido do Telegram.
        start_payload: Payload do comando /start, quando aplicável.

    Returns:
        Dicionário pronto para serialização JSON.
    """

    effective_user_id = ""
    if update.effective_user is not None:
        effective_user_id = str(update.effective_user.id)

    effective_chat_id = ""
    if update.effective_chat is not None:
        effective_chat_id = str(update.effective_chat.id)

    message = update.message
    assert message is not None

    return {
        "canal": "telegram",
        "tg_user_id": effective_user_id,
        "tg_chat_id": effective_chat_id,
        "message_id": str(message.message_id),
        "timestamp": message.date.isoformat(),
        "texto": message.text or "",
        "start_payload": start_payload,
    }


async def _post_to_api(api_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Envia o payload para a API via HTTP POST e retorna o JSON de resposta.

    Args:
        api_url: Endpoint da sua API.
        payload: JSON normalizado da mensagem.

    Returns:
        JSON retornado pela API.

    Raises:
        httpx.RequestError: Falhas de rede/timeouts.
        httpx.HTTPStatusError: Respostas HTTP não-2xx.
        ValueError: Resposta não é JSON válido.
    """

    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()


async def _send_service_unavailable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia a mensagem padrão quando a API estiver indisponível.

    Requisito: responder apenas uma vez (sem loop) e usar `bot.send_message`.

    Args:
        update: Update recebido do Telegram.
        context: Contexto do handler.
    """

    if update.effective_chat is None:
        return

    logger.warning("Falha ao chamar API; enviando fallback no chat_id=%s", update.effective_chat.id)
    await context.bot.send_message(chat_id=str(update.effective_chat.id), text="Serviço indisponível")


def _parse_reply_to_message_id(value: Any) -> int | None:
    """Converte `reply_to_message_id` vindo da API para inteiro ou `None`.

    Args:
        value: Valor retornado pela API (string, null, etc.).

    Returns:
        Inteiro se o valor for válido; caso contrário, `None`.
    """

    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            return int(stripped)

    return None


async def _handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE, start_payload: str | None) -> None:
    """Fluxo principal do adaptador: normaliza, POSTa na API e responde no Telegram.

    - Ignora tudo que não for chat privado.
    - Em caso de erro de rede/HTTP/JSON, responde "Serviço indisponível".

    Args:
        update: Update recebido.
        context: Contexto do PTB.
        start_payload: Payload do /start quando aplicável; caso contrário, `None`.
    """

    if not _is_private_message(update):
        return

    settings: Settings = context.application.bot_data["settings"]
    payload = _normalize_update(update, start_payload=start_payload)

    logger.info(
        "Recebido update privado (chat_id=%s user_id=%s message_id=%s start_payload=%s)",
        payload.get("tg_chat_id"),
        payload.get("tg_user_id"),
        payload.get("message_id"),
        payload.get("start_payload"),
    )

    try:
        api_response = await _post_to_api(settings.api_url, payload)
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        await _send_service_unavailable(update, context)
        return

    logger.info(
        "Resposta da API recebida (acao=%s tg_chat_id=%s)",
        api_response.get("acao"),
        api_response.get("tg_chat_id"),
    )

    action = api_response.get("acao")
    if action != "responder":
        return

    tg_chat_id = str(api_response.get("tg_chat_id", "") or "").strip()
    text = str(api_response.get("texto", "") or "")
    reply_to_message_id = _parse_reply_to_message_id(api_response.get("reply_to_message_id"))

    if not tg_chat_id:
        return

    await context.bot.send_message(
        chat_id=tg_chat_id,
        text=text,
        reply_to_message_id=reply_to_message_id,
    )


async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler do comando /start (somente privado).

    Extrai o payload do comando (primeiro argumento) e encaminha o evento para a API.

    Args:
        update: Update recebido.
        context: Contexto do handler (inclui `args`).
    """

    start_payload = context.args[0] if getattr(context, "args", None) else None
    await _handle_private_message(update, context, start_payload=start_payload)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler de mensagens comuns (somente privado).

    Encaminha a mensagem para a API com `start_payload=null`.

    Args:
        update: Update recebido.
        context: Contexto do handler.
    """

    await _handle_private_message(update, context, start_payload=None)


def build_application(settings: Settings) -> Application:
    """Cria e configura a Application do bot.

    Args:
        settings: Configurações já validadas (inclui o token do bot).

    Returns:
        Instância de `Application` pronta para executar.
    """

    request = HTTPXRequest(
        proxy_url=settings.telegram_proxy_url,
        read_timeout=settings.telegram_read_timeout_s,
        write_timeout=settings.telegram_write_timeout_s,
        connect_timeout=settings.telegram_connect_timeout_s,
        pool_timeout=settings.telegram_pool_timeout_s,
    )

    async def _post_init(application: Application) -> None:
        """Loga quando a Application termina a inicialização.

        Este callback ajuda a diferenciar "processo rodando" de "travado".

        Args:
            application: Instância inicializada.
        """

        me = application.bot
        logger.info("Bot inicializado e pronto para receber mensagens.")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .request(request)
        .post_init(_post_init)
        .build()
    )

    application.bot_data["settings"] = settings

    application.add_handler(CommandHandler("start", on_start, filters=filters.ChatType.PRIVATE))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, on_message))

    return application
