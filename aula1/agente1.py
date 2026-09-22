# agente1.py — Seção 1 do deck: "responder" — o primeiro agente possível (exercícios 1.1 e 1.2)
#
# Conceito central: Agent = modelo de linguagem + instructions (a "persona"/"system prompt").
# Sozinho, um Agent não faz nada — é só uma DEFINIÇÃO. Quem de fato executa o ciclo  é o Runner.
# O Runner chama o modelo, trata a resposta

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
# Necessário porque este arquivo roda como parte do pacote `aula1` (python -m aula1.agente1),
# mas `provedor.py` mora na raiz do repositório, fora do pacote.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# `Agent`: a classe do SDK openai-agents que representa o "funcionário" (modelo + instructions).
from agents import Agent

# `provedor` é o módulo compartilhado da raiz (ver README.md e a Seção 2 do aula1.md):
# - configurar(): lê o .env e liga o cliente OpenAI-compatível certo (Zen, Ollama ou OpenAI).
# - modelo(): devolve o nome do modelo do provedor ativo (evita hardcodar "gpt-4o-mini" etc.).
# - rodar(): executa o Runner com recuo automático para Ollama se o provedor principal falhar.
from provedor import configurar, modelo, rodar

# 1. Inicializa a infraestrutura de inferência definida no .env (Zen/Ollama/OpenAI).
# Precisa rodar ANTES de criar qualquer Agent, pois é aqui que o SDK aprende para onde
# mandar as chamadas (set_default_openai_client) e com qual API (chat_completions).
configurar()


# 2. Fábrica do agente: uma função SEM argumentos que devolve um Agent novo a cada chamada.
# Por que fábrica e não uma variável global? Porque `rodar()` pode precisar reconstruir o
# agente com um modelo diferente após um recuo para o Ollama (o modelo é resolvido de novo
# via modelo() a cada chamada da fábrica).
def criar_agente() -> Agent:
    return Agent(
        name="Primeiro agente",
        # `instructions` é o "manual do funcionário": o que ele SEMPRE deve fazer,
        # independentemente da pergunta do usuário. Equivale ao role "system" de um LLM cru.
        instructions="Você é um agente de teste e responde de forma objetiva.",
        # model=modelo() evita que o SDK caia no modelo padrão da OpenAI (que exigiria
        # uma chave da OpenAI de verdade e quebraria com Zen/Ollama).
        model=modelo()
    )


# 3. Ponto de entrada com a execução do Runner encapsulada e recuo para Ollama.
# Hábito 2 do exercício 1.2: encapsular a execução em main() evita que o script dispare
# uma chamada de rede automaticamente só por ser importado por outro módulo.
def main():
    # rodar() chama Runner.run_sync(criar_agente(), mensagem) por baixo dos panos.
    # run_sync devolve um RunResult — um objeto RICO, não uma string (ver exercício 1.1:
    # "imprimir resultado e resultado.final_output" para comparar os dois).
    resultado = rodar(criar_agente, "Quem é o presidente da Argentina?")
    # Hábito 1 do exercício 1.2: usar .final_output extrai só o texto da resposta final,
    # descartando o restante do objeto (histórico de turnos, uso de tokens, etc.).
    # Aqui é uma string porque não definimos output_type (isso é a Seção 4, feita em aula2).
    print(resultado.final_output)


if __name__ == "__main__":
    # Garante que `main()` só roda quando o arquivo é executado diretamente
    # (python -m aula1.agente1), não quando é importado por outro módulo.
    main()
