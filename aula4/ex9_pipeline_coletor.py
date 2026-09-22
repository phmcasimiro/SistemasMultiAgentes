# ex9_pipeline_coletor.py — Aula 4 (A2A), Exercício 9: "Encadeando 3 estágios pelo
# tópico" — 1º estágio da esteira (Coletor).
#
# Conceito central (slide "Encadeando 3 estágios pelo tópico"): tecnicamente NADA NOVO
# em relação ao que já vimos — é a soma do Lab 2 (subscriber + LLM, exercícios 5/6) com
# o publish encadeado do Exercício 7. O que muda é o DESENHO: em vez de um publisher e
# vários assinantes independentes (fan-out, como no ex6), aqui a saída de um estágio é a
# ENTRADA do próximo, formando uma esteira:
#
#   Coletor (este arquivo) --publica--> {PREFIXO}/pipeline/entrada
#   Triagem (ex9_pipeline_triagem.py)  --assina entrada, classifica, publica--> {PREFIXO}/pipeline/juridico
#   Jurídico (ex9_pipeline_juridico.py) --assina .../juridico, dá o parecer final
#
# Cada estágio só conhece o tópico de ENTRADA que assina e o de SAÍDA que publica —
# nunca os vizinhos do vizinho (o Coletor não sabe que existe um Jurídico na esteira).
#
# Este arquivo é só o publisher inicial — mesmo papel do ex4_mqtt_pub.py, mudando o
# tópico e o formato da mensagem. Sem Agent/Runner/provedor, sem sys.path.

import os
import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

if __name__ == "__main__":
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.connect(BROKER, PORT)

    # `relato` é o texto que os próximos estágios (Triagem e Jurídico) vão usar como
    # entrada do LLM — sem ele, os dois teriam só um "id" e nenhum conteúdo para avaliar.
    ocorrencia = {
        "id": 9001,
        "tipo": "roubo",
        "local": "Ceilândia",
        "relato": "Roubo à mão armada em estabelecimento comercial em Ceilândia.",
    }
    cli.publish(f"{PREFIXO}/pipeline/entrada", json.dumps(ocorrencia))
    print("ocorrência publicada na esteira:", ocorrencia)

    # Publica e SEGUE — mesmo comportamento "assíncrono" do ex4_mqtt_pub.py. O Coletor
    # não fica esperando a Triagem nem o Jurídico terminarem de processar.
    cli.disconnect()

# Como testar a esteira completa (3 terminais, da raiz do projeto, com a venv ativada):
#   Terminal 1: python -m aula4.ex9_pipeline_juridico   (fica ouvindo, é o último estágio)
#   Terminal 2: python -m aula4.ex9_pipeline_triagem    (fica ouvindo, é o estágio do meio)
#   Terminal 3: python -m aula4.ex9_pipeline_coletor    (publica e termina, dispara a esteira)
#
# Pergunta do deck para refletir: o que aconteceria se a Triagem (Terminal 2) caísse no
# meio da esteira, depois de você já ter rodado o Coletor? O Jurídico nunca receberia
# nada, e o Coletor nem perceberia — a ocorrência ficaria "perdida" em trânsito, porque
# não existe uma fila persistente aqui (ver "Mensageria/Filas" no README.md §6).
