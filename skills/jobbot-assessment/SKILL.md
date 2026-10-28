---
name: jobbot-assessment
description: Use depois da entrevista (jobbot-interview), antes da análise de mercado, para aplicar o teste de perfil (valores de trabalho, interesses, personalidade, âncoras de carreira, estilo de trabalho e perguntas abertas) e devolver percentuais por dimensão, em linguagem direta. É um arquivo de texto que a pessoa preenche de uma vez, em 20 a 30 minutos, e que pode ser pausado e retomado. Gatilhos - "teste vocacional", "qual minha área", "me conhecer melhor", "refazer o teste".
---

# JobBot: teste de perfil

O teste é **um arquivo de texto**: cada afirmação vem numa linha, e a pessoa escreve um número de 1 a 5 depois do sinal `=`. Seja breve: poucas mensagens, curtas, em português do Brasil.

## Antes de começar

1. `python3 -m jobbot status <nome>` deve responder `completo` e `python3 -m jobbot validate <nome>` deve responder `ok`. Se não, volte à skill `jobbot-interview`.
2. Rode `python3 -m jobbot form-new <nome> teste`. O arquivo é criado na pasta **Downloads** da pessoa. Mande **uma única mensagem** com o caminho e este resumo: 83 afirmações mais 3 perguntas abertas, cerca de 10 minutos; escreva o número depois do `=`, sem pensar na resposta certa; pode parar e voltar depois, o que ficar em branco continua pendente; os resultados ficam só neste computador.

## Aplicação

1. Quando a pessoa disser pronto, rode `python3 -m jobbot form-load <nome>`, sem caminho: ele acha o arquivo mais recente dela na pasta Downloads. Com o teste completo (ou com erro nenhum e o seguimento aplicado), o comando recolhe o arquivo para a pasta interna do perfil (`recolhido:`); com o teste pela metade, o arquivo fica em Downloads para a pessoa continuar. Se houver erros (número fora de 1 a 5, item desconhecido), o comando lista cada um com o número da linha e não salva nada: mostre a lista e peça para corrigir o mesmo arquivo.
2. A saída mostra `respondidas: N/M`. Se faltar item, diga quantos faltam e deixe a pessoa continuar o mesmo arquivo quando quiser (rodar `form-load` de novo soma ao que já foi salvo). Se a pessoa preferir responder no chat, grave num YAML `id: valor` e use `python3 -m jobbot assess-answer <nome> <arquivo.yaml>`; use `python3 -m jobbot assess-status <nome>` para ver onde parou. Nunca preencha, sugira ou complete uma resposta pela pessoa.
3. Quando a saída trouxer `proximo: assess-finish`, rode `python3 -m jobbot assess-finish <nome> --situations <pasta do perfil>/situations.yaml` (a pasta vem de `python3 -m jobbot path <nome>`; o arquivo existe se a pessoa respondeu as perguntas abertas).

## Como apresentar o resultado

- Monte o retrato em cinco blocos: **interesses** (com o `codigo_holland` da saída, por exemplo "IRC: investigativo, prático, convencional"), **personalidade** (cinco traços), **valores de trabalho** (os 3 mais altos e os 2 mais baixos) e **âncoras de carreira** (as 2 mais altas, e o que a `trilha` da saída significa: `especialista` = quer se aprofundar, `gestao` = quer liderar, `hibrido` = as duas são altas, perfil de liderança técnica, `indefinido` = as duas estão próximas e o estilo de liderança não desempatou; nesse caso pergunte à pessoa qual ela prefere e deixe a decisão com ela). A `trilha` já é gravada no perfil, exceto quando `indefinido`.
- O bloco **estilo de trabalho** traz oito competências (liderança, comunicação, planejamento, resolução de problemas, adaptabilidade, desempenho sob pressão, aprendizado e foco em resultado), como a pessoa se vê, não como um avaliador a vê. Mostre as 3 mais altas e as 2 mais baixas e diga o que cada uma pesa em vagas reais.
- Cruze os blocos em linguagem direta e só com o que os números mostram (por exemplo, "autonomia alta com estabilidade baixa combina com freela ou PJ"). Nada de diagnóstico.
- Mostre as dimensões em ordem, com os percentuais, em linguagem direta ("interesse investigativo 90%, prático 80%, social 40%").
- Diga sempre: a pontuação é relativa ao máximo possível em cada dimensão, não é ranking contra outras pessoas e não é diagnóstico.
- Se `confiabilidade: baixa`, diga com franqueza o motivo (`respostas_uniformes` ou `pares_incoerentes`) e que isso é um sinal, não uma acusação. O resultado fica salvo, mas marcado. Ofereça refazer o teste inteiro, com calma; não dá para refazer uma camada isolada.
- Compare com o histórico do perfil e aponte contradições com respeito, por exemplo "você diz gostar de lidar com pessoas, mas as respostas apontam o contrário". Pergunte qual lado é verdade, sem decidir por ela.
- Refazer o teste adiciona um novo resultado datado; os anteriores ficam no histórico, e o mais recente vale.

Depois, siga para a skill `jobbot-market`: ela usa este resultado para propor os cargos.

## Relatório para guardar

No fim desta etapa, escreva um mini relatório em Markdown, em português, para a pessoa guardar (o que foi dito só no chat se perde): a leitura do resultado: código de Holland, personalidade, valores, âncoras, estilo de trabalho e trilha, cada um em linguagem direta, com o que isso pesa na escolha de cargo, os limites do teste e a data. Grave num arquivo temporário (nunca em Downloads) e rode `python3 -m jobbot report-save <nome> 02-teste-de-perfil <arquivo.md>`. A saída `relatorio:` mostra o caminho na pasta `Documents/JobBot/<nome>`; diga esse caminho à pessoa. Use só fatos do perfil e do que foi lido; o relatório não traz senha nem dado que a pessoa disse ser confidencial.
