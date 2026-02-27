# telegram_api_adapter

Adaptador universal em Python para receber mensagens no Telegram e encaminhar para qualquer API via HTTP.

Este repositório contém um **adaptador Telegram** (baseado em `python-telegram-bot`) que atua como uma ponte:

- recebe mensagens no Telegram (**somente chat privado**),
- normaliza a mensagem para um JSON padrão,
- envia esse JSON para a sua API via HTTP `POST`,
- e devolve no Telegram a ação retornada pela API.

Objetivo: manter o bot “fino” e deixar a regra de negócio na sua API.

## Requisitos

- Python 3.10+ (recomendado)

Dependências principais:

- `python-telegram-bot==21.6`
- `httpx` (instalado como dependência do PTB)

## Setup

### 1) Ambiente virtual

Ative o venv:

- Linux/macOS:
  - `. .venv/bin/activate`

### 2) Dependências

Instale dependências:

- `pip install -r requirements.txt`

### 3) Configuração

Configure o `.env`:

- Edite o arquivo `.env` e preencha:
  - `TELEGRAM_BOT_TOKEN`: token do bot (BotFather)
  - `API_URL`: endpoint da sua API que receberá o POST

Exemplo de `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=123456:SEU_TOKEN_AQUI
API_URL=https://sua-api.exemplo.com/telegram
```

Observação: não publique seu token.

## Rodar

- Linux/macOS:
  - `PYTHONPATH=src ./.venv/bin/python -m telegram_api_adapter`

Observação: o uso de `PYTHONPATH=src` permite executar o pacote sem precisar instalá-lo.

## Comportamento (MVP)

- Modelo de execução: **long polling** (`run_polling`).
- Mensagens processadas: texto comum e comando `/start`.
- Escopo: **somente chat privado**.
- Persistência: **não usa banco local**.
- Falha de integração (rede/API): responde **uma vez** com `Serviço indisponível`.

## Como o adaptador funciona

### Regras principais

- **Somente chat privado**: mensagens fora de chat privado são ignoradas.
- **Sem banco local**: não há persistência local; cada mensagem é processada de forma independente.
- **Long polling (MVP)**: a execução usa `run_polling`.

### Fluxo ponta-a-ponta

1. O Telegram entrega um `Update` para o bot.
2. O bot verifica se é chat privado; se não for, ignora.
3. O bot normaliza a mensagem em um JSON e faz `POST` para `API_URL`.
4. A sua API responde um JSON dizendo qual ação executar.
5. Se `acao == "responder"`, o adaptador envia a mensagem de volta via `bot.send_message`.
6. Se o `POST` falhar (rede/timeout/HTTP não-2xx/JSON inválido), o adaptador responde apenas uma vez: **"Serviço indisponível"**.

Importante:

- O adaptador **não faz retry** no MVP (para evitar loops e duplicidades).
- O adaptador **não mantém estado** entre mensagens.

### JSON enviado para a sua API

Ao receber uma mensagem, o adaptador monta e envia o seguinte JSON:

```json
{
  "canal": "telegram",
  "tg_user_id": "<string>",
  "tg_chat_id": "<string>",
  "message_id": "<string>",
  "timestamp": "<ISO-8601>",
  "texto": "<string>",
  "start_payload": "<string|null>"
}
```

Campos:

- `canal`: sempre `"telegram"`.
- `tg_user_id`: `str(update.effective_user.id)`.
- `tg_chat_id`: `str(update.effective_chat.id)`.
- `message_id`: `str(update.message.message_id)`.
- `timestamp`: `update.message.date.isoformat()`.
- `texto`: `update.message.text or ""`.
- `start_payload`:
  - no comando `/start`, é o primeiro argumento (ex.: `/start abc123` → `"abc123"`),
  - em mensagens comuns, é `null`.

Dica: sua API pode usar `message_id` e `timestamp` para auditoria e rastreio.

#### Exemplo 1: mensagem comum

Exemplo de payload enviado quando o usuário digita uma mensagem comum (sem ser comando):

```json
{
  "canal": "telegram",
  "tg_user_id": "111111111",
  "tg_chat_id": "111111111",
  "message_id": "42",
  "timestamp": "2026-02-26T21:20:30+00:00",
  "texto": "oi, tudo bem?",
  "start_payload": null
}
```

#### Exemplo 2: /start com payload

Se o usuário enviar `/start promo123`, o adaptador envia:

```json
{
  "canal": "telegram",
  "tg_user_id": "111111111",
  "tg_chat_id": "111111111",
  "message_id": "43",
  "timestamp": "2026-02-26T21:21:10+00:00",
  "texto": "/start promo123",
  "start_payload": "promo123"
}
```

### Envio manual (simulando o adaptador com curl)

Você pode simular o POST que o adaptador faz para a sua API com `curl`:

```bash
curl -X POST "$API_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "canal": "telegram",
    "tg_user_id": "111111111",
    "tg_chat_id": "111111111",
    "message_id": "42",
    "timestamp": "2026-02-26T21:20:30+00:00",
    "texto": "oi, tudo bem?",
    "start_payload": null
  }'
```

Se sua API estiver local, um exemplo comum seria:

```bash
export API_URL="http://localhost:8000/telegram"
```

### JSON esperado como resposta da sua API

A API deve retornar um JSON no formato:

```json
{
  "acao": "responder",
  "tg_chat_id": "<string>",
  "texto": "<string>",
  "reply_to_message_id": "<string|null>"
}
```

Comportamento:

- Se `acao` for diferente de `"responder"`, o adaptador não envia mensagem.
- `reply_to_message_id` pode ser `null` ou uma string numérica. Quando válido, o adaptador envia como `reply_to_message_id`.

Recomendações:

- Retorne sempre `tg_chat_id` como string.
- Retorne `texto` como string (pode ser vazia, mas normalmente não faz sentido).

#### Exemplo A: responder sem reply

```json
{
  "acao": "responder",
  "tg_chat_id": "111111111",
  "texto": "Olá! Recebi sua mensagem.",
  "reply_to_message_id": null
}
```

#### Exemplo B: responder como reply (thread de resposta)

```json
{
  "acao": "responder",
  "tg_chat_id": "111111111",
  "texto": "Respondendo em cima da sua mensagem 42.",
  "reply_to_message_id": "42"
}
```

#### Exemplo C: ação ignorada

Qualquer `acao` diferente de `"responder"` é ignorada pelo adaptador (não envia mensagem):

```json
{
  "acao": "ignorar",
  "tg_chat_id": "111111111",
  "texto": "(não será enviado)",
  "reply_to_message_id": null
}
```

### Tratamento de erros (rede/API)

- Se ocorrer falha de rede, timeout, resposta HTTP não-2xx ou JSON inválido no POST para `API_URL`, o adaptador responde no Telegram:
  - `Serviço indisponível`
- Não há re-tentativa automática no MVP (para evitar loops).

Notas importantes:

- A sua API deve responder **HTTP 2xx** e um **JSON válido** para ser considerada sucesso.
- Se a API demorar muito, o adaptador pode estourar timeout (atualmente ~10s) e cair no fallback.

## Checklist de integração

Uma sequência prática para validar se está tudo certo ponta-a-ponta:

1) **Bot configurado**

- `.env` preenchido com `TELEGRAM_BOT_TOKEN` e `API_URL`.

2) **API respondendo**

- Sua API deve aceitar `POST` em `API_URL`.
- Deve responder com HTTP 2xx e JSON no formato esperado.

3) **Subir o adaptador**

- `PYTHONPATH=src ./.venv/bin/python -m telegram_api_adapter`

4) **Testes manuais no Telegram (chat privado)**

- Envie `/start teste123` e confirme que sua API recebe `start_payload="teste123"`.
- Envie uma mensagem comum (ex.: `oi`) e confirme que `start_payload=null`.

5) **Validação do filtro de privacidade**

- Envie mensagens em grupo/supergrupo/canal e confirme que o adaptador **não** chama a API.

6) **Teste de indisponibilidade**

- Derrube sua API (ou altere temporariamente `API_URL` para um host inválido).
- Envie uma mensagem no privado e confirme que o bot responde: `Serviço indisponível`.

## Exemplo de API (FastAPI)

Para testar rapidamente, existe uma API mock compatível com o adaptador em [examples/mock_api_fastapi.py](examples/mock_api_fastapi.py).

### Rodando o mock

1) Instale as dependências do mock (opcional; não faz parte do `requirements.txt` principal):

- `pip install fastapi uvicorn pydantic`

2) Inicie o servidor:

- `uvicorn examples.mock_api_fastapi:app --reload --port 8000`

3) Aponte o adaptador para o mock:

- No `.env`:
  - `API_URL=http://localhost:8000/telegram`

O mock faz:

- `/start <payload>` → responde confirmando o `start_payload`.
- mensagem comum → responde com eco e usa `reply_to_message_id=message_id`.

## Troubleshooting

### O bot inicia e cai com erro de configuração

- Verifique se o `.env` tem `TELEGRAM_BOT_TOKEN` e `API_URL` preenchidos.

### O bot responde “Serviço indisponível”

Isso significa que o `POST` falhou (por exemplo: API offline, DNS, timeout, HTTP 500, ou JSON inválido).

Checklist rápido:

- `API_URL` está correta e acessível a partir do host onde o bot roda.
- Sua API está respondendo HTTP 2xx.
- Sua API está retornando JSON válido.

## Segurança

- Não publique `TELEGRAM_BOT_TOKEN`.
- Evite logar payloads contendo dados sensíveis em produção.

## Estrutura

- `src/telegram_api_adapter/config.py`: leitura de configuração e `.env`
- `src/telegram_api_adapter/bot.py`: adaptador Telegram (handlers, normalização JSON e POST para a API)
- `src/telegram_api_adapter/adapters/`: espaço para adapters de APIs (opcional para expansões futuras)

