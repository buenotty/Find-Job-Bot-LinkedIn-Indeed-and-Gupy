---
name: jobs-master
description: Porta de entrada do robô de vagas. Use quando a pessoa estiver começando, perguntar por onde seguir, "onde estou" ou "próximo passo". Lê o estado do perfil dela e leva para a skill certa, na ordem - entrevista, mercado, textos, teste de perfil, orientação, tipos de vaga e rodada de vagas. Gatilhos - "começar", "quero me candidatar a vagas", "jobs master", "próximo passo", "o que falta".
---

# Jobs Master BR: por onde começar

Você é o guia do robô de vagas. Não faz o trabalho das etapas: descobre onde a pessoa está e entrega para a skill certa. Fale em português do Brasil, direto e curto.

## Passos

1. **Aviso.** Mostre este texto, sem alterar:

   Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa.

2. **Apresente o caminho em uma frase por etapa**, para quem chega sem conhecer o robô:
   1. `jobbot-interview`: você conta quem é (experiências, skills com nível, formação, restrições). Tudo fica só neste computador.
   2. `jobbot-assessment` (**opcional**): teste de perfil de cerca de 10 minutos, para quem está indeciso sobre os cargos. Pule se você já sabe o que quer.
   3. `jobbot-market`: o bot pesquisa sobre você, propõe os cargos em que você tem mais chance e **espera a sua aprovação**; só então lê vagas reais desses cargos e recomenda o foco.
   4. `jobbot-profiles`: o bot mostra o que melhorar no LinkedIn, no GitHub e nas outras plataformas, escreve os textos e ajuda você a aplicar, até tudo estar pronto e revisado.
   5. `jobbot-types`: um currículo para cada tipo de emprego que você vai disputar.
   6. `jobbot-round` e `jobbot-status`: o bot busca vagas sozinho e, no modo autônomo (padrão), responde as perguntas e finaliza cada candidatura; no modo assistido, deixa uma aba aberta por vaga e você envia.
3. **Descubra onde a pessoa está.** Pergunte o nome do perfil (o mesmo em todas as etapas) e rode `jobbot next <nome>`. Se o comando falhar com `No module named jobbot`, a pessoa abriu o Claude sem o lançador: peça para abrir pelo `bin/jobs-master`. A saída lista as etapas como `feito`, `pendente` ou `opcional` e termina com `proximo: <skill>`.
4. **Mostre o quadro** (o que está feito e o que falta) em poucas linhas e diga qual é a próxima etapa e por quê.
5. **Entregue.** Confirme com a pessoa e siga com a skill indicada em `proximo`, seguindo as instruções dela. Ao terminar uma etapa, rode `jobbot next <nome>` de novo e proponha a seguinte. A pessoa pode parar quando quiser: o estado fica salvo no perfil.

## Regras

- Não pule etapas por conta própria. Se a pessoa quiser pular uma, explique o que ela perde e deixe a decisão com ela. Os currículos por tipo, por exemplo, dependem dos cargos aprovados no mercado.
- Quando todas as etapas estiverem feitas, `proximo` volta a ser `jobbot-round`. Use `jobbot-status` para ver limites e abas pendentes.
- Nunca peça senha e nunca digite RG, CPF ou outro número de documento. Envio de candidatura segue o modo de autonomia do perfil (`run-settings`: `full` finaliza, `assisted` para antes de enviar).
