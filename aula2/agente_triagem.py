import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Literal

from pydantic import BaseModel
from agents import Agent
from provedor import configurar, modelo, rodar

configurar()


class Triagem(BaseModel):
    categoria: Literal["elogio", "denuncia", "reclamacao", "informacao", "solicitacao"]
    prioridade: Literal["baixa", "media", "alta"]
    urgente: bool
    resumo: str


# Fábrica do agente: valores fechados (Literal) + bool de verdade.
def criar_agente() -> Agent:
    return Agent(
        name="Triagem de Ouvidoria",
        instructions=(
            "Classifique a manifestação. Use SOMENTE os valores permitidos para "
            "categoria e prioridade. Indique se é urgente."
        ),
        model=modelo(),
        output_type=Triagem,
    )


def executar_triagem(mensagem: str) -> Triagem:
    resultado = rodar(criar_agente, mensagem)
    return resultado.final_output


if __name__ == "__main__":
    for texto in [
        "Preciso da cópia do meu boletim de ocorrência.",
        "Gostaria de elogiar o atendimento da recepção.",
        "Minha conta está bloqueada e é urgente.",
    ]:
        t = executar_triagem(texto)
        print(f"\n{texto}\n -> {t.model_dump()} | urgente={t.urgente} ({type(t.urgente).__name__})")
