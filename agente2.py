import os
import requests  # 1. Importação necessária para as requisições HTTP
from agents import Agent, Runner, function_tool
from provedor import configurar  #[cite: 1, 2]

# 2. Inicializa a infraestrutura de inferência (Ollama/OpenAI)[cite: 1, 2]
configurar()  #[cite: 1, 2]


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


# 3. Instanciação do agente com a ferramenta e o modelo corretos
agente = Agent(
    name="Agente Meteorológico",
    instructions="Você é um assistente meteorológico. Use a ferramenta get_temperatura sempre que o usuário perguntar sobre clima ou temperatura.",
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),  #[cite: 1]
    tools=[get_temperatura],  # Registra a tool no agente
)


def main():
    # 4. Execução do Runner e impressão da resposta final
    resultado = Runner.run_sync(
        agente,
        "Qual é o clima em São Paulo?",
    )
    print(resultado.final_output)  #[cite: 1]


if __name__ == "__main__":
    main()