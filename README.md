# Jobs Master BR v1

Plugin do Claude Code (antes chamado JobBot) que busca e se candidata a vagas no Brasil **de forma autônoma, ou quase**: você conta quem é uma vez e o bot entrega perfil, currículos e candidaturas feitas. Esta primeira fase (**A: mapeamento**) entrevista a pessoa, analisa o mercado e entrega o perfil pronto, o foco recomendado e um CV base.

## Roteiro

- **A. Mapeamento (esta versão):** questionário completo, análise de mercado com dados, recomendação de foco, textos do perfil LinkedIn, CV base e revisão do GitHub.
- **B1. Orientação de carreira (disponível):** teste de perfil em camadas, profissões sugeridas com custo, caminhos honestos e trilha de cursos.
- **B2. Tipos de vaga e currículos (disponível):** tipos de vaga e variantes de CV por tipo.
- **C. Candidatura semi-automática (disponível):** o bot abre cada vaga com tudo preenchido; você decide enviar ou fechar.
- **D. Vagas internacionais.**

## Aviso

O modo padrão é **autônomo**: o bot responde perguntas e finaliza candidaturas sem pedir confirmação a cada vaga, usando só dados do seu perfil. Respostas a perguntas eliminatórias não podem ser editadas. Se prefere revisar antes de cada envio, rode `jobbot run-settings <nome> --autonomy assisted`.

Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa.

## Instalação

**Como plugin (recomendado), sem clonar nada.** Dentro do Claude Code:

```
/plugin marketplace add buenotty/Find-Job-Bot-LinkedIn-Indeed-and-Gupy
/plugin install jobs-master-br-v1 --marketplace buenotty/Find-Job-Bot-LinkedIn-Indeed-and-Gupy
```

Depois diga "quero começar". O Claude Code coloca o `bin/` do plugin no PATH, e o comando `jobbot` instala o pacote Python num ambiente próprio (`~/.jobbot/venv`) na primeira chamada e de novo a cada atualização do plugin. Precisa do Python 3.10 ou mais novo.

**Só a CLI**, para quem quer rodar fora do Claude Code: `pipx install git+https://github.com/buenotty/Find-Job-Bot-LinkedIn-Indeed-and-Gupy` e depois `jobbot --help`.

**Para desenvolver (clone):**

```bash
git clone https://github.com/buenotty/Find-Job-Bot-LinkedIn-Indeed-and-Gupy jobbot && cd jobbot
bin/jobs-master
```

O `bin/jobs-master` cria o ambiente Python na primeira vez (precisa do Python 3.10 ou mais novo), instala o pacote e abre o Claude Code com o plugin carregado e a CLI `jobbot` no PATH. Qualquer argumento extra vai direto para o `claude`. Se preferir abrir o Claude por conta própria, o `jobbot --help` precisa funcionar no mesmo Python que o Claude Code usa.

## Por onde começar

Peça `jobs-master` (ou diga "quero começar"): a skill lê o estado do seu perfil (`jobbot next <nome>`) e leva você para a próxima etapa. As etapas, em ordem:

1. `jobbot-interview`: monta o seu perfil com **um arquivo de texto que você preenche de uma vez** (`questionario-<seu-nome>.txt`, na pasta **Downloads**; o bot lê a devolutiva dali, sem você informar caminho, e depois **recolhe** o arquivo para a pasta interna do perfil: nada de pessoal fica em Downloads); o bot carrega tudo e faz no máximo um arquivo de seguimento, só com as lacunas.
2. `jobbot-assessment` (**opcional**, para quem está indeciso sobre os cargos): teste de perfil (também um arquivo de texto na pasta Downloads, `teste-<seu-nome>.txt`, com um número de 1 a 5 em cada linha). Ele alimenta a escolha dos cargos.
3. `jobbot-market`: o bot pesquisa sobre você e propõe os cargos em que você tem mais chance, **para você aprovar**. Só depois lê as vagas dos cargos aprovados e escreve o foco recomendado.
4. `jobbot-profiles`: mostra o que melhorar no LinkedIn, no GitHub e nas outras plataformas, escreve os textos e ajuda você a aplicar, até tudo estar pronto e revisado.
5. `jobbot-types` (e `jobbot-resume` por vaga): um currículo em PDF para cada tipo de emprego que você vai disputar.
6. `jobbot-round` e `jobbot-status`: só agora o bot busca vagas e deixa as abas abertas.

Fora da linha principal, sob pedido: `jobbot-orientation` e `jobbot-courses` (mudança de área, custo, trilha de cursos) e `jobbot-posts` (planejar e escrever posts de LinkedIn, com as skills do plugin `linkedin-skills`).

O que mudou depois do primeiro uso real está em `docs/melhorias-do-piloto.md`. Um tutorial completo, do zero à primeira rodada, está em `docs/passo-a-passo.md`.

**Relatórios:** cada etapa termina com um mini relatório em Markdown, guardado em `Documents/JobBot/<seu-nome>/`, para você não perder o que foi dito no chat. O fluxo completo está em `docs/flow.md`.

Dependência opcional: `linkedin-skills` (`claude plugin marketplace add sergebulaev/linkedin-skills` e `claude plugin install linkedin-skills@linkedin-skills`). O JobBot funciona sem ela. As skills que ele pode consultar (`linkedin-profile-optimizer`, `linkedin-interviewer`) não exigem chave de API para esse uso; a `linkedin-humanizer` é voltada ao inglês.

## Como usar

1. `jobbot-interview`: entrevista em etapas, retomável.
2. `jobbot-market`: propõe cargos a partir do seu perfil; depois da sua aprovação, lê cerca de 50 vagas públicas por cargo aprovado e escreve `focus-report.md`.
3. `jobbot-profiles`: lê LinkedIn, GitHub e as outras plataformas, mostra o que melhorar, escreve os textos e ajuda a aplicar.

## Orientação de carreira (B1)

Depois do A, use as skills nesta ordem (o teste de perfil é opcional e, se feito, vem antes do mercado):

1. `jobbot-assessment`: teste de cerca de 10 minutos (83 afirmações e 3 perguntas abertas: valores, interesses, personalidade, âncoras de carreira e estilo de trabalho). Pode ser pausado e retomado. Devolve percentuais por dimensão, relativos à pontuação máxima (não são ranking nem diagnóstico).
2. `jobbot-orientation`: profissões sugeridas em dois grupos (disponíveis agora e as que exigem nova formação), com o custo de cada. Fala com franqueza sobre o que você ama e o que paga, só com dados de mercado: com menos de 30 vagas lidas ela escreve "indício", nunca "saturado".
3. `jobbot-courses`: trilha de cursos por lacuna, em faixas gratuito, barato (até R$ 200, ajustável em `cheap_course_max`) e caro, sempre com a data da consulta. Curso concluído recalcula o match, mas nunca altera suas skills sozinho.

As perguntas do teste são de redação original ou adaptadas de itens de domínio público; veja `references/assessment-sources.md`.

## Tipos de vaga e currículos (B2)

1. `jobbot-types`: cada profissão aceita e liberada vira um **tipo de vaga** (piso de salário, modalidade e contrato próprios) e ganha um currículo-modelo em PDF.
2. `jobbot-resume`: dada uma vaga, o bot classifica no tipo certo, calcula o match e gera o PDF daquela vaga (modelo do tipo, resumo novo e skills reordenadas). Vaga boa sem tipo (match de 70% ou mais, dentro das suas restrições e do menor piso) recebe um currículo do zero. Cada currículo vem com uma **folha de revisão**.

Regras do PDF: texto selecionável, uma coluna, títulos padrão, sem tabelas, imagens nem texto escondido. Skills que você ainda não domina só aparecem na lista de Competências (e são listadas na folha de revisão para você saber o que pode ser perguntado); nunca no resumo nem nos bullets. Vaga arriscada (abaixo do corte de match) também gera PDF, sem nenhuma skill esticada. Vaga abaixo do piso é marcada, nunca descartada. Empregador, cargo, datas e certificações vêm só do seu perfil, e números só se você os informou. O texto livre (resumo e bullets) é escrito pelo bot e só tem checagem automática de números, skills que você não tem e nomes de empresa e projeto; por isso você precisa ler e aprovar cada PDF. Nada é enviado: você decide.

## Rodada de vagas (C)

1. `jobbot-round` ("rodar vagas"): em cada plataforma (LinkedIn, Indeed e Gupy) o bot **busca as vagas sozinho**, pelos tipos de vaga que você definiu, filtra o que não serve (vaga repetida, do seu empregador atual, de empresa vetada ou fora das suas restrições), gera o currículo em PDF de cada uma e deixa **uma aba aberta por vaga, no último passo do formulário**, com o PDF anexado e as respostas preenchidas. **Por padrão o bot é autônomo** (`autonomy: full`): responde as perguntas da empresa (sempre com dados do seu perfil, nunca inventados), escreve o texto de apresentação de cada vaga e finaliza. Prefere revisar antes? `jobbot run-settings <nome> --autonomy assisted` faz o bot parar no último passo, e você envia ou fecha a aba. Mesmo assim ele **nunca digita RG, CPF ou outro número de documento**: esses campos ficam com você. Atenção: pergunta eliminatória reprova na hora e a resposta não pode ser editada.
2. `jobbot-status`: mostra os limites do dia, atualiza o que foi enviado ou descartado e libera uma plataforma pausada quando você pedir.

Limites padrão: 10 abas por rodada e 30 por dia, em cada plataforma (`run-settings` muda), e no máximo 50 vagas examinadas por rodada. Pergunta de formulário sem resposta no seu banco fica em branco e destacada; no fim da rodada o bot pergunta tudo de uma vez e guarda as respostas. Campos sensíveis (PCD, gênero, raça, autorização de trabalho) e consentimentos legais só são respondidos se você tiver guardado a resposta. Vaga que leva ao site da empresa abre numa aba, sem preenchimento (`externa`).

Testes de fit cultural: o bot tenta responder um rascunho honesto com o seu perfil comportamental real (`auto`, `perguntar` ou `pular`). Ele avisa quando o teste proíbe IA, é cronometrado ou tem uma tentativa só, e nunca responde teste vigiado por câmera. Ser pego usando IA onde é proibido pode desclassificar a candidatura, e o relógio de um teste cronometrado começa ao abrir a aba.

Freios: captcha, pedido de verificação, aviso de atividade incomum ou tela de login pausam a plataforma até você liberar. O bot não contorna nada. Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas, e o risco para a conta é seu. Se você usa o Claude com a integração do Indeed, a busca nessa plataforma passa por ela; sem a integração, o bot usa o navegador.

## Seus dados

Tudo fica em `~/.jobbot/profiles/<seu-nome>/` (ou em `$JOBBOT_HOME`), uma pasta por pessoa. Nada é enviado a serviço externo; só páginas públicas de vagas são lidas na análise de mercado. O repositório não guarda dados de ninguém.

## Honestidade e estiramento

O JobBot pode listar uma skill que você ainda não domina, conforme a regra de estiramento (veja `references/honesty-and-stretch.md`). Ele nunca inventa empregadores, cargos, datas, formação, certificações nem números de resultado, e recusa números que você não informou.

Rótulos de match: menos de 50% **Arriscado**; 50% a 69% **Chance média**; 70% a 79% **Bom match**; 80% a 99% **Ótimo match**; 100% **Vaga perfeita**.

## Desenvolvimento

```bash
.venv/bin/pytest
```

O teste `test_no_ebook_text` só roda com `JOBBOT_EBOOK_TXT` apontando para um texto de referência; ele garante que nenhum trecho de 8 palavras seguidas foi copiado.

## Licença

MIT. Veja `LICENSE`.
