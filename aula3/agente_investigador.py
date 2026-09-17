import os
import sys

# Coloca a raiz do curso no sys.path para importar provedor (e o .env) de qualquer aula.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import hashlib
import requests
from agents import Agent, Runner, function_tool
from provedor import configurar, modelo

configurar()

USER_AGENT = "sistema-multiagentes-curso/1.0 (contato@exemplo.com)"
BANCO: dict[str, int] = {}
_sequencial = 0


# ---------------------------------------------------------------------------
# 7.3 — consultar_cnpj resiliente: retry com backoff quando vier 429 (rate limit).
# ---------------------------------------------------------------------------
@function_tool
def consultar_cnpj(cnpj: str, max_tentativas: int = 4) -> str:
    """Consulta um CNPJ na BrasilAPI. Retry com backoff se a API limitar (429)."""
    cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")
    for tentativa in range(1, max_tentativas + 1):
        resp = requests.get(
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            timeout=10,
        )
        if resp.status_code == 429:
            espera = 0.5 * (2 ** (tentativa - 1))
            if tentativa == max_tentativas:
                raise RuntimeError("BrasilAPI limitando requisições (429).")
            print(f"  [retry] 429 — tentando de novo em {espera:.1f}s...")
            time.sleep(espera)
            continue
        resp.raise_for_status()
        dados = resp.json()
        return f"{dados.get('razao_social')} | situação: {dados.get('descricao_situacao_cadastral')}"
    raise RuntimeError("Não foi possível consultar o CNPJ.")


# ---------------------------------------------------------------------------
# 7.1 — consultar_ddd (decisão do modelo junto com o CNPJ).
# ---------------------------------------------------------------------------
@function_tool
def consultar_ddd(ddd: str) -> str:
    """Consulta um DDD na BrasilAPI e retorna estado e municípios."""
    resp = requests.get(f"https://brasilapi.com.br/api/ddd/v1/{ddd}", timeout=10)
    resp.raise_for_status()
    dados = resp.json()
    cidades = ", ".join(dados.get("cidades", [])[:4])
    return f"Estado: {dados.get('estado')} | Municípios: {cidades}"


# ---------------------------------------------------------------------------
# 7.2 — consultar_endereco (Nominatim, exige header User-Agent).
# ---------------------------------------------------------------------------
@function_tool
def consultar_endereco(endereco: str) -> str:
    """Converte um endereço em coordenadas via Nominatim."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": endereco, "format": "json", "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    resp.raise_for_status()
    resultados = resp.json()
    if not resultados:
        return "Endereço não localizado."
    r = resultados[0]
    return f"{r.get('display_name')} | lat={r.get('lat')}, lon={r.get('lon')}"


# ---------------------------------------------------------------------------
# 7.2 — registrar_ocorrencia (idempotente).
# ---------------------------------------------------------------------------
@function_tool
def registrar_ocorrencia(tipo: str, local: str, data: str) -> str:
    """Registra uma ocorrência (idempotente)."""
    global _sequencial
    chave = hashlib.sha1(f"{tipo}|{local}|{data}".encode()).hexdigest()
    if chave in BANCO:
        return f"[IDEMPOTENTE] id={BANCO[chave]}"
    _sequencial += 1
    BANCO[chave] = _sequencial
    return f"[REGISTRADA] id={_sequencial}"


# ---------------------------------------------------------------------------
# 7.1 — decisão do modelo entre duas fontes independentes.
# ---------------------------------------------------------------------------
agente_decisao = Agent(
    name="Analista de Cadastro",
    instructions=(
        "Você consulta dados cadastrais. Use consultar_cnpj e consultar_ddd "
        "conforme o que o usuário pedir. Decida quais chamar e em que ordem."
    ),
    model=modelo(),
    tools=[consultar_cnpj, consultar_ddd],
)

# ---------------------------------------------------------------------------
# 7.2 — apoio completo: investigar (cnpj + endereço) e SÓ ENTÃO registrar.
# ---------------------------------------------------------------------------
agente_investigador = Agent(
    name="Investigador",
    instructions=(
        "Você investiga um caso: consulte o CNPJ e o endereço quando relevantes. "
        "Depois de reunir os dados, registre a ocorrência com registrar_ocorrencia. "
        "Nunca registre antes de investigar."
    ),
    model=modelo(),
    tools=[consultar_cnpj, consultar_endereco, registrar_ocorrencia],
)


def main() -> None:
    print("=== 7.1 — duas fontes, decisão do modelo ===\n")
    r1 = Runner.run_sync(
        agente_decisao,
        "Consulte o CNPJ 12.345.678/0001-90 e o DDD 61.",
    )
    print(r1.final_output)

    print("\n=== 7.2 — investigar e só então registrar ===\n")
    r2 = Runner.run_sync(
        agente_investigador,
        "Investigue o CNPJ 60.701.190/0001-04 e o endereço 'Quadra 303, Brasília'. "
        "Depois registre a ocorrência 'furto de veículo' em 'Quadra 303' em '28/09'.",
    )
    print(r2.final_output)


if __name__ == "__main__":
    main()
