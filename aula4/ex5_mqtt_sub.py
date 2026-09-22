# ex5_mqtt_sub.py — Aula 4 (A2A), Lab 2 · Exercício 5: "Triagem (subscriber + LLM)".
#
# Conceito central (slide "O pulo do gato"): este arquivo é o par do ex4_mqtt_pub.py —
# junto, os dois formam a primeira troca A2A assíncrona e DISTRIBUÍDA do curso (cada um
# roda num processo/terminal separado). O Coletor (ex4) publica; a Triagem (este
# arquivo) assina o mesmo tópico e, quando uma mensagem chega, usa um `Agent` de verdade
# (com LLM) para classificá-la.
#
# O ponto pedagógico central: o Coletor NÃO CONHECE a Triagem, e a Triagem NÃO CONHECE o
# Coletor — os dois só compartilham um TÓPICO. Isso é "desacoplamento": dá para trocar,
# escalar ou adicionar novos consumidores (ver ex6, um "terceiro assinante") sem mexer em
# quem publica. Compare com o handoff do ex1, onde a Triagem tinha uma referência direta
# ao objeto `juridico` — aqui não existe nenhuma referência direta entre os dois lados.
#
# Diferente do ex4 (puro MQTT, sem IA), este arquivo VOLTA a usar Agent/Runner/provedor
# — por isso precisa do mesmo "truque" de sys.path dos exercícios 1-3.

import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
# Necessário aqui porque, diferente do ex4_mqtt_pub.py, este arquivo importa `provedor`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from agents import Agent
from provedor import configurar, modelo, rodar

# Mesma leitura de .env do ex4 — os dois lados (Coletor e Triagem) usam o MESMO
# PREFIXO para se encontrarem no broker compartilhado.
load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

# Liga o SDK ao provedor definido no .env (Zen/Ollama/OpenAI) ANTES de criar o Agent.
configurar()


# Fábrica (função sem argumentos que devolve um Agent novo) em vez de um Agent pronto no
# nível do módulo. Isso é o que permite usar `rodar()` abaixo: se a Zen falhar no meio de
# um `on_message`, `rodar()` reconstrói o agente chamando esta função de novo, já com
# `model=modelo()` apontando para o Ollama local — a mesma resiliência do
# `aula1/agente1.py`, agora dentro de um serviço que fica ouvindo para sempre.
def criar_agente() -> Agent:
    return Agent(
        name="Triagem",
        instructions="Classifique a ocorrência recebida (tipo e gravidade) em uma linha.",
        model=modelo(),
    )


def on_message(client, userdata, msg):
    """Callback do paho-mqtt: roda TODA VEZ que chega uma mensagem no tópico assinado.

    A assinatura (client, userdata, msg) é fixa — é o próprio paho-mqtt quem chama esta
    função e decide os três argumentos; nós só implementamos o que fazer com `msg`.
    """
    try:
        # `msg.payload` chega como bytes (texto puro); json.loads(...) desfaz o
        # json.dumps(...) que o ex4_mqtt_pub.py aplicou antes de publicar, devolvendo o
        # dicionário Python original ({"id": 123, "tipo": "furto", "local": "Asa Norte"}).
        oc = json.loads(msg.payload)

        # Aqui SIM é síncrono — dentro deste callback, `rodar()` roda e espera a
        # resposta do modelo normalmente, do mesmo jeito que nos exercícios 1 a 3. O que
        # é assíncrono é a CHEGADA da mensagem (o `on_message` pode disparar a qualquer
        # momento, sem a Triagem ter pedido); o processamento de cada mensagem, uma vez
        # que ela chegou, é síncrono como sempre.
        #
        # `rodar()` (em vez de `Runner.run_sync` direto) tenta primeiro o provedor
        # principal (Zen) e, se ele falhar (ex.: `403 Model access is disabled`, chave
        # expirada, cota estourada), recua sozinho para o Ollama local e tenta de novo —
        # sem isso, uma falha da Zen mataria o serviço inteiro no meio da 1ª mensagem.
        resultado = rodar(criar_agente, str(oc))
        print(f"[{oc.get('id')}] {resultado.final_output}")
    except Exception as exc:
        # Rede de segurança adicional: qualquer outro erro (JSON malformado, falha nos
        # DOIS provedores, etc.) fica só registrado no terminal — o `loop_forever()` no
        # `__main__` continua rodando e recebendo as PRÓXIMAS mensagens normalmente. Sem
        # este `try/except`, uma única mensagem problemática derrubaria o serviço
        # inteiro, exigindo reiniciá-lo manualmente (foi exatamente isso que aconteceu
        # ao testar sem essa proteção).
        print(f"[ERRO] não foi possível processar a mensagem: {exc}")


if __name__ == "__main__":
    # callback_api_version=... é exigido pelo paho-mqtt 2.x (mesmo ajuste do ex4) para
    # não emitir aviso de depreciação. A assinatura de on_message não muda entre as
    # versões da API de callbacks — só a de on_connect mudaria, e este script não define
    # um on_connect próprio.
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    # Registra a função acima como o "ouvinte": o paho-mqtt vai chamá-la sozinho sempre
    # que uma mensagem chegar — nós nunca a chamamos diretamente neste arquivo.
    cli.on_message = on_message

    cli.connect(BROKER, PORT)

    # O "#" no final é um WILDCARD multinível do MQTT: assina TODOS os subtópicos de
    # "{PREFIXO}/ocorrencias/" de uma vez (ex.: .../ocorrencias/nova,
    # .../ocorrencias/urgente etc.) — não precisa assinar um tópico por vez.
    cli.subscribe(f"{PREFIXO}/ocorrencias/#")

    print("Triagem ouvindo... (Ctrl+C para sair)")

    # `loop_forever()` é um laço BLOQUEANTE: o programa fica parado aqui, escutando o
    # broker, até você apertar Ctrl+C. É por isso que este script precisa rodar num
    # terminal separado do ex4_mqtt_pub.py — enquanto ele "ouve", nada mais roda nesse
    # mesmo terminal.
    cli.loop_forever()

# Como testar de verdade (par publisher/subscriber):
#   Terminal 1 (roda e fica ouvindo): python -m aula4.ex5_mqtt_sub
#   Terminal 2 (publica e termina):   python -m aula4.ex4_mqtt_pub
# A classificação da ocorrência deve aparecer no Terminal 1, poucos segundos depois de
# você rodar o Terminal 2.
