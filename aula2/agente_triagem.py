# agente_triagem.py — Seção 4 do deck (Aula 1): "saída em formato fixo" (exercício 4.3:
# Literal — valores fechados — + bool).
#
# Conceito central: além de forçar TIPOS (str, int...), o Pydantic permite forçar
# VALORES dentro de um conjunto fechado com `Literal[...]`. O SDK rejeita qualquer
# resposta do modelo que caia fora dessa lista — diferente de pedir "responda só com
# uma dessas opções" em texto livre, que o modelo pode ignorar.

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
    # `Literal[...]`: só estes 5 valores são aceitos como `categoria`. Qualquer outro
    # valor que o modelo tentasse devolver (ex.: "sugestao") seria rejeitado pela
    # validação do Pydantic embutida no SDK.
    categoria: Literal["elogio", "denuncia", "reclamacao", "informacao", "solicitacao"]
    prioridade: Literal["baixa", "media", "alta"]
    # `bool` de verdade: dá para usar direto em `if triagem.urgente:` no código Python
    # que consome o resultado, sem checar string "true"/"false".
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
    # Três manifestações de categorias/prioridades bem distintas, para observar o
    # classificador variando `categoria`, `prioridade` e `urgente` conforme o conteúdo.
    for texto in [
        "Preciso da cópia do meu boletim de ocorrência.",
        "Gostaria de elogiar o atendimento da recepção.",
        "Minha conta está bloqueada e é urgente.",
    ]:
        t = executar_triagem(texto)
        # `type(t.urgente).__name__` imprime "bool" — prova visual de que o campo voltou
        # com o tipo Python correto, não como texto "True"/"False".
        print(f"\n{texto}\n -> {t.model_dump()} | urgente={t.urgente} ({type(t.urgente).__name__})")
