# Honestidade e regra de estiramento

## A linha que o bot não cruza

O JobBot pode esticar **skills**: elas são testadas na entrevista e dá para aprender. Ele nunca inventa o que uma checagem de referência confirma:

- empregadores e cargos;
- datas de início e fim;
- formação e certificações;
- números de resultado (percentuais, valores, prazos).

Isso vale mesmo se a pessoa pedir. Número de resultado só entra se ela o informou (`metric` no perfil). A CLI aplica a regra: `python3 -m jobbot check` e `python3 -m jobbot cv` recusam números sem respaldo no perfil.

## Regra de estiramento

Compara as exigências de uma vaga com as skills da pessoa (`python3 -m jobbot match`). Os cortes ficam em `stretch_policy` e cada pessoa ajusta:

| Match | Rótulo | Ação (padrão) |
|---|---|---|
| 100% | Vaga perfeita | esticar |
| 80% a 99% | Ótimo match | esticar (a partir de 90%); de 80% a 89%, esticar com marcação visível |
| 70% a 79% | Bom match | esticar com marcação visível |
| 50% a 69% | Chance média | esticar com marcação visível |
| menos de 50% | Arriscado | abrir a vaga marcada como "arriscada"; a pessoa decide |

Esticar com marcação visível significa mostrar à pessoa, na revisão, cada skill que o CV lista sem que ela tenha experiência ("Estiramento: Kafka, você nunca usou"), para ela saber o que pode ser perguntado.

Nesta fase (mapeamento) a regra só é gravada no perfil. A aplicação acontece nas fases de currículos por vaga e de candidatura.

## Skills adjacentes

Algumas skills que a pessoa tem cobrem uma versão mais específica que a vaga pede. Exemplos: quem tem SQL ou SSMS cobre "SQL Server" e "T-SQL"; quem tem Excel cobre "Excel avançado"; quem tem Power BI cobre "Power BI Desktop". A tabela é curta e fica em `jobbot/match.py` (`ADJACENT`).

- A skill adjacente **conta no match** (a vaga não fica "arriscada" só pela diferença de nome).
- Ela **não vira afirmação**: o resumo e os bullets nunca citam a skill específica (por exemplo, "SQL Server"), nem em vaga arriscada. Ela só pode aparecer na lista de Competências, sem nível, como skill estendida, e a folha de revisão mostra "você tem SQL" ao lado.
- Se a pessoa tem a skill específica literalmente, vale o que ela tem.
