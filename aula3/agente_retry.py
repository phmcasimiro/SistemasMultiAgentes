import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import requests
from agents import Agent, Runner, function_tool
from provedor import configurar, modelo

configurar()


# ---------------------------------------------------------------------------
# Seção 4 do deck (Aula 3), exercício 4.1: retry manual com backoff exponencial.
#
# Conceito central: uma ferramenta que falha é como um telefone que não atende —
# desligar na hora não resolve, discar sem parar também não. A tool CONTINUA sendo
# uma função Python comum: o retry é só um `for` por dentro dela. O modelo nem sabe
# que houve tentativas — só vê o resultado final, ou o erro, se TODAS falharem.
#
# Distinção crítica: erro de NEGÓCIO (ex.: "cidade não encontrada") não melhora
# tentando de novo — a resposta vai ser a mesma; só erro TRANSITÓRIO (timeout,
# conexão recusada, 5xx) tem chance de se resolver numa nova tentativa.
# ---------------------------------------------------------------------------
@function_tool
def get_temperatura_resiliente(cidade: str, max_tentativas: int = 4) -> float:
    """Retorna a temperatura atual (°C) de uma cidade, com retry e backoff exponencial."""
    espera_base = 0.5  # segundos

    for tentativa in range(1, max_tentativas + 1):
        try:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
                timeout=3,
            )
            geo.raise_for_status()
            dados_geo = geo.json()
            if not dados_geo.get("results"):
                # Erro de NEGÓCIO: tentar de novo não muda o resultado (a cidade
                # continua não existindo), por isso não entra no bloco de retry abaixo.
                raise ValueError(f"Cidade não encontrada: {cidade}")
            local = dados_geo["results"][0]

            prev = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": local["latitude"], "longitude": local["longitude"],
                        "current": "temperature_2m", "timezone": "auto"},
                timeout=3,
            )
            prev.raise_for_status()
            return prev.json()["current"]["temperature_2m"]

        except ValueError:
            raise   # erro de negócio: propaga direto, sem tentar de novo

        except requests.exceptions.RequestException as erro:
            # RequestException é a classe-base do `requests` para falha TRANSITÓRIA:
            # timeout, conexão recusada, erro HTTP 5xx — tudo o que tem chance real de
            # se resolver numa nova tentativa (diferente do ValueError acima).
            if tentativa == max_tentativas:
                # Esgotou as tentativas: propaga um erro só (RuntimeError), não a pilha
                # de N exceções — o modelo recebe UMA mensagem de falha clara.
                raise RuntimeError(f"Falhou após {max_tentativas} tentativas: {erro}")
            # Backoff exponencial: 2**(tentativa-1) dá 1, 2, 4, 8... multiplicado pela
            # espera_base (0.5s) vira 0.5s, 1s, 2s, 4s nas tentativas 1, 2, 3, 4 — cada
            # falha espera o DOBRO da anterior antes de tentar de novo.
            espera = espera_base * (2 ** (tentativa - 1))
            print(f"  tentativa {tentativa} falhou ({erro}); tentando de novo em {espera}s...")
            time.sleep(espera)

agente = Agent(
    name="Agente de Clima Resiliente",
    instructions="Use a ferramenta quando perguntarem sobre o tempo.",
    model=modelo(),
    tools=[get_temperatura_resiliente],
)
r = Runner.run_sync(agente, "Qual a temperatura em Brasília?")
print("\nResposta final:", r.final_output)