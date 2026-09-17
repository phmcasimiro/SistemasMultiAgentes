import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, SQLiteSession
from provedor import configurar, modelo

configurar()

agente = Agent(
    name="agente_memoria",
    instructions=("Você é um agente que mantém o contexto da conversa em memória. Responda com precisão"),
    model=modelo(),
)

def main():
    sessao = SQLiteSession("conversa_do_molina", db_path="conversa_do_molina.db")  # ← o objeto de memória (com db_path = arquivo)

    r1 = Runner.run_sync(agente, "Qual a capital da França?", session=sessao)
    print(r1.final_output)
    r2 = Runner.run_sync(agente, "E quantos habitantes ela tem?", session=sessao)
    print(r2.final_output)

main()