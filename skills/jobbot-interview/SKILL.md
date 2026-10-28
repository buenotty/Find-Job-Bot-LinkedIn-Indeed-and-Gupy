---
name: jobbot-interview
description: Use quando a pessoa quiser montar ou atualizar seu perfil profissional completo para buscar vagas no Brasil. Pede de início o LinkedIn, o GitHub e o currículo mais atual, lê o que está público e pré-preenche um questionário em arquivo de texto que ela só confere e completa, carrega tudo de uma vez e faz no máximo um arquivo de seguimento só com as lacunas. Os dados ficam só na máquina dela. Gatilhos - "montar meu perfil", "mapear minha carreira", "jobbot".
---

# JobBot: perfil por questionário

O perfil é montado com **um arquivo de texto que a pessoa preenche de uma vez**, não com dezenas de perguntas no chat. Seja breve: poucas mensagens, curtas, em português do Brasil.

## Passos

1. Mostre este aviso, sem alterar o texto:

   Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa.

2. Confirme que a CLI funciona: `python3 -m jobbot --help`. Se der `No module named jobbot`, a pessoa abriu o Claude sem o lançador: peça para abrir pelo `bin/jobs-master`.
3. Pergunte só o nome da pessoa (ele identifica a pasta local dela; use o mesmo texto em todos os comandos, `<nome>`). Diga que os dados ficam só neste computador.
4. **Fontes (poupam tempo da pessoa).** Peça, numa única mensagem e tudo opcional: o link do **LinkedIn**, o usuário do **GitHub**, outros links (site, portfólio, YouTube) e o **currículo mais atual** (caminho de um PDF ou DOCX; ela pode arrastar o arquivo para o terminal). Diga que o bot só lê o que está público, nada é alterado e tudo fica neste computador. Depois leia o que veio:
   - **Currículo:** leia o arquivo (PDF e DOCX abrem com a ferramenta de leitura). Dele saem empregos, datas, cargos, formação, certificações, idiomas, contatos e entregas.
   - **GitHub:** só leitura, com `gh`: `gh repo list <usuario> --limit 30 --json name,description,pushedAt,isFork,languages` e o README dos repositórios relevantes. Dele saem projetos reais, linguagens e atividade recente. Nunca rode comando que altere algo.
   - **LinkedIn:** abra a página pública da pessoa no navegador, **uma página só**, com a sessão que ela já tem aberta. Nunca faça login por ela, nunca percorra perfis de outras pessoas e não use rolagem em massa. Dele saem cargo atual, resumo, experiências e skills listadas.
   - **Outros links:** leia a página inicial só para entender o que é.
   Cruze as fontes. Fato igual em duas fontes entra sem perguntar. Fato que diverge (data, cargo, empresa) vai para a lista de dúvidas do passo 8. Nível de skill **nunca** sai das fontes sozinho: um repositório em Python mostra uso, não nível. Registre onde cada skill aparece (GitHub, currículo, LinkedIn) como evidência e deixe o nível para a pessoa confirmar.
5. Rode `python3 -m jobbot form-new <nome> interview`. O arquivo é criado na pasta **Downloads** da pessoa (não numa pasta oculta); a saída `arquivo:` mostra o caminho. **Pré-preencha** o arquivo com o que as fontes trouxeram (use Edit nele, só com fatos lidos; nunca com número de resultado inventado). Mande **uma única mensagem**: o caminho, o que você já preencheu e de qual fonte, e "abra no seu editor, confira, complete o que falta (deixe em branco o que não se aplica), salve no mesmo lugar e me diga pronto". Se a pessoa não passou fonte nenhuma, mande o arquivo em branco. Não faça perguntas no chat e não repita o conteúdo do arquivo.
6. Quando a pessoa disser que terminou, rode `python3 -m jobbot form-load <nome>`, **sem caminho**: ele acha o arquivo mais recente dela na pasta Downloads e mostra `lendo:`. Se carregar, o comando **recolhe** o arquivo para a pasta interna do perfil (`recolhido:`) e nada de pessoal fica em Downloads.
7. **Se o comando listar erros, o modelo é só um guia: não devolva a lista de erros à pessoa.** Ninguém preenche exatamente como o modelo pede. Em vez disso:
   1. Leia o arquivo inteiro e entenda o que a pessoa quis dizer, mesmo fora do formato (estado e cidade trocados, mês por extenso, nível como "avançado", skills sem nível, formação escrita em outro campo, observações dentro de um campo).
   2. Escreva uma cópia corrigida no mesmo formato, **numa pasta temporária** (nunca em Downloads), usando só o que a pessoa escreveu. Mapeie com bom senso: "avançado" vira `especialista`, "intermediário" vira `medio`; idioma por nível (C1 = avançado, não fluente: pergunte se ficar em dúvida); fim de emprego "atual" fica vazio; projeto sem ano de fim está em andamento.
   3. Carregue a cópia: `python3 -m jobbot form-load <nome> <arquivo-corrigido>`. Repita a correção até carregar. O arquivo original fica em Downloads, intocado.
   4. Quando algo importante não tiver campo no perfil (por exemplo, "presencial só acima de R$ 6.000" tem o campo `Presencial só a partir de`), procure o campo certo em vez de descartar a informação. Se não existir mesmo, diga à pessoa que não existe e como vai ser tratado.
8. **Uma única mensagem de dúvidas.** Junte tudo o que você supôs ou não conseguiu mapear (nível de skill sem nível dado, datas faltando, ano de fim, idioma, disponibilidade, resultados em número) numa lista curta, com a sua suposição ao lado de cada item, e peça para a pessoa confirmar ou corrigir. Nunca invente número de resultado. Aplique as respostas com `python3 -m jobbot put <nome> <etapa> <arquivo.yaml>` (veja abaixo) ou refazendo a cópia corrigida; não mande a pessoa editar o arquivo de novo.
   **Se leu LinkedIn, GitHub ou currículo, acrescente nessa mesma mensagem uma lista curta "O que melhorar nos seus perfis"**: compare o que a pessoa de fato faz (skills, projetos e resultados que ela contou) com o que cada perfil público mostra, e aponte o que falta ou está desatualizado, com uma sugestão concreta por item (título do LinkedIn, skills e palavras-chave ausentes, seção Sobre, projetos no GitHub sem README, repositórios importantes privados, número de resultado que está só no currículo). Só sugestões: o bot nunca edita nada. O texto pronto vem depois, na skill `jobbot-profiles`.
9. Rode `python3 -m jobbot form-gaps <nome>`. Se imprimir `sem lacunas`, pule este passo. Se gerar um arquivo de seguimento, **leia você mesma** as perguntas e traga-as na mesma conversa, em vez de mandar a pessoa para outro arquivo; grave as respostas no formato do seguimento e rode `python3 -m jobbot form-load <nome> <arquivo>`. Faça **no máximo um** seguimento.
10. Rode `python3 -m jobbot validate <nome>`. Corrija com a pessoa só o que ele listar. Com `ok`, diga que o próximo passo é a skill `jobbot-assessment` (o teste de perfil, que melhora a escolha dos cargos) (ou `jobs-master` para ver o quadro).

## Regras

- Nunca invente nem sugira número de resultado, empregador, cargo, data, formação ou certificação. O que a pessoa não escreveu fica em branco.
- Se a pessoa preferir responder no chat, aceite, mas junte tudo e grave no mesmo formato: nunca devolva uma pergunta por vez.
- Fale em "entregas" e "resultados" (o que a pessoa fez e o que mudou), não em termos técnicos como "bullet" ou "parser".
- Escolhas A/B empatadas (4 a 4) deixam a trilha `indefinido`. Não force: o teste de perfil (`jobbot-assessment`) define a trilha com mais dados.
- Se duas respostas se contradizem, aponte numa única mensagem e deixe a pessoa decidir.
- Se a skill `linkedin-interviewer` estiver instalada, pode usá-la para extrair entregas concretas. Sem ela, siga normalmente.

## Correção pontual de uma etapa

Para corrigir uma etapa sem preencher o questionário de novo, use `python3 -m jobbot put <nome> <etapa> <arquivo.yaml>` (etapas: `identidade`, `experiencias`, `skills`, `certificacoes_idiomas`, `restricoes`, `triagem`, `comportamento`). Cada `put` substitui por inteiro os campos da etapa: leia o `profile.yaml` (na pasta de `python3 -m jobbot path <nome>`) e reenvie a lista inteira, não só o item alterado. Projetos aceitam `kind` (`projeto`, `voluntariado`, `autodidata` ou `freela`), `start` e `end` (anos). A formação fica em `education` (`level`: `medio`, `tecnico`, `graduacao`, `pos`, `mestrado` ou `doutorado`; `status`: `concluido`, `cursando` ou `trancado`) e `contract` aceita `CLT`, `PJ` ou `ambos`.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): o perfil como ficou (identidade, experiências com resultados, skills com nível e evidência, formação, restrições), as fontes lidas e o que cada uma trouxe, as decisões tomadas nas dúvidas e a lista **"O que melhorar nos seus perfis"**. Grave num arquivo temporário (nunca em Downloads) e rode `python3 -m jobbot report-save <nome> 01-perfil <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
