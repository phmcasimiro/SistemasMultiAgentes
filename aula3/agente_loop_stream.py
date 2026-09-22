import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import requests
from agents import Agent, Runner, function_tool
from agents.run_context import RunContextWrapper
from openai.types.responses import ResponseTextDeltaEvent

from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade."""
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()
    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")
    local = geo["results"][0]
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": local["latitude"], "longitude": local["longitude"],
                "current": "temperature_2m", "timezone": "auto"},
    ).json()
    return prev["current"]["temperature_2m"]


@function_tool(needs_approval=True)
def cancelar_ocorrencia(ocorrencia_id: str) -> str:
    """Cancela uma ocorrência (ação consequente, exige aprovação)."""
    return f"Ocorrência {ocorrencia_id} cancelada."


agente_clima = Agent(
    name="Assistente de Clima",
    instructions="Use a ferramenta de clima quando perguntarem sobre temperatura.",
    model=modelo(),
    tools=[get_temperatura],
)

agente_acoes = Agent(
    name="Agente de Ações",
    instructions="Use cancelar_ocorrencia para cancelar ocorrências.",
    model=modelo(),
    tools=[cancelar_ocorrencia],
)

# Triador para 6.3
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
# 6.1 — contar turnos + ver tokens, ao mesmo tempo
# ---------------------------------------------------------------------------
async def streaming_clima(pergunta: str) -> None:
    print(f"\n>>> {pergunta}")
    turnos = 0
    stream = Runner.run_streamed(agente_clima, pergunta)
    async for event in stream.stream_events():
        if event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print(f"  [turno {turnos + 1}] tool chamada: {event.item.raw_item.name}")
                turnos += 1
            elif event.item.type == "tool_call_output_item":
                print(f"  [tool devolveu] {event.item.output}")
        elif event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
    print(f"\n  -> total de turnos observados: {turnos}")


# ---------------------------------------------------------------------------
# 6.2 — streaming + aprovação humana juntos
# ---------------------------------------------------------------------------
async def streaming_aprovacao(pergunta: str) -> None:
    print(f"\n>>> {pergunta}")
    ctx = RunContextWrapper(context=None)

    # 1) Streaming: vê os tokens e detecta a tool que pede aprovação.
    stream = Runner.run_streamed(agente_acoes, pergunta, context=ctx)
    async for event in stream.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
        elif event.type == "run_item_stream_event" and event.item.type == "tool_call_item":
            print(f"\n  [tool] {event.item.raw_item.name} (aguardando aprovação humana...)")
    print()

    # 2) Aprovação humana: a stream pausa no tool; resolvemos no laço de interrupção.
    resultado = await Runner.run(agente_acoes, stream.to_input_list(), context=ctx)
    while resultado.interruptions:
        for interrup in resultado.interruptions:
            print(f"  [APROVAÇÃO] {interrup.tool_name} args={interrup.arguments}")
            ctx.approve_tool(interrup)
        resultado = await Runner.run(agente_acoes, resultado.to_input_list(), context=ctx)

    print("Final:", resultado.final_output)


# ---------------------------------------------------------------------------
# 6.3 — triagem streamada: os três tipos de evento juntos
# ---------------------------------------------------------------------------
async def streaming_triagem(pergunta: str) -> None:
    print(f"\n>>> {pergunta}")
    stream = Runner.run_streamed(triador, pergunta)
    async for event in stream.stream_events():
        if event.type == "agent_updated_stream_event":
            print(f"[HANDOFF] assumiu: {event.new_agent.name}")
        elif event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
    print()


async def main() -> None:
    await streaming_clima("Qual a temperatura em Brasília agora?")
    await streaming_aprovacao("Cancele a ocorrência 4821.")
    await streaming_triagem("Quem foi Pitágoras?")


if __name__ == "__main__":
    asyncio.run(main())
