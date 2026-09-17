import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import requests
from agents import Agent, function_tool
from provedor import configurar, modelo, rodar

# Paleta de cores e estilos ANSI nativos (Linux / Bash)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
LINE = "─" * 70

# 1. Inicializa o provedor configurado no .env (Zen/Ollama/OpenAI)
configurar()


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


# 2. Fábrica do agente, focado exclusivamente na cotação do dia.
def criar_agente() -> Agent:
    return Agent(
        name="Analista de Câmbio",
        instructions=(
            "Você é um assistente financeiro direto e objetivo. "
            "Sua ÚNICA ação inicial DEVE ser executar a ferramenta 'get_cotacao_dolar_hoje'. "
            "NUNCA imprima JSON ou a sintaxe da tool como texto puro. "
            "Com o dado retornado, informe ao usuário a data de referência oficial do Banco Central Europeu "
            "e o valor da cotação do Dólar em Reais."
        ),
        model=modelo(),
        tools=[get_cotacao_dolar_hoje],
    )


# 3. Execução e saída com ANSI nativo
def main():
    print(f"\n{BLUE}{LINE}{RESET}")
    print(f"{BOLD}{CYAN}🤖 AGENTE EM EXECUÇÃO:{RESET} {criar_agente().name}")
    print(f"{DIM}Modelo ativo: {modelo()}{RESET}")
    print(f"{BLUE}{LINE}{RESET}")

    resultado = rodar(criar_agente, "Qual é a cotação do dólar hoje?")

    print(f"\n{BOLD}{GREEN}💵 COTAÇÃO ATUALIZADA:{RESET}\n")
    print(resultado.final_output)

    print(f"\n{BLUE}{LINE}{RESET}")
    print(f"{GREEN}✔ Execução concluída{RESET}")
    print(f"{BLUE}{LINE}{RESET}\n")


if __name__ == "__main__":
    main()