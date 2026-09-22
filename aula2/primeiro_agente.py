# primeiro_agente.py — o mesmo padrão da Seção 1 da Aula 1 (Agent + Runner), reempacotado
# numa função `executar_agente(mensagem)` para ser importado por `main.py` (rota POST /tools)
# e usado como especialista de baseline nas comparações desta aula.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent
from provedor import configurar, modelo, rodar

# Liga o cliente OpenAI-compatível certo (Zen, Ollama ou OpenAI) conforme o .env.
# Roda uma única vez, na importação do módulo — necessário porque `criar_agente()`
# e `executar_agente()` dependem de `modelo()` já estar resolvendo o provedor certo.
configurar()


# Fábrica do agente: declara o modelo do provedor ativo (modelo()).
# É uma função (não uma variável global) para poder ser reconstruída pelo `rodar()`
# caso o provedor principal falhe e seja necessário recuar para o Ollama.
def criar_agente() -> Agent:
    return Agent(
        name="Primeiro agente",
        instructions="Você é um agente de teste. Responda em poucas palavras e de forma objetiva. "
        "Se não souber a resposta, diga que não sabe.",
        model=modelo()
    )


# Função de conveniência que encapsula fábrica + execução + extração do texto final,
# para que outros módulos (main.py) não precisem conhecer Agent/Runner diretamente —
# só chamam `executar_agente("pergunta")` e recebem uma string pronta.
def executar_agente(mensagem: str) -> str:
    # rodar() = Runner.run_sync(criar_agente(), mensagem) com recuo automático para Ollama
    # se o provedor principal (Zen) falhar.
    resultado = rodar(criar_agente, mensagem)
    # .final_output extrai só o texto da resposta, descartando o resto do RunResult.
    return resultado.final_output
