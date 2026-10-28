# Fontes e licenças do banco de perguntas

O banco de perguntas está em `jobbot/data/items.yaml`. Cada camada tem uma origem diferente.

## Personalidade (cinco grandes traços)

- **Fonte:** IPIP (International Personality Item Pool), um banco público de itens de personalidade mantido pelo Oregon Research Institute (`https://ipip.ori.org`). Os autores do IPIP declaram os itens de domínio público e de uso livre, inclusive comercial.
- **O que foi feito aqui:** adaptação livre para o português do Brasil de itens dos marcadores de cinco fatores do IPIP (abertura, conscienciosidade, extroversão, amabilidade e estabilidade emocional, esta última como inverso de neuroticismo). Cada traço tem 3 itens: 1 direto, 1 de polaridade inversa e 1 de checagem de consistência de redação própria.
- Os itens marcados com `reverse: true` têm polaridade negativa e são invertidos na pontuação.

## Interesses (seis áreas)

- **Modelo:** a divisão em seis áreas (prático, investigativo, artístico, social, empreendedor e convencional) segue o modelo teórico de interesses vocacionais de John Holland. Teorias e modelos não têm direito autoral.
- **Itens:** todos os 18 itens (3 por área) são de redação original do projeto. Nenhum item foi copiado de inventários publicados.

## Valores de trabalho

- **Itens:** os 16 itens (8 dimensões, 2 por dimensão, um direto e um de polaridade inversa que funciona como checagem) são de redação original do projeto.

## Âncoras de carreira (perfil de trabalho)

- **Modelo:** as âncoras de carreira de Edgar Schein (técnica, gestão, autonomia, segurança, empreendedorismo, serviço, desafio e estilo de vida), com criatividade separada de empreendedorismo. Estudos de validação do inventário original (Israel, 2008, com 1.847 trabalhadores; EUA e Turquia, 2018) encontraram melhor ajuste com nove fatores do que com oito. O modelo é uma teoria e não tem direito autoral; o inventário oficial é protegido, então nenhum item dele foi usado.
- **Itens:** os 18 itens (2 por âncora, com itens de polaridade inversa em gestão e segurança) são de redação original do projeto.
- **Uso:** a diferença entre as âncoras técnica e gestão define a trilha (`especialista` ou `gestao`); com diferença menor que 17 pontos, âncoras ambas altas (67 ou mais) dão `hibrido`; senão o estilo de liderança (63 ou mais para gestão, 37 ou menos para especialista) desempata. Sem desempate a trilha fica `indefinido` e vale o que a entrevista registrou.

## Estilo de trabalho (competências)

Oito competências (liderança, comunicação, planejamento, resolução de problemas, adaptabilidade, desempenho sob pressão, aprendizado e foco em resultado), 2 itens cada, de redação original, escritos como comportamentos concretos de autorrelato. Um item por competência tem polaridade inversa.

## Código de Holland

Os seis percentuais de interesses viram um código de três letras (RIASEC), das áreas mais altas para as mais baixas. É um resumo de leitura, não um diagnóstico.

## Itens de checagem (twins)

Em valores e personalidade, alguns itens repetem outro da mesma dimensão com outra redação (`twin`). Servem para detectar resposta apressada ou incoerente. A pontuação ajusta a polaridade antes de comparar os pares.

## Tamanho do teste

O teste tem 83 itens e 3 perguntas abertas (cerca de 10 minutos). Uma versão anterior tinha 220 itens e foi encurtada por ser longa demais. Com 2 a 3 itens por escala, a precisão é menor: os resultados servem para orientar a conversa, não para decidir sozinhos. Para uma leitura mais firme, a pessoa pode refazer o teste depois.

## Limites

As pontuações são percentuais da pontuação máxima possível em cada dimensão (autorrelativas). Não existe norma brasileira para estes itens, então os resultados não são percentis nem diagnóstico.
