import os
from agents import Agent, Runner
from provedor import configurar

# 1. Inicializa a infraestrutura de inferência definida no .env (Ollama/OpenAI)[cite: 1, 2]
configurar() #[cite: 1, 2]

# 2. Cria o agente declarando o modelo explicitamente para evitar erros de rota[cite: 1]
agente = Agent(
    name="Primeiro agente", #[cite: 1]
    instructions="Você é um agente de teste e responde de forma objetiva.",
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b") #[cite: 1]
)

# 3. Ponto de entrada com a execução do Runner encapsulada
def main():
    resultado = Runner.run_sync(agente, "Quem é o presidente da Argentina?")
    # .final_output aqui é uma string (não definimos output_type — isso vem no 4.x).
    print(resultado.final_output) #[cite: 1]

if __name__ == "__main__":
    main()