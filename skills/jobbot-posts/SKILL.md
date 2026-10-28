---
name: jobbot-posts
description: Use, sob pedido, para planejar e criar posts de LinkedIn a partir do que a pessoa realmente fez (projetos, aprendizados, resultados) e do foco de carreira aprovado, sem denunciar busca de emprego e sem expor nada confidencial. Monta um plano de 1 a 2 semanas, escreve os rascunhos em português, passa pela checagem de números e só publica com o OK explícito da pessoa, post a post. Usa as skills do plugin linkedin-skills quando instaladas. Gatilhos - "planejar posts", "criar post pro LinkedIn", "o que postar", "calendário de conteúdo".
---

# JobBot: posts de LinkedIn

Posts são **conteúdo público**, com o nome da pessoa e, muitas vezes, vistos pelo empregador atual. Fale em português do Brasil, direto e curto. Aviso, sem alterar o texto, ao começar:

Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa.

## Pré-requisitos

- `python3 -m jobbot validate <nome>` responde `ok`; leia o `profile.yaml`, o `focus-report.md` e o `perfis-revisados.md` na pasta de `python3 -m jobbot path <nome>`.
- Skills do plugin `linkedin-skills` (instaladas à parte): `linkedin-content-planner` (plano da semana), `linkedin-post-writer` (rascunho), `linkedin-interviewer` (tirar o fato concreto da pessoa), `linkedin-humanizer` (auditoria, feita para inglês). Sem elas, siga os passos abaixo por conta própria.

## Regras que valem antes de qualquer texto

1. **Discrição.** Pergunte (ou releia do `perfis-revisados.md`) se o empregador atual pode saber que a pessoa procura emprego. Se não puder: nenhum post diz "buscando vagas", "em transição", "disponível" ou usa `#opentowork`, e o ritmo e o assunto continuam coerentes com o cargo atual. O post mostra o que a pessoa **faz e aprende**, não que quer sair.
2. **Confidencialidade.** Pergunte o que é de empregador ou cliente. Nunca cite código, dado, nome de cliente, valor em dinheiro ou detalhe interno que a pessoa marcou como confidencial. O nome do empregador só aparece se a pessoa disser que pode. Prefira "um projeto privado" a um nome.
3. **Tom.** Factual e humilde, como se a chefia fosse ler. Resultado em número, sim; adjetivo sobre si mesmo, não. Dê crédito à equipe e a quem fez o código aberto de onde a pessoa partiu.
4. **Só fato real.** Todo número e todo resultado vêm do `profile.yaml` ou do que a pessoa acabou de dizer. Nunca invente caso, cliente, métrica ou depoimento. Sem fato, o post fala de aprendizado, não de resultado.
5. **Nunca publique sozinho.** Rascunho não é publicação. Só publique depois de um "sim" explícito da pessoa **para aquele post**, e sem agendar nada sem o OK. A pessoa pode preferir colar ela mesma.

## Passos

1. **Material.** Liste, junto com a pessoa, de 6 a 10 assuntos reais, tirados de: projetos públicos (o repositório de portfólio, projetos de código aberto), aprendizados de trabalho **sem** dado confidencial, resultados medidos que ela já mostra no perfil, e opinião técnica que ela de fato defende. Se faltar o fato concreto (o momento, o número, o que mudou), use `linkedin-interviewer` ou faça 2 a 3 perguntas curtas, de uma vez.
2. **Pilares.** Distribua em três pilares, ajustados ao foco aprovado: **autoridade** (o que a pessoa sabe fazer na área do foco), **narrativa** (o que aprendeu, errou e mudou) e **comunidade** (agradecer, citar quem ajudou, projetos abertos). Cargo atual não vira vitrine: o plano não pode parecer currículo.
3. **Plano.** Com `linkedin-content-planner`, monte 1 a 2 semanas, de 2 a 3 posts por semana para começar (aumento brusco de atividade chama atenção do empregador). Para cada post: dia, pilar, ideia em uma linha, formato e meta (comentários, salvamentos, repostagens). Salve em `posts-plan.md` na pasta da pessoa.
4. **Rascunhos.** Com `linkedin-post-writer`, escreva os posts escolhidos em português, um arquivo por post (`post-01.md`, `post-02.md`...). Regras de formato: a primeira linha é afirmação ou número, nunca pergunta; parágrafos de 1 a 2 frases; pergunta específica no fim; sem links no corpo (o link vai no primeiro comentário); no máximo 2 hashtags; sem "Aqui está", "Vou te contar", "o resultado?" nem listas de três adjetivos. Escreva como a pessoa fala: se houver `voice-profile`, siga.
5. **Checagem.** Para cada rascunho, rode `python3 -m jobbot check <nome> post-01.md`. Se sair com código 1, corrija ou tire os números listados. Releia pensando "o empregador atual leria isto sem problema?" e "isto expõe algo confidencial?". Passe o texto por `linkedin-humanizer --mode audit` só se a pessoa escreve em inglês; em português, faça você mesmo a limpeza de frases de efeito.
6. **Aprovação.** Mostre cada post com: ideia, texto, número de caracteres e horário sugerido (dia útil, 7h30 às 9h). Peça "sim", "ajustar" ou "descartar". Só com "sim" explícito, publique pelo navegador na sessão da pessoa (nunca faça login por ela), ou entregue o texto para ela colar. Depois de publicar, confira a página e informe o link.
7. **Depois de publicar.** Lembre a pessoa de responder comentários nas primeiras horas (a skill `linkedin-reply-handler` ajuda) e de comentar posts de outras pessoas da área em vez de só postar.

## Relatório para guardar

No fim, escreva um mini relatório em Markdown com o plano (tabela de dias, pilares e ideias), os rascunhos aprovados, os descartados e o que ficou pendente. Grave num arquivo temporário (nunca em Downloads) e rode `python3 -m jobbot report-save <nome> 07-posts-AAAA-MM-DD <arquivo.md>` (use a data de hoje). Diga à pessoa o caminho `relatorio:`. O relatório não traz dado que a pessoa disse ser confidencial.
