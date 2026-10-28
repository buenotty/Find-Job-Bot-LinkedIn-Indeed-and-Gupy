# Salário estimado quando a vaga não informa

**Problema.** A maioria das vagas não traz salário. Sem ele, o piso do tipo, a pretensão e o mínimo para presencial
(`constraints.onsite_min_salary`) não conseguem filtrar nada.

**Regra.** Sem `salary` na vaga, a skill busca na web o salário médio mensal (CLT, em reais) do cargo na empresa, e se
não achar, do cargo na cidade ou no mercado. Fontes aceitas: páginas públicas de salário (Glassdoor, Catho, Vagas,
Levels, Salario.com.br). Sem login, sem contornar bloqueio.

**Dados.** O `posting.yaml` ganha dois campos opcionais:
- `salary_estimate`: inteiro em reais por mês. Só preencher com número lido numa fonte.
- `salary_source`: texto curto com fonte e data da consulta, por exemplo `Glassdoor, Analista de Dados na Empresa X, 2026-10-26`.

**Uso no código.** `evaluate` usa `salary` quando existe; senão usa `salary_estimate`. O piso, o filtro
`good_without_type` e o mínimo para presencial valem para os dois. Quando só há estimativa:
- `Evaluation.salary_is_estimate` fica `True` e entra a nota `salário estimado (<fonte>)`;
- a folha de revisão mostra "estimado" ao lado do valor e da fonte. O número nunca é apresentado como o salário da vaga.

**Honestidade.** Estimativa nunca vai para o currículo nem para resposta de formulário. Sem fonte, o campo fica vazio e a
vaga segue como "salário não informado".

**Onde roda.** `jobbot-round` (passo 3.1) e `jobbot-resume` (passo 1) fazem a busca com o WebSearch/WebFetch.
Limite: a busca é do agente, não da CLI; a CLI só valida e usa o que recebe.
