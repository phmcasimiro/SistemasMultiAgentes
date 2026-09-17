import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import requests  # 1. Importação necessária para as requisições HTTP
from agents import Agent, function_tool
from provedor import configurar, modelo, rodar

# 2. Inicializa a infraestrutura de inferência (Zen/Ollama/OpenAI)
configurar()


@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    # 1) cidade -> coordenadas (endpoint de geocoding)
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()

    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")

    local = geo["results"][0]

    # 2) coordenadas -> temperatura atual (endpoint de forecast)
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m",
            "timezone": "auto",
        },
    ).json()

    return prev["current"]["temperature_2m"]


# 3. Fábrica do agente com a ferramenta e o modelo do provedor ativo.
def criar_agente() -> Agent:
    return Agent(
        name="Agente Meteorológico",
        instructions="Você é um assistente meteorológico. Use a ferramenta get_temperatura sempre que o usuário perguntar sobre clima ou temperatura.",
        model=modelo(),
        tools=[get_temperatura],  # Registra a tool no agente
    )


def main():
    # 4. Execução do Runner (com recuo para Ollama) e impressão da resposta final
    resultado = rodar(criar_agente, "Qual é o clima em São Paulo?")
    print(resultado.final_output)


if __name__ == "__main__":
    main()