"""Registro de adapters.

Este módulo mantém um registro em memória para mapear nomes de adapters para
implementações concretas.
"""

from __future__ import annotations

from typing import Dict

from telegram_api_adapter.adapters.base import ApiAdapter


_ADAPTERS: Dict[str, ApiAdapter] = {}


def register_adapter(adapter: ApiAdapter) -> None:
    """Registra um adapter para uso no roteamento.

    Args:
        adapter: Implementação do adapter.

    Raises:
        ValueError: Se o adapter não tiver `name` válido.
    """

    name = getattr(adapter, "name", "")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Adapter precisa ter um atributo 'name' não vazio.")

    _ADAPTERS[name] = adapter


def get_adapter(name: str) -> ApiAdapter | None:
    """Obtém um adapter registrado pelo nome.

    Args:
        name: Nome do adapter.

    Returns:
        O adapter, se existir; caso contrário, `None`.
    """

    return _ADAPTERS.get(name)


def list_adapters() -> list[str]:
    """Lista os nomes dos adapters atualmente registrados."""

    return sorted(_ADAPTERS.keys())
