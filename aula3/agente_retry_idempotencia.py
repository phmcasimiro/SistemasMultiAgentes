import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
from agents import Agent, Runner, function_tool
from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# "Banco" em memória + chave de idempotência (desafio 4.2 — slide 24).
# ---------------------------------------------------------------------------
BANCO: dict[str, int] = {}
_sequencial = 0


@function_tool
def registrar_ocorrencia(tipo: str, local: str, data: str) -> str:
    """Registra uma ocorrência no banco. É IDEMPOTENTE: a mesma ocorrência
    (mesmos tipo/local/data) gera a MESMA chave, então retry não duplica.
    """
    global _sequencial

    chave = hashlib.sha1(f"{tipo}|{local}|{data}".encode()).hexdigest()

    if chave in BANCO:
        return f"[IDEMPOTENTE] Ocorrência já registrada. id={BANCO[chave]}"

    _sequencial += 1
    BANCO[chave] = _sequencial
    return f"[REGISTRADA] Ocorrência gravada. id={_sequencial}"


def _chamar_direto(tipo: str, local: str, data: str) -> str:
    """Invoca a lógica da tool diretamente (para simular um retry)."""
    return registrar_ocorrencia.__wrapped__(tipo, local, data)


agente = Agent(
    name="Registrador de Ocorrência",
    instructions=(
        "Você registra ocorrências. Use a ferramenta registrar_ocorrencia "
        "com os dados que o usuário informar (tipo, local e data)."
    ),
    model=modelo(),
    tools=[registrar_ocorrencia],
)


def main() -> None:
    # 1) O agente registra a ocorrência.
    r = Runner.run_sync(agente, "Registre: furto de veículo na quadra 303, em 28/09.")
    print("Agente:", r.final_output)

    # 2) Simulação de RETRY: o mesmo registro é tentado de novo.
    print("\n[RETRY] Tentando registrar a MESMA ocorrência de novo...")
    print("  ", _chamar_direto("furto de veículo", "quadra 303", "28/09"))

    # 3) Uma ocorrência DIFERENTE gera uma nova entrada (não é bloqueada).
    print("\n[OUTRA] Registrando uma ocorrência diferente...")
    print("  ", _chamar_direto("furto de veículo", "quadra 303", "29/09"))

    print(f"\nRegistros no banco: {len(BANCO)} (esperado: 2)")


if __name__ == "__main__":
    main()
