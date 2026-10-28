---
name: jobbot-profiles
description: Use depois da aprovação dos cargos (jobbot-market) para melhorar os perfis da pessoa em todas as plataformas (LinkedIn, GitHub, Indeed, Gupy, site e YouTube) antes de qualquer busca de vagas. Lê cada perfil, aponta o que melhorar frente aos cargos aprovados, escreve o texto pronto e ajuda a pessoa a aplicar, e só termina quando todas as plataformas estão prontas e revisadas. Gatilhos - "melhorar meu LinkedIn", "revisar meu GitHub", "ajustar meus perfis", "arrumar minhas plataformas".
---

# JobBot: perfis prontos e revisados

Esta etapa vem **antes** do currículo por tipo e da busca de vagas: quem abre o seu perfil depois de uma candidatura precisa encontrar o mesmo que o currículo diz. Fale em português do Brasil, direto e curto.

## Pré-requisitos

- `jobbot validate <nome>` responde `ok`, existe `focus-report.md` na pasta da pessoa (saída de `jobbot path <nome>`) e há cargos aprovados em `targets`. Se não, volte à skill `jobbot-market`.
- Leia `references/principles.md` e `references/honesty-and-stretch.md` antes de escrever. O que pode ser esticado está em `honesty-and-stretch.md`.

## Passos

1. **Lista de plataformas.** Monte a lista a partir do `profile.yaml` (`linkedin`, `github`, `links`) e pergunte pelas que faltam: Indeed, Gupy, site ou portfólio, YouTube. Nunca peça senha.
2. **Diagnóstico por plataforma.** Leia cada uma, só leitura, e compare com o que a pessoa faz de verdade (`profile.yaml`) e com as palavras-chave e skills pedidas nos cargos aprovados (`focus-report.md`):
   - **GitHub:** `gh repo list <usuario> --limit 30 --json name,description,pushedAt,isFork,isPrivate,primaryLanguage`, o README de cada repositório relevante e os fixados. Nunca rode `gh repo edit`, `git push` nem comando que altere algo.
   - **LinkedIn:** uma página pública da pessoa no navegador, com a sessão que ela já tem aberta; nunca faça login por ela e nunca percorra perfis de outras pessoas.
   - **Indeed, Gupy e outras:** peça que a pessoa abra a página já logada, ou que cole o texto do perfil.
   Escreva uma lista "o que melhorar" por plataforma, em ordem de impacto, com uma sugestão concreta por item. Procure sobretudo: skills e ferramentas que a pessoa domina e o perfil não mostra, manchete que não bate com o cargo aprovado, resultados medidos que só estão no currículo, projetos sem README ou invisíveis, e informação que diverge entre plataformas.
3. **Discrição e tom (antes de escrever).** Pergunte duas coisas e respeite as respostas: (a) **o empregador atual pode saber que a pessoa procura emprego?** Se não, o texto público **nunca** diz "buscando vagas", "disponível" ou "em transição", a manchete não muda para algo que denuncie a busca, **não se liga o selo "Open to work"** (nem a versão "só recrutadores", que não garante esconder do empregador), e **não se adiciona cargo novo nem se usa o aviso de "notificar a rede"** nas edições; (b) **o tom.** Escreva como se o chefe atual fosse ler: humilde, factual, que dá crédito à equipe, sem superlativo e sem "eu sou o melhor". Resultado em número, sim; adjetivo sobre si mesmo, não.
3. **Confidencialidade.** Antes de sugerir qualquer coisa pública, pergunte o que é de empregador ou cliente. **Nunca sugira publicar código, dados, nome de cliente ou valor que a pessoa disse ser confidencial.** Para quem tem trabalho confidencial, proponha descrição sem nome e sem números sensíveis, ou um projeto equivalente com dados sintéticos.
4. **Texto pronto.** Para cada plataforma, escreva o texto na pasta da pessoa (`linkedin.md`, `github.md`, e um arquivo por plataforma extra): manchete, Sobre, uma entrada por experiência com resultados primeiro, competências, e para o GitHub o README de perfil, as descrições dos repositórios e o que fixar. Use só fatos do `profile.yaml`; número só se estiver em `metric`. Depois de `linkedin.md`, rode `jobbot check <nome> linkedin.md` e corrija os números listados se sair com código 1. Para o checklist de visibilidade do LinkedIn, use `references/visibility-checklist.md`.
5. **Aplicar nas plataformas.** Se a pessoa **autorizou que você preencha** (o texto dela no chat vale como a autorização, mas só para o que ela pediu), aplique você mesmo: no LinkedIn, no navegador, na sessão dela, um campo por vez, mostrando o que vai mudar antes de salvar e conferindo depois; no GitHub, com `gh`, só estas ações: criar o repositório de perfil, atualizar a descrição de repositórios e criar um repositório novo de portfólio. Sem autorização, ela cola e você só orienta. Em qualquer caso: nunca publique post, nunca altere configuração de conta ou de privacidade, nunca faça login por ela, nunca apague repositório, nunca force-push, nunca mude a visibilidade de repositório e nunca publique código ou dado que ela marcou como confidencial. Se algo na tela não for o esperado, pare e pergunte.
6. **Revisão.** Depois que a pessoa aplicar, releia a página pública e compare com o texto combinado. Marque a plataforma como pronta só quando conferida; o que faltar volta para a lista de pendências.
7. **Fechamento.** Quando **todas** as plataformas estiverem prontas e revisadas, escreva `perfis-revisados.md` na pasta da pessoa com uma linha por plataforma (`plataforma | estado | data | pendências`). Sem esse arquivo a jornada não avança. Diga que o próximo passo é a skill `jobbot-types`: um currículo para cada tipo de emprego.

O bot nunca edita nada sozinho. A skill `linkedin-profile-optimizer`, se instalada, pode servir de segunda opinião, mas foi pensada para perfis em inglês; não dependa dela.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): por plataforma: o que foi encontrado, o que melhorar, o texto aprovado, o estado (pronto ou pendente) e as pendências. É o `perfis-revisados.md` com os textos finais. Grave num arquivo temporário (nunca em Downloads) e rode `jobbot report-save <nome> 04-perfis <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
