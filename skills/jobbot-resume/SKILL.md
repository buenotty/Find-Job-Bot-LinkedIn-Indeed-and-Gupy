---
name: jobbot-resume
description: Use quando a pessoa tiver uma vaga (texto colado ou link) e quiser o currículo em PDF para ela. Classifica a vaga num tipo, calcula o match, ajusta o resumo e a ordem das skills do modelo do tipo (ou cria um currículo do zero para vaga boa sem tipo) e gera a folha de revisão com o que foi esticado. Nada é enviado. Gatilhos - "currículo para esta vaga", "adaptar currículo", "gerar PDF da vaga".
---

# JobBot: currículo para uma vaga

Nada é enviado a lugar nenhum. Esta skill só gera o PDF e a folha de revisão, e a pessoa decide o que fazer.

## Nome do arquivo

O PDF e a folha de revisão se chamam `curriculo-<nome>-<código>`. O código tem 5 caracteres e é estável por vaga. O nome **nunca** traz empresa ou cargo. Regenerar a mesma vaga reescreve o mesmo arquivo. As skills aprendíveis que a vaga pede e a pessoa não tem podem constar em Competências (a opção `stretch_policy.stretch` do perfil liga e desliga isso; se a pessoa não quiser, use `false`). Nunca escreva em currículo, mensagem ou resposta que ela "não sabe mas está estudando": ou a skill consta na lista, ou não se fala dela.

## Pré-requisitos

- Perfil válido, pelo menos um tipo definido e seu modelo gerado (skill `jobbot-types`), a menos que a vaga seja do tipo "do zero".
- Leia `references/resume-writing.md`.

## Passos

1. **Extrair a vaga.** Leia o texto ou a página pública da vaga e grave um YAML `posting.yaml` com `title`, `company`, `skills`, `salary`, `modality`, `contract` e `url`.
   - `skills`: só conhecimentos e ferramentas técnicas, em lista curta e padronizada. Não inclua soft skills.
   - `salary`: inteiro em reais por mês, apenas se a vaga informar. Sem `salary`, busque o salário médio do cargo na empresa (ou na cidade) em página pública de salário e grave `salary_estimate` (inteiro) e `salary_source` (fonte, cargo e data). O número aparece na folha de revisão como "estimado", nunca no currículo. Sem fonte, deixe os dois campos de fora. `modality`: `remoto`, `hibrido` ou `presencial`. `level`: `estagio`, `junior`, `pleno` ou `senior` (pelo título e pelos anos exigidos; 5 anos ou mais ou "Sr" é `senior`). `city`: a cidade do trabalho. `commute_minutes` e `address`: só para vaga híbrida ou presencial, medidos no Google Maps de `home_area` até a vaga (transporte público, só ida), se o perfil tem `max_commute_minutes`. `contract`: `CLT` ou `PJ`.
   - Nunca invente o que a vaga não diz: omita o campo.
2. **Avaliar.** Rode `jobbot vaga-eval <nome> posting.yaml` e mostre à pessoa: a classificação, o tipo, o match e o rótulo, as skills que faltam, as que seriam esticadas, se está abaixo do piso e se respeita as restrições. Se der `ambiguo`, pergunte qual tipo usar e passe `--type "<profissão>"` nos próximos comandos.
3. **Escrever o ajuste.** Num `content.yaml`, escreva um `summary` novo de até 4 linhas (480 caracteres) com as palavras-chave da vaga que a pessoa tem, e um `skill_order` com essas palavras-chave na ordem de destaque. Experiências e números continuam os do modelo. Nunca invente empregador, cargo, data, formação, certificação nem número. Não cite no resumo as skills esticadas: elas só aparecem em Competências.
4. **Vaga sem tipo.** Se `classificacao` for `sem_tipo` e `vaga_boa_sem_tipo` for `sim`, o currículo é feito do zero: o `content.yaml` precisa ter o conteúdo completo (`summary`, bullets por empresa e por projeto do perfil, `skill_order`). Se `vaga_boa_sem_tipo` for `nao`, diga à pessoa por quê e não gere currículo.
5. **Gerar.** Rode `jobbot vaga-resume <nome> posting.yaml --content-file content.yaml` (e `--type` se houver). A vaga arriscada (match abaixo do corte) também gera PDF, mas sem nenhuma skill esticada.
6. **Entregar e pedir aprovação.** Mostre os caminhos de `pdf:` e `revisao:`, peça que a pessoa abra o PDF e aprove antes de usar, e resuma a folha de revisão: o que foi esticado (pode ser perguntado na entrevista), o que falta e se a vaga está abaixo do piso. Lembre que a vaga abaixo do piso ou arriscada foi mantida e que a decisão é da pessoa.

Limite honesto: o texto livre do resumo e dos bullets é escrito por você. A CLI checa números, skills que a pessoa não tem, e se as chaves dos bullets são empresas e projetos do perfil, mas não consegue confirmar que o texto livre não cita outro empregador, uma certificação ou uma formação. Por isso a aprovação da pessoa é obrigatória.

Se um comando recusar o conteúdo, explique o motivo e corrija o texto. Nunca contorne a recusa.
