import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
