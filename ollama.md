# Ollama local

## Verificação da instalação

Verifiquei no ambiente e o Ollama está instalado e funcionando localmente nesta máquina.

Status verificado:
- Executável: `/usr/local/bin/ollama`
- Versão: `ollama version is 0.30.8`
- Serviço ativo: `/bin/ollama serve`
- API local respondendo em: `http://127.0.0.1:11434`
- Modelos já presentes:
  - `llama3.2:3b`
  - `qwen2.5:1.5b`
  - `bge-m3:latest`
  - `nomic-embed-text:latest`

## Setup de configuração desta máquina

- O Ollama está usando a configuração padrão do sistema, porque não há variáveis `OLLAMA_*` no ambiente.
- Diretório padrão de dados do usuário:
  - `~/.ollama`
- Local dos modelos:
  - `/home/phmcasimiro/.ollama/models`
- Porta padrão da API local:
  - `11434`
- Endpoint de listagem de modelos funcionando:
  - `http://127.0.0.1:11434/api/tags`

Resumo do setup:
- Instalação feita via binário do Ollama
- Serviço rodando em background
- API REST local habilitada
- Modelos locais já baixados e prontos para uso

## Roteiro básico para utilização do Ollama local

### 1. Verificar se o serviço está ativo

```bash
ollama list
```

ou

```bash
curl http://127.0.0.1:11434/api/tags
```

### 2. Baixar um modelo

```bash
ollama pull llama3.2:3b
ollama pull qwen2.5:1.5b
```

### 3. Rodar o modelo no chat interativo

```bash
ollama run llama3.2:3b
```

### 4. Fazer uma pergunta direta pelo terminal

```bash
ollama run llama3.2:3b "Explique em 3 linhas o que é inteligência artificial"
```

### 5. Usar a API REST

Exemplo de requisição:

```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Olá, tudo bem?",
  "stream": false
}'
```

### 6. Listar modelos instalados

```bash
ollama list
```

### 7. Remover modelo

```bash
ollama rm llama3.2:3b
```

## Observações úteis

- O Ollama usa modelos em GGUF, então ele faz download e cache localmente.
- Para uso em aplicações, o fluxo mais comum é:
  1. baixar modelo
  2. consumir via `curl` ou via Python/JavaScript
- Se quiser rodar modelos maiores, depende do hardware e da VRAM/memória RAM disponível.

## Comandos principais

```bash
ollama list
ollama pull <nome-do-modelo>
ollama run <nome-do-modelo>
ollama rm <nome-do-modelo>
```

## Conclusão

O Ollama está corretamente instalado nesta máquina, com o serviço local em funcionamento e vários modelos já disponíveis para uso imediato. O fluxo básico é simples: baixar o modelo, executar com `ollama run` ou consumir pela API em `127.0.0.1:11434`.
