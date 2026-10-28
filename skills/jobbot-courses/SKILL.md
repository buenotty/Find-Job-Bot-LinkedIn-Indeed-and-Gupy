---
name: jobbot-courses
description: Use depois da orientação (jobbot-orientation) para montar a trilha de cursos das profissões aceitas. Mostra a lacuna de skills de cada uma, busca cursos gratuitos, baratos e caros que cobrem essa lacuna, recalcula o match depois de cada curso concluído e nunca promete resultado. Gatilhos - "quais cursos fazer", "o que falta para essa vaga", "terminei um curso".
---

# JobBot: trilha de cursos

## Pré-requisitos

- Perfil válido e pelo menos uma profissão em `targets` (skill `jobbot-orientation`).

## Passos

1. **Lacuna.** Para cada profissão aceita com lista de skills, rode `jobbot project-match <nome> "<profissão>"`. A linha `missing` mostra o que falta e `pct` o match atual. Sem lista de skills a saída é um erro e não há recálculo de match. Nesse caso, mostre a ementa dos cursos que você achar como lista provisória, marcada "sem dado de mercado", e sugira rodar a análise de mercado ou pedir a lista à pessoa.
2. **Buscar cursos.** Procure em páginas públicas cursos que cubram cada skill que falta. Anote nome, instituição, link, preço e duração só quando a página informar. Nunca invente curso, preço ou duração. Registre a data da consulta e escreva-a junto de cada preço ("consultado em AAAA-MM-DD"), porque preços mudam.
3. **Classificar.** Para cada preço, rode `jobbot band <nome> <preço em reais | gratis>`. A saída é `gratuito`, `barato` ou `caro` (o limite de "barato" está em `cheap_course_max` no perfil, padrão R$ 200). Mostre os três grupos separados e diga qual combinação leva a pessoa mais perto da vaga.
4. **Falar a verdade.** Curso reduz a lacuna de skills; não garante seleção, entrevista nem salário. Nunca diga "100% pronto".
5. **Curso concluído.** Quando a pessoa disser que terminou um curso, proponha as skills que a ementa cobre e deixe a pessoa confirmar quais ela realmente aprendeu. Grave um YAML com `course`, `provider`, `date`, `skills_claimed` (só as confirmadas) e `evidence`, e rode `jobbot course-add <nome> <arquivo.yaml>`. Rode `project-match` de novo e mostre o novo match.
6. **O currículo não muda sozinho.** Curso concluído não altera `skills` no perfil. Só inclua a skill em `skills` (nível `iniciante`) se a pessoa confirmar e der uma evidência, como um projeto feito. Certificação só entra em `certifications` se o curso emitiu certificado e a pessoa informou nome e emissor.
7. **Liberação do currículo.** A linha `cv_liberado` diz se já vale gerar currículo para essa profissão: `sim` para as disponíveis agora e para as de formação cujo match chegou ao corte da pessoa (padrão 90%).

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): a trilha de cursos por lacuna, nas faixas gratuito, barato e caro, com link, preço e a data da consulta. Grave num arquivo temporário (nunca em Downloads) e rode `jobbot report-save <nome> 03c-trilha-de-cursos <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
