from agents import Agent
from pydantic import BaseModel
from provedor import configurar, modelo, rodar

configurar()


class Evento(BaseModel):
    nome: str
    data: str
    local: str
    participantes: int


# Fábrica do agente: extrai dados estruturados via output_type.
def criar_agente() -> Agent:
    return Agent(
        name="Executor de eventos",
        instructions=(
            "Extraia as informações do evento a partir do texto fornecido pelo usuário. "
            "Preencha nome, data, local e a quantidade de participantes."
        ),
        model=modelo(),
        output_type=Evento,
    )


def executar_agente_output(mensagem: str) -> Evento:
    resultado = rodar(criar_agente, mensagem)
    return resultado.final_output
