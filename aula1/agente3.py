# agente3.py — Seção 2 do deck, exercício 2.3 (câmbio) + o problema de
# "Tool Call Leakage" (vazamento de sintaxe da ferramenta) discutido no aula1.md (Seção 3
# do markdown, "Fase 3").
#
# Conceito central: modelos pequenos/locais (ex.: llama3.2:3b via Ollama) às vezes "vazam"
# a sintaxe da chamada de ferramenta como texto cru na resposta, em vez de disparar a
# invocação estruturada de verdade. Este arquivo mitiga isso com PROMPT DEFENSIVO
# (instruções imperativas) — a solução arquitetural definitiva vem no agente4.py
# (ModelSettings(tool_choice="required")).

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import requests
from agents import Agent, function_tool
from provedor import configurar, modelo, rodar

# Paleta de cores e estilos ANSI nativos (Linux / Bash).
# Não é uma lib externa: são sequências de escape que o terminal interpreta como cor/estilo.
# Usadas aqui só para feedback visual — ajudam a enxergar quando a tool de fato executou,
# distinguindo isso de um eventual vazamento de texto cru do modelo.
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
LINE = "─" * 70

# 1. Inicializa o provedor configurado no .env (Zen/Ollama/OpenAI).
configurar()


@function_tool
def get_cotacao_dolar_hoje() -> str:
    """Consulta a cotação oficial mais recente do Dólar (USD para BRL)

    utilizando o endpoint /latest da API Frankfurter.
    """
    # Este print roda DENTRO da tool, no momento em que ela é de fato executada —
    # é a prova visual de que o modelo chamou a ferramenta de verdade (não vazou o JSON).
    print(f"\n{YELLOW}[TOOL EXECUTADA]{RESET} Consultando cotação mais recente na API Frankfurter...")

    # Frankfurter é uma API pública e gratuita do Banco Central Europeu (BCE) para câmbio,
    # sem necessidade de cadastro/API key.
    url = "https://api.frankfurter.app/latest"
    params = {"from": "USD", "to": "BRL"}

    resposta = requests.get(url, params=params, timeout=10)

    # Verificação explícita de status HTTP (diferente do agente4.py, que usa
    # raise_for_status() — duas formas equivalentes de tratar falha de rede).
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
        # PROMPT DEFENSIVO: instruções imperativas e repetidas ("ÚNICA ação", "NUNCA
        # imprima JSON") são a defesa de engenharia de prompt contra o vazamento de tool
        # call — útil principalmente em modelos locais menores, que seguem instruções de
        # forma menos rígida que modelos maiores em nuvem.
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


# 3. Execução e saída com ANSI nativo.
def main():
    # Cabeçalho decorativo: mostra qual agente e qual modelo estão ativos antes de rodar,
    # útil para depurar em qual provedor (Zen/Ollama) o teste está de fato executando.
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
