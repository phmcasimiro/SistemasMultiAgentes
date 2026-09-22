# ex1_agente_handoff.py — Aula 4 (A2A), Lab 1 · Exercício 1: "Handoff básico".
#
# Conceito central (slide "Handoff", Lab 1): handoff é a forma mais simples de
# comunicação Agente-a-Agente (A2A) do SDK. Em vez de UM agente chamar uma FUNÇÃO Python
# comum (como fizemos com @function_tool na Aula 1), ele passa o "bastão" da conversa
# para OUTRO AGENTE, que assume e responde no lugar dele. É a mesma ideia já vista em
# `aula2/agente_handoff.py` — aqui ela ganha o nome A2A porque o foco da aula é como
# agentes conversam entre si, não só com ferramentas.
#
# Importante (slide "Handoff"): tudo isso acontece SÍNCRONO e IN-PROCESS — os dois
# agentes rodam no mesmo programa Python, na mesma máquina, sem nenhuma rede envolvida.
# É o oposto do que a Aula 4 também ensina com MQTT (assíncrono, entre processos
# separados, via um "broker" intermediário) — mas isso fica para os exercícios seguintes.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
# Sem esta linha, "python aula4/ex1_agente_handoff.py" dá
# "ModuleNotFoundError: No module named 'provedor'", porque o Python só procura módulos
# na pasta do próprio arquivo (aula4/) e no diretório atual — e provedor.py mora um
# nível acima, na raiz do curso.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner
from provedor import configurar, modelo

# Liga o SDK ao provedor definido no .env (Zen/Ollama/OpenAI) ANTES de criar qualquer
# Agent — é `configurar()` que decide para onde as chamadas de rede vão.
configurar()

# Agente especialista: só entra em ação quando o Triagem decide encaminhar para ele.
# Repare que ele não sabe nada sobre "handoff" — para ele, é só mais uma conversa normal.
juridico = Agent(
    name="Jurídico",
    instructions="Avalie o enquadramento legal da ocorrência e cite o artigo provável.",
    # model=modelo() é obrigatório em TODO Agent deste curso: sem ele, o SDK tenta usar
    # o modelo padrão da OpenAI, que não existe no provedor configurado (Zen/Ollama) e
    # gera o erro "model not found" (ver aula1.md, Seção 4 — Post-Mortem).
    model=modelo(),
)

# Agente triador: recebe a ocorrência primeiro e decide, sozinho, se resolve ele mesmo
# ou se transfere para o Jurídico.
triagem = Agent(
    name="Triagem",
    instructions=(
        "Classifique a ocorrência (tipo e gravidade). "
        "Se houver indício de crime, encaminhe ao agente Jurídico."
    ),
    model=modelo(),
    # `handoffs=[...]` é o que diferencia um handoff de uma tool comum: em vez de uma
    # função Python, a lista contém OUTROS AGENTS. Por baixo dos panos, o SDK transforma
    # cada um numa ferramenta especial chamada `transfer_to_<nome>` — mas quem decide SE
    # e QUANDO chamar essa "ferramenta" continua sendo o modelo, lendo as `instructions`
    # acima. Nenhuma linha deste arquivo diz "se for crime, chame o Jurídico" em Python;
    # essa decisão é 100% do modelo, em linguagem natural.
    handoffs=[juridico],
)

# Aviso esperado ao rodar (não é erro): o SDK monta o nome da ferramenta de handoff a
# partir do `name` do agente ("Jurídico" -> "transfer_to_Jurídico") e depois normaliza
# esse nome para caber nas regras de function calling (só letras sem acento, dígitos e
# underscore), virando "transfer_to_jur_dico". O aviso é só informativo — o roteamento
# funciona normalmente; ele aparece por causa do acento em "Jurídico".


def main() -> None:
    ocorrencia = "Furto de veículo na Asa Norte, sem vítimas, câmeras próximas."
    resultado = Runner.run_sync(triagem, ocorrencia)
    # .final_output é o texto de quem RESPONDEU DE FATO — no handoff, se a transferência
    # aconteceu, quem responde é o Jurídico, não mais a Triagem. Para confirmar quem
    # respondeu, dá para checar `resultado.last_agent.name` (não usado aqui, mas é assim
    # que se audita o roteamento sem escrever nenhum if/else).
    print(resultado.final_output)

    # "O que observar" (slide do exercício): troque a ocorrência abaixo por algo trivial,
    # sem indício de crime, e confirme que a Triagem NÃO aciona o Jurídico — quem decide
    # é sempre o modelo, a partir das instructions, nunca um if escrito à mão.
    # ocorrencia_trivial = "Bicicleta encontrada e devolvida ao dono na mesma tarde."
    # print(Runner.run_sync(triagem, ocorrencia_trivial).final_output)


if __name__ == "__main__":
    # Encapsular a execução em main() (hábito já visto em aula1/agente1.py) evita que
    # este arquivo dispare uma chamada de rede sozinho, só por ser importado por outro
    # módulo — a chamada só acontece quando você roda este arquivo diretamente.
    main()
