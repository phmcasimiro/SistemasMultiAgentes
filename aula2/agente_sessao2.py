# agente_sessao2.py — Seção 5 do deck (Aula 1): "memória" (exercício 5.2: sessão +
# ferramenta).
#
# Conceito central: a sessão não guarda só o TEXTO da conversa — ela também guarda os
# RESULTADOS das ferramentas já chamadas. Por isso um 3º turno consegue comparar dados
# buscados em turnos anteriores sem precisar chamar a API de novo.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner, SQLiteSession, function_tool

import requests

from provedor import configurar, modelo
configurar()


# Mesma ferramenta de temperatura já vista na Aula 1 (agente2.py): geocoding + forecast
# via Open-Meteo, sem chave de API.
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
    # Sem db_path -> sessão em RAM (`:memory:`): serve para o teste, mas não sobrevive
    # ao fim do processo (compare com agente_session.py, que usa db_path=... em arquivo).
    sessao = SQLiteSession("clima_comparativo")
    r1 = Runner.run_sync(agente_clima, "Qual a temperatura em Brasília agora?", session=sessao)
    print("1:", r1.final_output)
    r2 = Runner.run_sync(agente_clima, "E em São Paulo?", session=sessao)  # "E em..." só faz sentido com memória
    print("2:", r2.final_output)
    # 3º turno: exige lembrar as DUAS temperaturas buscadas antes. Sem nova chamada de API.
    # A sessão já guarda o RESULTADO da tool (o número retornado por get_temperatura) nos
    # dois turnos anteriores, então o modelo compara os dois valores só lendo o histórico —
    # não dispara get_temperatura pela 3ª vez.
    r3 = Runner.run_sync(agente_clima, "Qual das duas cidades está mais quente?", session=sessao)
    print("3:", r3.final_output)


main_sessao_clima()
