# Fluxo do robô (versão vigente)

Cada etapa só começa depois que a anterior está pronta e aprovada pela pessoa. O bot é autônomo por padrão (finaliza candidaturas); no modo assistido, para antes de enviar.

1. **Entrevista** (`jobbot-interview`). Pede no começo LinkedIn, GitHub, outros links e o currículo mais atual. Lê o que é público,
   pré-preenche o questionário e confirma as dúvidas numa mensagem só.
2. **Teste de perfil, opcional** (`jobbot-assessment`). Não bloqueia o fluxo; só para quem está indeciso ou quer mudar de área. 83 afirmações e 3 perguntas abertas, cerca de 10 minutos. Dá código de Holland,
   personalidade, valores, âncoras, estilo de trabalho e trilha.
3. **Cargos** (`jobbot-market`). Lista de 5 a 8 cargos com o motivo de cada. **Parada: a pessoa aprova.** Só então lê vagas dos
   cargos aprovados (palavras-chave, salário, concorrência), escreve o `focus-report.md` e registra os cargos aprovados.
4. **Perfis** (`jobbot-profiles`). Para LinkedIn, GitHub e outras plataformas: o que melhorar, texto pronto e ajuda guiada.
   A etapa só termina quando **todas as plataformas estão prontas e revisadas** (`perfis-revisados.md`).
5. **Currículos** (`jobbot-types`). **Um currículo-modelo para cada tipo de emprego** que a pessoa vai disputar, com a
   aprovação dela em cada PDF.
6. **Vagas** (`jobbot-round`). Só agora o bot busca vagas, gera o currículo de cada uma e deixa a aba aberta no último passo.

**Relatórios.** Cada etapa termina com um mini relatório em Markdown que a pessoa guarda em `Documents/JobBot/<nome>/` (`jobbot report-save`): `01-perfil`, `02-teste-de-perfil`, `03-cargos-e-mercado`, `04-perfis`, `05-curriculos` e `06-rodada-AAAA-MM-DD`. O que só foi dito no chat se perderia.

Fora da linha principal, sob pedido: `jobbot-orientation` e `jobbot-courses` (mudança de área, custo, trilha de cursos),
`jobbot-resume` (currículo de uma vaga), `jobbot-status` e `jobbot-posts` (planejar e escrever posts de LinkedIn, sem denunciar busca de vaga e sem publicar sem o OK da pessoa).
