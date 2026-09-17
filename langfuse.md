# Monitoramento de Agentes com Langfuse (Cloud)

Este documento é o roteiro para instrumentar os agentes das aulas (SDK `openai-agents`) com o **Langfuse Cloud**, dando visibilidade sobre cada chamada ao LLM, uso de ferramentas, latência, tokens e custo.

> **Status:** plano. Este roteiro descreve o que fazer; a execução (instalação + integração + teste) fica como checklist nas etapas.

---

## 1. O que é o Langfuse

O **Langfuse** é uma plataforma de observabilidade para agentes de IA. Ele registra **traces** (uma execução do agente) compostos por **spans** (cada etapa): chamadas ao modelo, execuções de ferramentas, handoffs, guardrails, etc. Permite responder: *quais ferramentas o agente chamou, quanto custou, quanto demorou, quais tokens usou*.

## 2. Arquitetura da integração

O SDK `openai-agents` é instrumentado pela biblioteca **OpenInference** (`openinference-instrumentation-openai-agents`), que captura as operações do agente e as exporta como spans **OpenTelemetry (OTel)**. O cliente `langfuse` recebe esses spans e os envia para o Langfuse Cloud.

```
Agent/Runner  →  OpenInference (captura spans OTel)  →  Langfuse client  →  Langfuse Cloud (dashboard)
```

---

## 3. Pré-requisitos

- Projeto em execução (as aulas 1–3 usam o SDK `openai-agents` na `venv` da raiz).
- Conta no **Langfuse Cloud** (https://cloud.langfuse.com) com um **projeto** criado.

---

## 4. Obter as credenciais (Langfuse Cloud)

1. Crie uma conta em https://cloud.langfuse.com.
2. Crie um **projeto**.
3. Em **Settings → API Keys**, copie:
   - `LANGFUSE_PUBLIC_KEY` (chave pública do projeto)
   - `LANGFUSE_SECRET_KEY` (chave secreta do projeto)
4. A URL base padrão do Cloud é `https://cloud.langfuse.com`.

> ⚠️ Guarde a `SECRET_KEY` com cuidado. Nunca commite valores reais — use o `.env` (ignorado pelo git).

---

## 5. Instalar as dependências (na venv da raiz)

```bash
cd ~/Documentos/pos_graduacao/11_Sistem_MultiAgentes
source venv/bin/activate
pip install langfuse openinference-instrumentation-openai-agents nest_asyncio
```

> **`nest_asyncio`:** necessário porque a instrumentação OTel usa `asyncio` e alguns ambientes exigem `nest_asyncio.apply()`. **Atenção:** `nest_asyncio.apply()` é incompatível com `uvloop` (usado pelo FastAPI) — veja a Seção 9.

---

## 6. Configurar o `.env`

Adicione ao `.env` (e ao `.env.example`, com placeholders):

```dotenv
# Langfuse Cloud
LANGFUSE_PUBLIC_KEY=pk-lf-...        # troque pela sua chave pública
LANGFUSE_SECRET_KEY=sk-lf-...        # troque pela sua chave secreta
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_TRACING_ENABLED=true
```

| Variável | Descrição | Padrão |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY` | Chave pública do projeto | — |
| `LANGFUSE_SECRET_KEY` | Chave secreta do projeto | — |
| `LANGFUSE_BASE_URL` | Host da API | `https://cloud.langfuse.com` |
| `LANGFUSE_TRACING_ENABLED` | Liga/desliga o envio de traces | `true` |

O `provedor.py` já faz `load_dotenv()` no topo, então essas variáveis ficam disponíveis automaticamente.

---

## 7. Instrumentar via `provedor.py` (todos os agentes)

Como todas as aulas chamam `configurar()` do `provedor.py` (na raiz), basta ativar o monitoramento **uma única vez** ali, para que todos os agentes sejam instrumentados.

Adicionar a função no `provedor.py`:

```python
def habilitar_monitoramento() -> None:
    """Ativa a instrumentação do openai-agents para o Langfuse Cloud."""
    if os.getenv("LANGFUSE_TRACING_ENABLED", "false").strip().lower() != "true":
        return

    import nest_asyncio
    nest_asyncio.apply()

    from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
    OpenAIAgentsInstrumentor().instrument()

    from langfuse import get_client
    cliente = get_client()
    print("Langfuse autenticado:", cliente.auth_check())


def configurar(provedor: str | None = None) -> str:
    ...
    habilitar_monitoramento()   # chamado junto com a configuração do provedor
    ...
```

Assim, qualquer `from provedor import configurar; configurar()` em qualquer aula já passa a exportar traces.

> **Alternativa pontual:** para instrumentar só um script, chame `habilitar_monitoramento()` (ou o bloco equivalente) antes de `Runner.run_*` naquele script.

---

## 8. Testar a instrumentação

Com as chaves no `.env`, rode um exemplo e verifique o trace no dashboard:

```bash
source venv/bin/activate
python -m aula2.primeiro_agente   # ou python -m aula2.agente_triagem
```

```bash
# Teste rápido de autenticação
python -c "
from langfuse import get_client
c = get_client()
print('auth ok:', c.auth_check())
c.flush()
"
```

No Langfuse Cloud, abra **Traces** para ver o trace com os sub-spans (chamada ao LLM, tools, tokens, latência, custo).

---

## 9. Pontos de atenção e segurança

- **Residência do dado (LGPD):** o **Langfuse Cloud** envia os traces (prompts, respostas, argumentos de ferramentas) **para fora da máquina**. Se houver **dado sigiloso** (contexto PCDF), prefira **self-hosted** (Langfuse via Docker, dados locais) — consulte a alternativa abaixo.
- **`nest_asyncio` vs `uvloop`:** `nest_asyncio.apply()` não é compatível com `uvloop`. Se a aplicação usar FastAPI/uvicorn com uvloop, será preciso **desabilitar o uvloop** (usar o event loop padrão do asyncio) ou instrumentar apenas nos pontos necessários.
- **Credenciais:** nunca commitar `LANGFUSE_SECRET_KEY`. O `.env` já está no `.gitignore`.
- **Desativar:** basta `LANGFUSE_TRACING_ENABLED=false` (ou remover a chamada a `habilitar_monitoramento()`).
- **Custo/volume:** traces aumentam o volume de telemetria; em ambiente com muitos agentes, use `LANGFUSE_SAMPLE_RATE` para amostrar.

### Alternativa self-hosted (dados locais)

Se a residência do dado for requisito, rode o Langfuse na máquina via Docker Compose (dados não saem da máquina) e aponte:

```dotenv
LANGFUSE_BASE_URL=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...   # gerados pelo próprio Langfuse local
LANGFUSE_SECRET_KEY=sk-lf-...
```

O restante da integração (Seções 5–8) é idêntico.

---

## 10. Checklist de execução

- [ ] Criar conta/projeto no Langfuse Cloud e copiar as chaves.
- [ ] `pip install langfuse openinference-instrumentation-openai-agents nest_asyncio`
- [ ] Adicionar `LANGFUSE_*` ao `.env` e `.env.example`.
- [ ] Adicionar `habilitar_monitoramento()` ao `provedor.py` e chamá-lo em `configurar()`.
- [ ] Rodar `python -m aula2.primeiro_agente` e conferir o trace no dashboard.
- [ ] Revisar a compatibilidade com uvloop (FastAPI) e a política de dados (Cloud vs self-hosted).
