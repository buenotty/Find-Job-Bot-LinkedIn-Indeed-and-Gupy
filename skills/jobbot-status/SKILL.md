---
name: jobbot-status
description: Use para ver o andamento das candidaturas e dos limites e para liberar uma plataforma pausada. Mostra quantas abas foram preparadas hoje em cada plataforma, confere quais abas foram enviadas ou fechadas e atualiza o log. Gatilhos - "status das vagas", "o que enviei", "liberar o LinkedIn", "quantas abas hoje".
---

# JobBot: status das candidaturas

## Passos

1. Pergunte o nome do perfil (`<nome>`), se ainda não souber.
2. **Limites.** Para `linkedin`, `indeed` e `gupy`, rode `python3 -m jobbot round-check <nome> <plataforma>` e mostre `hoje`, `pendentes`, `pausada` e o `motivo`.
3. **Conferir as abas.** Liste as candidaturas com `python3 -m jobbot applications <nome>`. Para cada uma com status `preparado`, olhe no Chrome se a aba ainda existe: se aparecer a confirmação de envio, rode `python3 -m jobbot app-status <nome> <url> enviada`; se a aba foi fechada sem confirmação, rode `app-status <nome> <url> descartada`; se não for possível saber, rode `app-status <nome> <url> desconhecido`. Nunca marque `enviada` sem ver a confirmação.
4. **Liberar uma plataforma pausada.** Só quando a pessoa pedir, rode `python3 -m jobbot platform-release <nome> <plataforma>`. Antes, lembre o motivo da pausa (captcha, verificação ou aviso) e que continuar é decisão e risco dela.
5. Mostre o resumo: preparadas, enviadas, descartadas, pendentes e pausadas.

Esta skill não envia nada e não abre novas candidaturas: para isso, use `jobbot-round`.
