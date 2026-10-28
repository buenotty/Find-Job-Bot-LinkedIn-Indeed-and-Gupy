# Notas por plataforma

Regras para as rodadas do JobBot. O bot prepara abas; quem envia é a pessoa.

## Regras que valem em todas as plataformas

- Uma aba por vez, em ritmo lento e irregular. Nunca em paralelo, nunca várias sessões.
- Sempre o Chrome em que a pessoa já está logada. O bot nunca pede, guarda ou digita senha.
- Limite padrão: 10 abas por rodada e 30 por dia, em cada plataforma, e no máximo 50 vagas examinadas por rodada.
- Confira o nome da conta logada no começo. Se não bater com o perfil, pare.
- Nunca clique em enviar. Pare no último passo.

## Condições de parada (freios)

Pare a plataforma na hora, rode `platform-pause`, avise a pessoa e não tente de novo nem contorne, quando aparecer:

- captcha ou desafio "não sou um robô";
- pedido de verificação de identidade, e-mail ou telefone;
- aviso de atividade incomum, restrição temporária ou limite de uso;
- tela de login ou sessão expirada;
- a página mudou e o bot não reconhece o formulário (nunca preencha às cegas).

A pausa só termina quando a pessoa pedir para liberar (`platform-release`).

## LinkedIn

- A página de resultados demora a carregar. Depois de abrir a busca, aguarde cerca de 4 segundos antes de ler. Se der leitura vazia, espere mais um pouco e tente de novo, no máximo 2 vezes; se continuar vazia, trate como falha da plataforma, rode `seen-add` com o motivo `falha` e passe adiante.
- O LinkedIn pode acrescentar filtros por conta própria à busca (por exemplo, faixa salarial das preferências da pessoa), e isso esconde vagas. Confira os filtros ativos na página e mencione-os no resumo da rodada.
- A página de resultados mostra, ao lado, o texto completo da vaga selecionada. Para outra vaga, abra o endereço dela (o número da vaga fica em `currentJobId`).

- Candidatura simplificada ("Easy Apply") fica dentro do LinkedIn: preencha até o último passo e pare.
- Quando a candidatura leva ao site da empresa, abra a página numa aba, sem preencher, e marque `externa`.
- Buscas e rolagem automatizadas também contam como automação: mantenha o ritmo lento.

## Indeed

- O salário costuma vir dentro do texto da descrição, não no campo de remuneração: leia a descrição antes de dizer que a vaga não informa salário.
- Com o conector do Claude para o Indeed, a busca e os detalhes da vaga vêm dele (sem navegar no site). O conector não envia candidatura: só devolve o link.
- Sem o conector, a busca é pelo navegador, como nas outras plataformas.
- O formulário é aberto e preenchido no navegador nos dois casos. Se levar a um site externo, marque `externa`.

## Gupy

- Cada empresa tem seu portal; o login costuma ser o mesmo da Gupy. Se pedir login, pare.
- Testes e questionários da Gupy podem ser cronometrados ou de uma tentativa só: use `fit-risks` e siga a ação.

## O que nunca fazer

- Enviar a candidatura, ou clicar em enviar, candidatar ou submeter.
- Resolver ou contornar captcha, trocar de IP ou de navegador para escapar de um bloqueio.
- Inventar uma resposta de formulário, ou responder um campo sensível ou consentimento legal sem resposta guardada.
- Candidatar-se a vaga do empregador atual, de empresa vetada ou já preparada antes.
- Passar do limite por rodada ou por dia.
