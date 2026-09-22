# agente1_gemini.py — "Fase 0" do curso: um agente feito à mão, SEM o SDK de agentes.
#
# Por que este arquivo existe? Para responder, na prática, à pergunta "o que faz um LLM
# virar um agente?" (ver aula1.md, Seção 1). Aqui construímos NÓS MESMOS as duas coisas
# que o SDK (usado em agente1.py e nos demais) faz automaticamente: a "persona" do agente
# e a memória da conversa. É mais código, mas mostra o que está por baixo dos panos.
#
# Diferente dos outros arquivos desta pasta, este script NÃO importa `provedor.py` — ele
# fala diretamente com a API do Gemini usando o cliente `OpenAI` "puro". Por isso não
# precisamos do truque de adicionar a raiz do curso ao sys.path (isso só é necessário
# para importar o módulo `provedor`, que aqui não é usado).

# 1. IMPORTAÇÃO DE BIBLIOTECAS
# 'os' permite interagir com o sistema operacional (ex.: ler variáveis de ambiente)
import os

# 'load_dotenv' lê o arquivo oculto '.env' e joga as chaves na memória do sistema
from dotenv import load_dotenv

# 'OpenAI' é a classe cliente oficial para fazer requisições HTTP compatíveis com o padrão OpenAI
from openai import OpenAI

# 2. CARREGAMENTO DAS CONFIGURAÇÕES
# Busca o arquivo '.env' (na raiz do curso) e disponibiliza as variáveis para o os.getenv()
load_dotenv()

# Instanciação do cliente de conexão:
# - api_key: sua credencial secreta de autenticação
# - base_url: o endpoint do servidor (no seu caso, a rota do Gemini compatível com OpenAI)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 3. DEFINIÇÃO DA CLASSE DO AGENTE
# Em orientação a objetos, a classe funciona como um molde para criar múltiplos agentes
class Agente:
    # O método __init__ é o "construtor": executado automaticamente ao criar o agente
    def __init__(self, nome: str, papel: str):
        self.nome = nome  # Identificador do agente (ex: "Pesquisador", "Revisor")

        # Lê o nome do modelo definido no .env (ex: "gemini-3.6-flash")
        self.modelo = os.getenv("OPENAI_MODEL")

        # MEMÓRIA DO AGENTE (Histórico de mensagens):
        # Todo LLM é 'stateless' (não tem memória própria entre requisições).
        # A lista 'self.mensagens' guarda o histórico da conversa.
        # Começamos com a mensagem de papel ('system'), que define o comportamento/persona do agente.
        self.mensagens = [{"role": "system", "content": papel}]

    # Método para interagir com o agente
    def falar(self, entrada_usuario: str) -> str:
        # Passo A: Adiciona a pergunta do usuário ao histórico com a role 'user'
        self.mensagens.append({"role": "user", "content": entrada_usuario})

        # Passo B: Envia todo o histórico acumulado para o modelo processar
        resposta = client.chat.completions.create(
            model=self.modelo,
            messages=self.mensagens,     # Envia a lista completa (memória de curto prazo)
            max_tokens=500,              # Limite máximo de tokens gerados na resposta
            temperature=0.7              # Criatividade (0.0 = determinístico/exato, 1.0 = muito criativo)
        )

        # Passo C: Extrai apenas o texto retornado pelo modelo dentro do JSON de resposta
        conteudo = resposta.choices[0].message.content

        # Passo D: Salva a resposta do próprio modelo no histórico com a role 'assistant'
        # Isso garante que, na próxima pergunta, o modelo lembre do que ele mesmo respondeu
        self.mensagens.append({"role": "assistant", "content": conteudo})

        # Retorna o texto gerado para quem chamou a função
        return conteudo

# 4. BLOCO DE EXECUÇÃO DIRETA
# O 'if __name__ == "__main__":' garante que este bloco só roda se você executar o arquivo diretamente
# (ex: 'python agente1_gemini.py'). Se outro arquivo importar este código, o teste abaixo não roda.
if __name__ == "__main__":
    # Instanciamos nosso primeiro agente dando um nome e sua diretriz de atuação (persona)
    agente_pesquisa = Agente(
        nome="Investigador",
        papel="Você é um agente especialista em síntese de literatura e pesquisa acadêmica."
    )

    # Fazemos a primeira pergunta
    pergunta = "Qual é o principal desafio na coordenação de múltiplos agentes?"
    resposta = agente_pesquisa.falar(pergunta)

    # Exibimos a resposta no terminal com o prefixo do nome do agente
    print(f"[{agente_pesquisa.nome}]: {resposta}")
