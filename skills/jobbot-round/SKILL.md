---
name: jobbot-round
description: Use quando a pessoa pedir para rodar vagas. Procura vagas sozinho no LinkedIn, no Indeed e na Gupy, filtra, gera o currículo de cada uma e prepara cada candidatura com o PDF anexado e as respostas preenchidas e, no modo autônomo (padrão), responde as perguntas da empresa e finaliza. No modo assistido, para no último passo e a pessoa envia ou fecha a aba. Gatilhos - "rodar vagas", "buscar vagas", "preparar candidaturas", "abrir as abas".
---

# JobBot: rodada de vagas

Você conduz uma rodada. O objetivo do JobBot é ser **autônomo, ou quase**: a pessoa define o perfil uma vez e o bot cuida do resto.

**Modo de autonomia** (`jobbot run-settings <nome>`, campo `autonomy`):
- `full` (padrão): em cada vaga, responda as perguntas da empresa com respostas verdadeiras do perfil, escreva o texto de apresentação (só pontos fortes) e **finalize a candidatura**.
- `assisted`: pare no último passo, com a aba aberta, e deixe o envio com a pessoa.

Na primeira rodada, confirme o modo uma vez ("quer que eu finalize as candidaturas sozinho?") e grave com `run-settings <nome> --autonomy full|assisted`. Não pergunte de novo.

**Limites que valem nos dois modos:**
- Nunca digite RG, CPF ou outro número de documento, mesmo que a pessoa informe: o campo fica com ela (anote na folha de revisão).
- Nunca invente dado. Falta um dado do perfil (salário atual, data de nascimento): peça **uma vez**, guarde com `answers-add` (`always: true`) e reaproveite nas próximas vagas.
- Consentimentos opcionais e campos sensíveis (PCD, gênero, raça, autorização de trabalho) só se a pessoa guardou a resposta.
- **Pergunta eliminatória reprova na hora e a resposta não se edita** (ex.: "Python e Golang?" respondida Não). Em pergunta composta com skill que a pessoa tem só pela metade, responda com verdade e registre na folha de revisão; não minta para passar.
- Pergunta de remuneração: use o piso do tipo de vaga (ou a faixa que cobre o piso) como pretensão, e o salário atual guardado como remuneração atual.

Leia `references/platforms.md` antes de começar. Fale em português do Brasil.

## Antes de começar

1. Mostre este aviso, sem alterar o texto:

   Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa.

2. Pergunte o nome do perfil (`<nome>`), se a pessoa ainda não disse. Confirme que a CLI funciona: `jobbot --help`.
3. Rode `jobbot validate <nome>` (deve dar `ok`) e `jobbot type-list <nome>`. Sem tipos definidos, mande a pessoa para a skill `jobbot-types`.
4. Para cada plataforma, abra a página no Chrome e confira o nome da conta logada. Se não bater com o nome do perfil, ou se pedir login, pare essa plataforma e avise. Nunca peça nem digite senha: a pessoa faz o login sozinha.

## Para cada plataforma (`linkedin`, `indeed`, `gupy`)

1. `jobbot round-check <nome> <plataforma>`. Se `permitido: 0`, diga o `motivo` à pessoa e passe para a próxima plataforma. Guarde `permitido` (abas a preparar) e `examinar_ate` (máximo de vagas a examinar).
2. **Buscar.** Para cada tipo de vaga definido, pesquise pelo cargo e pela modalidade do tipo. No Indeed, use o conector (`search_jobs` e `get_job_details`) quando existir; sem ele, use o navegador. No LinkedIn e na Gupy, use o navegador. Vá devagar e em ritmo irregular, uma aba por vez, nunca em paralelo. No LinkedIn, aguarde cerca de 4 segundos depois de abrir a busca; se der leitura vazia, espere e tente de novo no máximo 2 vezes (veja `references/platforms.md`). Confira os filtros que a plataforma tenha acrescentado sozinha.
3. **Para cada vaga encontrada**, até preparar `permitido` abas ou examinar `examinar_ate` vagas:
   1. Extraia os campos da vaga num `posting.yaml` (regras da skill `jobbot-resume`: `title`, `company`, `skills`, `salary`, `modality`, `contract`, `url`, e também `level` e `city`; omita o que a vaga não diz). `level`: `estagio`, `junior`, `pleno` ou `senior`, pelo título e pelos anos exigidos (5 anos ou mais ou "Sr" é `senior`). `city`: a cidade do trabalho. **Deslocamento:** para vaga híbrida ou presencial, se o perfil tem `max_commute_minutes` e `home_area`, abra o Google Maps no navegador, peça o trajeto de transporte público (ônibus e metrô) de `home_area` até o endereço da vaga, para chegar por volta das 9h em dia útil (use "Chegar às"; se só houver "Sair agora" fora do pico, some 30% ao tempo, porque o Maps costuma subestimar o pico), e grave `commute_minutes` (minutos, só ida) e `address` no `posting.yaml`. Sem endereço na vaga, use a cidade e o bairro; sem número confiável, deixe `commute_minutes` de fora e valerá a lista de cidades. **Sem `salary`**, procure o salário médio mensal (CLT, em reais) do cargo na empresa; se não achar, do cargo na cidade. Use só páginas públicas de salário (Glassdoor, Catho, Vagas, Levels, Salario.com.br), sem login. Com um número lido numa fonte, grave `salary_estimate` e `salary_source` (fonte, cargo e data de hoje). Sem fonte, não preencha. Detalhes em `docs/salary-estimate.md`.
   2. `jobbot vaga-check <nome> posting.yaml --platform <plataforma>`. Se `repetida` ou `filtro` não for `nao`, rode `jobbot seen-add <nome> <plataforma> posting.yaml --reason <motivo>` (use o próprio valor retornado: `repetida`, `empregador_atual`, `empresa_vetada` ou `fora_das_restricoes`) e vá para a próxima vaga.
   3. `jobbot vaga-eval <nome> posting.yaml`. Vaga arriscada ou abaixo do piso segue, marcada. Se der erro, `seen-add ... --reason falha` e próxima.
   4. Escreva o `content.yaml` e rode `jobbot vaga-resume <nome> posting.yaml --platform <plataforma> [--type ...] [--content-file content.yaml]`, como na skill `jobbot-resume`. Anote os caminhos `pdf:` e `revisao:`.
   5. Abra o formulário de candidatura numa aba nova e anexe o PDF. Se a candidatura leva ao site da própria empresa, abra a página, **não preencha nada**, rode `jobbot app-status <nome> <url> externa`, anote na folha de revisão e conte a vaga como preparada.
   6. **Mensagem para a equipe de seleção** (campo livre, quando existir e for opcional): escreva só o que a pessoa **tem** e faz, em tom humilde, com número só do perfil. **Nunca** cite o que ela não tem, o que está estudando ou lacuna da vaga: se a vaga se interessar, ela será chamada. Mostre o texto à pessoa; ela pode editar.
   6b. **Perguntas do formulário.** Junte os textos das perguntas num `questions.yaml` (lista de textos) e rode `jobbot answers-resolve <nome> questions.yaml --vaga "<título>@<empresa>"`. Preencha só as linhas `respondida`. Deixe as `em_branco` vazias e destacadas, e anote-as na folha de revisão. Nunca invente uma resposta; campos sensíveis (PCD, gênero, raça, autorização de trabalho) e consentimentos legais ficam em branco e desmarcados quando não há resposta guardada.
   7. **Testes de fit cultural.** Salve o texto de instruções do teste num arquivo e rode `jobbot fit-risks <nome> instrucoes.txt`. Siga a `acao`: `responder` (escreva um rascunho com `jobbot behavior <nome>`, de forma honesta, com o perfil real da pessoa e não com o "candidato ideal"), `perguntar` (pergunte antes), `pular` ou `deixar_para_pessoa` (teste vigiado: deixe a aba aberta, sem responder). Se `behavior` voltar com tudo em branco (a pessoa ainda não fez o teste), pergunte à pessoa em vez de redigir um rascunho. Registre os `flags` (`proibe_ia`, `cronometrado`, `tentativa_unica`, `vigiado`) na folha de revisão.
   8. **Finalizar.** Modo `assisted`: pare no último passo, com a aba aberta; não clique em enviar. Modo `full`: na Gupy, siga "Candidatar-se", "Continuar", "Dados adicionais" (Não/Não), "Salvar e continuar", "Responder agora" (perguntas da empresa, regras acima) e "Salvar e continuar"; no modal "Apresente-se", clique "Personalizar candidatura", escreva o texto (até 1.500 caracteres, só pontos fortes, em tom humilde, citando a empresa), escolha até 3 habilidades do perfil que a vaga pede e clique "Finalizar candidatura". Depois rode `jobbot app-status <nome> <url> enviada`. Em vaga que leva ao site da empresa, nada é enviado (`externa`).
   9. Respeite o ritmo: pausas curtas e irregulares entre as ações.
4. **Freios.** Se aparecer captcha, pedido de verificação, aviso de atividade incomum ou tela de login, pare imediatamente essa plataforma: `jobbot platform-pause <nome> <plataforma> --reason "<o que apareceu>"`, avise a pessoa e não tente de novo nem contorne.

## No fim da rodada

1. Mostre um resumo por plataforma: abas preparadas, vagas puladas e o motivo, avisos de fit (`proibe_ia`, `cronometrado`, `tentativa_unica`) e plataformas pausadas.
2. Rode `jobbot pending-list <nome>`. Se houver perguntas, faça-as à pessoa **uma vez**, grave as respostas num `answers.yaml` (lista de `question`, `answer`, `category`, `always`) e rode `jobbot answers-add <nome> answers.yaml`. O `answers-add` já tira da fila as perguntas respondidas; só rode `jobbot pending-clear <nome>` se a pessoa disser que quer descartar o restante. Se ela quiser, marque `always: true` para responder sempre igual.
3. Lembre que as abas esperam a decisão dela, e que a skill `jobbot-status` atualiza o que foi enviado ou descartado.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): o que foi feito na rodada: abas preparadas por plataforma, vagas puladas com o motivo, avisos de fit, plataformas pausadas e o que a pessoa precisa decidir. Use a data de hoje no nome. Grave num arquivo temporário (nunca em Downloads) e rode `jobbot report-save <nome> 06-rodada-AAAA-MM-DD <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
