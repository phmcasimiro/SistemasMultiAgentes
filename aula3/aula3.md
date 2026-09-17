# Aula 3: Engenharia de Agent Loops

Esta aula muda o foco de *conhecer o agente* para *controlar o loop*. A Aula 1 apresentou as peças soltas — `tools`, `handoff`, `output_type`, sessão, guardrails, streaming. Aqui o assunto é **o que acontece por dentro do `Runner`** entre uma pergunta e a resposta, e como **observar, parar, sobreviver e frear** esse loop.

**O loop:** o modelo decide (responder ou agir) → se age, reconsulta a própria mesa → repete até achar que terminou.

**Infraestrutura reaproveitada:** o mesmo `provedor.py` das Aulas 1–2 (provedor Zen/Ollama, `modelo()`, `rodar()`). Como a Aula 3 usa recursos mais recentes do SDK (`needs_approval`, `RunState`), confira se as dependências estão atualizadas.

> **Status:** todas as **7 seções** do deck estão **implementadas** (arquivos em `aula3/`). Veja a lista completa na **Seção 10**. Este documento descreve a teoria, os exercícios e os arquivos correspondentes.

> **Estrutura do repo:** a infraestrutura (`provedor.py`, `requirements.txt`, `.env`, `venv`) fica na **raiz** do curso. Os exemplos serão criados na pasta `aula3/` (pacote, com `__init__.py`) e rodados da raiz como `python -m aula3.arquivo`, usando `from provedor import configurar, modelo, rodar`.

---

## Mapa da Aula

| # | Seção | Ideia central |
|---|---|---|
| 1 | O loop por baixo dos panos | Tornar o loop visível com hooks |
| 2 | Hooks (RunHooks × AgentHooks) | Referência de todos os `on_*` e a ordem de disparo |
| 3 | Critérios de parada | Três formas de dizer "pare" |
| 4 | Retries e resiliência | Backoff, idempotência, dado real injetado |
| 5 | Autonomia e freio humano | `needs_approval` — pausa até alguém decidir |
| 6 | Observando o loop ao vivo | Streaming — ver cada decisão/token em tempo real |
| 7 | Loop com decisões encadeadas | Múltiplas tools independentes, ordem decidida pelo modelo |

---

## 1. O Loop por Baixo dos Panos (Hooks)

**Teoria.** Por padrão o loop é caixa-preta: só se vê o resultado final. `RunHooks` permite enxergar cada turno em tempo real. `on_llm_start` dispara **uma vez por chamada ao modelo** — isso sinaliza o custo (um turno com ferramenta gera mais de uma chamada).

**Ponto importante:** `on_agent_start` **não é contador de turno** — ele dispara "cada vez que o agente ativo muda" (ou seja, em *handoff*). Com um agente único (sem handoff), dispara **uma vez só**, mesmo que o loop rode vários turnos por dentro.

**Exemplo real (API + conversão encadeada):** `get_temperatura` + `converter_para_fahrenheit`. Nenhuma linha do código diz "primeiro chame X, depois Y" — quem decide a ordem, turno a turno, é o modelo, seguindo a instrução em linguagem natural.

**Instruções > pedido do usuário:** se as `instructions` dizem "SEMPRE em Fahrenheit, nunca em Celsius", o modelo trata como regra fixa — mesmo que o usuário peça em Celsius.

**Exercícios:**
- **1.1 Tornar o loop visível com hooks:** usar `RunHooks` para registrar cada chamada ao modelo e cada tool. ✅ `agente_loop.py`
- **1.2 Forçar e tratar `MaxTurnsExceeded`:** dar instruções que peçam para sempre consultar a ferramenta de novo; observar que a instrução em texto, sozinha, não impede o estouro — é o `max_turns` que corta. ✅ `agente_loop_max.py`
- **1.3 Clima completo (temperatura + vento):** a partir do agente de clima em Fahrenheit, acrescentar velocidade do vento (a mesma chamada à Open-Meteo devolve isso). ✅ `agente_clima_vento.py`

### Exemplos implementados — `aula3/agente_loop.py` e `agente_loop_max.py`

**`agente_loop.py`** (slides 6, 8, 9, 10):
- Subclasse de `RunHooks` (`LoopHooks`) com `on_llm_start/end`, `on_tool_start/end`, `on_agent_start/end` — métodos **`async`** (é assim que o SDK os declara).
- **Exemplo real (slide 9):** `get_temperatura` (Open-Meteo) + `converter_para_fahrenheit` — o modelo decide a ordem das tools, turno a turno; nenhuma linha do código encadeia as chamadas.
- **`on_agent_start` ≠ turno (slide 8):** com um único agente (sem handoff), ele dispara **uma vez só**, mesmo com várias chamadas ao modelo (o log conta `llm_calls`).
- **Instruções > pedido do usuário (slide 10):** mesmo que o usuário peça "em Celsius", as `instructions` ("SEMPRE em Fahrenheit") vencem — o log mostra a resposta em °F.

**`agente_loop_max.py`** (slide 7):
- Instrução que manda "SEMPRE consultar a ferramenta de novo".
- `Runner.run_sync(..., max_turns=N)`: com `N` baixo, dispara `MaxTurnsExceeded`; com `N` alto, o agente conclui. Demonstra que **quem corta o loop é o `max_turns`**, não a instrução.

**`agente_clima_vento.py`** (slide 11 — desafio 1.3):
- `get_clima` faz **uma única chamada** à Open-Meteo com `current="temperature_2m,wind_speed_10m"`, devolvendo temperatura e vento juntos.
- O agente converte a temperatura para Fahrenheit (`converter_para_fahrenheit`) e informa também a velocidade do vento.

**Como rodar (da raiz):**
```bash
source venv/bin/activate
python -m aula3.agente_loop
python -m aula3.agente_loop_max
python -m aula3.agente_clima_vento
```

---

## 2. Hooks — Referência e Famílias

**Teoria.** Hooks são sensores fixados em pontos exatos do loop: não mudam o que o agente faz, só avisam quando cada evento acontece. São ótimos para logging, auditoria e métricas.

**Duas famílias:**
- **`RunHooks`** — passado uma vez para o `Runner.run`/`run_sync`, enxerga o run inteiro, inclusive a troca de agente por handoff. Ex.: `on_llm_start(ctx, agent, system_prompt, input_items)` dispara antes de **cada** chamada ao modelo.
- **`AgentHooks`** — `agent.hooks = ...` em cada `Agent`; amarrado a um agente só, útil quando cada especialista de um handoff precisa de um log diferente. **Atenção:** os nomes **não** são idênticos entre as duas famílias.

**Ordem de disparo (num turno com 1 ferramenta):** `RunHooks` e `AgentHooks` disparam em paralelo para o mesmo evento; a ordem documentada é **RunHook primeiro, depois AgentHook**.

**Exemplos:** `agente_hook1.py`, `agente_hook2.py` (exemplos do professor — `RunHooks`) e `agente_hook3.py` (`AgentHooks` via `agent.hooks = ...`, demonstrando a ordem **RUN → AGENTE** para o mesmo evento).

---

## 3. Critérios de Parada

**Teoria.** Três formas diferentes de dizer "pare", como a um funcionário: um limite rígido de tentativas, ele mesmo declarar "terminei", ou um prazo de parede que ninguém pode estourar.

| Mecanismo | Onde roda | Problema que resolve |
|---|---|---|
| `max_turns` | **Dentro** do `Runner`, conta iterações do loop; dispara `MaxTurnsExceeded` | "o agente está preso repetindo ferramenta" |
| Sucesso declarado | **Fora** do `Runner`, um loop externo chama `run_sync` várias vezes | terminar quando o agente declarar conclusão |
| Timeout de parede | **Fora**, com `asyncio.wait_for` | nunca estourar um prazo real |

**Exercícios:**
- **3.1 Sucesso declarado (loop externo com `output_type`):** um loop por fora chama `Runner.run_sync` várias vezes; é o próprio agente — via um campo booleano na saída (ex.: `concluido: bool`) — que declara que terminou. ✅ `agente_parada.py`
- **3.2 Timeout de parede com `asyncio.wait_for`:** função assíncrona que roda um agente com limite de N segundos, usando `asyncio.wait_for` sobre `Runner.run`. ✅ `agente_parada_timeout.py`
- **3.3 Confirmação dupla antes de parar:** o 3.1 parava assim que `concluido=True` aparecesse uma vez — o que pode ser cedo demais. Alterar `investigar()` para só parar quando a conclusão for confirmada duas vezes. ✅ `agente_parada_dupla.py`

---

## 4. Retries e Resiliência

**Teoria.** Uma ferramenta que falha é como um telefone que não atende: desligar na hora não resolve, mas discar sem parar também não. É preciso uma estratégia — esperar um pouco mais a cada tentativa, e nunca fazer a mesma tentativa repetida quando a ação **escreve** dados.

**Backoff exponencial:** a ferramenta continua sendo uma função Python comum — o retry é só um `for` por dentro dela. O modelo nem sabe que houve tentativas: só vê o resultado final, ou o erro, se todas as tentativas falharem.

**Retry sem idempotência é perigoso:** repetir uma **leitura** é seguro (o segundo resultado só substitui o primeiro); repetir uma **escrita** (registrar ocorrência, disparar ofício) nem sempre — pode causar dano. Por isso, **idempotência** é essencial.

**O modelo não tem relógio / nem cotação em tempo real:**
- **Data:** injete a data real nas `instructions` (dá para calcular em Python).
- **Cotação:** vem de fora do código e muda a cada minuto → injete por uma **ferramenta**.

**Exercícios:**
- **4.1 Retry manual com backoff exponencial:** implementar o retry com pausa crescente dentro da ferramenta. ✅ `agente_retry.py`
- **4.2 Idempotência ao registrar uma ocorrência:** criar `registrar_ocorrencia(tipo, local, data)` que simule gravar num "banco" (dicionário em memória) e use uma chave de idempotência para não duplicar. ✅ `agente_retry_idempotencia.py`
- **Injeção de dado real (slide 25):** o modelo não tem relógio — injete a **data real** nas `instructions`. ✅ `agente_data.py`

---

## 5. Autonomia e Freio Humano

**Teoria.** É o "freio humano": um caixa que pode preparar um estorno, mas precisa da chave do supervisor antes da gaveta abrir. `needs_approval=True` faz literalmente isso: pausa a execução até alguém decidir.

**Mecânica:** a ferramenta continua uma função comum — `needs_approval` é só um parâmetro a mais no decorator. O loop `while resultado.interruptions:` é o "laço de aprovação": ele só continua quando a aprovação é dada.

**Autonomia graduada (um só mecanismo, três níveis):**
| Nível | Comportamento | Quando usar |
|---|---|---|
| Sem `needs_approval` | a ferramenta roda livre | seguro repetir, sem efeito consequente (leituras, cálculos) |
| `needs_approval=True` | pausa **sempre**, independente do argumento | ações consequentes |
| Aprovação condicional / `always_approve` | decide no código quando pausar | ação sensível só em certos casos |

**Exercícios:**
- **5.1 `needs_approval=True` (pausa sempre):** implementar o "laço de aprovação" com `while resultado.interruptions`. ✅ `agente_aprovacao.py`
- **5.2 Aprovação condicional:** ferramenta `enviar_notificacao(destinatario, mensagem)` que só exige aprovação quando a palavra "urgente" aparece na mensagem. ✅ `agente_aprovacao.py` (via `needs_approval=callable`)
- **5.3 Aprovação "para o resto da execução" (`always_approve`):** pedir ao agente para cancelar **três** ocorrências na mesma mensagem ("Cancele as ocorrências 4821, 4822 e 4823") com aprovação que vale para a execução inteira. ✅ `agente_aprovacao.py`

---

## 6. Observando o Loop ao Vivo (Streaming)

**Teoria.** Em vez de esperar o relatório do funcionário no fim do expediente (hooks), acompanha-se cada decisão e cada token **ao vivo**, enquanto o loop roda.

**Hooks vs Streaming:**
- **Hooks** — você define uma classe, o SDK chama os métodos sozinho. Bom para logging, auditoria, métricas (coisas que rodam por fora, sem UI acoplada).
- **Streaming** — você itera um `async for` e decide o que fazer com cada evento. Bom para UI ao vivo.

**Tipos de evento (de novo):** `run_item_stream_event` avisa cada ferramenta chamada/resultado (o mesmo que `on_tool_start`/`on_tool_end` faziam via hooks); `raw_response_event` entrega os tokens de texto.

**Exercícios:**
- **6.1 Contar turnos e ver tokens ao mesmo tempo:** um único `async for` cobre as duas coisas. ✅ `agente_loop_stream.py`
- **6.2 Streaming + aprovação humana juntos:** usar a ferramenta `cancelar_ocorrencia` (`needs_approval=True`) da Seção 5, mas com `Runner.run_streamed` em vez de `Runner.run`; drenar os eventos (incluindo a interrupção de aprovação). ✅ `agente_loop_stream.py`
- **6.3 Triagem streamada (três tipos de evento juntos):** triador (`handoffs=[...]`) com dois especialistas tratando `agent_updated_stream_event` + `run_item_stream_event` + `raw_response_event`. ✅ `agente_loop_stream.py`

---

## 7. Loop com Decisões Encadeadas

**Teoria.** O "investigador que não segue um roteiro fixo": decide, caso a caso, qual sistema consultar primeiro conforme o que já sabe, e para assim que julga ter o suficiente. Nenhum fluxograma escrito à mão decide por ele.

**Duas fontes reais, uma decisão do modelo:** `consultar_cnpj` e `consultar_ddd` são duas ferramentas independentes, sem relação escrita no código. Quem decide chamar uma, a outra, ou as duas — e em que ordem — é o modelo.

**O que estava embutido nesta seção (cada peça já vista, agora somada):**
- Várias tools independentes (Aula 1) — o modelo decide sozinho quais usar.
- Contagem de turno via hooks (Seção 1) — para ver a ordem das decisões acontecendo.
- Escalada/estratégia de erro (Seção 4) — retry e idempotência.

**Exercícios:**
- **7.1 Duas fontes, uma decisão:** `consultar_cnpj` + `consultar_ddd`, e observar a ordem que o modelo escolhe. ✅ `agente_investigador.py`
- **7.2 Apoio completo — investigar e só então registrar:** agente com três ferramentas — `consultar_cnpj`, `consultar_endereco` (Nominatim — lembre do header `User-Agent` obrigatório) e `registrar_ocorrencia` — e escalada quando algo falhar. ✅ `agente_investigador.py`
- **7.3 CNPJ resiliente dentro do loop encadeado:** a consulta ao CNPJ pode devolver **429 (rate limit)** — a BrasilAPI é gratuita e tem limite. Reescrever `consultar_cnpj` com retry/backoff (Seção 4) dentro do loop encadeado. ✅ `agente_investigador.py`

---

## 8. Resumo dos Conceitos-Chave

- **Observar:** hooks (logging/auditoria/métricas) e streaming (UI ao vivo).
- **Parar:** `max_turns` (dentro), sucesso declarado via `output_type` (fora), timeout de parede (`asyncio.wait_for`).
- **Sobreviver:** backoff exponencial + idempotência para escritas; injetar dado real (data via instructions, cotação via tool).
- **Frear:** `needs_approval` com autonomia graduada (livre / pausa sempre / condicional).
- **Decidir em cadeia:** múltiplas tools independentes, ordem escolhida pelo modelo, turno a turno.

---

## 9. Roteiro de Implementação Sugerido

1. **Seção 1 + 2 — hooks:** `agente_loop.py` (RunHooks) + desafio do `MaxTurnsExceeded`; exemplos de RunHooks vs AgentHooks.
2. **Seção 3 — critérios de parada:** `agente_stop.py` (sucesso declarado, timeout, confirmação dupla).
3. **Seção 4 — retries:** `agente_retry.py` (backoff + idempotência) + injeção de data/cotação.
4. **Seção 5 — autonomia:** `agente_aprovacao.py` (`needs_approval`, condicional, `always_approve`).
5. **Seção 6 — streaming:** `agente_loop_stream.py` (eventos ao vivo + aprovação + triagem).
6. **Seção 7 — decisões encadeadas:** `agente_investigador.py` (CNPJ + DDD + Nominatim + registro, com retry de 429).

> Cada exemplo deve seguir o padrão do projeto: `from provedor import configurar, modelo, rodar` e `model=modelo()` para evitar o erro de modelo padrão do SDK.

---

## 10. Implementação Completa — Arquivos e Como Rodar

Todas as seções foram implementadas. Arquivos em `aula3/`:

| Arquivo | Seção | O que faz |
|---|---|---|
| `agente_hook1.py` / `agente_hook2.py` | 1 | Exemplos do professor (`RunHooks`): `on_llm_start`, turnos, tools |
| `agente_hook3.py` | 2 | `AgentHooks` (`agent.hooks=...`) + ordem **RunHook → AgentHook** |
| `agente_loop.py` | 1 | Hooks + loop visível + conversão encadeada + instruções > pedido |
| `agente_loop_max.py` | 1 | `MaxTurnsExceeded` (1.2) |
| `agente_clima_vento.py` | 1 | Clima completo: temperatura + vento (1.3) |
| `agente_parada.py` | 3 | Sucesso declarado via `output_type` (3.1) |
| `agente_parada_timeout.py` | 3 | Timeout de parede com `asyncio.wait_for` (3.2) |
| `agente_parada_dupla.py` | 3 | Confirmação dupla antes de parar (3.3) |
| `agente_retry.py` | 4 | Retry com backoff exponencial (4.1) |
| `agente_retry_idempotencia.py` | 4 | Idempotência ao registrar ocorrência (4.2) |
| `agente_data.py` | 4 | Injetar a data real nas `instructions` (slide 25) |
| `agente_aprovacao.py` | 5 | `needs_approval` (5.1), condicional (5.2), `always_approve` (5.3) |
| `agente_loop_stream.py` | 6 | Streaming: turnos+tokens (6.1), + aprovação (6.2), triagem (6.3) |
| `agente_investigador.py` | 7 | CNPJ+DDD (7.1), investigar+registrar (7.2), retry 429 (7.3) |

### Como rodar (da raiz, com a `venv` ativada)

```bash
cd ~/Documentos/pos_graduacao/11_Sistem_MultiAgentes
source venv/bin/activate

# também funciona execução direta: python aula3/arquivo.py
python -m aula3.agente_loop
python -m aula3.agente_loop_max
python -m aula3.agente_clima_vento
python -m aula3.agente_hook3
python -m aula3.agente_parada
python -m aula3.agente_parada_timeout
python -m aula3.agente_parada_dupla
python -m aula3.agente_retry
python -m aula3.agente_retry_idempotencia
python -m aula3.agente_data
python -m aula3.agente_aprovacao
python -m aula3.agente_loop_stream
python -m aula3.agente_investigador
```

### Exposição na API (FastAPI da `aula2`)

Exemplos não-interativos da Aula 3 também estão disponíveis na API:

```bash
uvicorn aula2.main:app --reload
# em outro terminal:
curl -X POST http://127.0.0.1:8000/loop -H "Content-Type: application/json" -d '{"mensagem":"Qual a temperatura em São Paulo?"}'
curl -X POST http://127.0.0.1:8000/clima-vento -H "Content-Type: application/json" -d '{"mensagem":"Como está o clima em Brasília?"}'
```

> Aprovação (`needs_approval`) e streaming ficam como **scripts**, pois exigem interação humana/SSE, não cabem num `POST` simples.
