# ex4_mqtt_pub.py — Aula 4 (A2A), Lab 2 · Exercício 4: "Coletor (publisher)".
#
# Conceito central (slide "Três formas de trocar mensagens" e "Broker, tópico,
# publish/subscribe"): até o ex3, os agentes conversavam SÍNCRONO e no MESMO PROCESSO
# (handoff/as_tool — A rodava, chamava B, e ficava parado esperando a resposta de B).
# Aqui é o oposto: A2A ASSÍNCRONO e DISTRIBUÍDO, usando MQTT.
#
#   - Um BROKER é um intermediário: ninguém fala direto com ninguém. Este agente
#     ("Coletor") só PUBLICA uma mensagem num TÓPICO (uma string, tipo um endereço) e
#     SEGUE — ele não sabe, e não precisa saber, se existe alguém ouvindo do outro lado.
#   - Quem quiser receber essa mensagem PRECISA "assinar" (subscribe) o mesmo tópico —
#     isso é feito no próximo exercício (ex5_mqtt_sub.py, a Triagem), rodando num
#     processo SEPARADO (outro terminal), que ainda não existe nesta pasta.
#   - Publicar e assinar são desacoplados: o Coletor pode publicar mesmo que ninguém
#     esteja ouvindo no momento (a mensagem simplesmente não é recebida por ninguém).
#
# Diferença importante em relação aos scripts anteriores: este arquivo NÃO cria nenhum
# `Agent` nem chama `Runner` — é só uma troca de mensagem "crua", sem IA envolvida.
# Por isso ele não usa `provedor.py` (que só existe para configurar o provedor de LLM) e,
# consequentemente, não precisa do truque de `sys.path.insert(...)` usado nos outros
# arquivos desta pasta (esse truque só é necessário para importar `provedor`).

import os
import json

# `paho.mqtt.client` é a biblioteca (já em requirements.txt) que implementa o protocolo
# MQTT em Python — o "telefone" que fala com o broker.
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Mesma lógica de sempre: lê o .env da raiz do curso (dotenv encontra o arquivo andando
# para cima nas pastas a partir deste arquivo, sem precisar de sys.path) e disponibiliza
# as variáveis abaixo via os.getenv().
load_dotenv()

# As três variáveis novas desta aula (ver .env, seção "MQTT"):
#   MQTT_BROKER  -> endereço do intermediário (aqui, um broker PÚBLICO e gratuito).
#   MQTT_PORT    -> porta de conexão MQTT "crua" (sem criptografia) — padrão 1883.
#   MQTT_PREFIXO -> um "namespace" só seu dentro do broker compartilhado (ex.: pcdf/demo).
#     Como o broker é público, qualquer pessoa no mundo pode publicar/assinar tópicos
#     nele — o prefixo é o que isola o seu tráfego do de outra dupla/turma usando o
#     mesmo broker ao mesmo tempo.
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

# ⚠️ LGPD (mesmo aviso do deck, slide "Preparar o ambiente"): este broker é PÚBLICO —
# qualquer pessoa pode ler o que for publicado nele. Por isso os dados aqui são só de
# exemplo/fictícios. NUNCA publique CPF, nome completo ou qualquer dado pessoal real
# num broker público como este.


if __name__ == "__main__":
    # `callback_api_version=...` é exigido pelo paho-mqtt na versão 2.x (a que este
    # projeto usa) — sem esse argumento, o construtor ainda funciona, mas imprime um
    # aviso de depreciação no terminal. Passá-lo explicitamente evita esse ruído e deixa
    # claro qual versão da API de callbacks está em uso (não usamos callbacks neste
    # arquivo, mas o parâmetro é do construtor do cliente, então é preciso de qualquer
    # forma).
    cli = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cli.connect(BROKER, PORT)

    # A "ocorrência" é só um dicionário Python comum. `json.dumps(...)` o transforma em
    # texto (formato JSON) porque o MQTT só transporta bytes/texto — não sabe o que é um
    # dicionário Python.
    ocorrencia = {"id": 123, "tipo": "furto", "local": "Asa Norte"}

    # O tópico é montado com f-string a partir do PREFIXO do .env — é assim que cada
    # dupla/turma isola seu tráfego dentro do broker compartilhado. Rodar isto entrega a
    # mensagem ao broker; o broker é quem se encarrega de repassá-la para quem estiver
    # assinando este mesmo tópico (ver ex5_mqtt_sub.py).
    cli.publish(f"{PREFIXO}/ocorrencias/nova", json.dumps(ocorrencia))
    print("ocorrência publicada:", ocorrencia)

    # `disconnect()` logo em seguida, SEM esperar resposta de ninguém: publicar e seguir
    # é exatamente o que torna isto "assíncrono" — compare com o handoff do ex1, onde
    # `Runner.run_sync(...)` ficava PARADO até a resposta do outro agente chegar.
    cli.disconnect()

# Como testar de verdade (par publisher/subscriber): rode este arquivo só depois de ter
# o ex5_mqtt_sub.py (Triagem) já rodando e ouvindo em outro terminal — senão a mensagem
# é publicada e, como ninguém assinou o tópico a tempo, se perde (não fica guardada em
# nenhuma fila; ver o exercício 9 do deck sobre esse mesmo risco num pipeline maior).
#   Terminal 1 (roda e fica ouvindo): python -m aula4.ex5_mqtt_sub
#   Terminal 2 (publica e termina):   python -m aula4.ex4_mqtt_pub
