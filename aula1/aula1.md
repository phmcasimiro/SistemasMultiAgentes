
# Aula 1: Fundamentos de Sistemas Multiagentes — Da Infraestrutura aos Agentes com Ferramentas

Esta aula consolida os conceitos teóricos e a engenharia de software por trás do ciclo inicial da disciplina. O objetivo é compreender o que transforma um modelo de linguagem em um agente autônomo, como desacoplar provedores de inferência e como evoluir da simples geração textual para a execução determinística de ferramentas externas (*Tool Calling*).

---

## 1. O que Diferencia um LLM de um Agente de IA?

Um Modelo de Linguagem de Grande Porte (LLM) isolado é uma função matemática probabilística que recebe uma sequência de tokens e calcula a distribuição dos próximos tokens. Ele é **stateless** (sem memória persistente) e **passivo** (responde estritamente a um estímulo).

Um **Agente de IA** é um sistema computacional que utiliza o LLM como núcleo decisório, orquestrado por um runtime que gerencia contexto, ferramentas e objetivos:

| Dimensão | LLM Convencional (ex: `chat.completions`) | Agente de IA (ex: `Agent` + `Runner`) |
|---|---|---|
| **Comportamento** | Passivo e reativo a cada chamada. | Orientado a objetivos (*goal-oriented*) e sequencial. |
| **Memória** | Inexistente (requer envio manual de todo o histórico a cada chamada). | Gerenciada pelo ciclo de vida do framework (*conversation state*). |
| **Identidade** | Neutra até receber um `system prompt`. | Persona formal com restrições e diretrizes (`instructions`). |
| **Ação no Mundo** | Limitada à emissão de texto/código. | Executa funções Python, consulta APIs e interage com o ambiente. |
| **Orquestração** | Tratamento manual de respostas HTTP e exceções. | Runtime de controle (`Runner`) que gerencia turnos e execução de chamadas. |

---

## 2. A Camada de Infraestrutura: Desacoplamento de Provedores (`provedor.py`)

Para evitar dependência exclusiva de fornecedor (*vendor lock-in*) e suportar tanto inferência local quanto em nuvem, a inicialização dos clientes é isolada no módulo `provedor.py`:

```python
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_default_openai_key,
    set_tracing_disabled,
)

load_dotenv()

# Provedor atualmente ativo (atualizado por configurar()).
ATIVO = "openai"

RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"


def _configurar_ollama() -> None:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    # A api_key é obrigatória no construtor, mas o Ollama a ignora.
    cliente = AsyncOpenAI(base_url=base_url, api_key="ollama")
    set_default_openai_client(cliente)        # todas as chamadas vão para o Ollama
    set_default_openai_api("chat_completions")  # Ollama não implementa a Responses API
    set_tracing_disabled(True)                 # sem envio de traces para a OpenAI


def _configurar_zen() -> None:
    # OpenCode Zen: gateway OpenAI-compatível (rota /chat/completions).
    base_url = os.getenv("OPENAI_BASE_URL", "https://opencode.ai/zen/v1")
    cliente = AsyncOpenAI(base_url=base_url, api_key=os.getenv("OPENAI_API_KEY"))
    set_default_openai_client(cliente)         # todas as chamadas vão para o Zen
    set_default_openai_api("chat_completions")  # Zen serve por esta rota
    set_tracing_disabled(True)                 # sem envio de traces para a OpenAI


def configurar(provedor: str | None = None) -> str:
    """Aplica a configuração do provedor escolhido no `.env`. Devolve o nome dele."""
    global ATIVO
    provedor = (provedor or os.getenv("PROVEDOR", "openai")).strip().lower()
    ATIVO = provedor

    if provedor == "ollama":
        _configurar_ollama()
    elif provedor == "zen":
        _configurar_zen()
    else:
        # Caminho padrão: OpenAI de verdade.
        set_default_openai_key(os.getenv("OPENAI_API_KEY"))

    return provedor


def modelo() -> str:
    """Nome do modelo do provedor ativo (zen -> OPENAI_MODEL; senão -> OLLAMA_MODEL)."""
    if ATIVO == "zen":
        return os.getenv("OPENAI_MODEL", "deepseek-v4-flash")
    return os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def cair_para_ollama() -> None:
    """Força o recuo de segurança para o Ollama local."""
    configurar("ollama")


def rodar(agente_fabrica, mensagem):
    """Executa o agente via Runner. Em falha do provedor Zen, recua para o Ollama local.

    `agente_fabrica` é uma função sem argumentos que devolve um `Agent` construído com
    `model=modelo()`, permitindo reconstruí-lo com o modelo correto após o recuo.
    """
    try:
        return Runner.run_sync(agente_fabrica(), mensagem)
    except Exception as exc:
        if ATIVO != "zen":
            raise
        print(f"{RED}[FALHA - zen]{RESET} {exc}")
        print(f"{YELLOW}[RECUO]{RESET} Alternando para Ollama local e tentando novamente...")
        cair_para_ollama()
        return Runner.run_sync(agente_fabrica(), mensagem)
```

### Decisões Críticas de Arquitetura:

* **Padronização sobre a API OpenAI:** Servidores locais (Ollama, vLLM) e provedores em nuvem (OpenCode Zen, Gemini, DeepSeek) adotam a especificação REST da OpenAI (`/v1`), permitindo reutilizar o mesmo SDK apenas alterando a `base_url`.
* **`set_default_openai_api("chat_completions")`:** O Agents SDK tenta usar por padrão a rota `/responses`. O Ollama, o Zen e endpoints de compatibilidade implementam apenas a rota consolidada `/v1/chat/completions`. Esta diretiva evita erros `404 Not Found`.
* **`set_tracing_disabled(True)`:** Previne tentativas do SDK de exportar telemetria para a plataforma da OpenAI usando chaves locais ou inválidas, o que geraria falhas `401 Unauthorized` em segundo plano.
* **`modelo()` e `rodar()` — desacoplamento de modelo + resiliência:** Os agentes não fixam mais o nome do modelo; eles o obtêm via `modelo()`, que retorna `OPENAI_MODEL` quando o provedor ativo é o Zen e `OLLAMA_MODEL` caso contrário. O runner `rodar()` tenta a chamada pelo provedor principal (Zen) e, diante de qualquer exceção, **recua automaticamente para o Ollama local** (`cair_para_ollama()`), reconstruindo o agente com o modelo correto antes da segunda tentativa.

---

## 3. A Evolução Prática dos Agentes: Do Texto às Ferramentas

O laboratório desenvolve as capacidades de um agente através de quatro fases incrementais. Antes de adotar o Agents SDK, porém, o percurso passa por uma **Fase 0** que implementa a "memória" e a persona de um agente manualmente, usando apenas o cliente compatível com a API OpenAI:

### Fase 0: LLM Puro com Memória Manual (`agente1_gemini.py`)

Este arquivo antecede o SDK e responde à pergunta central da seção 1: *o que falta a um LLM para virar agente?* Aqui, a persona, o histórico e a orquestração são construídos à mão sobre o cliente `OpenAI` (endereçado ao Gemini via `base_url`).

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Cliente compatível com o padrão OpenAI, apontando para o Gemini:
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

class Agente:
    def __init__(self, nome: str, papel: str):
        self.nome = nome
        self.modelo = os.getenv("OPENAI_MODEL")
        # "Memória" do agente: histórico iniciado com a persona (role 'system')
        self.mensagens = [{"role": "system", "content": papel}]

    def falar(self, entrada_usuario: str) -> str:
        self.mensagens.append({"role": "user", "content": entrada_usuario})
        resposta = client.chat.completions.create(
            model=self.modelo,
            messages=self.mensagens,
            max_tokens=500,
            temperature=0.7
        )
        conteudo = resposta.choices[0].message.content
        self.mensagens.append({"role": "assistant", "content": conteudo})
        return conteudo

if __name__ == "__main__":
    agente_pesquisa = Agente(
        nome="Investigador",
        papel="Você é um agente especialista em síntese de literatura e pesquisa acadêmica."
    )
    pergunta = "Qual é o principal desafio na coordenação de múltiplos agentes?"
    resposta = agente_pesquisa.falar(pergunta)
    print(f"[{agente_pesquisa.nome}]: {resposta}")
```

* **Memória manual (`self.mensagens`):** Como o LLM é `stateless`, todo o histórico é acumulado em uma lista e reenviado a cada chamada — o papel do `system` define a persona, e os turnos `user`/`assistant` preservam o contexto.
* **`base_url` para o Gemini:** O mesmo cliente `OpenAI` funciona contra `generativelanguage.googleapis.com/v1beta/openai/` sem trocar de SDK, reforçando o desacoplamento de provedores discutido na seção 2.
* **Limitação:** Sem o runtime de um framework, orquestração, ferramentas e retry ficam por conta do desenvolvedor — é o que o Agents SDK passa a automatizar nas fases seguintes.

---

### Fase 1: O Agente Básico e Encapsulamento de Execução (`agente1.py`)

Estabelece a estrutura mínima: instanciação do agente com modelo sensível ao provedor, encapsulamento no ponto de entrada `main()` e invocação síncrona via `Runner` (com recuo automático para Ollama).

```python
from agents import Agent
from provedor import configurar, modelo, rodar

# 1. Inicializa a infraestrutura de inferência definida no .env (Zen/Ollama/OpenAI)
configurar()


# 2. Fábrica do agente: declara o modelo do provedor ativo (modelo()).
def criar_agente() -> Agent:
    return Agent(
        name="Primeiro agente",
        instructions="Você é um agente de teste e responde de forma objetiva.",
        model=modelo()
    )


# 3. Ponto de entrada com a execução do Runner encapsulada e recuo para Ollama
def main():
    resultado = rodar(criar_agente, "Quem é o presidente da Argentina?")
    # .final_output aqui é uma string (não definimos output_type — isso vem no 4.x).
    print(resultado.final_output)

if __name__ == "__main__":
    main()
```

* **Encapsulamento no `main()`:** Garante que o script possa ser importado por outros módulos orquestradores sem disparar requisições automáticas no momento do `import`.
* **Fábrica `criar_agente()`:** Como o `rodar()` precisa reconstruir o agente com o modelo do provedor após um recuo, a construção é isolada em uma função sem argumentos que usa `model=modelo()`.
* **Saída direta (`resultado.final_output`):** Retorna o conteúdo textual final resolvido pelo loop do runner.

---

### Fase 2: Acesso ao Mundo Externo via Tool Calling (`agente2.py`)

Um LLM isolado desconhece fatos em tempo real ou dados dinâmicos. A anotação `@function_tool` transforma funções Python normais em schemas JSON (OpenAPI/JSON Schema) passados ao modelo.

```python
import requests
from agents import Agent, function_tool
from provedor import configurar, modelo, rodar

# 2. Inicializa a infraestrutura de inferência (Zen/Ollama/OpenAI)
configurar()


@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    # 1) cidade -> coordenadas (endpoint de geocoding)
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()

    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")

    local = geo["results"][0]

    # 2) coordenadas -> temperatura atual (endpoint de forecast)
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m",
            "timezone": "auto",
        },
    ).json()

    return prev["current"]["temperature_2m"]


# 3. Fábrica do agente com a ferramenta e o modelo do provedor ativo.
def criar_agente() -> Agent:
    return Agent(
        name="Agente Meteorológico",
        instructions="Você é um assistente meteorológico. Use a ferramenta get_temperatura sempre que o usuário perguntar sobre clima ou temperatura.",
        model=modelo(),
        tools=[get_temperatura],  # Registra a tool no agente
    )


def main():
    # 4. Execução do Runner (com recuo para Ollama) e impressão da resposta final
    resultado = rodar(criar_agente, "Qual é o clima em São Paulo?")
    print(resultado.final_output)


if __name__ == "__main__":
    main()
```

* **Assinatura e Docstrings:** O nome da função, as anotações de tipo (`cidade: str -> float`) e a docstring são lidos pelo framework para montar a especificação de chamada que orienta a IA.
* **Execução em Duas Etapas:** A tool encadeia geocodificação (nome $\rightarrow$ coordenadas) e consulta meteorológica de forma imperceptível para o usuário final.

---

### Fase 3: Vazamento de Sintaxe (*Tool Call Leakage*) e Defesa via Prompt (`agente3.py`)

Ao utilizar modelos menores executados localmente (como `llama3.2:3b`), é frequente o modelo emitir a sintaxe da ferramenta como texto cru na resposta em vez de disparar a invocação estruturada:
`{"name":"get_cotacao_dolar_hoje","parameters":{}}`

Para contornar essa fragilidade sem bibliotecas externas pesadas, adotam-se **prompts defensivos imperativos** e **feedback via ANSI nativo**:

```python
import requests
from agents import Agent, function_tool
from provedor import configurar, modelo, rodar

# Paleta de cores e estilos ANSI nativos (Linux / Bash)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
LINE = "─" * 70

# 1. Inicializa o provedor configurado no .env (Zen/Ollama/OpenAI)
configurar()


@function_tool
def get_cotacao_dolar_hoje() -> str:
    """Consulta a cotação oficial mais recente do Dólar (USD para BRL)

    utilizando o endpoint /latest da API Frankfurter.
    """
    print(f"\n{YELLOW}[TOOL EXECUTADA]{RESET} Consultando cotação mais recente na API Frankfurter...")

    url = "https://api.frankfurter.app/latest"
    params = {"from": "USD", "to": "BRL"}

    resposta = requests.get(url, params=params, timeout=10)

    if resposta.status_code != 200:
        raise ValueError(f"Falha na API Frankfurter: status {resposta.status_code}")

    dados = resposta.json()
    data_referencia = dados.get("date")
    taxa_brl = dados.get("rates", {}).get("BRL")

    if not taxa_brl:
        return "Cotação não disponível no momento."

    return f"Data de referência: {data_referencia} | 1 USD = R$ {taxa_brl:.4f}"


# 2. Fábrica do agente, focado exclusivamente na cotação do dia.
def criar_agente() -> Agent:
    return Agent(
        name="Analista de Câmbio",
        instructions=(
            "Você é um assistente financeiro direto e objetivo. "
            "Sua ÚNICA ação inicial DEVE ser executar a ferramenta 'get_cotacao_dolar_hoje'. "
            "NUNCA imprima JSON ou a sintaxe da tool como texto puro. "
            "Com o dado retornado, informe ao usuário a data de referência oficial do Banco Central Europeu "
            "e o valor da cotação do Dólar em Reais."
        ),
        model=modelo(),
        tools=[get_cotacao_dolar_hoje],
    )


# 3. Execução e saída com ANSI nativo
def main():
    print(f"\n{BLUE}{LINE}{RESET}")
    print(f"{BOLD}{CYAN}🤖 AGENTE EM EXECUÇÃO:{RESET} {criar_agente().name}")
    print(f"{DIM}Modelo ativo: {modelo()}{RESET}")
    print(f"{BLUE}{LINE}{RESET}")

    resultado = rodar(criar_agente, "Qual é a cotação do dólar hoje?")

    print(f"\n{BOLD}{GREEN}💵 COTAÇÃO ATUALIZADA:{RESET}\n")
    print(resultado.final_output)

    print(f"\n{BLUE}{LINE}{RESET}")
    print(f"{GREEN}✔ Execução concluída{RESET}")
    print(f"{BLUE}{LINE}{RESET}\n")


if __name__ == "__main__":
    main()
```

---

### Fase 4: Tool Calling Determinístico com Múltiplos Argumentos (`agente4.py`)

A solução arquitetural definitiva para o *Tool Call Leakage* não depende exclusivamente de engenharia de prompt, mas sim de configurações de inferência no nível da API: **`ModelSettings(tool_choice="required")`**.

```python
import requests

from agents import Agent, function_tool, ModelSettings
from provedor import configurar, modelo, rodar


# 1. Configuração do provedor
configurar()


# 2. Ferramenta
@function_tool
def converter_moeda(
    valor: float,
    moeda_origem: str,
    moeda_destino: str
) -> str:
    """Converte um valor entre duas moedas."""

    origem = moeda_origem.upper()
    destino = moeda_destino.upper()

    print(f"[TOOL] Convertendo {valor} {origem} para {destino}")

    resposta = requests.get(
        f"https://api.frankfurter.dev/v2/rate/{origem}/{destino}",
        timeout=10
    )

    resposta.raise_for_status()

    dados = resposta.json()

    cotacao = dados["rate"]
    convertido = valor * cotacao

    return (
        f"{valor:.2f} {origem} = "
        f"{convertido:.2f} {destino}"
    )


# 3. Fábrica do agente (modelo do provedor ativo)
def criar_agente() -> Agent:
    return Agent(
        name="Agente Financeiro",

        instructions=(
            "Você é um agente financeiro especializado em conversão de moedas. "
            "Sempre use converter_moeda para realizar conversões. "
            "Nunca invente cotações."
        ),

        model=modelo(),
        tools=[converter_moeda],

        model_settings=ModelSettings(
            tool_choice="required"
        )
    )


# 4. Execução
def main():

    print("Iniciando agente...")

    resultado = rodar(criar_agente, "Quanto são 100 dólares em reais?")

    print("\nResposta:")
    print(resultado.final_output)


# 5. Inicia o programa
if __name__ == "__main__":
    main()
```

* **Extração de Argumentos Estruturados:** O modelo extrai dinamicamente múltiplos parâmetros a partir do comando em linguagem natural (`valor=100.0`, `moeda_origem="USD"`, `moeda_destino="BRL"`).
* **`tool_choice="required"`:** Desativa a liberdade do LLM de responder com texto puro no primeiro turno, obrigando-o a emitir um payload estruturado para a ferramenta registrada.

---

## 4. Post-Mortem de Engenharia: Falhas e Diagnósticos

Durante o desenvolvimento do laboratório, foram identificados e mitigados os seguintes pontos de falha:

* **Falha de Resolução de Domínio (`Name or service not known`):**
* *Causa:* Uso de placeholders de documentação no `.env` (ex.: `.example`).
* *Observação:* O arquivo `.env.example` neste repositório não é um template estático — ele é um script bash que regenera o `.env` via heredoc e roda `pip freeze > requirements.txt`. Confirme que os endpoints apontados no `.env` gerado estão ativos (`localhost:11434` ou URLs válidas de provedores) e que a `OPENAI_API_KEY` real não foi commitada.
* *Solução:* Apontar para endpoints válidos (`localhost:11434` ou URLs ativas de provedores).
* **Erro 404 no SDK (`client.responses.create`):**
* *Causa:* Descompasso entre a nova Responses API exigida pelo SDK e servidores locais.
* *Solução:* Executar `set_default_openai_api("chat_completions")` no setup do cliente.
* **Erro 401 de Telemetria (`Tracing client error 401`):**
* *Causa:* O framework tenta submeter métricas para a nuvem da OpenAI com chaves não autorizadas.
* *Solução:* Desabilitar o rastreio via `set_tracing_disabled(True)`.
* **Modelo Não Encontrado (`model 'gpt-...' not found`):**
* *Causa:* Instanciar `Agent()` omitindo o argumento `model` faz o SDK adotar modelos padrão proprietários da OpenAI.
* *Solução:* Declarar o modelo explicitamente via `model=modelo()`, que resolve o nome do modelo do provedor ativo (Zen ou Ollama).
* **Falha do provedor principal (`[FALHA - zen]` → `[RECUO]`):**
* *Causa:* O OpenCode Zen pode estar inacessível, com cota esgotada ou com chave inválida.
* *Solução:* O runner `rodar()` captura a exceção, chama `cair_para_ollama()` e re-executa o agente com o modelo local `llama3.2:3b`, garantindo degradação graciosa.
* **Vazamento de Tool Call (*Tool Call Leakage*):**
* *Causa:* Modelos compactos (ex.: 3B) convertem a intenção de execução em texto literal.
* *Solução:* Aplicar `ModelSettings(tool_choice="required")` e reforçar a restrição nas instruções do agente.

---

## 5. Nuvem vs. Local na Disciplina de Agentes

A escolha do motor de inferência equilibra capacidade analítica e restrições operacionais:

* **Modelos em Nuvem (ex: OpenCode Zen / Gemini Flash / GPT-4o-mini):**
* *Vantagens:* Rigor sintático imediato para esquemas complexos e baixa ocorrência de vazamento de ferramentas.
* *Desvantagens:* Dependência de conectividade, risco de esgotamento de cotas de requisição (RPM) e latência de rede.
* **Modelos Locais (ex: Ollama com Llama 3.2 3B):**
* *Vantagens:* Custo zero por token, isolamento de dados na máquina e ausência de limites comerciais de taxa.
* *Desvantagens:* Exigem diretivas de prompt mais estritas e controle determinístico (`tool_choice="required"`) para garantir a invocação de ferramentas.
* **Estratégia Híbrida (Zen + fallback Ollama):** O laboratório adota o OpenCode Zen como provedor principal e usa o Ollama local como reserva automática. Na indisponibilidade do Zen, o runner `rodar()` reconfigura o cliente e reconstitui o agente com o modelo local — as ferramentas (`@function_tool`) são idênticas nos dois provedores, então a degradação é transparente para o usuário final.

> **Multiplicação de Chamadas em Sistemas Multiagentes:** Em uma arquitetura com $N$ agentes operando cooperativamente em $R$ rodadas com ferramentas, cada solicitação gera pelo menos $N \times R$ chamadas de inferência. Ambientes locais garantem previsibilidade e custo zero para a depuração de fluxos complexos antes da publicação em nuvem.

---

## 6. Mapa de Implementação vs. Teoria do Professor

O deck `aula1/TeoriaAula1` organiza o curso em **9 seções + extra**, cada uma somando uma capacidade ao mesmo "funcionário". A tabela abaixo cruza cada seção com o que **já está implementado** e o que **ainda falta**.

| # | Capacidade (deck) | Arquivo(s) | Status |
|---|---|---|---|
| 1 | Responder — primeiro agente | `agente1.py` | ✅ Implementado |
| 2 | Usar ferramentas (tools) | `agente2.py`, `agente3.py`, `agente4.py` | ✅ Parcial (Open-Meteo + Frankfurter; faltam ViaCEP/CNPJ) |
| 3 | Encaminhar (handoff) | — | ⏳ Pendente em `aula1` (feito em `aula2`) |
| 4 | Saída em formato fixo (`output_type`) | — | ⏳ Pendente em `aula1` (feito em `aula2`) |
| 5 | Memória de sessão (`SQLiteSession`) | — | ⏳ Pendente |
| 6 | Guardrails (travas de segurança) | — | ⏳ Pendente |
| 7 | Streaming (resposta em tempo real) | — | ⏳ Pendente |
| 8 | Integrador (tudo junto) | — | ⏳ Pendente |
| 9 | Limites, segurança e produção | — | ⏳ Pendente |
| Extra | Expor como API (FastAPI) | `main.py` (`aula2`) | ✅ Feito em `aula2` |

**Convenção adotada neste laboratório:** o professor usa `OPENAI_DEFAULT_MODEL` no `.env` e **não passa `model=` no código**. Aqui seguimos o padrão explícito `model=modelo()`, que resolve o modelo do provedor ativo (Zen/Ollama) e evita o erro de "model not found". As duas abordagens são válidas; a nossa é mais explícita e resiliente.

---

## 7. Exercícios Práticos e Explicações Teóricas

Cada seção do deck propõe exercícios. Abaixo, os exercícios ganham contexto teórico e indicação de status.

### 7.1 Seção 1 — O Primeiro Agente ✅

**Teoria.** Um `Agent` é a definição de um funcionário: um modelo de linguagem + um conjunto de `instructions` (a "persona", que manda mais que o pedido do usuário). Sozinho ele não faz nada — quem executa é o `Runner`. `run_sync` devolve um objeto rico (`RunResult`), do qual se extrai o texto final com `.final_output`.

**Exercícios:**
- **1.1 Primeiro agente:** `Agent(name=..., instructions=...)` + `Runner.run_sync(...)`. Imprimir `resultado` (objeto inteiro) e `resultado.final_output` (só texto). ✅ `agente1.py`
- **1.2 Dois hábitos:** (1) usar `resultado.final_output`; (2) encapsular a execução em `main()`. ✅ `agente1.py`
- **1.1 Ollama:** o mesmo agente 100% local — muda apenas `PROVEDOR=ollama` no `.env` e o `model`. ✅ (via `provedor.py` + `modelo()`)

### 7.2 Seção 2 — Ferramentas (Tools) ✅ (parcial)

**Teoria.** `@function_tool` transforma uma função Python comum em ferramenta: o schema (JSON Schema/OpenAPI) é gerado a partir da **assinatura** e da **docstring**. Por isso a docstring não é enfeite — o modelo a lê para decidir *quando* e *como* usar a ferramenta. Durante a execução, o próprio modelo decide chamá-la.

**Exercícios:**
- **2.1 Primeira ferramenta:** `@function_tool` + `tools=[...]` no agente. ✅
- **2.2 API real (Open-Meteo):** geocodificação (nome → coordenadas) + forecast (coordenadas → temperatura). Se a cidade não existir, `raise ValueError(...)` — o SDK entrega o erro ao modelo. ✅ `agente2.py`
- **2.3 Câmbio (2 argumentos):** a ferramenta recebe `moeda_origem` e `moeda_destino`; o modelo extrai os dois da frase ("dólar em reais" → USD, BRL). ✅ `agente4.py` (e `agente3.py`)
- **2.4 CEP (ViaCEP) — ⏳ pendente:** consulta `https://viacep.com.br/ws/{cep}/json/`, limpa o CEP (com/sem hífen). **Pegadinha:** CEP inexistente não dá erro HTTP — vem `{"erro": "true"}`. Retorne logradouro, bairro, cidade e UF em texto; o modelo reescreve de forma natural.
- **2.5 CNPJ (BrasilAPI) + LGPD — ⏳ pendente:** consulta `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`. Retorne razão social, situação cadastral, atividade, endereço e o quadro de sócios (`qsa`). **Ponto LGPD:** os CPFs dos sócios já vêm mascarados pela fonte — a minimização acontece na origem.

### 7.3 Seção 3 — Handoff (Transferência entre Agentes) ⏳

**Teoria.** *Handoff* é a transferência de uma conversa de um agente para outro. Por baixo dos panos, cada agente disponível vira uma ferramenta `transfer_to_<nome>` que o agente de origem pode chamar. O triador tem `handoffs=[...]` em vez de `tools=[...]`, e a decisão é só linguagem natural — nenhum `if/else` de roteamento. `resultado.last_agent` diz quem respondeu.

**Exercícios:**
- **3.1 Triador + especialistas:** `handoffs=[especialista_a, especialista_b]`; imprimir `resultado.last_agent.name`.
- **3.2 Observar a transferência:** usar `handoff(agente, on_handoff=callback)` para registrar um `[LOG]` no momento da transferência (auditoria). O triador responde sozinho o trivial ("Bom dia!") e só encaminha dúvidas.
- **3.3 Central de Atendimento (handoff + tools):** dois especialistas, cada um com uma tool de API real (clima Open-Meteo, endereços ViaCEP), e um triador que só roteia.
- **3.4 Apoio à Investigação (Nominatim):** especialista cadastral (CNPJ/BrasilAPI) + um de georreferenciamento (Nominatim, endereço → coordenadas). **Atenção:** o Nominatim exige header `User-Agent` identificando a aplicação, senão bloqueia.
- **3.5 Custo de um 3º especialista:** adicionar telefonia (DDD via BrasilAPI) — ferramenta + agente + uma linha em `handoffs` + uma frase nas instruções. Nenhum `if/else`.

> Feito parcialmente em `aula2` (`agente_handoff.py` com `handoffs` e `agente_handoff2.py` com `as_tool`).

### 7.4 Seção 4 — Saída Estruturada (`output_type`) ⏳

**Teoria.** `output_type` obriga o modelo a devolver dados num formato fixo, validado por um modelo Pydantic, em vez de texto livre — um contrato que o resto do sistema consome sem *parsing* frágil de string. O SDK traduz o schema Pydantic em JSON Schema; `final_output` deixa de ser `str` e passa a ser uma instância do modelo declarado.

**Exercícios:**
- **4.1 `output_type` com Pydantic:** `class Evento(BaseModel): ...`; `participantes: int` volta como `int` de verdade (não `"12"`). No `Agent`, usar `output_type=Evento`.
- **4.2 Ocorrência — modelos aninhados + lista:** gerar um `Ocorrencia` com `tipo`, `data`, `local`, `resumo` e uma `list[Envolvido]`, onde `Envolvido` é um `BaseModel` com `nome` e `papel` (vítima/suspeito/testemunha). Percorrer a lista no final. ✅ `agente_bo.py` (em `aula2`)
- **4.3 Triagem — `Literal` + `bool`:** `categoria` e `prioridade` só aceitam valores de uma lista fechada (`Literal[...]`), mais um `bool urgente`. O SDK rejeita valores fora da lista; o `bool` volta como `bool` (dá para usar em `if t.urgente:`).

> Feito parcialmente em `aula2` (`agente_bo.py` e `agente_output.py`).

### 7.5 Seção 5 — Sessão / Memória de Conversa ⏳

**Teoria.** *Sessão* é a memória de conversa entre turnos. Sem ela, cada chamada ao `Runner` começa do zero. A `SQLiteSession` guarda o histórico sob um identificador e o reinjeta a cada novo turno. Sem `db_path`, ela é `:memory:` (mora na RAM); com `db_path=...`, persiste em arquivo.

**Exercícios:**
- **5.1 `SQLiteSession` entre turnos:** `sessao = SQLiteSession("id")`; passar `session=sessao` em cada `run_sync`. "Ela" do 2º turno só funciona com o histórico.
- **5.2 Sessão + ferramenta:** agente de clima com sessão; perguntar a temperatura de duas cidades e, no 3º turno, comparar qual está mais quente **sem repetir números** — a sessão guarda também os resultados das ferramentas.
- **5.3 Isolamento entre sessões:** duas sessões com ids distintos ("dois casos"); informar um dado na 1ª, perguntar na 2ª (não deve saber) e confirmar na 1ª (deve lembrar). O id impede vazamento de contexto — decisão de segurança, não detalhe técnico.
- **5.4 Coleta progressiva:** o usuário fornece tipo, local e data em turnos separados e, no fim, pede o resumo consolidado — só a sessão acumula.
- **5.5 Memória em arquivo:** `db_path=...` para a conversa sobreviver ao fim do programa. Detectar se é a 1ª execução (o `.db` ainda não existe) e rodar duas vezes para provar que o programa fechou entre elas.

### 7.6 Seção 6 — Guardrails (Travas de Segurança) ⏳

**Teoria.** Guardrails são travas que rodam em paralelo ao agente. Um `input_guardrail` inspeciona o pedido do usuário **antes** de gastar tokens com o agente principal; um `output_guardrail` inspeciona a resposta **antes** de ela sair. Se a trava detecta algo proibido, dispara o *tripwire* e a execução para com exceção.

**Exercícios:**
- **6.1 Input guardrail (Python puro):** `@input_guardrail` com uma lista de palavras proibidas; retornar `GuardrailFunctionOutput(output_info={}, tripwire_triggered=bool)`.
- **6.2 Input guardrail com LLM (LGPD):** um agente "verificador" (com `output_type`) classifica se a mensagem pede dados pessoais sensíveis de terceiros (CPF, endereço residencial, telefone); se sim, dispara o tripwire.
- **6.3 Output guardrail (regex, sem LLM):** `@output_guardrail` que inspeciona a resposta e dispara se ela contiver um CPF (regex Python puro). Exceção: `OutputGuardrailTripwireTriggered`.

### 7.7 Seção 7 — Streaming (Resposta em Tempo Real) ⏳

**Teoria.** Streaming é receber a resposta do agente em pedaços (eventos), à medida que o modelo gera cada token, em vez de esperar a resposta inteira pronta. `Runner.run_streamed` devolve um iterador assíncrono de eventos; `stream_events()` é um gerador assíncrono (`async for`).

**Exercícios:**
- **7.1 Tokens um a um:** `run_streamed` (sem `await`) + `stream_events()`; filtrar `event.type == "raw_response_event"` e `isinstance(event.data, ResponseTextDeltaEvent)`, imprimindo `event.data.delta`.
- **7.2 Streaming + ferramenta (ciclo de vida):** tratar `run_item_stream_event` para imprimir quando a tool é chamada (`name == "tool_called"`) e quando o resultado chega (`name == "tool_output"`, em `event.item.output`). Ordem: ferramenta acionada → dado voltando → resposta digitada.
- **7.3 Streaming + handoff:** tratar `agent_updated_stream_event` e imprimir `event.new_agent.name` quando o agente ativo mudar — torna visível o instante exato do handoff.

### 7.8 Seção 8 — Integrador (Tudo Junto) ⏳

**Teoria.** Não é uma capacidade nova do SDK, e sim a combinação das anteriores num único agente: **tools + handoff + saída estruturada + memória de sessão** — o atendimento completo. A observação do professor: quando um `guardrail` é `async` e usa `await Runner.run(...)`, o `run_sync` quebra — é preciso usar a versão assíncrona.

**Exercício:** montar um agente com `tools=[...]`, `input_guardrails=[...]`, `output_type=...` e uma `SQLiteSession`, e exercitar: turno 1 → ferramenta; turno 2 → memória; turno 3 → guardrail barra.

### 7.9 Seção 9 — Limites, Segurança e Produção ⏳

**Teoria.** Não é sobre uma classe do SDK, e sim sobre o que separa um protótipo de aula de um sistema em produção: tracing/observabilidade, custo e limites de uso, tratamento de erro, e onde os guardrails realmente importam quando o dado é sensível (LGPD).

**Conceitos-chave:**
- **O loop do agente e `max_turns`:** um turno = o modelo decide responder OU chamar ferramenta → se chamou, o `Runner` executa e devolve → decide de novo. `Runner.run(..., max_turns=N)`, padrão 10; estourou → `MaxTurnsExceeded`.
- **Prompt injection indireta (conteúdo das ferramentas):** a Seção 6 protege contra o que o cidadão digita; o ataque também vem de dentro — uma ferramenta lê um PDF/e-mail/página com "IGNORE suas instruções...". Para o modelo, dado e instrução chegam do mesmo jeito: como texto.
- **Quando NÃO usar um agente:** consulta determinística (validar CPF, buscar CEP, somar) → código comum: mais rápido, de graça, testável, sempre igual. Agente só quando é preciso entender linguagem ambígua ou decidir rota sem regra fixa.
- **Ação consequente exige aprovação humana:** quando uma ferramenta *escreve* (registra ocorrência, dispara ofício, altera cadastro), o padrão é: a ferramenta propõe → um humano aprova → só então roda.

### 7.10 Extra — Expor um Agente como API (FastAPI) ✅ (em `aula2`)

**Teoria.** FastAPI não substitui o `Agent` — é a porta HTTP de entrada. Uma rota recebe uma mensagem, chama `Runner.run_sync(agente, mensagem)` e devolve `resultado.final_output` em JSON. Arquitetura: `Cliente → FastAPI → Agent → Runner → LLM`. O Pydantic valida entrada/saída e o `/docs` (Swagger) documenta a integração. **Ponto-chave:** a API não chama a tool — o agente decide.

**Estrutura:** `provedor.py` (configuração) + `agente.py` (Agent + tool + `executar_agente(mensagem)`) + `main.py` (FastAPI com `POST /perguntar`).

**Exercícios:**
- **Desafio 1:** acrescentar `consultar_cotacao(moeda)` ao agente e testar: só clima, só cotação, os dois juntos, nenhum dos dois.
- **Desafio 2:** criar `POST /clima` chamando `consultar_clima()` direto e comparar com `POST /perguntar` — a mesma pergunta, duas arquiteturas.
- **Próximo passo:** a mesma API cresce para RAG ou rotear entre agentes especialistas (Supervisor + Agente A/B/C) sem mudar o contrato HTTP.

---

## 8. Roteiro Recomendado para Conclusão

Para alinhar o laboratório ao deck completo, a ordem sugerida das seções pendentes:

1. **Seção 2 — completar:** ViaCEP (2.4) e BrasilAPI/CNPJ (2.5) — reforçam o padrão de tools + tratamento de "erro" sem HTTP error.
2. **Seção 3 — handoff:** triador + especialistas, com callback de auditoria e o caso da investigação (Nominatim/DDD).
3. **Seção 4 — saída estruturada:** `Literal` + `bool` (Triagem) — complementa os modelos aninhados já feitos em `aula2`.
4. **Seção 5 — sessão:** memória entre turnos, isolamento por id e persistência em arquivo.
5. **Seções 6–7 — guardrails e streaming:** travas de LGPD (entrada/saída) e o ciclo de vida ao vivo.
6. **Seção 8 — integrador:** combinar tudo num único agente.
7. **Seção 9 — produção:** `max_turns`, defesa contra prompt injection indireta e o princípio de aprovação humana.
