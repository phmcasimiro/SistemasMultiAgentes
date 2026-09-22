# agente_memoria.py — Seção 5 do deck (Aula 1): "memória" (exercício 5.5: memória em
# arquivo reutilizável) — a versão de `agente_session.py` pensada para ser IMPORTADA pela
# API (`main.py`, rota POST /memoria), em vez de rodar como script solto.
#
# Conceito central: cada requisição HTTP é isolada (não existe "processo que continua
# rodando" entre uma chamada e outra), então a única forma de a API "lembrar" de uma
# conversa entre requisições é persistir a sessão em ARQUIVO (`db_path`) e reabri-la a
# cada chamada usando o mesmo identificador.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, SQLiteSession
from provedor import configurar, modelo

configurar()


# ============================================================
# 1. AGENTE COM MEMÓRIA
# ============================================================
# Note que o Agent é criado UMA VEZ, no nível do módulo (diferente do padrão
# "fábrica sem argumentos" de outros arquivos) — ele não tem estado próprio, então pode
# ser reaproveitado por todas as chamadas de executar_agente_memoria(); quem carrega o
# estado da conversa é a SQLiteSession, criada a cada chamada.
agente_memoria = Agent(
    name="agente_memoria",
    instructions=(
        "Você é um agente que mantém o contexto da conversa em memória. "
        "Utilize as informações anteriores da conversa quando forem necessárias "
        "para responder às próximas perguntas. Responda com precisão e clareza."
    ),
    model=modelo(),
)


# ============================================================
# 2. EXECUÇÃO COM SESSÃO PERSISTIDA
# ============================================================
def executar_agente_memoria(mensagem: str, sessao_id: str) -> str:
    # Cria ou recupera a sessão. Se o sessao_id já existir no banco,
    # o histórico daquela conversa é recuperado e reinjetado.
    # `db_path="conversas.db"` é o arquivo SQLite compartilhado por TODAS as sessões
    # desta função — o que isola uma conversa da outra não é o arquivo, é o `sessao_id`
    # (cada id vira uma "tabela"/partição lógica dentro do mesmo banco).
    session = SQLiteSession(sessao_id, db_path="conversas.db")

    resultado = Runner.run_sync(
        agente_memoria,
        mensagem,
        session=session,
    )

    # A API (main.py) só precisa do texto final — é por isso que esta função devolve
    # `str`, diferente de agente_bo.py/agente_output.py, que devolvem objetos Pydantic.
    return resultado.final_output
