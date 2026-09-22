# agente_bo.py — Seção 4 do deck (Aula 1): "saída em formato fixo" (exercício 4.2:
# modelos aninhados + lista).
#
# Conceito central: até aqui os agentes devolviam texto livre. Para consumir o resultado
# de forma programática (gravar num banco, montar um JSON de API), `output_type` obriga
# o modelo a devolver um objeto Pydantic — inclusive com modelos ANINHADOS dentro de uma
# lista, como o boletim de ocorrência abaixo (uma ocorrência tem VÁRIOS envolvidos).

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from agents import Agent
from provedor import configurar, modelo, rodar

configurar()


# Modelo aninhado: representa CADA pessoa citada no relato.
class Envolvido(BaseModel):
    nome: str
    papel: str  # ex.: 'vítima', 'suspeito', 'testemunha'


# Modelo principal: note que `envolvidos` é uma LISTA de Envolvido — o SDK traduz isso
# num JSON Schema com um array de objetos aninhados, e o modelo precisa identificar
# TODAS as pessoas do relato e classificar o papel de cada uma.
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
        # `output_type=Ocorrencia`: o SDK gera o JSON Schema a partir da classe Pydantic
        # e instrui o modelo a devolver SOMENTE um JSON válido conforme esse schema —
        # não mais texto livre.
        output_type=Ocorrencia,
    )


def extrair_ocorrencia(texto: str) -> Ocorrencia:
    resultado = rodar(criar_agente, texto)
    # Diferente dos agentes sem output_type, aqui `.final_output` NÃO é uma string —
    # é uma instância de `Ocorrencia` já validada pelo Pydantic (campos com os tipos
    # certos, lista de Envolvido populada). Pode ser serializada com `.model_dump()`
    # (dict) ou `.model_dump_json()` (string), pronta para persistência ou resposta HTTP.
    return resultado.final_output
