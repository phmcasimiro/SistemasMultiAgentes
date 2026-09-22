import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, RunHooks, AgentHooks, function_tool
from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Tool simples (rápida) para disparar eventos de ferramenta.
# ---------------------------------------------------------------------------
@function_tool
def consultar_clima(cidade: str) -> str:
    """Retorna o clima atual de uma cidade."""
    dados = {"São Paulo": "22°C, nublado", "Brasília": "28°C, sol"}
    return dados.get(cidade, "Cidade não encontrada.")


# ---------------------------------------------------------------------------
# HooksRun — família GLOBAL (passada ao Runner, enxerga o run inteiro)
# ---------------------------------------------------------------------------
class HooksRun(RunHooks):
    def __init__(self, tag):
        self.tag = tag

    async def on_llm_start(self, ctx, agent, system_prompt, input_items):
        print(f"  [RUN {self.tag}] on_llm_start")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"  [RUN {self.tag}] on_tool_start: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"  [RUN {self.tag}] on_tool_end: {tool.name} -> {result}")


# ---------------------------------------------------------------------------
# HooksAgente — família por AGENTE (amarrada a um agente específico)
# ---------------------------------------------------------------------------
class HooksAgente(AgentHooks):
    def __init__(self, tag):
        self.tag = tag

    async def on_llm_start(self, ctx, agent, system_prompt, input_items):
        print(f"  [AGENTE {self.tag}] on_llm_start")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"  [AGENTE {self.tag}] on_tool_start: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"  [AGENTE {self.tag}] on_tool_end: {tool.name} -> {result}")


agente = Agent(
    name="Assistente de Clima",
    instructions="Use a ferramenta quando perguntarem sobre o tempo.",
    model=modelo(),
    tools=[consultar_clima],
    hooks=HooksAgente("especialista"),  # hooks amarrados a ESTE agente (slide 14)
)


# slide 15: a ordem de disparo é RunHook primeiro, depois AgentHook.
resultado = Runner.run_sync(
    agente,
    "Como está o tempo em Brasília?",
    hooks=HooksRun("global"),
)
print("\nResposta final:", resultado.final_output)
