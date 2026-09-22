# main.py — Aula Extra do deck (Aula 1): "atender por HTTP" — o mesmo funcionário, agora
# também atendendo por telefone, não só no balcão.
#
# Conceito central: FastAPI NÃO substitui o Agent — é só a porta HTTP de entrada. Uma
# rota recebe uma mensagem, chama a função que executa o agente e devolve
# `resultado.final_output` como JSON. A API nunca decide sozinha se uma ferramenta deve
# ser chamada — quem decide isso é sempre o modelo, dentro do Runner.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel  # Pydantic valida o corpo (body) de cada requisição.
from fastapi import FastAPI
from agents import Runner

# Imports relativos (".agente_x"): main.py faz parte do pacote `aula2`, então cada agente
# é importado como submódulo do próprio pacote — é por isso que a API sobe com
# `uvicorn aula2.main:app`, não com `uvicorn main:app` direto de dentro da pasta.
from .primeiro_agente import executar_agente               # Seção 1 — agente único
from .agente_handoff import executar_agente_handoff         # Seção 3 — handoff
from .agente_handoff2 import executar_agente_handoff2       # Seção 3 — agente como ferramenta
from .agente_bo import extrair_ocorrencia                   # Seção 4 — output_type aninhado
from .agente_output import executar_agente_output           # Seção 4 — output_type simples
from .agente_memoria import executar_agente_memoria         # Seção 5 — sessão persistida
# Agentes da Aula 3 (engenharia de agent loops), reaproveitados aqui para expor também
# por API — mostra que a mesma FastAPI cresce sem reescrever o contrato HTTP.
from aula3.agente_loop import agente as agente_loop
from aula3.agente_clima_vento import agente as agente_clima_vento

app = FastAPI()

# Corpo de requisição padrão: toda rota que só precisa de uma pergunta usa este schema.
class Pergunta(BaseModel):
    mensagem: str

# Corpo de requisição para a rota de memória: além da mensagem, precisa saber A QUAL
# conversa ela pertence (o "caso"/sessão), para reinjetar o histórico certo.
class PerguntaMemoria(BaseModel):
    mensagem: str
    sessao_id: str

@app.get("/")
def inicio():
    # Healthcheck simples: confirma que a API está de pé, sem tocar em nenhum agente.
    return {
        "mensagem": "Olá mundo!"
    }

@app.post("/tools")
def perguntar_tools(pergunta: Pergunta):
    # Rota mais simples: um único agente, sem handoff, sem memória, sem saída estruturada.
    resultado = executar_agente(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/handoff")
def perguntar_handoff(pergunta: Pergunta):
    # Mecanismo 1 (Seção 3): o triador pode transferir o turno para um especialista —
    # a API não sabe (nem precisa saber) qual dos dois respondeu.
    resultado = executar_agente_handoff(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/handoff2")
def perguntar_handoff2(pergunta: Pergunta):
    # Mecanismo 2 (Seção 3): o triador consulta o especialista como ferramenta e
    # permanece no controle da resposta final.
    resultado = executar_agente_handoff2(
        pergunta.mensagem
    )

    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/bo")
def extrair_bo(pergunta: Pergunta):
    # Saída estruturada com modelo aninhado (Seção 4, exercício 4.2): o retorno já é
    # um objeto Pydantic (`Ocorrencia`); `.model_dump()` o converte em dict serializável
    # em JSON pelo FastAPI, sem parsing manual de string.
    ocorrencia = extrair_ocorrencia(pergunta.mensagem)
    return ocorrencia.model_dump()

@app.post("/output")
def extrair_output(pergunta: Pergunta):
    # Saída estruturada com campos simples (Seção 4, exercício 4.1).
    evento = executar_agente_output(pergunta.mensagem)
    return evento.model_dump()

@app.post("/memoria")
def perguntar_memoria(pergunta: PerguntaMemoria):
    # Seção 5: cada `sessao_id` distinto é um "caso" isolado — chamadas repetidas com o
    # mesmo id acumulam contexto; ids diferentes nunca vazam contexto entre si.
    resultado = executar_agente_memoria(pergunta.mensagem, pergunta.sessao_id)
    return {
        "sessao_id": pergunta.sessao_id,
        "pergunta": pergunta.mensagem,
        "mensagem": resultado
    }

@app.post("/loop")
def perguntar_loop(pergunta: Pergunta):
    # Agente da Aula 3 (engenharia de agent loops), chamado direto via Runner.run_sync
    # (sem passar por uma função "executar_..." própria, diferente dos agentes acima).
    resultado = Runner.run_sync(agente_loop, pergunta.mensagem)
    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado.final_output
    }

@app.post("/clima-vento")
def perguntar_clima_vento(pergunta: Pergunta):
    # Idem, para o agente de clima com ferramenta de vento da Aula 3.
    resultado = Runner.run_sync(agente_clima_vento, pergunta.mensagem)
    return {
        "pergunta": pergunta.mensagem,
        "mensagem": resultado.final_output
    }
