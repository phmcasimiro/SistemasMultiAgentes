import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_default_openai_key,
    set_tracing_disabled,
)

load_dotenv()

# Provedor atualmente ativo (atualizado por configurar()).
ATIVO = "openai"

RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"


def _configurar_ollama() -> None:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    # A api_key é obrigatória no construtor, mas o Ollama a ignora.
    cliente = AsyncOpenAI(base_url=base_url, api_key="ollama")
    set_default_openai_client(cliente)        # todas as chamadas vão para o Ollama
    set_default_openai_api("chat_completions")  # Ollama não implementa a Responses API
    set_tracing_disabled(True)                 # sem envio de traces para a OpenAI


def _configurar_zen() -> None:
    # OpenCode Zen: gateway OpenAI-compatível (rota /chat/completions).
    base_url = os.getenv("OPENAI_BASE_URL", "https://opencode.ai/zen/v1")
    cliente = AsyncOpenAI(base_url=base_url, api_key=os.getenv("OPENAI_API_KEY"))
    set_default_openai_client(cliente)         # todas as chamadas vão para o Zen
    set_default_openai_api("chat_completions")  # Zen serve por esta rota
    set_tracing_disabled(True)                 # sem envio de traces para a OpenAI


def configurar(provedor: str | None = None) -> str:
    """Aplica a configuração do provedor escolhido no `.env`. Devolve o nome dele."""
    global ATIVO
    provedor = (provedor or os.getenv("PROVEDOR", "openai")).strip().lower()
    ATIVO = provedor

    if provedor == "ollama":
        _configurar_ollama()
    elif provedor == "zen":
        _configurar_zen()
    else:
        # Caminho padrão: OpenAI de verdade.
        set_default_openai_key(os.getenv("OPENAI_API_KEY"))

    return provedor


def modelo() -> str:
    """Nome do modelo do provedor ativo (zen -> OPENAI_MODEL; senão -> OLLAMA_MODEL)."""
    if ATIVO == "zen":
        return os.getenv("OPENAI_MODEL", "deepseek-v4-flash")
    return os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def cair_para_ollama() -> None:
    """Força o recuo de segurança para o Ollama local."""
    configurar("ollama")


def rodar(agente_fabrica, mensagem):
    """Executa o agente via Runner. Em falha do provedor Zen, recua para o Ollama local.

    `agente_fabrica` é uma função sem argumentos que devolve um `Agent` construído com
    `model=modelo()`, permitindo reconstruí-lo com o modelo correto após o recuo.
    """
    try:
        return Runner.run_sync(agente_fabrica(), mensagem)
    except Exception as exc:
        if ATIVO != "zen":
            raise
        print(f"{RED}[FALHA - zen]{RESET} {exc}")
        print(f"{YELLOW}[RECUO]{RESET} Alternando para Ollama local e tentando novamente...")
        cair_para_ollama()
        return Runner.run_sync(agente_fabrica(), mensagem)
