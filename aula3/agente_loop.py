import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from agents import Agent, Runner, RunHooks, function_tool

from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Ferramentas (slide 9 — exemplo real: API + conversão encadeada)
# ---------------------------------------------------------------------------
@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()
    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")
    local = geo["results"][0]
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


@function_tool
def converter_para_fahrenheit(celsius: float) -> float:
    """Converte uma temperatura de Celsius para Fahrenheit."""
    return celsius * 9 / 5 + 32


# ---------------------------------------------------------------------------
# Hooks — sensores que tornam o loop visível (slide 6 e 8)
# ---------------------------------------------------------------------------
class LoopHooks(RunHooks):
    """Registra cada evento do loop em tempo real.

    on_llm_start dispara uma vez por CHAMADA ao modelo (não por turno).
    on_agent_start dispara quando o agente ativo muda (em handoff) — com um
    único agente, dispara UMA vez só, mesmo com vários turnos por dentro.
    """

    def __init__(self):
        self.llm_calls = 0
        self.tool_calls = 0

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        self.llm_calls += 1
        print(f"  [on_llm_start] chamada #{self.llm_calls} ao modelo ({agent.name})")

    async def on_llm_end(self, context, agent, response):
        print(f"  [on_llm_end] modelo respondeu")

    async def on_tool_start(self, context, agent, tool):
        self.tool_calls += 1
        print(f"  [on_tool_start] chamando tool: {tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        print(f"  [on_tool_end] {tool.name} -> {result}")

    async def on_agent_start(self, context, agent):
        print(f"  [on_agent_start] {agent.name} assumiu")

    async def on_agent_end(self, context, agent, output):
        print(f"  [on_agent_end] {agent.name}")


# ---------------------------------------------------------------------------
# Agente — instructions VENCEM o pedido do usuário (slide 10)
# ---------------------------------------------------------------------------
agente = Agent(
    name="Assistente de Clima",
    instructions=(
        "Você é um assistente de clima. "
        "SEMPRE consulte get_temperatura para a cidade e SEMPRE devolva a resposta "
        "em Fahrenheit, usando converter_para_fahrenheit. Nunca responda em Celsius."
    ),
    model=modelo(),
    tools=[get_temperatura, converter_para_fahrenheit],
)


def executar(pergunta: str) -> None:
    print(f"\n>>> {pergunta}")
    hooks = LoopHooks()
    resultado = Runner.run_sync(agente, pergunta, hooks=hooks)
    print(f"Final: {resultado.final_output}")
    print(f"-> LLM calls: {hooks.llm_calls} | tool calls: {hooks.tool_calls}")
    print(f"-> on_agent_start disparou 1 vez (sem handoff), apesar de {hooks.llm_calls} chamadas ao modelo.")


if __name__ == "__main__":
    # slide 9/10: o modelo decide a ordem das tools e segue as instructions.
    executar("Qual a temperatura em São Paulo agora?")
    # slide 10: mesmo pedindo Celsius, as instructions (Fahrenheit) vencem.
    executar("Me diga a temperatura de Brasília, em Celsius por favor.")
