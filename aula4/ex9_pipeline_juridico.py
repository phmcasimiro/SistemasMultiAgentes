# ex9_pipeline_juridico.py — Aula 4 (A2A), Exercício 9: 3º e último estágio da esteira
# (Jurídico).
#
# Fim da linha: este estágio só assina {PREFIXO}/pipeline/juridico (o que a Triagem
# publica) e não publica nada adiante — ele é quem "fecha" a esteira, dando o parecer
# final. Ver ex9_pipeline_coletor.py para o desenho completo e como testar os três
# estágios juntos.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from agents import Agent
from provedor import configurar, modelo, rodar

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

configurar()


# Fábrica em vez de Agent pronto — é o que permite usar `rodar()` abaixo (recuo
# automático Zen -> Ollama). Ver o comentário completo em ex5_mqtt_sub.py. Mesma
# persona do Jurídico já vista em ex1/ex2/ex3/ex7 — mais uma vez, o que muda é só de
# onde a mensagem chega (aqui, o tópico de saída da Triagem na esteira).
def criar_agente() -> Agent:
    return Agent(
        name="Jurídico",
        instructions="Avalie o enquadramento legal e cite o artigo provável, em 2 linhas.",
        model=modelo(),
    )


def on_message(client, userdata, msg):
    try:
        dados = json.loads(msg.payload)

        # Usa o "relato" original (não a "classificacao" da Triagem) como entrada do
        # parecer jurídico — cada estágio decide, com suas próprias instructions, o que
        # fazer com os dados que recebeu; nada obriga o Jurídico a usar o que a Triagem
        # concluiu, só a ter acesso a essa informação (ela vem junto no payload).
        parecer = rodar(criar_agente, dados.get("relato", "")).final_output

        print(
            f"[{dados.get('id')}] Jurídico -> {parecer}\n"
            f"    (classificação da Triagem: {dados.get('classificacao')})"
        )
    except Exception as exc:
        # Fim da esteira: se este estágio morresse aqui, você nem saberia que a
        # ocorrência chegou até o Jurídico e falhou só no último passo — mesma
        # proteção do ex5_mqtt_sub.py.
        print(f"[ERRO] Jurídico não conseguiu processar a mensagem: {exc}")


if __name__ == "__main__":
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/pipeline/juridico")
    print("Jurídico (esteira) ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
