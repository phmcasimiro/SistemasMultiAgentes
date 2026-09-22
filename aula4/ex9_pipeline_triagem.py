# ex9_pipeline_triagem.py — Aula 4 (A2A), Exercício 9: 2º estágio da esteira (Triagem).
#
# Este estágio só conhece DOIS tópicos: assina {PREFIXO}/pipeline/entrada (o que o
# Coletor publica) e publica em {PREFIXO}/pipeline/juridico (o que o Jurídico vai
# assinar). Ele não sabe que existe um "Coletor" ou um "Jurídico" — só sabe ouvir de um
# lugar e falar para outro. Ver ex9_pipeline_coletor.py para o desenho completo da
# esteira e como testar os três estágios juntos.

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
# persona da Triagem já vista em ex1/ex2/ex5 — o que muda é só de onde a mensagem chega
# (aqui, o tópico de entrada da esteira, em vez de handoff ou de .../ocorrencias).
def criar_agente() -> Agent:
    return Agent(
        name="Triagem",
        instructions="Classifique a ocorrência recebida (tipo e gravidade) em uma linha.",
        model=modelo(),
    )


def on_message(client, userdata, msg):
    try:
        oc = json.loads(msg.payload)

        # `rodar()` em vez de `Runner.run_sync` direto: se este estágio ficar sem
        # resposta da Zen, ele recua sozinho para o Ollama em vez de travar a esteira
        # inteira aqui no meio do caminho.
        classificacao = rodar(criar_agente, str(oc)).final_output

        # Repassa a ocorrência ADIANTE na esteira, agora com a classificação anexada —
        # o Jurídico (próximo estágio) recebe tanto o relato original quanto o que a
        # Triagem já concluiu, sem precisar reprocessar do zero.
        saida = {"id": oc.get("id"), "relato": oc.get("relato"), "classificacao": classificacao}
        client.publish(f"{PREFIXO}/pipeline/juridico", json.dumps(saida))
        print(f"[{oc.get('id')}] Triagem -> {classificacao}  (encaminhado ao Jurídico)")
    except Exception as exc:
        # Sem isso, uma única ocorrência problemática (ou os DOIS provedores fora do
        # ar) derrubaria este estágio, e o Jurídico nunca mais receberia nada de
        # ninguém — mesma proteção do ex5_mqtt_sub.py.
        print(f"[ERRO] Triagem não conseguiu processar a mensagem: {exc}")


if __name__ == "__main__":
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/pipeline/entrada")
    print("Triagem (esteira) ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
