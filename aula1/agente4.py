import requests

from agents import Agent, function_tool, ModelSettings
from provedor import configurar, modelo, rodar


# 1. Configuração do provedor
configurar()


# 2. Ferramenta
@function_tool
def converter_moeda(
    valor: float,
    moeda_origem: str,
    moeda_destino: str
) -> str:
    """Converte um valor entre duas moedas."""

    origem = moeda_origem.upper()
    destino = moeda_destino.upper()

    print(f"[TOOL] Convertendo {valor} {origem} para {destino}")

    resposta = requests.get(
        f"https://api.frankfurter.dev/v2/rate/{origem}/{destino}",
        timeout=10
    )

    resposta.raise_for_status()

    dados = resposta.json()

    cotacao = dados["rate"]
    convertido = valor * cotacao

    return (
        f"{valor:.2f} {origem} = "
        f"{convertido:.2f} {destino}"
    )


# 3. Fábrica do agente (modelo do provedor ativo)
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

        model_settings=ModelSettings(
            tool_choice="required"
        )
    )


# 4. Execução
def main():

    print("Iniciando agente...")

    resultado = rodar(criar_agente, "Quanto são 100 dólares em reais?")

    print("\nResposta:")
    print(resultado.final_output)


# 5. Inicia o programa
if __name__ == "__main__":
    main()
