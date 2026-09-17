import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============ HANDOFF 2 ===============
from agents import Agent, Runner
from provedor import configurar, modelo

configurar()

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
    tools=[
        agente_matematico.as_tool(
            tool_name="consultar_matematico",
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
    return resultado.final_output