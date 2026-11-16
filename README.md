# Citizen Assist AI

Assistente web que ajuda cidadãos a se informarem, usando a API do Claude (Anthropic). É um protótipo acadêmico da Global Solution GS26_2 (Ciência da Computação, 1CC). Não é um canal oficial do governo e não confirma a concessão de serviços ou direitos.

**Integrantes:** [PENDENTE: nome completo e RM de cada integrante]

## Situação atual

| Módulo | Disciplina | Situação |
|---|---|---|
| Dúvidas gerais de cidadania | Produto | Funcionando (chat com busca em fontes oficiais) |
| Decisão lógica | Computer Science | Em construção |
| Dados e estatística | Modelagem Linear para Aprendizado de Máquina | Em construção |
| Energia | Soluções em Energias Renováveis e Sustentáveis | Em construção |

## O que você precisa ter

- **Python 3.11 ou mais novo.** Para conferir, abra o terminal (no Windows, o programa "PowerShell") e rode o comando abaixo. Deve aparecer algo como `Python 3.12.4`. Se aparecer erro, instale pelo site https://www.python.org/downloads/ e, no Windows, marque a opção "Add Python to PATH" durante a instalação.

  ```bash
  python --version
  ```

- **Uma chave da API da Anthropic.** Crie uma conta em https://console.anthropic.com/, adicione crédito e gere uma chave em "API Keys". A chave começa com `sk-ant-`. Trate-a como uma senha: não envie por mensagem e não coloque no código.

## Instalação

Rode os comandos na ordem, dentro da pasta do projeto.

1. Baixe o projeto e entre na pasta:

   ```bash
   git clone https://github.com/bielw12/CitizenAssist-AI.git
   ```

   ```bash
   cd CitizenAssist-AI
   ```

2. Crie o ambiente virtual, uma pasta `.venv` que guarda as bibliotecas só deste projeto:

   ```bash
   python -m venv .venv
   ```

3. Ative o ambiente virtual. Depois disso, o começo da linha do terminal mostra `(.venv)`.

   No Windows (PowerShell):

   ```bash
   .venv\Scripts\Activate.ps1
   ```

   No macOS ou Linux:

   ```bash
   source .venv/bin/activate
   ```

4. Instale as bibliotecas. Leva cerca de um minuto e termina com uma linha que começa com `Successfully installed`.

   ```bash
   pip install -r requirements.txt
   ```

## Configuração do arquivo .env

O arquivo `.env` guarda a sua chave e fica só no seu computador. Ele está no `.gitignore`, então o Git nunca o envia.

1. Faça uma cópia do arquivo de exemplo.

   No Windows (PowerShell):

   ```bash
   copy .env.example .env
   ```

   No macOS ou Linux:

   ```bash
   cp .env.example .env
   ```

2. Abra o arquivo `.env` em um editor de texto e cole a sua chave logo depois de `ANTHROPIC_API_KEY=`, sem espaços e sem aspas. Salve o arquivo.

As outras linhas do `.env` já vêm com valores padrão:

| Variável | Para que serve | Padrão |
|---|---|---|
| `CLAUDE_MODEL` | Modelo do Claude usado no chat | `claude-haiku-5-5` |
| `MAX_TOKENS` | Tamanho máximo de cada resposta | `8000` |
| `MAX_CARACTERES_MENSAGEM` | Tamanho máximo de cada pergunta | `2000` |
| `MAX_MENSAGENS_HISTORICO` | Quantas mensagens anteriores seguem para o modelo | `20` |
| `LIMITE_REQUISICOES_POR_MINUTO` | Perguntas por minuto aceitas de cada endereço IP | `10` |
| `BUSCA_WEB` | Liga (`1`) ou desliga (`0`) a busca na web | `1` |
| `BUSCA_WEB_MAX_USOS` | Máximo de buscas por pergunta | `3` |
| `BUSCA_WEB_DOMINIOS` | Sites em que a busca pode procurar | `gov.br,jus.br,leg.br,mp.br,def.br` |

A busca na web é cobrada à parte pela Anthropic (US$ 10 por 1.000 buscas, conferido em 14/11/2026 em https://platform.claude.com/docs/en/about-claude/pricing). Em algumas contas ela precisa ser ativada no console da Anthropic.

## Como rodar

Com o ambiente virtual ativado, rode:

```bash
uvicorn app.main:app --port 8000
```

O terminal mostra `Uvicorn running on http://127.0.0.1:8000`. Abra esse endereço no navegador. Para parar o servidor, volte ao terminal e aperte `Ctrl + C`.

## Como testar

```bash
python -m pytest
```

A última linha deve ser parecida com `21 passed`. Os testes não usam a sua chave e não gastam crédito.

## Exemplos de uso

No módulo "Dúvidas gerais", experimente:

- "Quais documentos preciso para tirar a carteira de identidade?"
- "Como faço para pedir a segunda via da certidão de nascimento?"
- "O que é o CadÚnico e quem pode se inscrever?"

Se a chave estiver ausente ou errada, o chat mostra uma mensagem explicando o problema em vez de um erro técnico.

## Organização das pastas

```
app/            servidor (FastAPI) e tela (app/static)
  config.py     lê o arquivo .env
  prompts.py    instruções dadas ao modelo
  chat.py       chamada à API do Claude, com streaming e mensagens de erro
  main.py       rotas, validação de entrada e limite de uso
tests/          testes automáticos
```
