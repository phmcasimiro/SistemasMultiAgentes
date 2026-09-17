from pydantic import BaseModel
from agents import Agent
from provedor import configurar, modelo, rodar

configurar()


class Envolvido(BaseModel):
    nome: str
    papel: str  # ex.: 'vítima', 'suspeito', 'testemunha'


class Ocorrencia(BaseModel):
    tipo: str
    data: str
    local: str
    envolvidos: list[Envolvido]   # lista de modelos aninhados
    resumo: str


# Fábrica do agente: extrai dados estruturados via output_type.
def criar_agente() -> Agent:
    return Agent(
        name="agente_bo",
        instructions=(
            "Extraia os dados da ocorrência a partir do relato. "
            "Para cada pessoa citada, defina o papel (vítima, suspeito ou testemunha)."
        ),
        model=modelo(),
        output_type=Ocorrencia,
    )


def extrair_ocorrencia(texto: str) -> Ocorrencia:
    resultado = rodar(criar_agente, texto)
    return resultado.final_output
