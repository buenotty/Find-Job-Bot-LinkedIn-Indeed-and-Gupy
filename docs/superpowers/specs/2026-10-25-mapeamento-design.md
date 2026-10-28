# JobBot — Projeto A: Mapeamento de perfil (design)

Data: 2026-10-25. Idioma do produto: PT-BR. Mercado do v1: Brasil.

## Contexto e intenção

Candidatar-se a vagas (LinkedIn, Indeed, Gupy) consome tempo demais, principalmente adaptar o currículo a cada vaga e repetir formulários. O JobBot reduz esse trabalho. Ele é feito de 4 projetos independentes, construídos nesta ordem:

- **A. Mapeamento (este documento).** Entrevista a pessoa, analisa o mercado, recomenda o foco e gera perfil e CV base.
- **B. Alvos e currículos.** Define os tipos de vaga, gera variantes de CV por tipo e cria CV do zero quando nenhum encaixa.
- **C. Bot de candidatura semi-automático.** Abre uma aba por vaga com tudo preenchido. A pessoa clica em enviar ou fecha a aba.
- **D. v2 internacional.** Fora do v1.

A não depende de nenhum outro projeto. B e C dependem das saídas de A.

O produto é para **qualquer pessoa**, de qualquer profissão, distribuído como **repositório público**. O criador (Samuel, analista de dados que avalia migrar para AI Engineer) é o primeiro usuário e o caso de teste, mas nada no código ou nos dados dele pode ficar fixo.

## O que "missão cumprida" significa para A

Ao fim de A, a pessoa tem:

1. Um **perfil completo** em arquivos locais.
2. Um **foco recomendado**: qual cargo ou área perseguir, com justificativa baseada em dados de mercado e no perfil dela.
3. Um **CV base** (um único arquivo). As variantes por tipo de vaga pertencem a B.

Também recebe os textos prontos do perfil LinkedIn (headline, Sobre, experiências, competências) para colar, um checklist de visibilidade do perfil e sugestões de melhoria para o GitHub.

## Objetivos

- Questionário profundo, em conversa no Claude Code, em etapas e retomável. Cobre: nome, idade, estado, cidade, experiências de trabalho (empresas, cargos, datas, resultados), conhecimentos com nível (especialista, médio, iniciante), certificações, idiomas com nível, restrições (modalidade, cidades, setores e empresas vetadas, incluindo o empregador atual), banco de respostas de triagem e perfil comportamental no estilo de teste vocacional (especialista ou gestão, ritmo, motivadores).
- Análise de mercado com dados: para cada cargo candidato, ler cerca de 50 vagas e medir demanda, saturação, faixa salarial e skills pedidas. Cruzar com o perfil, recomendar o foco e listar lacunas de skill.
- Revisão do GitHub da pessoa, somente leitura, com sugestões (README, projetos fixados, um projeto rápido para cobrir lacuna).
- Geração dos textos de LinkedIn e do CV base a partir do perfil.
- Banco de respostas de triagem: pretensão salarial, anos de experiência por tecnologia, CLT ou PJ, disponibilidade, dados de contato. B e C usam esse banco para preencher formulários.

## Não objetivos

- Candidatar-se a vagas (é C).
- Variantes de CV por tipo de vaga (é B).
- Vagas internacionais (é D).
- Editar o LinkedIn ou o GitHub da pessoa. O bot só gera texto e sugestões.
- Questionário em Google Forms.
- Funcionar em outro idioma além de PT-BR.

## Anti-objetivos (seria falha mesmo que tecnicamente funcione)

- Dados pessoais saindo da máquina da pessoa (nuvem, repositório, serviço de terceiro).
- Misturar dados de duas pessoas.
- Inventar fatos verificáveis (ver "Honestidade").
- Copiar texto, templates ou exemplos do ebook de referência.

## Decisões já tomadas pelo dono (como ele decidiu)

- **Formato:** conversa no Claude Code, não formulário. Motivo: adapta perguntas, cobra prova, mantém dados locais.
- **Base:** instalar e usar o repo `sergebulaev/linkedin-skills` (skills `linkedin-profile-optimizer`, `linkedin-interviewer`, `linkedin-humanizer`). A instalação faz parte de A, depois da aprovação deste documento.
- **Conhecimento do ebook** (Guia Prático LinkedIn 10k, de Lucas Siqueira): o bot deve incorporar os princípios. Como o repo é público, os princípios são **reescritos em texto original**. Nada de copiar templates, exemplos ou frases. Ideias não têm direito autoral, o texto sim. Princípios a cobrir, em palavras próprias: o perfil precisa ser achável por busca de recrutador (palavra-chave no título, no Sobre, nas experiências e nas competências, nessa ordem de peso); configurações de visibilidade e de contato; conexões mútuas com recrutadores; atividade do perfil; preencher abas secundárias (projetos, certificados, idiomas, publicações, voluntariado, cursos); projetos pessoais valem como experiência; resultados mensuráveis no topo de cada experiência; candidatura em volume sozinha rende pouco.
- **Regra de estiramento (stretch)**, valor padrão do dono, configurável por pessoa:
  - Match de 90% ou mais entre as exigências da vaga e as skills da pessoa: o CV pode listar as skills que faltam como skill, sem ressalva.
  - Entre 50% e 90%: padrão proposto pelo bot (não confirmado pelo dono): mesmo estiramento, com cada item estirado marcado de forma visível na revisão.
  - Abaixo de 50%: a vaga é aberta e marcada como "arriscada", não descartada. A pessoa decide.
  - Rótulos de match mostrados na revisão (definidos pelo dono): menos de 50% "Arriscado"; 50% a 70% "Chance média"; 70% a 80% "Bom match"; 90% "Ótimo match"; 100% "Vaga perfeita". A faixa de 80% a 90% não foi definida pelo dono; decisão do bot (aprovada junto com o documento): "Ótimo match" a partir de 80%.
  - Essa regra é aplicada em B e C. Em A ela só é gravada no perfil, junto com os rótulos.
- **Dados:** arquivos Markdown/YAML locais, uma pasta por pessoa. O padrão de risco de conta é conservador (semi-automático, limite baixo). Isso é configurado em C, mas o aviso de risco aparece já em A.
- **Distribuição:** repositório público. Skill do Claude Code.

## Honestidade (linha que o bot não cruza)

O bot pode esticar **skills** (testadas em entrevista, aprendíveis). Ele **nunca inventa** itens verificáveis em checagem de referência: empregadores, cargos, datas, formação, certificações e números de resultado. Isso vale mesmo sob a regra de estiramento e mesmo se a pessoa pedir. Resultados numéricos só entram se a pessoa os informou.

## Restrições

- Skill do Claude Code; conversa em terminal.
- Dados 100% locais; nenhum envio a serviço externo, exceto a leitura pública de vagas na análise de mercado.
- Funcionar para qualquer profissão, não só tecnologia. Os exemplos do ebook são todos de desenvolvedores e não podem virar regra.
- Repo público: sem dados do dono, sem texto do ebook.
- Mercado e idioma: Brasil, PT-BR.
- Aviso obrigatório: automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa.

## Entregáveis de A

1. Skill de entrevista (etapas, retomável), gravando em `profile/` local.
2. Rotina de análise de mercado (cerca de 50 vagas por cargo candidato) e relatório de foco recomendado.
3. Revisão de GitHub somente leitura, via CLI `gh` ou leitura pública.
4. Gerador de textos de LinkedIn e do CV base a partir do perfil.
5. Checklist de visibilidade do perfil em texto original.
6. Esquema do `profile` (campos, incluindo banco de respostas de triagem e `stretch_policy`) estável o bastante para B e C lerem.

## Deixado para o construtor

- Estrutura exata das pastas e do esquema YAML.
- Fonte e método de coleta das vagas na análise de mercado, desde que funcione em um repo público sem conectores privados e respeite os termos do site.
- Formato do CV base e do relatório de foco.
- Teste vocacional e de estilo de trabalho: escolher um instrumento simples e documentar.
- Como o bot avalia "prova" por skill, dentro da regra de honestidade.
- Nome do repositório, licença e README.
