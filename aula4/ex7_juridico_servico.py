# ex7_juridico_servico.py — Aula 4 (A2A), Exercício 7: "Request/Reply sobre MQTT"
# (lado SERVIÇO). Par de `ex7_triagem_cliente.py`.
#
# Conceito central (slide "Request/Reply sobre MQTT"): MQTT é nativamente Pub/Sub — não
# existe "pedir e receber a resposta" pronto no protocolo. Simulamos isso com DOIS
# tópicos e dois papéis:
#
#   {PREFIXO}/juridico/analisar  -> cliente (Triagem) publica; SERVIÇO (este arquivo) assina
#   {PREFIXO}/juridico/resposta  -> SERVIÇO (este arquivo) publica; cliente (Triagem) assina
#
# Do ponto de vista de quem chama (o cliente), parece síncrono — "pedi e recebi". Mas por
# baixo são DOIS PROCESSOS, DOIS TÓPICOS, e nenhuma garantia de resposta se este serviço
# cair no meio do caminho (diferente de `Runner.run_sync`, que ou devolve uma resposta ou
# lança uma exceção — aqui, se o serviço estiver fora do ar, o cliente simplesmente nunca
# recebe nada, sem nenhum erro).

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
# Necessário aqui porque este arquivo usa Agent/Runner/provedor (diferente do cliente
# deste mesmo exercício, que não precisa de LLM nenhum — ver ex7_triagem_cliente.py).
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
# automático Zen -> Ollama). Ver o comentário completo em ex5_mqtt_sub.py.
def criar_agente() -> Agent:
    return Agent(
        name="Jurídico",
        instructions="Avalie o enquadramento legal e cite o artigo provável, em 2 linhas.",
        model=modelo(),
    )


def on_message(client, userdata, msg):
    """Roda a cada PEDIDO que chega no tópico .../juridico/analisar."""
    try:
        pedido = json.loads(msg.payload)

        # Síncrono aqui dentro (igual ex5_mqtt_sub.py): o serviço só publica a resposta
        # depois que `rodar()` devolver o parecer completo. Usar `rodar()` em vez de
        # `Runner.run_sync` direto é o que dá ao serviço o mesmo recuo automático
        # Zen -> Ollama do `aula1/agente1.py` — sem isso, um erro como
        # `403 Model access is disabled` na Zen derruba o serviço inteiro no meio do
        # primeiro pedido, e o cliente (ex7_triagem_cliente.py) nunca recebe resposta.
        parecer = rodar(criar_agente, str(pedido)).final_output

        # `"id": pedido.get("id")` é o que permite ao cliente casar esta resposta com o
        # pedido certo, caso hajam vários pedidos em voo ao mesmo tempo.
        resposta = {"id": pedido.get("id"), "parecer": parecer}

        # `client` aqui é o MESMO objeto Client que recebeu a mensagem (o paho-mqtt
        # passa ele como 1º argumento do callback) — por isso dá para publicar a
        # resposta com ele, sem precisar guardar uma referência separada ao cliente MQTT.
        client.publish(f"{PREFIXO}/juridico/resposta", json.dumps(resposta))
        print(f"[serviço] pedido {pedido.get('id')} respondido.")
    except Exception as exc:
        # Mesmo se os DOIS provedores falharem (ou o payload vier malformado), o
        # serviço continua ouvindo o PRÓXIMO pedido em vez de morrer — ver a mesma
        # proteção, com mais detalhe, em ex5_mqtt_sub.py.
        print(f"[ERRO] não foi possível processar o pedido: {exc}")


if __name__ == "__main__":
    # callback_api_version=... é exigido pelo paho-mqtt 2.x (mesmo ajuste dos demais
    # exercícios de MQTT) para não emitir aviso de depreciação.
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/juridico/analisar")
    print("Serviço Jurídico ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()

# Como testar (2 terminais, da raiz do projeto, com a venv ativada):
#   Terminal 1 (este arquivo, fica ouvindo): python -m aula4.ex7_juridico_servico
#   Terminal 2 (o cliente, pede e aguarda):  python -m aula4.ex7_triagem_cliente
