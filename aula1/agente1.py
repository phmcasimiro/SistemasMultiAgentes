import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent
from provedor import configurar, modelo, rodar

# 1. Inicializa a infraestrutura de inferência definida no .env (Zen/Ollama/OpenAI)
configurar()


# 2. Fábrica do agente: declara o modelo do provedor ativo (modelo()).
def criar_agente() -> Agent:
    return Agent(
        name="Primeiro agente",
        instructions="Você é um agente de teste e responde de forma objetiva.",
        model=modelo()
    )


# 3. Ponto de entrada com a execução do Runner encapsulada e recuo para Ollama
def main():
    resultado = rodar(criar_agente, "Quem é o presidente da Argentina?")
    # .final_output aqui é uma string (não definimos output_type — isso vem no 4.x).
    print(resultado.final_output)

if __name__ == "__main__":
    main()