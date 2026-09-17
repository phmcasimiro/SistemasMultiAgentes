# Aula 2: Sistemas Multiagentes — Orquestração com Handoffs e Agente como Ferramenta

Esta aula dá o passo central da disciplina de Sistemas Multiagentes: fazer múltiplos agentes cooperarem, delegando tarefas entre si. Ela se apoia na infraestrutura criada na aula 1 (`provedor.py`), mantendo o desacoplamento de provedores (OpenCode Zen + fallback Ollama).

---

## 1. Estrutura do Projeto

| Arquivo | Responsabilidade |
|---|---|
| `provedor.py` | Abstração de provedor (Zen/Ollama/OpenAI), `modelo()`, `rodar()` com recuo automático. |
| `primeiro_agente.py` | Agente básico (fábrica `criar_agente()` + `rodar()`). |
| `agente_handoff.py` | Orquestração por **handoff** (delegação de turno entre agentes). |
| `agente_handoff2.py` | Orquestração por **agente como ferramenta** (`as_tool`). |
| `agente_bo.py` | **Saída estruturada** (`output_type`) para extração de dados (Boletim de Ocorrência). |
| `agente_output.py` | **Saída estruturada** (`output_type`) para extração de dados de um evento (campos simples). |
| `agente_triagem.py` | **Saída estruturada** com `Literal[...]` + `bool` (valores fechados). |
| `agente_session.py` | **Memória** entre turnos com `SQLiteSession` (persistência em arquivo). |
| `agente_sessao2.py` | **Memória** + ferramenta de clima (comparação no 3º turno). |
| `agente_memoria.py` | **Memória** reutilizável (`executar_agente_memoria`) para a API. |
| `agente_isolamento.py` | **Isolamento** entre sessões (5.3). |
| `agente_coleta.py` | **Coleta progressiva** de dados (5.4). |
| `agente_guardrail.py` | **Guardrail de entrada** (input_guardrail com LLM + `output_type`). |
| `agente_output_guardrail.py` | **Guardrail de saída** (regex de CPF, sem LLM). |
| `agente_streaming.py` | **Streaming** (tokens + ciclo de vida da tool + handoff). |
| `agente_integrador.py` | **Integrador** (tool + sessão + guardrail + `output_type`). |
| `agente_handoff_callback.py` | **Handoff** com callback de auditoria (`on_handoff`). |
| `agente_producao.py` | **Produção** (`max_turns` + prompt injection indireta). |
| `main.py` | API REST (FastAPI) expondo os agentes. |
| `.env` | Configuração do provedor (Zen como padrão, Ollama como reserva). |

---

## 2. O Problema: um Agente Não Sabe de Tudo

Um único agente é limitado pelo seu contexto e instruções. Para responder perguntas de áreas distintas (matemática, história, etc.), a solução é **decompor o problema em especialistas** e ter um **agente orquestrador** (triador) que roteia cada pergunta para o especialista certo.

A aula apresenta **duas maneiras** de implementar essa coordenação:

---

## 3. Mecanismo 1: Handoff (Delegação de Turno) — `agente_handoff.py`

No *handoff*, o controle do turno é **transferido** de um agente para outro. O agente triador *decide* passar a vez e o `Runner` entrega a execução ao agente-destino, que passa a responder diretamente.

```python
from agents import Agent, Runner
from provedor import configurar, modelo

configurar()

agente_matematico = Agent(
    name="agente_matematico",
    instructions="Você é um especialista em matemática. Responda com precisão e clareza.",
    model=modelo(),
    handoff_description=("Se a pergunta for sobre matemática, eu devo responder."),
)

agente_historiador = Agent(
    name="agente_historiador",
    instructions="Você é um especialista em história. Responda com precisão e clareza.",
    model=modelo(),
    handoff_description=("Se a pergunta for sobre história, eu devo responder."),
)

agente_triador = Agent(
    name="agente_triador",
    instructions=" Você é um agente triador. Sua função é direcionar perguntas para o agente mais adequado com base no conteúdo da pergunta. "
    "Se a pergunta for sobre matemática, encaminhe para o agente_matematico. Se for sobre história, encaminhe para o agente_historiador. "
    "Se não se enquadrar em nenhuma dessas categorias, responda que não sabe.",
    model=modelo(),
    handoffs=[agente_matematico, agente_historiador],
)

def executar_agente_handoff(mensagem: str) -> str:
    resultado = Runner.run_sync(agente_triador, mensagem)
    return resultado.final_output
```

* **`handoff_description`:** texto que o agente triador lê para *saber quando* delegar a um especialista. É a "placa de sinalização" de cada destino.
* **`handoffs=[...]`:** lista de agentes disponíveis para delegação. O triador escolhe um deles, e o turno é transferido — o especialista responde diretamente ao usuário.
* **Saída do fluxo:** o resultado final vem do agente especialista que recebeu o turno.

---

## 4. Mecanismo 2: Agente como Ferramenta — `agente_handoff2.py`

Em vez de transferir o turno, o especialista é **empacotado como uma ferramenta** (`as_tool`). O triador mantém o controle e *invoca* o especialista como se fosse uma função externa, obtendo o retorno e decidindo a resposta final.

```python
# ============ HANDOFF 2 ===============
from agents import Agent, Runner
from provedor import configurar, modelo

configurar()

agente_matematico = Agent(
    name="agente_matematico",
    instructions="Você é um especialista em matemática. Responda com precisão e clareza.",
    model=modelo(),
)

agente_historiador = Agent(
    name="agente_historiador",
    instructions="Você é um especialista em história. Responda com precisão e clareza.",
    model=modelo(),
)

agente_triador = Agent(
    name="agente_triador",
    instructions=(
        " Você é um agente triador. Sua função é direcionar perguntas para o agente mais adequado com base no conteúdo da pergunta. "
        "Se a pergunta for sobre matemática, encaminhe para o agente_matematico. Se for sobre história, encaminhe para o agente_historiador. "
        "Se não se enquadrar em nenhuma dessas categorias, responda que não sabe."
    ),
    model=modelo(),
    tools=[
        agente_matematico.as_tool(
            tool_name="consultar_matematico",
            tool_description="Se a pergunta for sobre matemática, eu devo responder.",
        ),
        agente_historiador.as_tool(
            tool_name="consultar_historiador",
            tool_description="Se a pergunta for sobre história, eu devo responder.",
        )
    ]
)

def executar_agente_handoff2(mensagem: str) -> str:
    resultado = Runner.run_sync(agente_triador, mensagem)
    return resultado.final_output
```

* **`agente.as_tool(tool_name=..., tool_description=...)`:** transforma o agente especialista em uma ferramenta registrada nas `tools` do triador. O `tool_description` cumpre o papel do `handoff_description`: informa ao triador *quando* usar aquele especialista.
* **Fluxo:** o triador decide se chama `consultar_matematico` ou `consultar_historiador`; a resposta do especialista volta como resultado da ferramenta e o **triador** compõe a resposta final.
* **Diferença essencial:** no *handoff*, o especialista "assume" a resposta final; no *agente como ferramenta*, o triador continua no comando e apenas consome o retorno do especialista.

---

## 5. Mecanismo 3: Saída Estruturada com Modelos Aninhados — `agente_bo.py`

Até aqui os agentes devolviam **texto livre**. Para consumir os resultados de forma programática (ex.: gravar num banco, gerar um JSON), usa-se **`output_type`** do Agents SDK, que obriga o modelo a devolver um objeto tipado por Pydantic — inclusive com **modelos aninhados**.

```python
from pydantic import BaseModel
from agents import Agent
from provedor import configurar, modelo, rodar

configurar()


class Envolvido(BaseModel):
    nome: str
    papel: str  # ex.: 'vítima', 'suspeito', 'testemunha'


class Ocorrencia(BaseModel):
    tipo: str
    data: str
    local: str
    envolvidos: list[Envolvido]   # lista de modelos aninhados
    resumo: str


# Fábrica do agente: extrai dados estruturados via output_type.
def criar_agente() -> Agent:
    return Agent(
        name="agente_bo",
        instructions=(
            "Extraia os dados da ocorrência a partir do relato. "
            "Para cada pessoa citada, defina o papel (vítima, suspeito ou testemunha)."
        ),
        model=modelo(),
        output_type=Ocorrencia,
    )


def extrair_ocorrencia(texto: str) -> Ocorrencia:
    resultado = rodar(criar_agente, texto)
    return resultado.final_output
```

* **`output_type=Ocorrencia`:** o framework traduz o schema Pydantic em JSON Schema e instrui o modelo a retornar somente JSON válido conforme esse schema. O `final_output` passa a ser uma instância de `Ocorrencia`, não uma string.
* **Modelos aninhados (`list[Envolvido]`):** o agente identifica cada pessoa citada no relato e a classifica (vítima/suspeito/testemunha), gerando uma lista estruturada.
* **Consumo do resultado:** a instância pode ser serializada com `.model_dump()` (dict) ou `.model_dump_json()` (string), pronta para resposta HTTP ou persistência.

**Variação mais simples — `agente_output.py`:** o mesmo padrão, mas com um modelo de campos simples (`Evento`: `nome`, `data`, `local`, `participantes: int`), sem modelo aninhado. Útil quando os dados extraídos são planos.

```python
class Evento(BaseModel):
    nome: str
    data: str
    local: str
    participantes: int

def criar_agente() -> Agent:
    return Agent(
        name="Executor de eventos",
        instructions=(
            "Extraia as informações do evento a partir do texto fornecido pelo usuário. "
            "Preencha nome, data, local e a quantidade de participantes."
        ),
        model=modelo(),
        output_type=Evento,
    )
```

Exemplo de saída para o relato do professor:

```json
{
  "tipo": "furto de veículo",
  "data": "28/09",
  "local": "Quadra 303 da Asa Norte, Brasília (próximo à entrada do bloco B)",
  "envolvidos": [
    {"nome": "Camila Rodrigues", "papel": "vítima"},
    {"nome": "João Martins", "papel": "suspeito"},
    {"nome": "Antônio Ferreira", "papel": "testemunha"}
  ],
  "resumo": "Furto de veículo de cor prata, ocorrido por volta das 22h10."
}
```

---

## 6. API REST (`main.py`)

Os agentes são expostos por uma API FastAPI:

```python
from pydantic import BaseModel
from fastapi import FastAPI

from primeiro_agente import executar_agente
from agente_handoff import executar_agente_handoff
from agente_handoff2 import executar_agente_handoff2
from agente_bo import extrair_ocorrencia
from agente_output import executar_agente_output

app = FastAPI()

class Pergunta(BaseModel):
    mensagem: str

@app.get("/")
def inicio():
    return {"mensagem": "Olá mundo!"}

@app.post("/tools")
def perguntar_tools(pergunta: Pergunta):
    resultado = executar_agente(pergunta.mensagem)
    return {"pergunta": pergunta.mensagem, "mensagem": resultado}

@app.post("/handoff")
def perguntar_handoff(pergunta: Pergunta):
    resultado = executar_agente_handoff(pergunta.mensagem)
    return {"pergunta": pergunta.mensagem, "mensagem": resultado}

@app.post("/handoff2")
def perguntar_handoff2(pergunta: Pergunta):
    resultado = executar_agente_handoff2(pergunta.mensagem)
    return {"pergunta": pergunta.mensagem, "mensagem": resultado}

@app.post("/bo")
def extrair_bo(pergunta: Pergunta):
    ocorrencia = extrair_ocorrencia(pergunta.mensagem)
    return ocorrencia.model_dump()

@app.post("/output")
def extrair_output(pergunta: Pergunta):
    evento = executar_agente_output(pergunta.mensagem)
    return evento.model_dump()
```

* **`GET /`** — healthcheck.
* **`POST /tools`** — agente único (`primeiro_agente`).
* **`POST /handoff`** — orquestração por handoff (`agente_handoff`).
* **`POST /handoff2`** — orquestração por agente como ferramenta (`agente_handoff2`).
* **`POST /bo`** — extração estruturada de ocorrência (`agente_bo`); retorna um JSON conforme o schema `Ocorrencia`.
* **`POST /output`** — extração estruturada de evento (`agente_output`); retorna um JSON conforme o schema `Evento`.
* **`POST /memoria`** — agente com memória (`agente_memoria`); recebe `mensagem` + `sessao_id` e mantém o histórico por sessão.

---

## 7. Como Testar

```bash
# 1) Testar o agente único
python -c "from primeiro_agente import executar_agente; print(executar_agente('Qual é a capital do Brasil?'))"

# 2) Testar o handoff (delegação de turno)
python -c "from agente_handoff import executar_agente_handoff; print(executar_agente_handoff('Quanto é 7 vezes 8?'))"

# 3) Testar o agente como ferramenta
python -c "from agente_handoff2 import executar_agente_handoff2; print(executar_agente_handoff2('Em que ano foi a independência do Brasil?'))"

# 4) Testar a extração estruturada (agente_bo)
python -c "from agente_bo import extrair_ocorrencia; print(extrair_ocorrencia('No dia 28/09, ocorreu um furto de veículo. A vítima, Camila Rodrigues, ...').model_dump_json(indent=2))"

# 5) Testar a extração estruturada de evento (agente_output)
python -c "from agente_output import executar_agente_output; print(executar_agente_output('A reunião de planejamento será dia 15/10 na Enap, em Brasília, com 12 pessoas.').model_dump_json(indent=2))"

# 6) Subir a API
uvicorn main:app --reload
# em outro terminal:
curl -X POST http://127.0.0.1:8000/tools -H "Content-Type: application/json" -d '{"mensagem":"Quem descobriu o Brasil?"}'
curl -X POST http://127.0.0.1:8000/handoff -H "Content-Type: application/json" -d '{"mensagem":"Quanto é 9 vezes 6?"}'
curl -X POST http://127.0.0.1:8000/handoff2 -H "Content-Type: application/json" -d '{"mensagem":"Quem proclamou a independência do Brasil?"}'
curl -X POST http://127.0.0.1:8000/bo -H "Content-Type: application/json" -d '{"mensagem":"No dia 28/09, ocorreu um furto de veículo. A vítima, Camila Rodrigues, ..."}'
curl -X POST http://127.0.0.1:8000/output -H "Content-Type: application/json" -d '{"mensagem":"A reunião de planejamento será dia 15/10 na Enap, em Brasília, com 12 pessoas."}'
curl -X POST http://127.0.0.1:8000/memoria -H "Content-Type: application/json" -d '{"mensagem":"Qual a capital do Brasil?","sessao_id":"caso_a"}'
curl -X POST http://127.0.0.1:8000/memoria -H "Content-Type: application/json" -d '{"mensagem":"E qual é a população?","sessao_id":"caso_a"}'
```

**Demos das seções 5–9** (executar direto):

```bash
python agente_session.py        # memória entre turnos (arquivo)
python agente_sessao2.py        # memória + clima (comparação no 3º turno)
python agente_isolamento.py     # isolamento entre sessões (5.3)
python agente_coleta.py         # coleta progressiva (5.4)
python agente_triagem.py        # output_type com Literal + bool (4.3)
python agente_guardrail.py      # input guardrail com LLM (6.2)
python agente_output_guardrail.py  # output guardrail regex CPF (6.3)
python agente_streaming.py      # streaming (7.1-7.3)
python agente_integrador.py     # integrador (8)
python agente_handoff_callback.py  # handoff + callback (3.2)
python agente_producao.py       # max_turns + prompt injection (9)
```

---

## 8. Seções 5–9 do Professor: Memória, Guardrails, Streaming, Integrador e Produção

### 8.1 Memória de conversa — `SQLiteSession` (Seção 5)

Cada `Runner.run` é, por padrão, um atendente novo: o agente esquece o turno anterior. A `SQLiteSession(id)` guarda o histórico sob um identificador e o reinjeta a cada chamada. Sem `db_path` é `:memory:` (RAM); com `db_path` persiste em arquivo.

* **`agente_session.py`** — memória entre turnos com persistência em arquivo.
* **`agente_sessao2.py`** — memória + ferramenta de clima: no 3º turno o agente compara as duas cidades **sem nova chamada de API**.
* **`agente_memoria.py`** — função reutilizável `executar_agente_memoria(mensagem, sessao_id)` para a API (`POST /memoria`).
* **5.3 Isolamento** (`agente_isolamento.py`): dois ids distintos não vazam contexto entre si — o id da sessão é decisão de segurança, não detalhe técnico.
* **5.4 Coleta progressiva** (`agente_coleta.py`): o usuário dá tipo, local e data em turnos separados; só a sessão acumula para o resumo final.

### 8.2 Guardrails (Seção 6)

Travas que rodam em paralelo ao agente: um `input_guardrail` inspeciona o pedido **antes** de gastar tokens; um `output_guardrail` inspeciona a resposta **antes** de sair. Se a trava detecta algo proibido, dispara o *tripwire* e a execução para com exceção.

* **`agente_guardrail.py`** — `input_guardrail` com LLM: um agente classificador (`output_type`) avalia similaridade a tópicos proibidos e dispara o tripwire.
* **`agente_output_guardrail.py`** — `output_guardrail` com **regex** de CPF (sem LLM): barra respostas que vazam um CPF.

### 8.3 Streaming (Seção 7)

`Runner.run_streamed` devolve um iterador assíncrono de eventos. Filtramos os eventos de texto cru (`raw_response_event` + `ResponseTextDeltaEvent`) para "ver o agente digitando", e os eventos de itens (`run_item_stream_event`) para o ciclo de vida da ferramenta.

* **`agente_streaming.py`** — tokens um a um, ciclo de vida da tool (`tool_call_item` / `tool_call_output_item`) e o instante do handoff (`agent_updated_stream_event`).

### 8.4 Integrador (Seção 8)

Combina todas as capacidades num único agente: **tool + sessão + guardrail + `output_type`**. 

* **`agente_integrador.py`** — agente com ferramenta de clima, `input_guardrail` de LGPD, `SQLiteSession` e `output_type=Atendimento`. **Atenção:** como o guardrail é `async` e usa `await Runner.run(...)`, o `run_sync` **quebra** aqui — use a versão assíncrona.

### 8.5 Limites, segurança e produção (Seção 9)

* **`max_turns`** — um turno = o modelo decide responder OU chamar ferramenta. `Runner.run(..., max_turns=N)`, padrão 10; estourou → `MaxTurnsExceeded`.
* **Prompt injection indireta** — ataque que vem de *dentro* das ferramentas (um PDF/e-mail lido com "IGNORE suas instruções..."). Trate o conteúdo de ferramentas como dado não confiável.
* **Quando não usar um agente** — consulta determinística (validar CPF, somar) → código comum, mais rápido e testável.
* **Ação consequente exige aprovação humana** — quando a tool *escreve*, o padrão é: propõe → humano aprova → só então roda.
* **`agente_producao.py`** — demonstra `max_turns` (estourando o limite) e a defesa contra prompt injection.

---

## 9. Pontos de Atenção

* **Modelo explícito:** todo `Agent()` deve declarar `model=modelo()`. Omitir o `model` faz o SDK usar o modelo padrão (ex.: `gpt-5.6-luna`), que não é servido pelos provedores configurados — gera erro `404`/`500`.
* **Segurança:** a `OPENAI_API_KEY` real não deve ser commitada no `.env`; use variáveis de ambiente ou um arquivo ignorado pelo git.
* **`handoff_description` vs `tool_description`:** ambos orientam a decisão do triador; o primeiro é usado no mecanismo de *handoff*, o segundo no de *agente como ferramenta*.
* **Saída estruturada depende do modelo:** `output_type` exige que o provedor suporte *structured output* (JSON Schema). O `deepseek-v4-flash` do Zen suporta; modelos menores via Ollama podem apresentar menor fidelidade ao schema, então o `rodar()` (com recuo) deve ser usado com cautela quando há `output_type`.
