import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, function_tool
from agents.run_context import RunContextWrapper
from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Ação CONSEQUENTE: escreve em um sistema. Precisa de aprovação humana.
# needs_approval=True -> pausa a execução até alguém decidir (slide 28).
# ---------------------------------------------------------------------------
@function_tool(needs_approval=True)
def cancelar_ocorrencia(ocorrencia_id: str) -> str:
    """Cancela uma ocorrência no sistema (ação consequente)."""
    return f"Ocorrência {ocorrencia_id} cancelada com sucesso."


# 5.2 — aprovação CONDICIONAL: só pede aprovação quando a mensagem for "urgente".
def exigir_aprovacao_se_urgente(ctx, tool_input, call_id) -> bool:
    mensagem = (tool_input.get("mensagem") or "").lower()
    return "urgente" in mensagem


@function_tool(needs_approval=exigir_aprovacao_se_urgente)
def enviar_notificacao(destinatario: str, mensagem: str) -> str:
    """Envia uma notificação (exige aprovação apenas em mensagens urgentes)."""
    return f"Notificação enviada a {destinatario}."


agente = Agent(
    name="Agente de Ações",
    instructions=(
        "Você executa ações solicitadas. Use cancelar_ocorrencia para cancelar "
        "uma ocorrência e enviar_notificacao para enviar avisos."
    ),
    model=modelo(),
    tools=[cancelar_ocorrencia, enviar_notificacao],
)


def rodar_com_aprovacao(pergunta: str, always_approve: bool = False) -> str:
    """5.1 — laço de aprovação: enquanto houver interrupções, decide aprovar."""
    ctx = RunContextWrapper(context=None)
    resultado = Runner.run_sync(agente, pergunta, context=ctx)

    while resultado.interruptions:
        for interrup in resultado.interruptions:
            print(f"  [APROVAÇÃO] {interrup.tool_name} args={interrup.arguments}")
            ctx.approve_tool(interrup, always_approve=always_approve)
        resultado = Runner.run_sync(agente, resultado.to_input_list(), context=ctx)

    return resultado.final_output


def main() -> None:
    # 5.1 — pausa sempre (aprova cada chamada).
    print(">>> 5.1 needs_approval (aprova cada chamada):")
    print("Resultado:", rodar_com_aprovacao("Cancele a ocorrência 4821.", always_approve=False))
    print()

    # 5.3 — always_approve: aprova a PRIMEIRA e vale para o resto da execução.
    print(">>> 5.3 always_approve (aprova para a execução inteira):")
    print("Resultado:", rodar_com_aprovacao("Cancele as ocorrências 4821, 4822 e 4823.", always_approve=True))
    print()

    # 5.2 — aprovação condicional: só quando há "urgente".
    print(">>> 5.2 aprovação condicional (sem urgente -> NÃO pede aprovação):")
    print("Resultado:", rodar_com_aprovacao(
        "Envie uma notificação ao chefe com a mensagem 'O relatório está pronto.'"
    ))
    print()
    print(">>> 5.2 aprovação condicional (com 'urgente' -> pede aprovação):")
    print("Resultado:", rodar_com_aprovacao(
        "Envie uma notificação ao chefe com a mensagem 'URGENTE: vazamento de dados.'"
    ))


if __name__ == "__main__":
    main()
