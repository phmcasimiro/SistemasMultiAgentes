import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from fastapi import FastAPI
from agents import Runner

from .primeiro_agente import executar_agente
from .agente_handoff import executar_agente_handoff
from .agente_handoff2 import executar_agente_handoff2
from .agente_bo import extrair_ocorrencia
from .agente_output import executar_agente_output
from .agente_memoria import executar_agente_memoria
from aula3.agente_loop import agente as agente_loop
from aula3.agente_clima_vento import agente as agente_clima_vento

app = FastAPI()

class Pergunta(BaseModel):
    mensagem: str

class PerguntaMemoria(BaseModel):
    mensagem: str
    sessao_id: str

@app.get("/")
def inicio():
    return {
        "mensagem": "Olá mundo!"
    }

@app.post("/tools")
def perguntar_tools(pergunta: Pergunta):
    resultado = executar_agente(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/handoff")
def perguntar_handoff(pergunta: Pergunta):
    resultado = executar_agente_handoff(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/handoff2")
def perguntar_handoff2(pergunta: Pergunta):
    resultado = executar_agente_handoff2(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/bo")
def extrair_bo(pergunta: Pergunta):
    ocorrencia = extrair_ocorrencia(pergunta.mensagem)
    return ocorrencia.model_dump()

@app.post("/output")
def extrair_output(pergunta: Pergunta):
    evento = executar_agente_output(pergunta.mensagem)
    return evento.model_dump()

@app.post("/memoria")
def perguntar_memoria(pergunta: PerguntaMemoria):
    resultado = executar_agente_memoria(pergunta.mensagem, pergunta.sessao_id)
    return {
        "sessao_id": pergunta.sessao_id,
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/loop")
def perguntar_loop(pergunta: Pergunta):
    resultado = Runner.run_sync(agente_loop, pergunta.mensagem)
    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado.final_output
    }

@app.post("/clima-vento")
def perguntar_clima_vento(pergunta: Pergunta):
    resultado = Runner.run_sync(agente_clima_vento, pergunta.mensagem)
    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado.final_output
    }