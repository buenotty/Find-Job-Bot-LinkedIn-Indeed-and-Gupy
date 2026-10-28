# Jobs Master BR v1 — Projeto B1: Orientação de carreira (design)

Data: 2026-10-25. Idioma: PT-BR. Mercado: Brasil.

## Contexto e intenção

O projeto A (`2026-10-25-mapeamento-design.md`) entrevista a pessoa, analisa o mercado e gera perfil e CV base. O B foi dividido em:

- **B1 (este documento):** teste de perfil, profissões sugeridas com custo, caminhos honestos e trilha de cursos.
- **B2:** tipos de vaga (piso de salário, modalidade e contrato por tipo), currículos por tipo e CV do zero.
- **C:** candidatura semi-automática, incluindo as respostas de testes de fit cultural.

B1 depende de A: usa o `profile` local, a análise de mercado e a regra de honestidade. B1 alimenta B2 com a lista de profissões que a pessoa aceitou.

Problema que B1 resolve: a pessoa não sabe em qual área disputar vagas. Hoje ela escolhe por impressão. B1 a conhece a fundo e diz, com dados e sem rodeio, o que combina com ela, o que o mercado paga e o que falta aprender.

## O que "missão cumprida" significa para B1

Ao fim de B1, a pessoa tem:

1. **Resultado do teste**: percentuais por dimensão (interesses, personalidade, valores de trabalho), em linguagem direta.
2. **Profissões sugeridas**, em dois grupos, cada uma com custo:
   - **Disponíveis agora**: dá para disputar vagas já, com o perfil atual. Mostram vagas reais lidas, salário mediano e concorrência.
   - **Exigem nova formação**: mostram o custo e o tempo estimados para chegar lá.
3. **Três caminhos honestos** quando amor e dinheiro divergem: o que a pessoa ama (com o custo real), o que paga e tem espaço, e um híbrido.
4. **Profissões aceitas**: a lista que a pessoa marcou, mais as que ela acrescentou por conta própria. Essa lista é a entrada do B2.
5. **Trilha de cursos** por lacuna de skill de cada profissão aceita, separada em gratuitos, baratos e caros, com o match recalculado depois de cada curso.

## Objetivos

- Teste longo, em camadas, de cerca de 20 a 30 minutos, retomável: o dono quer um bot que conheça o usuário a ponto de ser o mais preciso possível.
  - **Interesses**: modelo de seis áreas (prático, investigativo, artístico, social, empreendedor, convencional), com itens de redação própria.
  - **Personalidade**: cinco grandes traços, com itens de banco de domínio público (IPIP).
  - **Valores de trabalho**: salário, estabilidade, autonomia, propósito e quanto a pessoa abre mão de cada um.
  - **Perguntas de situação**: pedem exemplos reais ("conte uma vez em que...") para o bot cruzar com as respostas fechadas.
- Precisão: itens repetidos com frase invertida para detectar resposta apressada ou incoerente; o bot aponta contradições entre o teste e o histórico da pessoa; notas datadas, para refazer e comparar.
- Resultado em percentuais por dimensão, em tom direto, com a ressalva de que é autorrelato e não diagnóstico.
- Sugestão de profissões a partir dos percentuais, das skills do perfil e dos dados de mercado (reaproveita o módulo de mercado do A).
- Diagnóstico honesto: afirmações como "mercado saturado" ou "paga pouco" só aparecem se os dados de mercado mostrarem isso (muitos candidatos por vaga, salário mediano baixo), com o tamanho da amostra.
- Trilha de cursos: busca cursos que cobrem cada lacuna, classifica por preço e informa a data da consulta.
- Recalcular o match da pessoa com cada profissão aceita depois de cada curso concluído que ela informar.

## Não objetivos

- Diagnóstico psicológico validado. O teste é indicativo.
- Garantir "100% pronto" ou qualquer resultado de seleção. O bot mostra a lacuna e os cursos; não promete aprovação.
- Currículos por tipo e CV do zero (B2).
- Responder testes de fit cultural de empresas (C).
- Editar qualquer coisa fora da máquina da pessoa.

## Anti-objetivos (seria falha mesmo que tecnicamente funcione)

- Apresentar percentuais como diagnóstico clínico.
- Inventar preço, duração ou existência de curso, ou apresentar preço antigo sem a data da consulta.
- Empurrar a pessoa só para o que paga mais. As duas opções (amor e dinheiro) e o híbrido aparecem, e a escolha é dela.
- Dados do teste saírem da máquina da pessoa.
- Copiar itens de testes proprietários ou com direitos (por exemplo, inventários comerciais). Só itens de domínio público ou de redação própria.
- Afirmar mercado saturado ou salário baixo sem dado que sustente.

## Decisões já tomadas pelo dono

- Teste longo e preciso é aceito e desejado.
- As sugestões incluem profissões disponíveis agora e profissões que exigem nova formação, mostrando o custo de cada.
- O bot deve falar com sinceridade, no estilo de teste vocacional: percentuais por área e profissões sugeridas, seguidos de decisão da pessoa sobre quais aceita e quais acrescentar.
- Caminho honesto entre o que a pessoa ama (mercado possivelmente saturado e de pouca remuneração) e o que dá dinheiro (mercado mais livre e melhor pago).
- Cursos classificados em gratuitos, baratos e caros, com o match recalculado.
- Dados psicológicos são sensíveis: ficam só locais, com permissão restrita, como o resto do perfil.

## Decisões do bot (aprovação junto com este documento)

- "Barato" significa até R$ 200 por curso; "caro", acima disso; "gratuito", R$ 0. O limite é configurável por pessoa.
- Teste em camadas de 20 a 30 minutos, na ordem: valores, interesses, personalidade, situações.
- Os resultados entram no `profile` como um bloco novo (`assessment`), com data. O bloco novo não quebra os perfis do A.
- A lista de profissões aceitas é gravada no perfil (`targets`) e consumida pelo B2.
- **Curso concluído é projeção, não fato do currículo.** O recálculo de match usa uma lista de cursos concluídos guardada à parte (`courses_done`) e não altera `profile.skills`. Uma skill só entra em `skills` (nível `iniciante`) se a pessoa confirmar e der evidência (nome do curso e o que fez). Uma certificação só entra em `certifications` se o curso emitiu certificado e a pessoa informou nome e emissor. Isso preserva a regra de honestidade do A.
- **`targets` guarda, por profissão:** `role`, `group` (`agora` ou `nova_formacao`), `source` (`sugerida` ou `propria`), `required_skills`, `match_at_acceptance` e a data. Profissões `nova_formacao` entram em `targets` com status `em_formacao`. O B2 só gera currículo para `agora` ou para `nova_formacao` cujo match recalculado chegou ao corte da pessoa. Profissão acrescentada pela própria pessoa pode entrar sem análise, marcada como "sem dado de mercado" até a análise rodar.
- **Mínimo de amostra:** com menos de 30 vagas lidas para um cargo, o bot não escreve "saturado" nem "paga pouco"; escreve "indício, amostra de N vagas". Profissão `nova_formacao` sem anúncios que sirvam para análise aparece como "sem dado de mercado", só com custo e tempo de formação.
- **"Disponível agora" e "corte da pessoa":** profissão com match de 50% ou mais (o `risky_below` da `stretch_policy`) é `agora`. Profissão abaixo de 50% ("Arriscado") é sempre `nova_formacao`. O "corte da pessoa" que libera o B2 para uma `nova_formacao` é o `stretch_from` da mesma política (padrão 90%). Nenhum campo novo de corte.
- **Sem `required_skills`** (profissão própria ou `nova_formacao` sem anúncios): não há recálculo de match até a análise de mercado rodar ou a pessoa informar a lista. A trilha de cursos mostra a ementa dos cursos como lista provisória, marcada "sem dado de mercado". `coverage()` nunca recebe lista vazia.
- **Registro em `courses_done`:** `course`, `provider`, `date`, `skills_claimed` (skills que a pessoa confirma que o curso cobriu) e `evidence`. O bot sugere skills a partir da ementa, mas só entram na projeção as que a pessoa confirmar e que estão em `required_skills`. Isso impede projeção inflada.
- **Percentuais são autorrelativos:** parcela da pontuação máxima possível em cada dimensão, não percentil de uma população (não existem normas brasileiras para estes itens). O bot nunca escreve "você está entre os X% mais".
- **Leitura de mercado em rodadas:** cada execução lê de 30 a 50 vagas só para uma lista curta (cerca de 5 profissões, escolhidas pelo encaixe com perfil e teste). As demais saem como "sem dado de mercado" e a pessoa pode pedir o aprofundamento de qualquer uma.
- **Pré-requisito:** a entrevista do A está completa e o perfil é válido. O nome do arquivo de estado do teste é escolha do construtor.
- **`assessment` é um histórico datado** (lista; a mais recente vale). O progresso do teste fica em um arquivo de estado próprio, separado do `state.yaml` do A. Perfis já gravados pelo A continuam válidos sem migração: `assessment`, `targets` e `courses_done` começam vazios.

## Restrições

- Skills do Claude Code mais CLI Python, como no A. Reaproveita `store`, `schema`, `match`, `market` e `honesty`.
- Dados 100% locais. Só páginas públicas são lidas, para vagas e cursos.
- PT-BR e Brasil.
- Itens do teste: redação própria ou domínio público, com a fonte e a licença documentadas no repositório.
- Repositório público: nenhum dado de pessoa real e nenhum texto de material com direitos.

## Entregáveis de B1

1. Skill de teste (camadas, retomável), gravando `assessment` no perfil.
2. Cálculo de percentuais por dimensão e checagem de consistência.
3. Skill de orientação: profissões sugeridas em dois grupos com custo, três caminhos e lista de aceitas (`targets`).
4. Skill de trilha de cursos com classificação de preço e data da consulta, e recálculo do match.
5. Extensão do esquema do `profile` (`assessment`, `targets`) e dos comandos da CLI.
6. Documentação das fontes e licenças dos itens do teste.

## Deixado para o construtor

- Redação dos itens e escalas, quantidade exata por camada, e o cálculo das notas.
- Como mapear notas para profissões: modelo guiado por dados de mercado, base de ocupações, ou os dois.
- Fontes de cursos e como estimar custo e tempo de uma formação longa.
- Formato dos resultados e do relatório de orientação.
- Estrutura dos arquivos e nomes dos comandos da CLI.
