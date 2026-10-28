# Jobs Master BR v1 — Projeto C: Candidatura semi-automática (design)

Data: 2026-10-25. Idioma: PT-BR. Mercado: Brasil. Plataformas do v1: LinkedIn, Indeed e Gupy.

## Contexto e intenção

O A mapeia a pessoa, o B1 orienta a carreira e o B2 gera os currículos em PDF por tipo de vaga. O C fecha o ciclo: o bot **procura vagas sozinho**, prepara cada candidatura e deixa uma **aba aberta por vaga**, no último passo do formulário. A pessoa olha, clica em enviar ou fecha a aba. **O bot nunca envia.**

Problema que o C resolve: candidatar-se em volume consome tempo demais, principalmente achar vagas, adaptar o currículo e repetir os mesmos formulários e testes. Quanto menos trabalho manual, melhor: o dono pediu que a busca seja 100% do bot.

C depende de tudo que existe: perfil e banco de respostas de triagem (A), profissões aceitas (B1), tipos de vaga, `vaga-eval`, `vaga-resume`, PDF, folha de revisão e log `applications` (B2).

## O que "missão cumprida" significa para o C

1. A pessoa pede **"rodar vagas"**. Em uma rodada, para cada plataforma, o bot busca vagas dos tipos definidos, filtra, prepara até **10 candidaturas** e deixa **10 abas abertas**, cada uma no último passo do formulário, com o PDF certo anexado e as respostas preenchidas.
2. Cada aba tem a **folha de revisão** da vaga à mão (o que foi esticado, o que falta, abaixo do piso, perguntas sem resposta, avisos).
3. A pessoa envia ou fecha. O bot registra o resultado no log.
4. O limite é **10 por rodada e 30 por dia, em cada plataforma**, configurável.
5. No fim da rodada, o bot junta as **perguntas novas** que não soube responder, pergunta uma vez e guarda as respostas no banco para a próxima.

## Objetivos

- **Busca sozinha, por tipo de vaga e por plataforma**, usando o cargo, a modalidade e o contrato dos tipos definidos no B2.
  - **Indeed:** usa a integração do Claude com o Indeed (`search_jobs`, `get_job_details`, `get_company_data`) quando existir na conta da pessoa; se não existir, cai para o navegador. A integração não envia candidatura; só dá o link.
  - **LinkedIn e Gupy:** pelo navegador, no Chrome real em que a pessoa já está logada.
- **Filtro antes de preparar:** descarta vaga já vista ou já registrada, vaga do empregador atual, de empresa ou setor vetado, e vaga fora das restrições de modalidade e contrato. Vaga abaixo do piso ou "arriscada" **segue marcada**, não é descartada (regra do B2). O bot usa `vaga-eval` e `vaga-resume` do B2; o currículo é o do tipo ajustado para a vaga, ou do zero para vaga boa sem tipo.
- **Preenchimento do formulário:** anexa o PDF, preenche com o banco de respostas de triagem (salário, contrato, disponibilidade, contato, anos por skill, respostas guardadas) e para no último passo.
- **Pergunta sem resposta no banco:** o bot deixa o campo em branco e destacado, anota na folha de revisão e, no fim da rodada, junta as perguntas novas, pergunta uma vez e grava as respostas no banco (nova estrutura de banco de respostas por pergunta).
- **Testes de fit cultural:** o bot tenta responder todos, com rascunho baseado no perfil comportamental real da pessoa (testes do A e do B1) e nunca no "candidato ideal". Modos configuráveis `auto`, `perguntar` e `pular`; **padrão `auto`** (decisão do dono). Quando os termos ou o teste disserem que proíbem ajuda de IA, que é cronometrado ou que é de uma tentativa só, o bot marca isso na folha de revisão. Teste vigiado por câmera ao vivo o bot não faz: deixa a aba aberta para a pessoa.
- **Freios:** captcha, pedido de verificação, aviso de atividade incomum ou parede de login fazem o bot **parar aquela plataforma** na hora, avisar a pessoa e não tentar contornar. Ritmo lento e irregular, uma aba por vez, nunca em paralelo.
- **Registro e status** no log `applications` do B2: `preparado`, `enviada`, `descartada` (aba fechada sem envio), `bloqueada` (parou por freio). Contadores por plataforma e por dia. O bot verifica o estado das abas no início da rodada seguinte e quando a pessoa pedir o status.
- **Início da rodada:** só quando a pessoa pede (comando em linguagem natural, "rodar vagas"). Rodada programada em horário fica para uma versão futura.

## Não objetivos

- **Enviar candidatura**, em qualquer hipótese.
- Rodada agendada em horário fixo (versão futura).
- Vagas internacionais (D) e outras plataformas além de LinkedIn, Indeed e Gupy.
- Resolver captcha, criar contas, editar o perfil da pessoa nas plataformas, convidar contatos ou fazer networking automatizado.
- Guardar ou pedir senha: a pessoa faz o login sozinha no Chrome.

## Anti-objetivos (seria falha mesmo que tecnicamente funcione)

- Enviar qualquer candidatura sem o clique da pessoa.
- Contornar captcha, verificação ou bloqueio; trocar de IP ou impressão digital do navegador; abrir várias sessões em paralelo.
- Responder campo com algo que não vem do perfil ou do banco de respostas (resposta inventada). Na dúvida, em branco e destacado.
- Inventar empregador, cargo, data, formação, certificação ou número (regra do A e do B2 continua valendo no currículo e nos formulários).
- Candidatar-se a vaga do empregador atual, de empresa vetada ou já enviada antes.
- Perder o controle do ritmo: passar do limite de 10 por rodada ou 30 por dia por plataforma.
- Dados pessoais saírem da máquina além do que cada formulário exige.

## Decisões já tomadas pelo dono

- **Semi-automático**, com aba aberta por vaga ("como um Tinder"): a pessoa envia ou fecha; o bot nunca envia.
- **O bot busca as vagas sozinho**; quanto menos trabalho manual, melhor.
- Limites de **10 abas por rodada e 30 por dia, em cada plataforma**.
- **Perguntas sem resposta:** campo em branco e destacado, nota na folha de revisão, e uma pergunta única no fim da rodada para guardar no banco.
- **Testes de fit cultural:** o bot tenta todos; se bloquear, paciência. Padrão `auto`. O dono está ciente de que teste cronometrado pode perder a tentativa e de que ser pego usando IA onde é proibido pode desclassificar.
- **A rodada começa quando a pessoa pede.**
- A integração do Claude com o Indeed deve ser usada quando existir.

## Decisões do bot (aprovação junto com este documento)

- O bot marca na folha de revisão os testes que proíbem IA, são cronometrados ou têm uma única tentativa; o clique de envio continua sendo da pessoa.
- Aba fechada sem envio vira `descartada` e a vaga não volta.
- O contador diário e o histórico ficam no perfil local, com permissão restrita.
- Em qualquer freio (captcha, verificação, aviso), a plataforma fica pausada até a pessoa liberar; o bot não tenta de novo sozinho no mesmo dia.
- Configurações da rodada (limites por plataforma e modo de fit) ficam no perfil, com os padrões acima.
- O conector do Indeed é caminho opcional: sem ele, o Indeed usa o navegador como as outras plataformas. Com ou sem o conector, o formulário de candidatura do Indeed é aberto e preenchido no navegador, como nas outras plataformas.
- **Fit com risco:** o bot responde o rascunho mesmo assim (decisão do dono); o aviso (proíbe IA, cronometrado, uma tentativa) vai para a folha de revisão e para o resumo da rodada. O envio continua sendo o clique da pessoa.
- **O que conta nos limites:** só aba preparada com sucesso conta nos 10 por rodada e nos 30 por dia. Vaga que falha no meio, é bloqueada ou é filtrada não conta. Para a rodada não varrer sem fim, o bot examina no máximo 50 vagas por plataforma em cada rodada. O bot não começa uma rodada numa plataforma que já tenha 10 ou mais abas `preparado` sem resposta; ele pede que a pessoa revise essas antes.
- **Candidatura em site externo da empresa:** na v1 o bot abre a página externa numa aba, sem preencher, marca `externa` na folha de revisão com o caminho do PDF, e conta a vaga como preparada.
- **Memória de vagas:** além das candidaturas, o perfil guarda as vagas já vistas, inclusive filtradas e com falha, com o motivo. A chave de repetição é o endereço normalizado (sem parâmetros); se vier de outra plataforma, também se compara empresa mais título normalizado.
- **Status:** `preparado`, `enviada`, `descartada`, `bloqueada`, `externa` e `desconhecido` (quando a aba some e não há confirmação de envio). Mudar status é uma operação de atualização, não de acréscimo.
- **Pausa de plataforma:** persiste até a pessoa liberar, por pedido em linguagem natural (que roda um comando de liberar). O contador diário zera no dia seguinte; a pausa não.
- **Campos sensíveis e consentimentos** (PCD, gênero, raça, autorização de trabalho, termos legais): ficam em branco ou desmarcados e destacados, a menos que a pessoa tenha uma resposta guardada no banco para a pergunta. Eles entram na pergunta única do fim da rodada, e a pessoa pode marcar "sempre responder X".
- **Perfil e conta:** uma rodada roda para um perfil, informado pela pessoa. No início, o bot lê o nome da conta logada na plataforma e, se não bater com o nome do perfil, para e avisa.

## Restrições

- Skills do Claude Code mais CLI Python para a lógica determinística (limites, contadores, filtros, deduplicação, banco de respostas, avisos), como nos projetos anteriores. A automação do navegador roda pelas ferramentas de navegador do Claude.
- PT-BR e Brasil. Dados 100% locais, com permissão restrita.
- Aviso obrigatório (já no A): automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas; o risco para a conta é de cada pessoa.
- Repositório público: nenhum dado de pessoa real.
- Sites mudam: o código de cada plataforma precisa falhar de forma clara e parar, nunca preencher às cegas.

## Entregáveis do C

1. Esquema de configuração da rodada, contadores por plataforma e por dia, e banco de respostas por pergunta, no perfil.
2. Lógica de limites, filtros, deduplicação, vaga já vista e vaga do empregador atual ou vetada.
3. Lógica do banco de respostas: casar uma pergunta do formulário com a resposta guardada, e marcar o que ficou sem resposta.
4. Rascunho de respostas de fit com base no perfil comportamental, com as marcações de risco.
5. Skills do Claude Code que conduzem a rodada em cada plataforma (busca, preparo, abas, freios) e a skill de status.
6. Comandos da CLI para contadores, filtros, banco de respostas e registro.
7. Documentação dos riscos e dos freios.

## Deixado para o construtor

- Qual ferramenta de navegador usar (a extensão do Claude para o Chrome, Playwright ou outra) e como tratar cada site.
- Como montar as buscas a partir dos tipos, e a ordem de prioridade das vagas.
- Como detectar captcha, verificação e avisos, e o ritmo exato das pausas.
- Como casar perguntas de formulário com o banco de respostas (regras, semelhança de texto, apoio do modelo).
- Como verificar o estado das abas e inferir `enviada` ou `descartada`.
- Estrutura exata dos dados novos e dos comandos.
- Como testar o que depende de sites reais: dados determinísticos com testes automáticos, e fluxos de navegador com páginas salvas ou verificação manual documentada.
