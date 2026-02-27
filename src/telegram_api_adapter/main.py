"""Execução do bot do Telegram.

Este módulo concentra o bootstrap da aplicação: carrega configurações, cria o bot e inicia o polling.
"""

from __future__ import annotations

from telegram_api_adapter.bot import build_application
from telegram_api_adapter.config import load_settings


def main() -> None:
    """Inicializa e executa o bot via polling.

    Carrega as configurações (incluindo o token do bot), constrói a aplicação do
    `python-telegram-bot` e inicia o loop de polling.
    """

    settings = load_settings()
    application = build_application(settings)

    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
