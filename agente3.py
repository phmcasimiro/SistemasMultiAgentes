import os
import requests
from agents import Agent, Runner, function_tool
from provedor import configurar  #[cite: 1, 2]

# Paleta de cores e estilos ANSI nativos (Linux / Bash)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
LINE = "─" * 70

# 1. Inicializa o provedor configurado no .env (Ollama/OpenAI)[cite: 1, 2]
configurar()  #[cite: 1, 2]


@function_tool
def get_cotacao_dolar_hoje() -> str:
    """Consulta a cotação oficial mais recente do Dólar (USD para BRL)

    utilizando o endpoint /latest da API Frankfurter.
    """
    print(f"\n{YELLOW}[TOOL EXECUTADA]{RESET} Consultando cotação mais recente na API Frankfurter...")

    url = "https://api.frankfurter.app/latest"
    params = {"from": "USD", "to": "BRL"}

    resposta = requests.get(url, params=params, timeout=10)

    if resposta.status_code != 200:
        raise ValueError(f"Falha na API Frankfurter: status {resposta.status_code}")

    dados = resposta.json()
    data_referencia = dados.get("date")
    taxa_brl = dados.get("rates", {}).get("BRL")

    if not taxa_brl:
        return "Cotação não disponível no momento."

    return f"Data de referência: {data_referencia} | 1 USD = R$ {taxa_brl:.4f}"


# 2. Agente focado exclusivamente na cotação do dia
agente_cambio = Agent(
    name="Analista de Câmbio",
    instructions=(
        "Você é um assistente financeiro direto e objetivo. "
        "Sua ÚNICA ação inicial DEVE ser executar a ferramenta 'get_cotacao_dolar_hoje'. "
        "NUNCA imprima JSON ou a sintaxe da tool como texto puro. "
        "Com o dado retornado, informe ao usuário a data de referência oficial do Banco Central Europeu "
        "e o valor da cotação do Dólar em Reais."
    ),
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),  #
    tools=[get_cotacao_dolar_hoje],
)


# 3. Execução e saída com ANSI nativo
def main():
    print(f"\n{BLUE}{LINE}{RESET}")
    print(f"{BOLD}{CYAN}🤖 AGENTE EM EXECUÇÃO:{RESET} {agente_cambio.name}")
    print(f"{DIM}Modelo ativo: {os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}{RESET}")  #[cite: 1]
    print(f"{BLUE}{LINE}{RESET}")

    resultado = Runner.run_sync(
        agente_cambio,
        "Qual é a cotação do dólar hoje?",
    )

    print(f"\n{BOLD}{GREEN}💵 COTAÇÃO ATUALIZADA:{RESET}\n")
    print(resultado.final_output)  #[cite: 1]

    print(f"\n{BLUE}{LINE}{RESET}")
    print(f"{GREEN}✔ Execução concluída{RESET}")
    print(f"{BLUE}{LINE}{RESET}\n")


if __name__ == "__main__":
    main()