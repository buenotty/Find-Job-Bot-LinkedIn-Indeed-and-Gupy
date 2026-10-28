# Passo a passo: do zero à primeira rodada de vagas

Este guia leva uma pessoa nova do download do projeto até as candidaturas feitas. Cada passo diz o que você faz, o que o bot faz e o que fica guardado.

## 0. Antes de começar

- **Python 3.10 ou mais novo** e o **Claude Code** instalados.
- **Chrome com a extensão Claude in Chrome** (o bot precisa dela para abrir vagas e preencher formulários).
- Esteja logado no LinkedIn, no Indeed e na Gupy no mesmo Chrome. O bot nunca digita sua senha.
- Leia o aviso do `README.md`: automação nessas plataformas viola os termos delas. O risco para a conta é seu.

## 1. Instalar

Dentro do Claude Code:

```
/plugin marketplace add buenotty/Find-Job-Bot-LinkedIn-Indeed-and-Gupy
/plugin install jobs-master-br-v1 --marketplace buenotty/Find-Job-Bot-LinkedIn-Indeed-and-Gupy
```

O comando `jobbot` (do `bin/` do plugin) cria um ambiente Python próprio em `~/.jobbot/venv` na primeira chamada e o atualiza quando o plugin muda. Para desenvolver, clone o repositório e use `bin/jobs-master`, que cria um `.venv` local e abre o Claude Code com o plugin carregado. Nada pessoal fica no repositório: seus dados vão para `~/.jobbot/profiles/<seu-nome>/`.

## 2. Começar

Digite `começar`. A skill `jobs-master` roda `jobbot next <nome>`, que lê o estado do perfil e diz a próxima etapa. Pode parar e voltar quando quiser: o estado fica salvo.

## 3. As etapas, em ordem

| # | Skill | Você faz | O bot faz | Sai dali |
|---|---|---|---|---|
| 1 | `jobbot-interview` | Preenche **um arquivo de texto** na pasta Downloads (`questionario-<nome>.txt`), do seu jeito: "avançado", "sim", "2 anos" servem | Interpreta as respostas, valida, pede só as lacunas | `profile.yaml` e relatório `01-perfil` |
| 2 (opcional) | `jobbot-assessment` | Responde o teste de ~10 minutos (nota de 1 a 5 por linha) | Calcula valores, interesses, personalidade, âncoras e estilo | Código Holland e trilha sugerida |
| 3 | `jobbot-market` | Aprova a lista de cargos proposta | Lê ~50 vagas por cargo aprovado, estima salário quando a vaga não informa | `focus-report.md` |
| 4 | `jobbot-profiles` | Autoriza as mudanças | Reescreve LinkedIn, GitHub e Gupy (e preenche, se você deixar) | Perfis revisados |
| 5 | `jobbot-types` | Aprova os tipos de vaga | Cria um tipo por profissão (piso, modalidade, contrato) e um currículo PDF por tipo | `types/*.pdf` |
| 6 | `jobbot-round` | Pede "rodar vagas" | Busca, filtra, gera um currículo por vaga e prepara a candidatura | Abas abertas ou candidaturas feitas |
| 7 | `jobbot-status` | Pergunta "como estamos" | Mostra limites do dia, atualiza enviadas e descartadas | Relatório da rodada |

Opcional: `jobbot-posts` (posts de LinkedIn), `jobbot-orientation` e `jobbot-courses` (mudar de área).

## 4. O que o bot filtra em cada vaga

Cada vaga passa por `vaga-check` (repetida? empregador atual? empresa vetada?), `vaga-eval` (match, salário, deslocamento, senioridade, modalidade) e `vaga-resume` (PDF com nome genérico `curriculo-<nome>-<CÓDIGO>.pdf`, sem nome de empresa). Vaga fora das suas restrições é descartada com o motivo.

## 5. Dois modos de candidatura

- **Autônomo (`full`, padrão):** o bot responde as perguntas da empresa, escreve o texto de apresentação e finaliza. Ele confirma esse modo com você uma vez, na primeira rodada.
- **Assistido (`assisted`):** o bot deixa a aba no último passo, com tudo preenchido, e você clica em enviar. Mude com `jobbot run-settings <nome> --autonomy assisted`.

Em qualquer modo o bot **nunca digita RG, CPF ou outro número de documento**, não aceita consentimento opcional por você e não inventa dado que não está no perfil. Quando falta um dado (por exemplo, salário atual), ele pergunta uma vez e guarda em `answers` para as próximas vagas.

## 6. Cuidados que aprendemos usando

- **Pergunta eliminatória** (Gupy): uma resposta "Não" reprova na hora e não dá para editar. O bot avisa antes de responder perguntas compostas ("Python e Golang?").
- **Discrição:** se seu empregador pode ver seus perfis, diga isso na entrevista. O bot não liga "aberto a oportunidades" nem avisa sua rede nas edições.
- **Sem lacunas no texto:** mensagens e resumos só citam o que você tem. Skill que falta pode aparecer só na lista de Competências, se for aprendível.
- **Limites:** 10 abas por rodada e 30 por dia em cada plataforma (`jobbot run-settings` muda).
- **Captcha ou aviso de atividade incomum:** o bot pausa a plataforma e espera você.

## 7. Seus dados e relatórios

- Perfil, currículos e respostas: `~/.jobbot/profiles/<nome>/` (ou `$JOBBOT_HOME`). Não vão para o Git.
- Relatórios de cada etapa: `~/Documents/JobBot/<nome>/`.
- Para apagar tudo, apague essas duas pastas.

## 8. Testes

```bash
.venv/bin/pytest
```

O teste `tests/test_no_personal_data.py` falha se um CPF, e-mail real ou caminho de usuário entrar nos arquivos versionados.
