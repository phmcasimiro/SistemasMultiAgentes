# ex3_agente_as_tool.py — Aula 4 (A2A), Lab 1 · Exercício 3: "Agente como ferramenta"
# (`as_tool`).
#
# Conceito central (slide "Agente como ferramenta"): é o SEGUNDO jeito de fazer A2A
# síncrono, e o oposto do handoff dos exercícios 1 e 2 num ponto crucial — QUEM FICA NO
# COMANDO da conversa:
#
#   Handoff (ex1/ex2)      -> quem responde é o OUTRO agente; o controle "passa de vez"
#                              ("transfiro a ligação").
#   as_tool() (este arquivo) -> quem responde é sempre o agente que CHAMA a ferramenta;
#                              ele consulta o especialista e continua no comando
#                              ("consulto um especialista e sigo a chamada").
#
# Este é o mesmo mecanismo já visto em `aula2/agente_handoff2.py` — aqui ele aparece
# lado a lado com o handoff "de verdade" para deixar clara a diferença de controle.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner
from provedor import configurar, modelo

configurar()

# Os dois especialistas: cada um é um Agent comum, sem `handoff_description` nenhuma —
# essa propriedade só faz sentido dentro de uma lista `handoffs=[...]`, que não é o caso
# aqui (eles vão virar ferramentas, não destinos de handoff).
juridico = Agent(name="Jurídico", instructions="Enquadramento legal provável, 1-2 linhas.", model=modelo())
investigador = Agent(name="Investigador", instructions="2 diligências investigativas iniciais.", model=modelo())

coordenador = Agent(
    name="Coordenador",
    instructions=(
        "Você coordena o atendimento de uma ocorrência. "
        "Consulte o Jurídico e o Investigador e produza um resumo único "
        "com: enquadramento e próximos passos."
    ),
    model=modelo(),
    # `tools=[...]`, não `handoffs=[...]`: o Coordenador MANTÉM o controle da conversa.
    tools=[
        # `agente.as_tool(...)` empacota um Agent inteiro (com suas próprias
        # instructions e modelo) como se fosse uma função Python decorada com
        # @function_tool. Por dentro, chamar essa "ferramenta" roda um Runner completo
        # sobre o agente especialista e devolve o texto final dele como resultado — o
        # Coordenador recebe essa resposta e decide o que fazer com ela.
        juridico.as_tool(
            tool_name="consultar_juridico",
            # `tool_description` cumpre, para uma tool, o mesmo papel que
            # `handoff_description` cumpre para um destino de handoff: é o texto que o
            # Coordenador lê para decidir QUANDO chamar esta ferramenta.
            tool_description="Obtém o enquadramento legal provável da ocorrência.",
        ),
        investigador.as_tool(
            tool_name="consultar_investigador",
            tool_description="Obtém diligências investigativas iniciais.",
        ),
    ],
)


def main() -> None:
    ocorrencia = "Arrombamento de residência no Lago Sul com subtração de eletrônicos."
    resultado = Runner.run_sync(coordenador, ocorrencia)
    # "O que observar" (slide do exercício): a resposta final vem SEMPRE do Coordenador
    # (confira: resultado.last_agent.name é sempre "Coordenador", nunca "Jurídico" nem
    # "Investigador") — diferente do handoff, onde last_agent muda conforme quem assumiu
    # a conversa.
    print(f"[{resultado.last_agent.name}] {resultado.final_output}")


if __name__ == "__main__":
    main()
