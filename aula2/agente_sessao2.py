import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, SQLiteSession, function_tool

import requests

from provedor import configurar, modelo
configurar()


@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

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
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": local["latitude"], "longitude": local["longitude"],
                "current": "temperature_2m", "timezone": "auto"},
    ).json()
    return prev["current"]["temperature_2m"]


agente_clima = Agent(
    name="Assistente de Clima",
    instructions="Responda sobre clima de forma concisa, em português. Use a ferramenta quando precisar da temperatura.",
    model=modelo(),
    tools=[get_temperatura],
)


def main_sessao_clima():
    sessao = SQLiteSession("clima_comparativo")
    r1 = Runner.run_sync(agente_clima, "Qual a temperatura em Brasília agora?", session=sessao)
    print("1:", r1.final_output)
    r2 = Runner.run_sync(agente_clima, "E em São Paulo?", session=sessao)  # "E em..." só faz sentido com memória
    print("2:", r2.final_output)
    # 3º turno: exige lembrar as DUAS temperaturas buscadas antes. Sem nova chamada de API.
    r3 = Runner.run_sync(agente_clima, "Qual das duas cidades está mais quente?", session=sessao)
    print("3:", r3.final_output)


main_sessao_clima()