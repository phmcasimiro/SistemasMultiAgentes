from agents import Agent, Runner, SQLiteSession
from provedor import configurar, modelo

configurar()

agente = Agent(
    name="agente_coleta",
    instructions=(
        "Você atende um registro de ocorrência coletando dados aos poucos. "
        "A cada turno o usuário informa um campo (tipo, local ou data). "
        "No fim, consolide um resumo com tudo o que foi coletado nesta conversa."
    ),
    model=modelo(),
)


def main():
    sessao = SQLiteSession("coleta_progressiva", db_path="coleta.db")

    # Nenhum turno isolado tem a informação completa — a sessão acumula.
    passos = [
        "O tipo de ocorrência é furto de veículo.",
        "O local foi a quadra 303 da Asa Norte, Brasília.",
        "A data foi 28/09, por volta das 22h10.",
        "Agora faça o resumo consolidado.",
    ]

    for i, passo in enumerate(passos, 1):
        resultado = Runner.run_sync(agente, passo, session=sessao)
        print(f"{i}) {passo}\n   -> {resultado.final_output}\n")


if __name__ == "__main__":
    main()
