"""Configuração do projeto.

- Lê o token do bot a partir de variáveis de ambiente.
- Carrega um arquivo `.env` simples (sem dependências externas), se existir.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Configurações carregadas para execução do serviço."""

    telegram_bot_token: str
    api_url: str
    telegram_proxy_url: str | None
    telegram_read_timeout_s: float
    telegram_write_timeout_s: float
    telegram_connect_timeout_s: float
    telegram_pool_timeout_s: float


def _get_env_float(name: str, default: float) -> float:
    """Lê uma variável de ambiente numérica (float) com fallback.

    Args:
        name: Nome da variável.
        default: Valor padrão se ausente/inválida.

    Returns:
        O valor convertido para float, ou `default`.
    """

    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _parse_env_line(line: str) -> tuple[str, str] | None:
    """Interpreta uma linha do arquivo `.env` no formato `CHAVE=VALOR`.

    - Ignora linhas vazias e comentários (iniciados por `#`).
    - Remove aspas simples ou duplas ao redor do valor, quando presentes.

    Args:
        line: Linha crua lida do arquivo.

    Returns:
        Um par (chave, valor) se a linha for válida; caso contrário, `None`.
    """

    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()

    if not key:
        return None

    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    return key, value


def load_dotenv(dotenv_path: str | Path = ".env") -> None:
    """Carrega variáveis do arquivo `.env` para o ambiente do processo.

    Esta implementação é propositalmente simples para manter o projeto leve.
    Por padrão, ela **não sobrescreve** variáveis já existentes em `os.environ`.

    Args:
        dotenv_path: Caminho para o arquivo `.env`.
    """

    path = Path(dotenv_path)
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(raw_line)
        if parsed is None:
            continue

        key, value = parsed
        os.environ.setdefault(key, value)


def load_settings() -> Settings:
    """Carrega e valida as configurações necessárias para iniciar o bot.

    Returns:
        Um objeto `Settings` com as configurações resolvidas.

    Raises:
        RuntimeError: Se `TELEGRAM_BOT_TOKEN` ou `API_URL` não estiverem configurados.
    """

    load_dotenv(".env")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não configurado. Preencha o arquivo .env ou exporte a variável de ambiente."
        )

    api_url = os.getenv("API_URL", "").strip()
    if not api_url:
        raise RuntimeError("API_URL não configurada. Preencha o arquivo .env ou exporte a variável de ambiente.")

    telegram_proxy_url = os.getenv("TELEGRAM_PROXY_URL", "").strip() or None

    # Timeouts do Bot API (úteis em redes lentas/restritas)
    telegram_read_timeout_s = _get_env_float("TELEGRAM_READ_TIMEOUT_S", 20.0)
    telegram_write_timeout_s = _get_env_float("TELEGRAM_WRITE_TIMEOUT_S", 20.0)
    telegram_connect_timeout_s = _get_env_float("TELEGRAM_CONNECT_TIMEOUT_S", 20.0)
    telegram_pool_timeout_s = _get_env_float("TELEGRAM_POOL_TIMEOUT_S", 10.0)

    return Settings(
        telegram_bot_token=token,
        api_url=api_url,
        telegram_proxy_url=telegram_proxy_url,
        telegram_read_timeout_s=telegram_read_timeout_s,
        telegram_write_timeout_s=telegram_write_timeout_s,
        telegram_connect_timeout_s=telegram_connect_timeout_s,
        telegram_pool_timeout_s=telegram_pool_timeout_s,
    )
