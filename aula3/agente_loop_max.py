import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, MaxTurnsExceeded, function_tool

from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Tool que sempre retorna algo — para o loop "nunca terminar" sozinho
# ---------------------------------------------------------------------------
@function_tool
def consultar_sistema() -> str:
    """Consulta um sistema externo (simulação)."""
    return "dados_do_sistema_123"


# Instrução que pede para SEMPRE consultar de novo (1.2 — slide 7).
# A instrução em texto, sozinha, NÃO corta o loop — quem corta é o max_turns.
agente = Agent(
    name="Agente Preso no Loop",
    instructions=(
        "Você é um analista. SEMPRE consulte consultar_sistema antes de responder. "
        "Nunca responda sem consultar o sistema uma vez mais."
    ),
    model=modelo(),
    tools=[consultar_sistema],
)


def main() -> None:
    for limite in (3, 1):
        print(f"\n>>> Rodando com max_turns={limite}")
        try:
            resultado = Runner.run_sync(
                agente,
                "Qual a situação do processo?",
                max_turns=limite,
            )
            print("Resposta:", resultado.final_output)
        except MaxTurnsExceeded:
            print(f"[MaxTurnsExceeded] O agente estourou o limite de {limite} turno(s) sem concluir.")


if __name__ == "__main__":
    main()
