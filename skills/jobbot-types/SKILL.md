---
name: jobbot-types
description: Use depois dos perfis revisados (jobbot-profiles) para transformar cada cargo aprovado e liberado em um tipo de vaga, com piso de salário, modalidade e contrato próprios, e gerar o currículo-modelo em PDF de cada tipo. Gatilhos - "definir tipos de vaga", "gerar meu currículo por tipo", "currículo para hardware", "modelo de currículo".
---

# JobBot: tipos de vaga e currículos-modelo

Cada tipo de vaga nasce de uma profissão aceita (`targets`) que já foi liberada para currículo. O PDF de cada tipo é o modelo que a skill `jobbot-resume` ajusta para cada vaga.

## Pré-requisitos

- `jobbot validate <nome>` responde `ok` e existe pelo menos uma profissão em `targets`.
- Leia `references/resume-writing.md` antes de escrever qualquer texto de currículo.
- Rode `jobbot type-list <nome>`. A linha `sem_tipo_definido` lista as profissões liberadas que ainda não viraram tipo. Profissão de nova formação só aparece quando o match recalculado chegou ao seu corte; as demais aguardam os cursos.

## Passos

1. **Definir o tipo.** Para cada profissão liberada, pergunte o piso de salário, as modalidades aceitas (`remoto`, `hibrido`, `presencial`) e o contrato (`CLT`, `PJ` ou `ambos`). Explique que o que ficar vazio usa o padrão do perfil (pretensão salarial, restrições e contrato da triagem), e que o piso pode ser menor numa área que a pessoa ama e paga menos. Opcionalmente peça palavras-chave extras do tipo (`keywords`). Grave um YAML com `role`, e os campos informados, e rode `jobbot type-define <nome> <arquivo.yaml>`.
2. **Escrever o currículo-modelo.** Para cada tipo, escreva um YAML de conteúdo e rode `jobbot type-resume <nome> "<profissão>" <conteudo.yaml>`:
   - `summary`: até 480 caracteres (4 linhas), voltado ao tipo;
   - `experience_bullets`: mapa `empresa: [bullets]`, só com empresas que existem no perfil; as empresas listadas são as únicas que aparecem no PDF, na ordem do mapa (vazio = todas), então deixe de fora a experiência que a pessoa disse não ser relevante para o tipo;
   - `project_bullets`: mapa `nome do projeto: [bullets]`, só com projetos do perfil; os projetos listados são os únicos que aparecem no PDF, na ordem do mapa (vazio = todos), então escolha os que importam para o tipo;
   - `headline`: uma linha sob o nome com o foco deste currículo (por exemplo, "Engenheiro de Dados e IA aplicada"), sem inventar cargo que a pessoa não tem;
   - `skill_groups`: mapa `rótulo: [skills]` para mostrar as competências agrupadas (por exemplo, "IA e agentes", "Programação", "Dados"). Só aceita skills que a pessoa tem, e o grupo substitui a lista corrida;
   - `show_projects`: `false` tira a seção de projetos inteira, para o tipo em que nenhum projeto é relevante (o padrão é `true`);
   - `skill_order`: as skills do tipo que a pessoa tem, na ordem em que devem aparecer.
   Siga o padrão XYZ e as regras de `references/resume-writing.md`. Use números só se a pessoa os informou.
3. **Sem experiência formal na área.** Use os projetos do perfil: `kind` `autodidata` ou `voluntariado`, com `start`. Eles aparecem em "Projetos e voluntariado" com o rótulo do tipo (por exemplo, "Autodidata desde 2022"). Não crie cargo nem empregador. Se o projeto ainda não tem `kind` e `start` no perfil, peça os dados e regrave a etapa `experiencias` (reenvie as listas inteiras, com os projetos assim: `{name: Montagem de PCs, description: ..., kind: autodidata, start: "2022-03"}`).
4. **Revisar.** Mostre o caminho do PDF (saída `pdf:`) e peça para a pessoa abrir e aprovar. Corrija o YAML e rode `type-resume` de novo se ela quiser mudar algo.

Se um comando recusar o conteúdo (número sem respaldo, empresa fora do perfil), explique o motivo à pessoa e corrija o texto. Nunca contorne a recusa.

Depois de aprovados os modelos, use a skill `jobbot-resume` em cada vaga.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): os tipos de emprego definidos (piso, modalidade, contrato), o caminho de cada currículo em PDF e o que cada um destaca. Grave num arquivo temporário (nunca em Downloads) e rode `jobbot report-save <nome> 05-curriculos <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
