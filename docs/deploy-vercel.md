# Publicar o Citizen Assist AI na Vercel (passo a passo)

> **Aviso:** este roteiro foi preparado a partir da documentação da Vercel (consultada em 16/11/2026), mas **o deploy em si não foi testado**, porque exige a sua conta. No Passo 6 há uma lista curta de conferências para o primeiro deploy.

## Antes de começar

- Conta na Vercel, plano **Hobby** (grátis, para projetos pessoais e acadêmicos sem fins comerciais).
- O código no GitHub. O branch padrão do repositório hoje é `claude/upbeat-cannon-vxhl03`, e é ele que a Vercel publica como "produção".
- Uma chave da Anthropic **com limite de gasto** (Passo 1).

O projeto já vem preparado: `index.py` (ponto de entrada), `vercel.json` (tempo máximo e arquivos incluídos), `.vercelignore` (o que não vai para o servidor) e `requirements.txt` só com o necessário para rodar.

## Passo 1: proteja o seu dinheiro antes de publicar

Quem tiver o link poderá usar o chat, e cada pergunta gasta crédito da sua conta.

1. Entre em https://console.anthropic.com/ e abra as configurações de limite de gasto (Settings → Limits). Defina um valor mensal baixo, por exemplo o orçamento do trabalho.
2. Crie **uma chave só para este deploy** (Settings → API Keys → Create Key), com um nome como `citizen-assist-vercel`. Assim você apaga só ela depois da apresentação, sem mexer na chave que usa no computador.
3. Comece com `BUSCA_WEB=0`, porque a busca na web é cobrada à parte.

## Passo 2: crie a conta e importe o projeto

1. Acesse https://vercel.com/signup e escolha **Continue with GitHub**.
2. Clique em **Add New… → Project**.
3. Na lista, encontre `CitizenAssist-AI` e clique em **Import**. Se o repositório não aparecer, clique em **Adjust GitHub App Permissions**, dê acesso a ele e volte. Se o repositório estiver na conta de outra pessoa do grupo e continuar sem aparecer, use o Passo 5, que não depende do GitHub.
4. Na tela de configuração:
   - **Framework Preset:** deve aparecer *FastAPI*. Se aparecer *Other*, deixe assim.
   - **Root Directory:** `./`
   - **Build Command** e **Output Directory:** deixe em branco.

## Passo 3: variáveis de ambiente (a chave fica aqui, nunca no código)

Ainda na tela de configuração, abra **Environment Variables** e adicione uma por uma (nome, valor, **Add**):

| Nome | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | a chave criada no Passo 1 |
| `CLAUDE_MODEL` | `claude-haiku-5-5` |
| `BUSCA_WEB` | `0` (mude para `1` depois do primeiro teste) |
| `LIMITE_REQUISICOES_POR_MINUTO` | `6` |

As demais variáveis do `.env.example` têm valor padrão e podem ser omitidas. Clique em **Deploy**.

## Passo 4: espere e abra o site

A publicação leva de 1 a 3 minutos. Quando aparecer **Congratulations**, clique em **Visit**. O endereço terá a forma `https://citizen-assist-ai-xxxx.vercel.app`.

## Passo 5: alternativa, publicar pelo terminal (sem GitHub)

Na pasta do projeto, com o Node.js instalado (https://nodejs.org):

```bash
npm install -g vercel
```

```bash
vercel login
```

```bash
vercel
```

Responda às perguntas com Enter (aceite os padrões). Depois cadastre a chave e publique em produção:

```bash
vercel env add ANTHROPIC_API_KEY production
```

```bash
vercel --prod
```

## Passo 6: confira o deploy

Os três testes em negrito cobrem pontos que a documentação da Vercel não confirmou.

| Teste | Deve acontecer | Se falhar |
|---|---|---|
| Abrir a página inicial | Aparece a tela com a barra lateral e "Como posso ajudar hoje?" | Veja o erro em **Logs** (Passo 8) |
| **Streaming:** pergunte algo no chat de cidadania | O texto aparece aos poucos, não de uma vez só no fim | A resposta funciona, só sem o efeito de digitação. Não é erro grave |
| **Arquivos da tela:** abra `/static/estilo.css` | Mostra o CSS | A tela abre sem estilo. Peça para mover `app/static` para `public/static` |
| **Arquivos lidos pelo servidor:** abra Dados e estatística → Relatório e Decisão lógica → Relatório | Os relatórios carregam e o botão de PDF funciona | Se der 404 ou 500, ajuste o `includeFiles` do `vercel.json` (por exemplo, `"app/**"`, `"modulos/**"` e `"docs/**"` em itens separados) |
| Energia → Simulador solar: preencha e simule | Aparecem as placas e os números | Mesmo ajuste de `includeFiles` (o CSV de irradiação fica em `modulos/energia/`) |
| Mande 7 mensagens seguidas no chat | A 7ª recebe "Você enviou muitas mensagens…" | O IP real não está sendo lido: avise quem mantém o código |

## Passo 7: atualizar o site depois

Com o GitHub conectado, cada `git push` no branch de produção publica de novo sozinho. Pushes em outros branches geram um endereço de **prévia**, que não é o de produção.

## Passo 8: quando algo der errado

No painel da Vercel, **projeto → Logs** mostra os erros em tempo real.

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| "falta a chave da API" na tela | Variável não cadastrada, ou cadastrada depois do deploy | Cadastre em **Settings → Environment Variables** e faça **Redeploy** (as variáveis só valem em deploys novos) |
| "chave inválida" | Chave colada com espaço ou aspas | Apague e cadastre de novo |
| Erro 500 ao abrir | Falha na importação ou dependência faltando | Leia o último erro em Logs |
| Página abre sem estilo | Pasta `app/static` não encontrada | Veja o Passo 6 |
| Todos recebem "muitas mensagens" | IP real não está sendo lido | Veja o Passo 6 |

## Passo 9: depois da apresentação

1. Na Vercel: **Settings → Advanced → Delete Project**, para o site sair do ar.
2. Na Anthropic: apague a chave `citizen-assist-vercel`.

## Limites que você deve conhecer

- **O limite de mensagens é por servidor, não global.** A Vercel pode criar várias cópias do servidor, cada uma com a sua contagem. Ele reduz abuso, mas não o impede. O teto de segurança é o limite de gasto do Passo 1.
- **O site fica público.** Qualquer pessoa com o link pode usar o chat. Compartilhe o link só com quem precisa (professor e grupo) e tire o site do ar depois.
- **A primeira visita depois de um tempo parado é mais lenta** (partida a frio).
- **O plano Hobby é só para uso pessoal e não comercial**, que é o caso deste trabalho.
- **Nada é gravado no servidor:** as conversas continuam só na tela de quem usa.
- **Para o vídeo do trabalho,** guarde também uma gravação feita rodando local, por segurança.

## Referências (consultadas em 16/11/2026)

- [Deploy a FastAPI app on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- [How to ship a FastAPI app on Vercel](https://vercel.com/kb/guide/ship-a-fastapi-app-on-vercel)
- [Limites das Vercel Functions](https://vercel.com/docs/functions/limitations)
- [Fluid compute](https://vercel.com/docs/fluid-compute)
- [Configuração com vercel.json](https://vercel.com/docs/project-configuration/vercel-json)
