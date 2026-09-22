# agente_parada.py — Seção 3 do deck (Aula 3), exercício 3.1: "sucesso declarado" —
# um loop EXTERNO chama o agente repetidas vezes até ele mesmo declarar que terminou.
#
# Conceito central: diferente do max_turns (que limita o loop DE DENTRO do Runner, em
# turnos), aqui quem decide parar é um loop escrito por FORA, checando a cada rodada um
# campo booleano (`concluido`) que o próprio agente preenche via output_type. É o padrão
# certo para tarefas que se resolvem em VÁRIAS INTERAÇÕES separadas com o usuário — não
# num único `run_sync`.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession
from provedor import configurar, modelo

configurar()


# Saída estruturada (Seção 4 da Aula 1): o agente não devolve só texto — ele também
# devolve um veredito sobre o próprio progresso (`concluido`), que o loop externo lê.
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
    # output_type força o formato — é o que garante que `status.concluido` sempre existe
    # e é um bool de verdade, nunca uma string "sim"/"não" para o loop interpretar.
    output_type=StatusInvestigacao,
)


def investigar(mensagens_do_usuario: list[str], max_rodadas: int = 5):
    # Sessão (Seção 5 da Aula 1): sem ela, cada rodada esqueceria o que já foi dito nas
    # anteriores — o agente não conseguiria "ir completando" um resumo ao longo do tempo.
    sessao = SQLiteSession("investigacao_001")
    for rodada, msg in enumerate(mensagens_do_usuario, start=1):
        # Teto de segurança: mesmo um loop "externo" precisa de um limite — sem isso,
        # uma lista de mensagens muito longa (ou um agente que nunca conclui) rodaria
        # para sempre. Note que este limite conta RODADAS DA LISTA, não turnos do Runner.
        if rodada > max_rodadas:
            raise RuntimeError("Não concluiu dentro do limite de rodadas.")

        resultado = Runner.run_sync(agente, msg, session=sessao)
        # .final_output já é uma instância de StatusInvestigacao (não uma string),
        # graças ao output_type declarado acima.
        status = resultado.final_output
        print(f"Rodada {rodada}: concluido={status.concluido} — {status.resumo}")

        # O CRITÉRIO DE PARADA em si: nada no Runner decide isso — é este `if`, escrito
        # por fora, que encerra o laço assim que o próprio agente sinaliza conclusão.
        if status.concluido:
            return status

    raise RuntimeError("Não concluiu dentro do limite de rodadas.")


# Simula um cidadão informando o caso aos poucos, mensagem por mensagem — só na 3ª
# rodada o agente já deve ter nome, local e data suficientes para marcar concluido=True.
investigar([
    "Recebemos uma denúncia sobre um caso em Taguatinga.",
    "Foi na semana passada, terça-feira.",
    "A vítima se chama João Silva.",
])
