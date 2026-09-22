# ex8_fipa_acl.py — Aula 4 (A2A), Exercício 8: "Colocando a performativa em prática".
#
# Conceito central (slide "FIPA-ACL — A linguagem clássica de agentes"): antes dos LLMs,
# agentes já trocavam mensagens PADRONIZADAS entre si. Toda mensagem carrega uma
# INTENÇÃO — não só um texto solto. A FIPA-ACL formaliza isso em cinco campos:
#
#   performative -> a intenção da mensagem: "request" (pedido), "inform" (aviso),
#                    "query" (pergunta)...
#   sender       -> quem enviou
#   receiver     -> para quem foi enviada
#   content      -> o que está sendo pedido/informado (o "corpo" da mensagem)
#   ontology     -> o domínio do conteúdo (aqui, sempre "seguranca-publica")
#   language     -> o idioma do conteúdo (aqui, sempre "pt-BR")
#
# Este arquivo NÃO usa MQTT nem Agent/Runner — é só Python puro, para focar no que
# importa aqui: a ESTRUTURA da mensagem e como o receptor decide o que fazer a partir
# dela. Por isso não precisa do truque de `sys.path`.


def msg_acl(performativa: str, sender: str, receiver: str, content: str, **extra) -> dict:
    """Monta uma mensagem no formato FIPA-ACL (como um dicionário Python).

    `**extra` captura QUALQUER argumento nomeado a mais que você passar (ex.:
    `msg_acl(..., prioridade="alta")`) e injeta no dicionário final via `base.update`,
    sem precisar prever esses campos extras na assinatura da função.
    """
    base = {
        "performative": performativa,
        "sender": sender,
        "receiver": receiver,
        "content": content,
        "ontology": "seguranca-publica",
        "language": "pt-BR",
    }
    base.update(extra)
    return base


def despachar(m: dict) -> None:
    """O receptor: decide o que fazer com a mensagem SÓ pelo campo `performative`.

    Lógica aplicada (slide "Ex 8"): o receptor nunca faz algo como
    `if "classificar" in m["content"]:` — ler o TEXTO LIVRE do conteúdo para decidir
    a ação seria frágil (e, em sistemas com IA, é literalmente a porta de entrada de
    prompt injection — ver aula3/aula3.md §9.2). Ramificar pela `performative`
    (um campo ESTRUTURADO, de valores fechados) é o ponto central da FIPA-ACL: a
    intenção da mensagem é dado de primeira classe, não algo a ser adivinhado do texto.
    """
    perf = m["performative"]
    if perf == "request":
        print(f"[request] {m['sender']} pediu a {m['receiver']}: {m['content']}")
    elif perf == "inform":
        print(f"[inform]  {m['sender']} informou a {m['receiver']}: {m['content']}")
    elif perf == "query":
        print(f"[query]   {m['sender']} perguntou a {m['receiver']}: {m['content']}")
    else:
        # Qualquer performativa não tratada explicitamente ainda tem um caminho —
        # nenhuma mensagem é silenciosamente ignorada só por ter uma intenção nova.
        print(f"[{perf}] {m['sender']} -> {m['receiver']}: {m['content']}")


if __name__ == "__main__":
    # Simula uma pequena troca entre os agentes já vistos nos exercícios anteriores —
    # sem precisar de rede nem de LLM para demonstrar o conceito.
    mensagens = [
        msg_acl("request", "coletor", "triagem", "classificar(ocorrencia-123)"),
        msg_acl("inform", "triagem", "coletor", "ocorrencia-123 classificada: furto, gravidade baixa"),
        msg_acl("query", "estatistica", "triagem", "quantas ocorrências foram classificadas hoje?"),
        msg_acl("inform", "triagem", "estatistica", "3 ocorrências classificadas hoje", prioridade="baixa"),
    ]

    for m in mensagens:
        despachar(m)

    # Modelo mental (slide "FIPA-ACL"): uma mensagem FIPA-ACL de verdade se parece com
    # (request :sender coletor :receiver triagem :content "classificar(ocorrencia-123)"
    #           :ontology seguranca-publica :language pt-BR)
    # — o dicionário Python acima é a mesma ideia, só que na sintaxe do curso.
