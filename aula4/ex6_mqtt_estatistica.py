# ex6_mqtt_estatistica.py — Aula 4 (A2A), Lab 2 · Exercício 6: "Um terceiro assinante".
#
# Conceito central (slide "Desafio guiado · Um terceiro assinante"): este arquivo prova,
# na prática, o que o desacoplamento do Pub/Sub (ex4/ex5) permite. A Estatística assina
# o MESMO tópico que a Triagem (ex5_mqtt_sub.py) já assinava — sem tocar em UMA LINHA do
# Coletor (ex4_mqtt_pub.py) nem da Triagem. Adicionar um novo "ouvinte" é só rodar mais
# um processo que assina o mesmo tópico; o publicador nem fica sabendo que agora existem
# dois consumidores em vez de um.
#
# Diferente da Triagem, este agente NÃO usa LLM — é só contagem pura em Python
# (collections.Counter), por isso não importa Agent/Runner/provedor nem precisa do
# truque de sys.path (mesmo caso do ex4_mqtt_pub.py: sem `provedor`, sem sys.path).

import os
import json
from collections import Counter

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

# `Counter` é um dicionário especializado em contar: `contagem["furto"] += 1` funciona
# mesmo na primeira vez (chave ainda não existe), porque todo valor não visto antes
# começa em 0 automaticamente — evita escrever um `if "furto" not in contagem: ...`.
contagem = Counter()


def on_message(client, userdata, msg):
    oc = json.loads(msg.payload)
    # `.get("tipo", "desconhecido")` evita um KeyError se, por algum motivo, chegar uma
    # mensagem sem o campo "tipo" — vira "desconhecido" em vez de quebrar o programa.
    contagem[oc.get("tipo", "desconhecido")] += 1
    print("Ocorrências por tipo:", dict(contagem))


if __name__ == "__main__":
    # callback_api_version=... é exigido pelo paho-mqtt 2.x (mesmo ajuste do ex4/ex5)
    # para não emitir aviso de depreciação.
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.on_message = on_message
    cli.connect(BROKER, PORT)

    # MESMO tópico do ex5_mqtt_sub.py (mesmo PREFIXO, do mesmo .env) — é só isso que faz
    # este processo também receber as mensagens que o Coletor publica. Repare que o
    # Coletor (ex4) e a Triagem (ex5) não precisaram de NENHUMA alteração para isso
    # funcionar: o broker entrega a mesma mensagem para todo mundo que assinou o tópico.
    cli.subscribe(f"{PREFIXO}/ocorrencias/#")
    print("Estatística ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()

# Como testar (3 terminais, na raiz do projeto, com a venv ativada):
#   Terminal 1: python -m aula4.ex5_mqtt_sub          (Triagem — classifica com LLM)
#   Terminal 2: python -m aula4.ex6_mqtt_estatistica  (Estatística — só conta por tipo)
#   Terminal 3: python -m aula4.ex4_mqtt_pub           (publica e termina)
# Publique 2-3 vezes (mude o "tipo" no ex4 entre uma publicação e outra) e confirme que
# TANTO a Triagem quanto a Estatística recebem cada mensagem, de forma independente.
