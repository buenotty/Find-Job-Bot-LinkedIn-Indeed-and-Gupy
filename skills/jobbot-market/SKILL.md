---
name: jobbot-market
description: Use depois da entrevista e do teste de perfil para descobrir em quais cargos a pessoa tem mais chance e qual deve ser o foco. Primeiro pesquisa sobre a própria pessoa e propõe de 5 a 8 cargos com o motivo de cada; só depois que ela aprova a lista, lê cerca de 50 vagas públicas por cargo aprovado, mede demanda, salário, concorrência e skills pedidas e escreve o relatório de foco. Gatilhos - "qual cargo focar", "analisar o mercado", "em que vagas eu me encaixo", "vale migrar de área".
---

# JobBot: mercado e foco recomendado

São duas fases, com uma **parada obrigatória** entre elas. A fase 1 é sobre a pessoa. A fase 2, a leitura de vagas, só começa depois que a pessoa aprova a lista de cargos. Fale em português do Brasil, direto e curto.

## Pré-requisitos

- `python3 -m jobbot status <nome>` deve responder `completo` e `python3 -m jobbot validate <nome>` deve responder `ok`. Se não, volte à skill `jobbot-interview`.
- A pasta da pessoa é a saída de `python3 -m jobbot path <nome>`. Leia o `profile.yaml` dela.
- O teste de perfil (`jobbot-assessment`) deixa o diagnóstico bem melhor. Se `python3 -m jobbot behavior <nome>` vier com `ultimo_teste` vazio, ofereça fazer o teste agora (cerca de 10 minutos) ou seguir só com o perfil, e diga que sem teste o diagnóstico fica menos preciso. A decisão é da pessoa.

## Fase 1: diagnóstico e cargos candidatos (sem ler vaga nenhuma)

1. **Retrato da pessoa.** Se o `profile.yaml` tem `github` ou `linkedin`, releia as páginas públicas (GitHub com `gh`, só leitura; LinkedIn uma página no navegador) para ver o que mudou desde a entrevista. Do `profile.yaml`, do teste e do que ela contou, escreva em poucas linhas: o que ela faz melhor (skills de nível alto com evidência, projetos e resultados com número), o nível provável (júnior, pleno) pelo tempo real de experiência, o que ela quer (trilha, valores e âncoras mais altos, pretensão salarial, modalidade e cidade), e o que **não** deve pesar (experiências que ela disse não servirem para as vagas que quer).
2. **Cargos candidatos.** Proponha de 5 a 8, de três tipos: os que ela já faz, os vizinhos pelas skills e os que combinam com o teste mesmo sem experiência formal. Para cada cargo, mostre:
   - **por que combina**: a evidência no perfil, em uma frase;
   - **nível provável** de entrada;
   - **faixa de salário típica** (uma busca rápida em páginas públicas de salário, com fonte e data) contra a pretensão e o mínimo para presencial dela;
   - **skills que faltam**: rode `python3 -m jobbot match <nome> --required "skill1,skill2,..."` com as skills que o cargo costuma pedir;
   - **encaixe nas restrições** (modalidade, cidade, contrato).
3. **PARE e peça aprovação.** Mostre a lista numa tabela curta e pergunte: quais ela aprova, quais descarta e se falta algum. **Não leia nenhuma vaga antes da resposta.** Se ela pedir mudanças, ajuste a lista e mostre de novo.

## Fase 2: leitura de vagas, só dos cargos aprovados

4. **Coleta.** Para cada cargo aprovado, junte cerca de 50 anúncios de páginas públicas (busca na web, leitura de páginas públicas ou navegador). Respeite os termos de cada site: sem login em massa, sem contornar bloqueios, sem ritmo agressivo. Se um site bloquear, use menos vagas e diga isso no relatório.
5. **Extração.** Por vaga, anote `title`, `company`, `skills` (só ferramentas e conhecimentos técnicos, uma lista curta e padronizada), `salary_min` e `salary_max` (só se o anúncio informar), `applicants` (só se o site mostrar) e `url`. Não preencha o que o anúncio não traz.
6. **Arquivos.** Grave um `jobs-<cargo>.json` por cargo na pasta da pessoa:
   ```json
   {"role": "Analista de Dados", "jobs": [{"title": "...", "company": "...", "skills": ["SQL", "Power BI"], "salary_min": 5000, "salary_max": 7000, "applicants": 45, "url": "..."}]}
   ```
7. **Ranking.** Rode `python3 -m jobbot market <nome> jobs-a.json jobs-b.json ...`. A tabela ordena por quanto do que o mercado mais pede a pessoa já tem, depois por número de vagas e por menos candidatos.
8. **Relatório.** Escreva `focus-report.md` na pasta da pessoa com:
   - o retrato e a lista de cargos aprovados (e os descartados, com o motivo);
   - a tabela do passo 7;
   - o foco recomendado e por quê, citando vagas, salário mediano e concorrência quando houver dado;
   - as lacunas de skill de cada cargo e, para cada lacuna, um projeto prático de 1 a 2 dias que a cubra;
   - o tamanho real da amostra por cargo e os limites dela (só vagas públicas, poucos anúncios, salário ausente). Com menos de 30 vagas num cargo, diga que o resultado é apenas um indício.

9. **Registrar os cargos aprovados.** Para cada cargo aprovado, grave um YAML com `role`, `source` (`sugerida` ou `propria`) e `required_skills` (as skills mais pedidas nas vagas lidas) e rode `python3 -m jobbot target-add <nome> <arquivo.yaml>`. É isso que libera o currículo por tipo na etapa seguinte.

Não decida pela pessoa: apresente a recomendação com o motivo e deixe a escolha final com ela. Depois, siga para a skill `jobbot-profiles`. Se a pessoa quiser mudar de área, ver custo de formação ou montar uma trilha de cursos, ofereça `jobbot-orientation` e `jobbot-courses`, que são opcionais.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): o retrato da pessoa, os cargos aprovados e descartados (com o motivo), a tabela de mercado, o foco recomendado, as lacunas de skill com um projeto de 1 a 2 dias para cada, e o tamanho e os limites da amostra. É o `focus-report.md` com o resumo no topo. Grave num arquivo temporário (nunca em Downloads) e rode `python3 -m jobbot report-save <nome> 03-cargos-e-mercado <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
