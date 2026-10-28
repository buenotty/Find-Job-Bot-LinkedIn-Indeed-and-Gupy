# Jobs Master BR v1 — Projeto B2: Tipos de vaga e currículos (design)

Data: 2026-10-25. Idioma: PT-BR. Mercado: Brasil.

## Contexto e intenção

O A mapeia a pessoa e gera um CV base. O B1 recomenda profissões e grava as aceitas em `targets`. O B2 transforma cada profissão aceita em um **tipo de vaga** com regras próprias e gera os **currículos em PDF**: um modelo por tipo, um ajuste leve por vaga e um currículo do zero para vaga boa que não encaixa em nenhum tipo. O C usa o que o B2 produz para abrir as candidaturas.

Problema que o B2 resolve: candidatar-se em volume exige currículo adaptado a cada tipo e a cada vaga, e hoje isso consome tempo demais. Os sistemas de triagem automática leem o currículo antes de uma pessoa, então o texto precisa ser fácil de ler para uma máquina, verdadeiro e orientado a resultado.

## O que "missão cumprida" significa para o B2

1. Cada profissão aceita e liberada tem um **tipo de vaga** (piso de salário, modalidade, contrato).
2. Cada tipo tem um **currículo-modelo em PDF**.
3. Dada uma vaga, o bot classifica a vaga num tipo (ou em "sem tipo"), calcula o match e gera o **PDF daquela vaga**: modelo do tipo com resumo novo e skills reordenadas.
4. Vaga boa sem tipo recebe um **currículo do zero**.
5. Cada currículo gerado vira um **registro** (vaga, tipo, match, arquivo), e o que foi esticado aparece numa **folha de revisão** para a pessoa.

## Objetivos

- **Tipo de vaga** = profissão aceita de `targets` com `cv_released` verdadeiro (regra do B1) mais regras: piso de salário, modalidades e contrato. Os padrões vêm do perfil (`screening.salary_expectation`, `constraints.modality`, `screening.contract`) e a pessoa pode sobrescrever por tipo. Exemplo do dono: Analista de Dados com IA (híbrido, CLT, acima de 5 mil) e hardware (piso próprio, mais baixo).
- **Currículo-modelo por tipo**, em português do Brasil:
  - resumo, experiências, projetos e skills reescritos para o tipo, usando só fatos do perfil (reenquadrar ênfase, ordem e vocabulário; nunca inventar);
  - bullets no padrão XYZ ("realizei X, medido por Y, fazendo Z"); o Y só existe se for número que a pessoa informou (`metric`); sem número, o bullet sai sem número;
  - quem não tem experiência formal numa área (por exemplo, hardware como hobby e projetos desde 2022, trabalho voluntário na igreja) usa projetos e voluntariado como experiência, descritos como autodidata, sem fingir cargo.
- **Formato para triagem automática:** PDF com texto selecionável, coluna única, títulos de seção padrão (Resumo, Experiência, Projetos, Competências, Formação ou Certificações, Idiomas), sem tabelas, imagens, ícones, foto nem texto escondido.
- **Ajuste por vaga:** o modelo do tipo, mais um resumo novo de até 4 linhas e as skills reordenadas para as keywords da vaga que a pessoa tem (ou que a regra de estiramento permite) ficarem no topo. Experiências e números não mudam.
- **Classificação da vaga:** a vaga entra em um tipo pelo cargo e pelas skills pedidas; se dois tipos empatam, o bot pergunta à pessoa; se nenhum serve, é "sem tipo".
- **Estiramento:** aplica a regra do A (match de 90% ou mais estica sem ressalva; entre 50% e 90% estica com marcação; abaixo de 50% a vaga fica marcada como "arriscada", nunca descartada). A marcação aparece na **folha de revisão**, não no PDF.
- **Vaga boa sem tipo:** é boa quando o match com o perfil é de 70% ou mais, a modalidade e o contrato estão dentro das restrições da pessoa e o salário é igual ou maior que o menor piso entre os tipos (salário não informado passa, com aviso). Nesse caso gera-se um currículo do zero, pelo mesmo motor, usando as keywords da vaga em vez de um tipo.
- **Registro** de cada currículo gerado, para o C consultar.

## Não objetivos

- Enviar candidaturas (C) e achar as vagas (C). O B2 recebe a vaga como entrada.
- Responder testes de fit cultural (C).
- DOCX, foto, currículo em outro idioma, ou layout gráfico elaborado.
- Texto escondido ou truque de keyword para enganar sistemas de triagem.
- Editar qualquer coisa fora da máquina da pessoa.

## Anti-objetivos (seria falha mesmo que tecnicamente funcione)

- Inventar empregador, cargo, data, formação, certificação ou número de resultado.
- Texto invisível, keyword que a pessoa não tem apresentada como experiência, ou prompt escondido para "convencer" uma IA.
- PDF em que o texto não possa ser extraído.
- Descartar sozinho uma vaga que a pessoa poderia querer (abaixo do piso ou "arriscada" é marcada, não removida).
- Dados sensíveis (contato, histórico) saírem da máquina.

## Decisões já tomadas pelo dono

- Tipos de vaga vêm das profissões aceitas, com piso, modalidade e contrato por tipo.
- Currículo-modelo por tipo mais ajuste leve por vaga (resumo e ordem de keywords); currículo do zero só para vaga boa sem tipo.
- Formato PDF.
- Critério de "vaga boa": match de 70% ou mais, restrições respeitadas, salário igual ou acima do menor piso.
- Padrão XYZ e currículo objetivo, pensado para triagem automática.
- Em hardware, o currículo se apoia em projetos e voluntariado, como autodidata.

## Decisões do bot (aprovação junto com este documento)

- Vaga abaixo do piso do tipo é marcada "abaixo do piso" e segue para revisão; não é descartada.
- Salário não informado na vaga passa no critério, com aviso.
- Empate entre tipos: o bot pergunta; ele não escolhe sozinho.
- Texto escondido nunca é gerado, mesmo se a pessoa pedir.
- **Vaga "arriscada" (match abaixo de 50%) também recebe PDF, sem estiramento.** O currículo lista só as skills que a pessoa já tem; a folha de revisão mostra as skills que faltam. A regra de estiramento do A só vale a partir de 50%.
- **Voluntariado e trabalho autodidata ficam em `projects`, não em `experiences`.** `experiences` continua sendo emprego formal, com empresa e cargo reais. B2 acrescenta ao `Project` um campo opcional `kind` (`projeto`, `voluntariado`, `autodidata`, `freela`; padrão `projeto`), compatível com os perfis do A e do B1. O PDF mostra esses itens sob "Projetos e voluntariado", com o tipo escrito (por exemplo "Voluntariado" ou "Autodidata desde 2022"), nunca com cargo inventado.
- **Datas de projeto:** `Project` ganha também `start` e `end` opcionais (`AAAA` ou `AAAA-MM`), para "desde 2022" ser verdadeiro. A checagem de números aceita os anos desses campos. Anos de prática só valem se estiverem em `years_by_skill`.
- **Extração de skills da vaga:** a skill do Claude Code lê a vaga e entrega à CLI campos estruturados (título, skills, salário, modalidade, contrato, link). A CLI não interpreta texto livre de vaga; os testes usam fixtures.
- **Garantia de honestidade:** empregador, cargo, datas, formação e certificações são renderizados só a partir de campos do perfil. O modelo escreve apenas o resumo e a redação dos bullets, e a checagem de números do A vale para esses textos. Um teste confere que todo empregador, cargo e certificação do PDF existe no perfil.
- **Skill estendida aparece só em Competências**, sem nível e sem alegação de experiência, nunca em bullets nem no resumo.
- **`cv_released` é calculado**, não guardado: usa a regra do B1 (`agora`, ou `nova_formacao` com match recalculado no corte `stretch_from`).
- **Empate entre tipos** volta como resultado "ambíguo", e a pessoa escolhe por um parâmetro da CLI. Tipo sem piso não tem verificação de piso.
- O registro de currículos fica no perfil local (`applications`), com permissão restrita como o resto.
- A folha de revisão é um arquivo de texto ao lado do PDF.

## Restrições

- Skills do Claude Code mais CLI Python, como no A e no B1. Reaproveita `schema`, `store`, `match`, `honesty`, `cv`, `orientation`.
- Honestidade do A: números do currículo só se vierem do perfil; a checagem de números vale para resumo e bullets.
- Dados 100% locais; arquivos do perfil e PDFs com permissão restrita.
- PT-BR e Brasil.
- A geração de PDF pode exigir uma biblioteca; ela deve funcionar offline, em Python 3.10 ou mais novo, e o texto do PDF deve ser extraível (verificado em teste).
- Repositório público: sem dados de pessoa real.

## Entregáveis do B2

1. Esquema do tipo de vaga e do registro de currículos no perfil.
2. Motor de currículo: modelo por tipo, ajuste por vaga e currículo do zero, com a checagem de honestidade.
3. Geração do PDF e verificação de que o texto é extraível.
4. Classificador de vaga em tipo e cálculo do critério de "vaga boa".
5. Folha de revisão com o que foi esticado e o que ficou abaixo do piso ou "arriscado".
6. Skills do Claude Code para definir tipos, gerar os modelos e gerar o currículo de uma vaga, e os comandos da CLI.

## Deixado para o construtor

- Biblioteca e layout do PDF, fontes e espaçamento.
- Formato do modelo e do registro (campos exatos).
- Como a vaga entra (texto colado, campos estruturados) e como se classifica (regras, apoio do modelo, ou os dois).
- Heurística de reescrita para XYZ e de reordenação de skills.
- Nomes dos comandos e estrutura dos arquivos.
