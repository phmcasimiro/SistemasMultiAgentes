import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent
from provedor import configurar, modelo, rodar

configurar()


# Fábrica do agente: declara o modelo do provedor ativo (modelo()).
def criar_agente() -> Agent:
    return Agent(
        name="Primeiro agente",
        instructions="Você é um agente de teste. Responda em poucas palavras e de forma objetiva. "
        "Se não souber a resposta, diga que não sabe.",
        model=modelo()
    )


def executar_agente(mensagem: str) -> str:
    resultado = rodar(criar_agente, mensagem)
    return resultado.final_output