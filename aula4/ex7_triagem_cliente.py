# ex7_triagem_cliente.py — Aula 4 (A2A), Exercício 7: "Request/Reply sobre MQTT"
# (lado CLIENTE). Par de `ex7_juridico_servico.py` — rode o serviço primeiro, em outro
# terminal, antes deste arquivo.
#
# Este arquivo NÃO usa Agent/Runner/provedor — quem tem o LLM é o SERVIÇO
# (ex7_juridico_servico.py); o cliente só monta um pedido, publica, e espera a resposta
# chegar por outro tópico. Por isso, ao contrário do serviço, este arquivo não precisa
# do truque de `sys.path` (mesmo caso do ex4_mqtt_pub.py e ex6_mqtt_estatistica.py).

import os
import json
import time

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")


def on_message(client, userdata, msg):
    """Roda quando a RESPOSTA chega no tópico .../juridico/resposta."""
    resposta = json.loads(msg.payload)
    print(f"[resposta] id={resposta.get('id')} -> {resposta.get('parecer')}")


if __name__ == "__main__":
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.on_message = on_message
    cli.connect(BROKER, PORT)

    # ⚠️ ORDEM IMPORTA (ponto central do exercício, ver README.md §5.1): o cliente
    # ASSINA a resposta ANTES de publicar o pedido. Se publicasse o pedido primeiro, e o
    # serviço fosse rápido o bastante, a resposta poderia chegar ANTES de a assinatura
    # existir — e MQTT não guarda mensagens para quem assina depois (diferente de uma
    # fila de verdade; ver "Mensageria/Filas" no README.md §6). A mensagem simplesmente
    # se perderia, sem nenhum erro avisando.
    cli.subscribe(f"{PREFIXO}/juridico/resposta")

    # `loop_start()` roda o laço de rede do paho-mqtt numa THREAD em segundo plano — ao
    # contrário de `loop_forever()` (usado no serviço), ele NÃO bloqueia esta linha, o
    # que permite ao script continuar e publicar o pedido logo em seguida.
    cli.loop_start()

    pedido = {"id": 1, "resumo": "Furto de veículo na Asa Norte, sem vítimas, câmeras próximas."}
    cli.publish(f"{PREFIXO}/juridico/analisar", json.dumps(pedido))
    print(f"[pedido] id={pedido['id']} publicado, aguardando resposta do serviço Jurídico...")

    # Como este é um script de demonstração "de uma vez só" (não um serviço que fica
    # ouvindo para sempre), esperamos alguns segundos para dar tempo do round-trip
    # completo (pedido -> serviço processa com o LLM -> resposta) antes de encerrar.
    # Numa aplicação real, isso seria substituído por algo mais robusto (ex.: um
    # `Event` que o `on_message` sinaliza ao receber a resposta certa).
    time.sleep(6)

    cli.loop_stop()
    cli.disconnect()

# Como testar (2 terminais, da raiz do projeto, com a venv ativada):
#   Terminal 1 (o serviço, fica ouvindo): python -m aula4.ex7_juridico_servico
#   Terminal 2 (este arquivo, pede e aguarda): python -m aula4.ex7_triagem_cliente
