# agente_output.py — Seção 4 do deck (Aula 1): "saída em formato fixo" (exercício 4.1:
# output_type com Pydantic, campos simples — sem aninhamento, ao contrário de agente_bo.py).
#
# Conceito central: `output_type` obriga o modelo a devolver dados num formato fixo,
# validado por Pydantic, em vez de texto livre — um contrato que o resto do sistema
# consome sem parsing frágil de string.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent
from pydantic import BaseModel
from provedor import configurar, modelo, rodar

configurar()


# Modelo plano: nenhum campo é outro BaseModel nem uma lista de modelos — todos os
# quatro campos são tipos primitivos.
class Evento(BaseModel):
    nome: str
    data: str
    local: str
    # `participantes: int` é o ponto-chave do exercício: o modelo precisa devolver um
    # NÚMERO de verdade (12), não a string "12" — é isso que output_type garante e que
    # texto livre jamais garantiria sem parsing manual.
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
    # `.final_output` é uma instância de `Evento`, não uma string — `participantes` já
    # vem como `int` de verdade, pronto para usar em cálculo ou comparação sem `int(...)`.
    return resultado.final_output
