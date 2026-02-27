"""Interfaces base para adapters de APIs.

A ideia é que cada adapter encapsule a lógica de integração com uma API externa,
permitindo registrar e roteá-los de forma uniforme.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AdapterRequest:
    """Representa uma solicitação genérica para um adapter.

    Você pode expandir este modelo conforme as necessidades do projeto (ex.: headers,
    payload, autenticação, etc.).
    """

    route: str
    payload: str | None = None


@dataclass(frozen=True)
class AdapterResponse:
    """Representa uma resposta genérica de um adapter."""

    ok: bool
    message: str


class ApiAdapter(Protocol):
    """Contrato mínimo que um adapter precisa implementar."""

    name: str

    async def handle(self, request: AdapterRequest) -> AdapterResponse:
        """Processa uma requisição genérica e devolve uma resposta.

        Args:
            request: Dados normalizados para a chamada.

        Returns:
            Resposta normalizada.
        """

        ...
