import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from agents import Agent, Runner, function_tool
from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Tool assíncrona "lenta" — simula um sistema que demora mais que o prazo.
# ---------------------------------------------------------------------------
@function_tool
async def processar_lentamente() -> str:
    """Processa uma consulta de forma demorada (simulação)."""
    await asyncio.sleep(3)
    return "processamento concluído"


agente = Agent(
    name="Agente de Análise",
    instructions="Sempre use a ferramenta processar_lentamente antes de responder.",
    model=modelo(),
    tools=[processar_lentamente],
)


async def rodar_com_prazo(pergunta: str, segundos: float) -> str:
    """3.2 — timeout de PAREDE: nenhum loop pode estourar este prazo."""
    return await asyncio.wait_for(
        Runner.run(agente, pergunta),
        timeout=segundos,
    )


async def main() -> None:
    print(">>> Rodando com prazo de 1s (a tool leva 3s)...")
    try:
        resultado = await rodar_com_prazo("Qual o resultado?", segundos=1)
        print("Resposta:", resultado.final_output)
    except asyncio.TimeoutError:
        print("[TimeoutError] O agente estourou o prazo de parede de 1s.")


if __name__ == "__main__":
    asyncio.run(main())
