# Instruções para o GitHub Copilot neste repositório

Estas regras devem ser seguidas sempre que você gerar, modificar ou sugerir código neste projeto.

## Princípios

- **Código limpo e modular**: prefira funções pequenas, coesas e reutilizáveis. Evite “funções Deus”.
- **Boas práticas**: siga padrões Python (PEP 8), trate erros de forma explícita, valide entradas e mantenha responsabilidades bem separadas.
- **Legibilidade > esperteza**: evite truques desnecessários. Nomes devem ser descritivos.
- **Mudanças mínimas e focadas**: altere apenas o necessário para cumprir a tarefa.

## Comentários e documentação (obrigatório)

- **Toda função deve ser comentada/documentada em português**.
- Use **docstring** em português (estilo simples) descrevendo:
  - o que a função faz,
  - parâmetros e retornos,
  - exceções relevantes (se houver).
- Comentários inline devem ser raros e úteis; prefira refatorar para ficar autoexplicativo.

## Organização e estilo

- Separe camadas (ex.: cliente HTTP, serviços, validação, modelos) quando fizer sentido.
- Evite dependências globais e efeitos colaterais ocultos.
- Use **type hints** sempre que possível.
- Escreva funções e classes com responsabilidade única.

## Qualidade e segurança

- Não registre (log) tokens/segredos.
- Trate respostas e erros de APIs externas (timeouts, retries quando apropriado, e mensagens claras).
- Evite copiar código de fontes externas; se precisar de uma referência, reescreva de forma original.

## Testes (quando aplicável)

- Se o projeto tiver testes, atualize/adicione testes para cobrir o comportamento alterado.
- Testes devem ser claros, determinísticos e fáceis de manter.
