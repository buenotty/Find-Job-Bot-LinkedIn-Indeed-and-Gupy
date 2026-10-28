---
name: jobbot-orientation
description: Use, sob pedido e de forma opcional, depois da análise de mercado (jobbot-market) para sugerir profissões em dois grupos (disponíveis agora e as que exigem nova formação) com o custo de cada, falar com franqueza sobre o que a pessoa ama e o que paga, e registrar as profissões que ela aceita. Gatilhos - "que profissão seguir", "vale mudar de área", "o que combina comigo", "sugerir carreiras".
---

# JobBot: orientação de carreira

## Pré-requisitos

- Perfil válido (`python3 -m jobbot validate <nome>` responde `ok`), pelo menos um resultado de teste (`assessments` no `profile.yaml`, na pasta de `python3 -m jobbot path <nome>`) e o `focus-report.md` da skill `jobbot-market`, que já traz os cargos que a pessoa aprovou.
- Leia `references/honest-career-talk.md` antes de falar com a pessoa.

## Passos

1. **Ler.** Leia o `profile.yaml`: skills, restrições, pretensão salarial, o resultado mais recente do teste e as respostas abertas. Releia o `focus-report.md`.
2. **Sugerir.** Comece pelos cargos aprovados no `focus-report.md` e acrescente de 8 a 15 profissões a partir dos percentuais do teste, das skills e do mercado. Separe em dois grupos:
   - **Disponíveis agora:** a pessoa pode disputar vagas com o perfil atual.
   - **Exigem nova formação:** falta mais do que alguns cursos.
3. **Ler o mercado de uma lista curta.** Escolha cerca de 5 profissões pelo encaixe com perfil e teste e leia de 30 a 50 vagas públicas de cada uma, com as mesmas regras da skill `jobbot-market` (páginas públicas, sem login em massa, sem contornar bloqueio). Anote salário mediano, candidatos por vaga e skills pedidas. As demais saem como "sem dado de mercado"; ofereça aprofundar qualquer uma sob pedido.
4. **Afirmar só com dado.** Antes de dizer "saturado" ou "paga pouco", rode `python3 -m jobbot market-claims <nome> --n-jobs N --salary-median S --applicants-median A`. Se a resposta for `indicio`, escreva "indício, amostra de N vagas". Se for `sem_dado`, não afirme nada. Atenção: `paga_pouco` compara o salário mediano com a pretensão da pessoa. Diga "abaixo da sua pretensão", e só diga "o mercado paga pouco" se o salário mediano também ficar baixo frente às outras profissões lidas.
5. **Mostrar o custo de cada profissão.** Para as disponíveis agora: vagas lidas, salário mediano, concorrência e match. Para as que exigem formação: custo e tempo estimados para chegar lá, com a fonte e a data da consulta. Nunca invente valor.
6. **Falar com franqueza.** Quando o que a pessoa ama divergir do que paga, apresente os três caminhos de `references/honest-career-talk.md`. A escolha é dela.
7. **Registrar.** A pessoa marca as profissões que aceita e pode acrescentar outras. Para cada uma, grave um YAML com `role`, `source` (`sugerida` ou `propria`) e `required_skills` (as skills mais pedidas nas vagas lidas, se houver) e rode `python3 -m jobbot target-add <nome> <arquivo.yaml>`. Sem lista de skills, a profissão fica como "sem dado de mercado" e o match só é calculado depois da análise de mercado.

A seguir, `jobbot-courses` monta a trilha de cursos para cada lacuna.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): as profissões sugeridas nos dois grupos, o custo de cada, a conversa franca sobre o que a pessoa ama e o que paga, e as que ela aceitou. Grave num arquivo temporário (nunca em Downloads) e rode `python3 -m jobbot report-save <nome> 03b-orientacao <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
