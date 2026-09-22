# Sistemas Multiagentes com IA

Laboratório da disciplina **Sistemas Multiagentes com IA** (MBA em BI & Data Science — Ibmec), com ênfase em segurança pública. Exemplos com o SDK `openai-agents`.

## Estrutura

A infraestrutura é **compartilhada na raiz** e usada por todas as aulas:

```
11_Sistem_MultiAgentes/
  provedor.py        # abstração do provedor (Zen/Ollama/OpenAI): configurar(), modelo(), rodar()
  requirements.txt   # dependências (uma única lista para todas as aulas)
  .env               # configuração do provedor (PROVEDOR, chaves, modelo)
  venv/              # ambiente virtual único
  aula1/             # Fundamentos (agentes, tools, provedor) — pacote
  aula2/             # Multiagentes (handoff, output, sessão, guardrails, streaming)
  aula3/             # Engenharia de Agent Loops
```

## Como rodar

Cada `aulaN` é um pacote (tem `__init__.py`). Rode **sempre da raiz**, com a `venv` da raiz ativada:

```bash
cd 11_Sistem_MultiAgentes
source venv/bin/activate

# Exemplo de uma aula:
python -m aula2.agente_triagem

# Expor a API da Aula 2:
uvicorn aula2.main:app --reload
```

## Configuração

Copie `.env.example` para `.env` e ajuste:

- `PROVEDOR=zen` — usa o OpenCode Zen (requer `OPENAI_API_KEY` e `OPENAI_MODEL`).
- `PROVEDOR=ollama` — usa o Ollama local (sem custo; requer `OLLAMA_MODEL`).

O `provedor.py` resolve o modelo do provedor ativo via `modelo()` e, em falha do Zen, recua automaticamente para o Ollama via `rodar()`.

> ⚠️ Nunca commite o `.env` (contém chaves). Ele já está no `.gitignore`.
