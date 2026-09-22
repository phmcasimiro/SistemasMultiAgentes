# teste.py — Aula 4 (A2A), Seção "02 · Setup" do deck: checagem rápida de que o
# ambiente está funcionando ANTES de começar os exercícios. O deck só pede que rodar
# este arquivo imprima "ambiente ok!" — se isso acontecer, o .env e o provedor.py estão
# lidos corretamente e dá para seguir para o ex1_agente_handoff.py.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
# Sem esta linha, rodar "python aula4/teste.py" direto dá
# "ModuleNotFoundError: No module named 'provedor'", porque o Python só olha a pasta
# do próprio arquivo (aula4/) e o diretório atual — e provedor.py mora um nível acima.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner
from provedor import configurar, modelo

# Liga o SDK ao provedor definido no .env (Zen/Ollama/OpenAI) antes de criar o Agent.
configurar()

# `model=modelo()` é obrigatório: sem ele, o SDK tenta usar o modelo padrão da OpenAI,
# que não existe no provedor configurado (Zen/Ollama) e gera erro de "modelo não encontrado".
agente = Agent(name="Teste", instructions="Responda em uma frase", model=modelo())

resultado = Runner.run_sync(agente, "Diga 'ambiente ok!'.")
# .final_output (com PONTO, não vírgula) é o texto da resposta — resultado.final_output
# é um atributo do objeto RunResult, não um segundo argumento para o print().
print(resultado.final_output)
