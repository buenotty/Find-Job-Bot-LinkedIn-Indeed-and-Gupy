# Melhorias vindas do primeiro uso real (piloto)

A primeira pessoa a usar o robô de ponta a ponta (outubro de 2026) mostrou onde o fluxo não fazia sentido. Cada item abaixo é uma mudança já feita, com o problema que a causou. Os commits estão no histórico do repositório.

## Entrevista
| Problema visto | Mudança |
|---|---|
| O questionário era rígido: ninguém preenche exatamente como o modelo pede (estado e cidade trocados, "avançado" no lugar de "especialista", datas por extenso) e o robô devolvia uma lista de erros | O modelo virou um guia com formato e exemplo em cada campo. A skill agora lê o arquivo como veio, carrega uma cópia corrigida e faz **uma** mensagem de dúvidas. O parser aceita `out 2022`, `atual` e `-` ou `?` como vazio |
| A pessoa tinha LinkedIn, GitHub e currículo prontos e mesmo assim digitava tudo | A entrevista **pede os links e o currículo mais atual no começo**, lê o que é público e pré-preenche o questionário |
| As fontes mostravam divergências (cargo, datas, projeto que era fork) que a pessoa não tinha lembrado | As divergências viram dúvidas, e as fontes viram uma lista de "o que melhorar nos seus perfis" |
| Skills com nome composto ("Git e GitHub") não eram reconhecidas pelo cálculo de match | Skills atômicas, uma por linha |

## Teste de perfil
| Problema visto | Mudança |
|---|---|
| O teste anterior era curto e a trilha de carreira ficava `indefinido` com 4 respostas A e 4 B | Camadas novas: âncoras de carreira e estilo de trabalho. A trilha vem de técnica contra gestão, aceita `hibrido` e usa o estilo de liderança para desempatar |
| Uma versão intermediária ficou longa demais (220 itens, 30 a 40 minutos) | Versão final: **83 afirmações e 3 perguntas abertas, cerca de 10 minutos**, mantendo itens invertidos e pares de checagem |
| Faltava devolutiva | Código de Holland (RIASEC) e leitura por bloco |

## Fluxo
| Problema visto | Mudança |
|---|---|
| O mercado lia 50 vagas por cargo sem a pessoa aprovar nem os cargos, e sem pesquisar sobre ela | `jobbot-market` em duas fases com **parada obrigatória**: diagnóstico e cargos para aprovar, e só depois a leitura de vagas |
| Textos do LinkedIn e currículo eram escritos antes de a carreira estar escolhida | Nova ordem: entrevista, teste, cargos, **perfis revisados em todas as plataformas**, **um currículo por tipo de emprego**, e só então a busca de vagas |
| Orientação de carreira e trilha de cursos travavam o caminho principal | Viraram etapas opcionais, sob pedido |
| O que era dito no chat se perdia | **Cada etapa termina com um relatório em Markdown** guardado em `Documents/JobBot/<nome>/` (`report-save`) |

## Perfis e plataformas
| Problema visto | Mudança |
|---|---|
| O robô só sugeria texto e a pessoa tinha de aplicar tudo | Com autorização, o robô aplica no LinkedIn (um campo por vez), no GitHub e na Gupy, e **confere depois de salvar** |
| O empregador atual podia ver o perfil, e o texto dizia "aberto a oportunidades" | A skill **pergunta sobre discrição** antes de escrever: nada de "buscando vagas", sem selo Open to work, sem notificar a rede, sem cargo novo |
| Tom agressivo sobre o trabalho atual | Tom factual e humilde, como se a chefia fosse ler, com crédito à equipe |
| Risco de publicar algo confidencial | A skill pergunta o que é confidencial, nunca sugere publicar código ou dado do empregador ou cliente e renomeia projeto confidencial que pode identificar a empresa |
| Projeto de portfólio sem nada que se possa mostrar | Demonstração pública com dados sintéticos do mesmo padrão do trabalho confidencial |

## Vagas e currículos
| Problema visto | Mudança |
|---|---|
| A maioria das vagas não informa salário | Campo `salary_estimate` com fonte e data, vindo de página pública de salário, sempre marcado como estimado |
| Vaga presencial só valia acima de um salário | `onsite_min_salary`, usado junto com a estimativa |
| Vaga sênior aparecia para quem só quer júnior ou pleno | `seniority` no perfil e `level` na vaga |
| A lista de cidades era só informativa | Cidade aplicada ao filtro, e **tempo de deslocamento medido no Google Maps** (ônibus e metrô, com margem para o pico) substitui a lista para vaga híbrida ou presencial |
| O currículo mostrava um emprego que a pessoa não queria destacar | `experience_bullets` também escolhe os empregos |
| Projeto sem relação com o tipo aparecia, e o mesmo projeto aparecia duas vezes | `show_projects: false` e revisão do conteúdo por tipo |
| O PDF era simples demais | Novo visual (cor de destaque, fios, datas à direita, competências agrupadas, links) sem abrir mão de coluna única e texto em ordem de leitura |

## Candidaturas
| Problema visto | Mudança |
|---|---|
| O nome do arquivo do currículo trazia a empresa e o cargo, o que deixa claro que ele foi feito para aquela vaga | O arquivo agora é `curriculo-<nome>-<código>.pdf`, com um código de 5 caracteres estável por vaga. A relação código e vaga fica só num índice da pessoa |
| Gerar de novo o currículo da mesma vaga criava um segundo arquivo e um segundo registro | A mesma vaga reescreve o mesmo arquivo e substitui o registro |
| O currículo da vaga lista, só em Competências, o que a vaga pede e a pessoa não tem ("esticar") | A pessoa decidiu **manter**, desde que seja algo aprendível: não aparece em resumo nem em bullet, e a folha de revisão lista cada uma. Existe a opção `stretch_policy.stretch`; com `false` o currículo da vaga nunca lista skill que a pessoa não tem. No piloto ficou **ligada** |
| A mensagem para a equipe de seleção explicava o que a pessoa não tem ou está estudando | Regra da skill: mensagem só com pontos fortes. Nunca "ainda não tenho X" nem "estou estudando Y" (em mensagem, resposta ou currículo) |
| Anexar currículo em página externa | O arquivo precisa estar numa pasta que a sessão lê (usa-se a pasta de rascunho e apaga depois). Campos de upload escondidos em componentes encapsulados (SmartRecruiters) exigem injetar o arquivo pela página |
| Campos obrigatórios que o robô não deve preencher | CPF e documentos, e dados que o perfil não tem (data de nascimento), ficam com a pessoa. Consentimentos opcionais ficam desmarcados |

## Gupy
| Problema visto | Mudança |
|---|---|
| A Gupy usa o currículo do cadastro, não o PDF da vaga, e cria a candidatura ao clicar em "Candidatar-se" | O robô abre a candidatura, confirma os "dados adicionais" com as respostas verdadeiras e **para em "Perguntas criadas pela empresa"**, porque as respostas ali não podem ser editadas depois. O link da vaga (`/job/<código>`) se obtém clicando na lista, não por script |
| A busca por "trainee" na Gupy retorna pouco para tecnologia | Documentado no relatório da rodada; o filtro de senioridade trata trainee como júnior |

## Posts
Skill nova `jobbot-posts`: planeja e escreve posts de LinkedIn com as skills do plugin `linkedin-skills`, mantém a discrição, confere números e **só publica com o "sim" explícito da pessoa, post a post**.

## O que ainda não foi testado com uma pessoa real
- A rodada de vagas (`jobbot-round`) de ponta a ponta.
- O backend com LLM da demonstração de triagem.
- A leitura do LinkedIn por navegador em outras contas.
- Gupy: perguntas eliminatórias reprovam na hora (ex.: 'Python e Golang' respondida Não = reprovado na hora). Pergunta composta com skill que ele tem pela metade: avisar antes de responder.
