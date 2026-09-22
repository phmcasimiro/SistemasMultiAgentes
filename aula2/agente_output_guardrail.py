import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re

from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    output_guardrail,
)

from provedor import configurar, modelo

configurar()

# Regex de CPF: 3 dígitos . 3 dígitos . 3 dígitos - 2 dígitos
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")


# ---------------------------------------------------------------------------
# Output guardrail: trava que roda DEPOIS do agente, na saída.
# ---------------------------------------------------------------------------
@output_guardrail
async def bloquear_cpf_na_saida(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    conteudo = output if isinstance(output, str) else str(output)
    encontrado = CPF_RE.search(conteudo)
    return GuardrailFunctionOutput(
        output_info={"cpf": encontrado.group(0) if encontrado else None},
        tripwire_triggered=encontrado is not None,
    )


agente = Agent(
    name="Assistente de Dados",
    instructions=(
        "Você responde dúvidas sobre processamento de dados. "
        "Quando o usuário citar um CPF, transcreva-o na resposta."
    ),
    model=modelo(),
    output_guardrails=[bloquear_cpf_na_saida],
)


async def perguntar(pergunta: str) -> None:
    print(f"\n>>> Pergunta: {pergunta}")
    try:
        resultado = await Runner.run(agente, pergunta)
        print(f"Resposta: {resultado.final_output}")
    except OutputGuardrailTripwireTriggered as e:
        info = e.guardrail_result.output.output_info
        print(f"[BLOQUEADO] CPF detectado na saída: {info['cpf']}")


async def main() -> None:
    await perguntar("Qual o significado de 'dado pessoal' na LGPD?")
    await perguntar("Extraia o CPF 123.456.789-09 deste documento e devolva-o.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
