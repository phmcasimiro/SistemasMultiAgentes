import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

import requests
from agents import Agent, Runner, function_tool
from openai.types.responses import ResponseTextDeltaEvent

from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Tool de clima (para o ciclo de vida 7.2)
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


agente_clima = Agent(
    name="Assistente de Clima",
    instructions="Use a ferramenta de clima quando perguntarem sobre temperatura.",
    model=modelo(),
    tools=[get_temperatura],
)

# Triador para o handoff (7.3)
agente_matematica = Agent(
    name="Especialista_Matematica",
    instructions="Resolve matemática, com passo a passo.",
    model=modelo(),
)
agente_historia = Agent(
    name="Especialista_Historia",
    instructions="Responde história de forma clara.",
    model=modelo(),
)
triador = Agent(
    name="Triador",
    instructions="Encaminhe para o especialista certo. Não responda você mesmo.",
    model=modelo(),
    handoffs=[agente_matematica, agente_historia],
)


# ---------------------------------------------------------------------------
# 7.1 + 7.2 — Streaming de texto e ciclo de vida das ferramentas
# ---------------------------------------------------------------------------
async def streaming_clima(pergunta: str) -> None:
    print(f"\n>>> {pergunta}")
    stream = Runner.run_streamed(agente_clima, pergunta)  # SEM await

    async for event in stream.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
        elif event.type == "run_item_stream_event":
            item = event.item
            if item.type == "tool_call_item":
                print(f"\n[TOOL CHAMADA] {item.raw_item.name}")
            elif item.type == "tool_call_output_item":
                print(f"[TOOL RESULTADO] {item.output}")
    print()


# ---------------------------------------------------------------------------
# 7.3 — Streaming + handoff: instante da transferência
# ---------------------------------------------------------------------------
async def streaming_handoff(pergunta: str) -> None:
    print(f"\n>>> {pergunta}")
    stream = Runner.run_streamed(triador, pergunta)  # SEM await

    async for event in stream.stream_events():
        if event.type == "agent_updated_stream_event":
            print(f"[HANDOFF] assumiu: {event.new_agent.name}")
        elif event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
    print()


async def main() -> None:
    await streaming_clima("Qual a temperatura em Brasília agora?")
    await streaming_handoff("Quem foi Pitágoras?")


if __name__ == "__main__":
    asyncio.run(main())
