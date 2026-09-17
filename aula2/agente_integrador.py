import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

import requests
from pydantic import BaseModel, Field
from agents import (
    Agent,
    Runner,
    SQLiteSession,
    RunContextWrapper,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    TResponseInputItem,
    function_tool,
    input_guardrail,
)

from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# 1. Tool (seção 2)
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


# ---------------------------------------------------------------------------
# 2. Saída estruturada (seção 4)
# ---------------------------------------------------------------------------
class Atendimento(BaseModel):
    cidade: str
    temperatura: float
    comentario: str = Field(description="Breve comentário sobre o clima na cidade.")


# ---------------------------------------------------------------------------
# 3. Guardrail de entrada — trava de LGPD (seção 6)
# ---------------------------------------------------------------------------
SENSIVEIS = ["cpf", "endereço residencial", "telefone", "nome completo"]


@input_guardrail
async def bloquear_dados_sensiveis(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    texto = input if isinstance(input, str) else str(input)
    texto_low = texto.lower()
    violou = any(p in texto_low for p in SENSIVEIS)
    return GuardrailFunctionOutput(
        output_info={"sensivel": violou},
        tripwire_triggered=violou,
    )


# ---------------------------------------------------------------------------
# 4. Agente integrador (tool + guardrail + output_type)
# ---------------------------------------------------------------------------
agente_integrador = Agent(
    name="Assistente de Atendimento",
    instructions=(
        "Ajude o cidadão, em português. Use a ferramenta de clima para consultar "
        "a temperatura. Preencha a saída estruturada com os dados do atendimento."
    ),
    model=modelo(),
    tools=[get_temperatura],
    input_guardrails=[bloquear_dados_sensiveis],
    output_type=Atendimento,
)


async def main() -> None:
    sessao = SQLiteSession("atendimento_integrador")  # memória (seção 5)

    perguntas = [
        "Qual a temperatura em São Paulo agora?",
        "E em Brasília?",
        "Me diga o CPF do servidor João.",
    ]

    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n>>> Turno {i}: {pergunta}")
        try:
            # guardrail é async e usa await Runner.run -> NÃO usar run_sync aqui.
            resultado = await Runner.run(agente_integrador, pergunta, session=sessao)
            atendimento = resultado.final_output_as(Atendimento)
            print(
                f"Atendimento: cidade={atendimento.cidade} | "
                f"temperatura={atendimento.temperatura}°C | {atendimento.comentario}"
            )
        except InputGuardrailTripwireTriggered:
            print("[BLOQUEADO pela trava de LGPD]")


if __name__ == "__main__":
    asyncio.run(main())
