import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession
from provedor import configurar, modelo

configurar()

class StatusInvestigacao(BaseModel):
    resumo: str
    concluido: bool

agente = Agent(
    name="Investigador",
    instructions=(
        "Você está reunindo informações sobre um caso aos poucos, uma mensagem por vez. "
        "A cada rodada, resuma o que já sabe e marque concluido=True quando achar que já tem "
        "pelo menos nome, local e data do caso."
    ),
    model=modelo(),
    output_type=StatusInvestigacao,
)

def investigar(mensagens_do_usuario: list[str], max_rodadas: int = 5):
    sessao = SQLiteSession("investigacao_001")
    for rodada, msg in enumerate(mensagens_do_usuario, start=1):
        if rodada > max_rodadas:
            raise RuntimeError("Não concluiu dentro do limite de rodadas.")
        resultado = Runner.run_sync(agente, msg, session=sessao)
        status = resultado.final_output
        print(f"Rodada {rodada}: concluido={status.concluido} — {status.resumo}")
        if status.concluido:
            return status
    raise RuntimeError("Não concluiu dentro do limite de rodadas.")

investigar([
    "Recebemos uma denúncia sobre um caso em Taguatinga.",
    "Foi na semana passada, terça-feira.",
    "A vítima se chama João Silva.",
])
