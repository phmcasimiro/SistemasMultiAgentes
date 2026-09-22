# agente_handoff_callback.py — Seção 3 do deck (Aula 1), exercício 3.2: "Observar e
# customizar a transferência" — um handoff com callback de auditoria.
#
# Conceito central: além de rotear a conversa, a transferência pode disparar um efeito
# colateral (log, auditoria, métrica) exatamente no instante em que acontece — e o
# triador pode ser instruído a resolver sozinho o que é trivial, só delegando dúvidas
# de verdade.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# `handoff` (função, minúscula) é diferente do parâmetro `handoffs=[...]` do Agent:
# ela ENVOLVE um Agent e permite anexar comportamento extra à transferência, como o
# callback `on_handoff` usado abaixo.
from agents import Agent, Runner, handoff

from provedor import configurar, modelo

configurar()


async def registrar_transferencia(ctx) -> None:
    """Callback de auditoria: registra o instante da transferência.

    A assinatura do on_handoff no SDK recebe apenas o contexto (ctx).
    """
    # Roda no exato momento em que o triador decide transferir — antes de o especialista
    # começar a gerar a resposta. É aqui que, num sistema real, entraria um registro em
    # log/banco de auditoria (quem transferiu, quando, para qual fluxo).
    print("[LOG] Transferência de agente realizada (handoff)")


agente_matematica = Agent(
    name="Especialista_Matematica",
    instructions="Resolve matemática, com passo a passo.",
    model=modelo(),
)
agente_historia = Agent(
    name="Especialista_Historia",
    instructions="Responde história de forma clara.",
    model=modelo(),
)

triador = Agent(
    name="Triador",
    instructions=(
        "Você é uma mesa de triagem. "
        # Diferença-chave em relação a agente_handoff.py: aqui o triador é instruído a
        # NÃO encaminhar tudo — perguntas triviais (saudações) ele responde sozinho,
        # só dúvidas de conteúdo (matemática/história) disparam o handoff (e, com ele,
        # o [LOG] do callback).
        "Perguntas triviais de saudação (ex.: 'Bom dia!') você responde você mesmo. "
        "Dúvidas de matemática encaminhe ao especialista de matemática; "
        "dúvidas de história, ao especialista de história."
    ),
    model=modelo(),
    handoffs=[
        # `handoff(agente, on_handoff=callback)` substitui o agente "puro" que
        # apareceria numa lista `handoffs=[agente_matematica, ...]` comum — o
        # comportamento de roteamento é o mesmo, mas agora com o efeito colateral do
        # callback anexado a cada transferência.
        handoff(agente_matematica, on_handoff=registrar_transferencia),
        handoff(agente_historia, on_handoff=registrar_transferencia),
    ],
)


def main():
    # A 1ª pergunta é trivial (não deve disparar [LOG] nem handoff); as outras duas
    # são de conteúdo (cada uma deve imprimir [LOG] e ser respondida pelo especialista).
    for pergunta in ["Bom dia!", "Quanto é 7 vezes 8?", "Quem foi Pitágoras?"]:
        print(f"\n>>> {pergunta}")
        resultado = Runner.run_sync(triador, pergunta)
        print("Resposta:", resultado.final_output)


if __name__ == "__main__":
    main()
