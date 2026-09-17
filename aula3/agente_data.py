import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from agents import Agent, Runner
from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Slide 25 — o modelo não tem relógio: injete a data REAL nas instructions.
# ---------------------------------------------------------------------------
def criar_agente() -> Agent:
    hoje = datetime.now().strftime("%d/%m/%Y")
    return Agent(
        name="Agente de Datas",
        instructions=(
            "Você responde sobre datas e prazos. "
            f"HOJE é {hoje} (confie nesta informação, não use a data do seu treinamento). "
            "Ao responder, considere que 'hoje' é a data informada."
        ),
        model=modelo(),
    )


def main() -> None:
    resultado = Runner.run_sync(criar_agente(), "Que dia é hoje?")
    print("Pergunta: Que dia é hoje?")
    print("Resposta:", resultado.final_output)

    print("\nPergunta: O que é 'amanhã'?")
    resultado2 = Runner.run_sync(criar_agente(), "O que é amanhã?")
    print("Resposta:", resultado2.final_output)


if __name__ == "__main__":
    main()
