# agente_session.py — Seção 5 do deck (Aula 1): "memória" — o prontuário do atendimento
# (exercício 5.1: SQLiteSession entre turnos).
#
# Conceito central: cada `Runner.run_sync` é, por padrão, um atendente NOVO — o agente não
# lembra do turno anterior. A `SQLiteSession` guarda o histórico sob um identificador e o
# reinjeta a cada nova chamada, dando ao agente memória de curto prazo entre turnos.

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
    # `db_path="conversa_do_molina.db"` faz a sessão PERSISTIR em arquivo (SQLite de
    # verdade), em vez de viver só na RAM (o padrão, quando db_path é omitido, é
    # `:memory:` — a conversa se perde ao final do processo).
    sessao = SQLiteSession("conversa_do_molina", db_path="conversa_do_molina.db")  # ← o objeto de memória (com db_path = arquivo)

    # `session=sessao` é o que muda tudo: o SDK injeta automaticamente o histórico
    # gravado sob o id "conversa_do_molina" antes de mandar a mensagem ao modelo,
    # e grava o novo turno (pergunta + resposta) de volta na sessão ao final.
    r1 = Runner.run_sync(agente, "Qual a capital da França?", session=sessao)
    print(r1.final_output)
    # "ela" só resolve corretamente porque o 1º turno (com "capital da França") está
    # na sessão — sem `session=sessao` aqui, o agente não saberia a que "ela" se refere.
    r2 = Runner.run_sync(agente, "E quantos habitantes ela tem?", session=sessao)
    print(r2.final_output)

main()
