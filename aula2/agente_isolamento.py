from agents import Agent, Runner, SQLiteSession
from provedor import configurar, modelo

configurar()

agente = Agent(
    name="agente_isolamento",
    instructions="Responda com base apenas no contexto desta conversa.",
    model=modelo(),
)


def main():
    # Dois "casos" com ids distintos — devem ser isolados entre si.
    caso_a = SQLiteSession("caso_a", db_path="isolamento.db")
    caso_b = SQLiteSession("caso_b", db_path="isolamento.db")

    # 1) Informa um dado na sessão A.
    r1 = Runner.run_sync(
        agente,
        "Anote que o suspeito se chama João.",
        session=caso_a,
    )
    print("[CASO A] anotação:", r1.final_output)

    # 2) Pergunta na sessão B — NÃO deve saber.
    r2 = Runner.run_sync(
        agente,
        "Qual é o nome do suspeito?",
        session=caso_b,
    )
    print("[CASO B] não deve saber:", r2.final_output)

    # 3) Confirma na sessão A — DEVE lembrar.
    r3 = Runner.run_sync(
        agente,
        "Qual é o nome do suspeito?",
        session=caso_a,
    )
    print("[CASO A] deve lembrar:", r3.final_output)


if __name__ == "__main__":
    main()
