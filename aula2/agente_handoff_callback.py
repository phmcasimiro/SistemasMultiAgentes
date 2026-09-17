import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, handoff

from provedor import configurar, modelo

configurar()


async def registrar_transferencia(ctx) -> None:
    """Callback de auditoria: registra o instante da transferência.

    A assinatura do on_handoff no SDK recebe apenas o contexto (ctx).
    """
    print("[LOG] Transferência de agente realizada (handoff)")


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
    instructions=(
        "Você é uma mesa de triagem. "
        "Perguntas triviais de saudação (ex.: 'Bom dia!') você responde você mesmo. "
        "Dúvidas de matemática encaminhe ao especialista de matemática; "
        "dúvidas de história, ao especialista de história."
    ),
    model=modelo(),
    handoffs=[
        handoff(agente_matematica, on_handoff=registrar_transferencia),
        handoff(agente_historia, on_handoff=registrar_transferencia),
    ],
)


def main():
    for pergunta in ["Bom dia!", "Quanto é 7 vezes 8?", "Quem foi Pitágoras?"]:
        print(f"\n>>> {pergunta}")
        resultado = Runner.run_sync(triador, pergunta)
        print("Resposta:", resultado.final_output)


if __name__ == "__main__":
    main()
