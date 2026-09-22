# agente4.py — Seção 2 do deck, exercício 2.3 (câmbio com 2 argumentos) + a solução
# ARQUITETURAL (não apenas de prompt) para o "Tool Call Leakage" visto no agente3.py.
#
# Conceito central: em vez de confiar só em instruções de texto para forçar o uso da
# ferramenta, ModelSettings(tool_choice="required") desativa, no nível da API de
# inferência, a possibilidade de o modelo responder com texto puro no primeiro turno —
# ele É OBRIGADO a emitir uma chamada de ferramenta.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

# `ModelSettings`: classe de configuração de baixo nível repassada à chamada de inferência
# (temperature, tool_choice, etc.) — diferente de `instructions`, que é só texto e pode ser
# ignorado por um modelo pouco obediente.
from agents import Agent, function_tool, ModelSettings
from provedor import configurar, modelo, rodar


# 1. Configuração do provedor.
configurar()


# 2. Ferramenta.
@function_tool
def converter_moeda(
    valor: float,
    moeda_origem: str,
    moeda_destino: str
) -> str:
    """Converte um valor entre duas moedas."""
    # Três argumentos tipados (float, str, str): o modelo precisa extrair TODOS os três
    # da frase em linguagem natural do usuário (ex.: "100 dólares em reais" ->
    # valor=100.0, moeda_origem="USD", moeda_destino="BRL") — é isso que o SDK traduz em
    # JSON Schema a partir desta assinatura.

    origem = moeda_origem.upper()
    destino = moeda_destino.upper()

    # Print de diagnóstico: confirma no terminal os argumentos que o modelo de fato
    # extraiu e passou para a tool, útil para depurar extração errada.
    print(f"[TOOL] Convertendo {valor} {origem} para {destino}")

    resposta = requests.get(
        f"https://api.frankfurter.dev/v2/rate/{origem}/{destino}",
        timeout=10
    )

    # raise_for_status(): forma idiomática do `requests` de levantar exceção em respostas
    # HTTP de erro (4xx/5xx) — equivalente ao `if status_code != 200: raise` do agente3.py.
    resposta.raise_for_status()

    dados = resposta.json()

    cotacao = dados["rate"]
    convertido = valor * cotacao

    return (
        f"{valor:.2f} {origem} = "
        f"{convertido:.2f} {destino}"
    )


# 3. Fábrica do agente (modelo do provedor ativo).
def criar_agente() -> Agent:
    return Agent(
        name="Agente Financeiro",

        instructions=(
            "Você é um agente financeiro especializado em conversão de moedas. "
            "Sempre use converter_moeda para realizar conversões. "
            "Nunca invente cotações."
        ),

        model=modelo(),
        tools=[converter_moeda],

        # A defesa de verdade contra o vazamento de tool call (Seção 3 do aula1.md):
        # tool_choice="required" obriga o modelo a chamar ALGUMA ferramenta registrada
        # no primeiro turno, em vez de deixar essa obrigação só nas mãos do prompt.
        model_settings=ModelSettings(
            tool_choice="required"
        )
    )


# 4. Execução.
def main():

    print("Iniciando agente...")

    resultado = rodar(criar_agente, "Quanto são 100 dólares em reais?")

    print("\nResposta:")
    print(resultado.final_output)


# 5. Inicia o programa.
if __name__ == "__main__":
    main()
