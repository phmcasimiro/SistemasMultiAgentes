import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#HOOK 01

from agents import Agent, Runner, RunHooks
from provedor import configurar, modelo

configurar()


class MeuHook(RunHooks):

    async def on_llm_start(
        self, # meu próprio objeto Hook
        ctx, # o contexto do agente
        agent, # o agente
        system_prompt, # o prompt do sistema
        input_items # entradas enviadas ao modelo
    ):
        print("O modelo começou a trabalhar! ")
        print(f"O agente {agent.name} começou a trabalhar!")


agente = Agent(
    name="Assistente",
    instructions="Responda de forma simples e objetiva.",
    model=modelo(),
)


resultado = Runner.run_sync(
    agente,
    "O que é inteligência artificial?",
    hooks=MeuHook()
)


print("Resposta:", resultado.final_output)