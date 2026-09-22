# agente2.py — Seção 2 do deck: "usar ferramentas" (exercícios 2.1 e 2.2)
#
# Conceito central: um LLM isolado não sabe o clima agora (é um fato dinâmico, fora do que
# ele aprendeu no treinamento). Uma "tool" (function calling) dá a ele um "telefone" para
# consultar um sistema externo e trazer o dado de volta antes de responder.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import requests  # 1. Biblioteca HTTP usada DENTRO da tool para consultar APIs externas.
# `function_tool`: decorator que transforma uma função Python comum numa ferramenta que o
# modelo pode decidir chamar. O schema (JSON Schema/OpenAPI) é gerado automaticamente a
# partir da assinatura da função (tipos) e da docstring — por isso elas não são opcionais.
from agents import Agent, function_tool
from provedor import configurar, modelo, rodar

# 2. Inicializa a infraestrutura de inferência (Zen/Ollama/OpenAI) — igual à Seção 1.
configurar()


# `@function_tool` é o que converte esta função Python numa ferramenta que o Agent
# pode invocar. Sem o decorator, seria só uma função comum e o modelo nunca saberia
# que ela existe.
@function_tool
def get_temperatura(cidade: str) -> float:
    """Retorna a temperatura atual (°C) de uma cidade.

    Args:
        cidade: nome da cidade (ex.: 'Brasília').
    """
    # A docstring acima é LIDA PELO MODELO — é o que ele usa para decidir quando chamar
    # esta tool e como preencher o argumento `cidade`. Não é comentário de enfeite.

    # 1) cidade -> coordenadas (endpoint de geocoding).
    # A API Open-Meteo separa a resolução do nome em duas etapas: primeiro descobre
    # latitude/longitude, depois consulta a previsão para essas coordenadas.
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": cidade, "count": 1, "language": "pt", "format": "json"},
    ).json()

    # Se a API não encontrar a cidade, "results" vem vazio/ausente.
    # `raise ValueError(...)` aqui não quebra o programa: o SDK do Agents captura essa
    # exceção e entrega o erro como texto para o próprio modelo decidir o que responder
    # (ex.: "não encontrei essa cidade, você quis dizer...?").
    if not geo.get("results"):
        raise ValueError(f"Cidade não encontrada: {cidade}")

    local = geo["results"][0]

    # 2) coordenadas -> temperatura atual (endpoint de forecast).
    # Execução em duas etapas encadeadas (geocoding -> forecast), mas de forma
    # imperceptível para o usuário final: ele só vê a resposta final do agente.
    prev = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m",
            "timezone": "auto",
        },
    ).json()

    # O tipo de retorno declarado (-> float) também vira parte do schema entregue ao
    # modelo: ele sabe que vai receber um número, não uma string.
    return prev["current"]["temperature_2m"]


# 3. Criação do agente com a ferramenta e o modelo do provedor ativo.
def criar_agente() -> Agent:
    return Agent(
        name="Agente Meteorológico",
        instructions="Você é um assistente meteorológico. Use a ferramenta get_temperatura sempre que o usuário perguntar sobre clima ou temperatura.",
        model=modelo(),
        # `tools=[...]` é como o agente "recebe" a ferramenta: uma lista de funções
        # decoradas com @function_tool que ele pode escolher chamar durante a execução.
        tools=[get_temperatura],  # Registra a tool no agente
    )


def main():
    # 4. Execução do Runner (com recuo para Ollama) e impressão da resposta final.
    # Durante a execução, é o PRÓPRIO MODELO quem decide se e quando chama get_temperatura
    # — não há nenhum "if 'clima' in mensagem" no nosso código.
    resultado = rodar(criar_agente, "Qual é o clima em São Paulo?")
    print(resultado.final_output)


if __name__ == "__main__":
    main()
