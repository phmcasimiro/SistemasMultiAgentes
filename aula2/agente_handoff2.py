# agente_handoff2.py — mecanismo ALTERNATIVO ao handoff: "agente como ferramenta"
# (`as_tool`). Não é numerado como exercício próprio no deck, mas a Seção 3 pede para
# entender a diferença entre os dois mecanismos de coordenação.
#
# Conceito central: em vez de TRANSFERIR o turno (handoff), o especialista é empacotado
# como uma função que o triador pode CHAMAR e cujo resultado ele próprio consome — o
# triador nunca perde o controle da conversa.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ HANDOFF 2 ===============
from agents import Agent, Runner
from provedor import configurar, modelo

configurar()

# Os mesmos dois especialistas de agente_handoff.py, mas SEM handoff_description —
# aqui eles não vão para uma lista `handoffs=[...]`, então essa propriedade não se aplica.
agente_matematico = Agent(
    name="agente_matematico",
    instructions="Você é um especialista em matemática. Responda com precisão e clareza.",
    model=modelo(),
)

agente_historiador = Agent(
    name="agente_historiador",
    instructions="Você é um especialista em história. Responda com precisão e clareza.",
    model=modelo(),
)

agente_triador = Agent(
    name="agente_triador",
    instructions=(
        " Você é um agente triador. Sua função é direcionar perguntas para o agente mais adequado com base no conteúdo da pergunta. " \
        "Se a pergunta for sobre matemática, encaminhe para o agente_matematico. Se for sobre história, encaminhe para o agente_historiador. " \
        "Se não se enquadrar em nenhuma dessas categorias, responda que não sabe."
    ),
    model=modelo(),
    # `tools=[...]`, não `handoffs=[...]`: o triador MANTÉM o controle do turno.
    tools=[
        # `agente.as_tool(...)` empacota um Agent inteiro (com seu próprio modelo e
        # instructions) como se fosse uma função Python comum decorada com
        # @function_tool. Internamente, chamar essa tool roda um Runner completo sobre
        # o agente especialista e devolve o texto final dele como resultado da "função".
        agente_matematico.as_tool(
            tool_name="consultar_matematico",
            # `tool_description` cumpre aqui o mesmo papel que `handoff_description`
            # cumpria no mecanismo de handoff: é o texto que o TRIADOR lê para decidir
            # quando chamar esta ferramenta.
            tool_description="Se a pergunta for sobre matemática, eu devo responder.",
        ),
        agente_historiador.as_tool(
            tool_name="consultar_historiador",
            tool_description="Se a pergunta for sobre história, eu devo responder.",
        )
    ]
)

def executar_agente_handoff2(mensagem: str) -> str:
    resultado = Runner.run_sync(
        agente_triador,
        mensagem
    )
    # Diferença essencial em relação a agente_handoff.py: aqui `resultado.last_agent`
    # é SEMPRE o `agente_triador` — ele nunca cede a resposta final, apenas consome o
    # retorno das ferramentas (os especialistas) e compõe a resposta ele mesmo.
    return resultado.final_output
