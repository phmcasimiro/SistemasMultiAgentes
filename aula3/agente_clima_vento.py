import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from agents import Agent, Runner, function_tool

from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Desafio 1.3 (slide 11): clima completo — temperatura + vento.
# A MESMA chamada à Open-Meteo devolve as duas métricas.
# ---------------------------------------------------------------------------
@function_tool
def get_clima(cidade: str) -> str:
    """Retorna temperatura (°C) e velocidade do vento (km/h) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()
    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")

    local = geo["results"][0]

    # current traz as duas métricas de uma única chamada.
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m,wind_speed_10m",
            "timezone": "auto",
        },
    ).json()

    temp = prev["current"]["temperature_2m"]
    vento = prev["current"]["wind_speed_10m"]
    return f"temperatura_celsius={temp:.1f}; vento_kmh={vento:.1f}"


@function_tool
def converter_para_fahrenheit(celsius: float) -> float:
    """Converte uma temperatura de Celsius para Fahrenheit."""
    return celsius * 9 / 5 + 32


agente = Agent(
    name="Assistente de Clima Completo",
    instructions=(
        "Você é um assistente de clima. "
        "Sempre consulte get_clima para a cidade. "
        "Converta a temperatura para Fahrenheit usando converter_para_fahrenheit "
        "e informe também a velocidade do vento em km/h."
    ),
    model=modelo(),
    tools=[get_clima, converter_para_fahrenheit],
)


def main() -> None:
    resultado = Runner.run_sync(agente, "Como está o clima em São Paulo agora?")
    print("Resposta:", resultado.final_output)


if __name__ == "__main__":
    main()
