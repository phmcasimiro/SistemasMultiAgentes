# ex2_agente_handoff_roteamento.py — Aula 4 (A2A), Lab 1 · Exercício 2: "Roteamento
# entre múltiplos especialistas".
#
# Conceito central (slide "O que muda"): este exercício NÃO introduz nenhuma classe ou
# mecanismo novo em relação ao ex1_agente_handoff.py — a única diferença é que
# `handoffs=[...]` agora tem DOIS agentes em vez de um, e as `instructions` do Triagem
# explicam o critério de escolha entre eles. Ou seja: o esforço de programar um "roteador"
# vira esforço de ESCREVER BEM as instructions — o modelo é quem decide para qual dos
# dois (ou nenhum) a conversa deve ir, olhando o conteúdo de cada ocorrência.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner
from provedor import configurar, modelo

configurar()

# Especialista 1: para ocorrências com indício de crime.
juridico = Agent(
    name="Jurídico",
    instructions="Avalie o enquadramento legal e cite o artigo provável, em 2 linhas.",
    model=modelo(),
)

# Especialista 2: para registros puramente administrativos, sem crime.
# Note que "estatistica" não sabe nada sobre "juridico", nem vice-versa — cada um só
# conhece a própria especialidade. Quem sabe que os dois existem, e quando usar cada um,
# é só o Triagem (via `handoffs=[...]` abaixo).
estatistica = Agent(
    name="Estatística",
    instructions="Registre a ocorrência para fins estatísticos e diga a categoria, em 1 linha.",
    model=modelo(),
)

triagem = Agent(
    name="Triagem",
    instructions=(
        "Você tria ocorrências. Se houver indício de crime, encaminhe ao Jurídico. "
        "Se for apenas um registro administrativo sem crime, encaminhe à Estatística."
    ),
    model=modelo(),
    # Lista com DOIS destinos possíveis (em vez de um só, como no ex1). O SDK cria uma
    # ferramenta transfer_to_<nome> para CADA agente da lista; o modelo escolhe no máximo
    # uma delas — ou nenhuma, se a ocorrência não se encaixar em nenhum dos dois perfis.
    handoffs=[juridico, estatistica],
)


def main() -> None:
    # Dois casos propositalmente de perfis diferentes: o primeiro deve ir para o
    # Jurídico (é um crime), o segundo deve ir para a Estatística (é só um registro).
    casos = [
        "Roubo à mão armada em estabelecimento comercial em Ceilândia.",
        "Registro de achados e perdidos: bicicleta encontrada no Parque da Cidade.",
    ]
    for caso in casos:
        resultado = Runner.run_sync(triagem, caso)
        # `resultado.last_agent.name` mostra QUEM respondeu de fato — útil aqui para
        # confirmar, caso a caso, que o roteamento escolheu o especialista esperado.
        print(f"[{resultado.last_agent.name}] {resultado.final_output}")


if __name__ == "__main__":
    main()
