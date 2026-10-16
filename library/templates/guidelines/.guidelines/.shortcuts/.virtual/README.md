# `.virtual/` — o relance do agente

> Escrito para o agente, não para quem abre o repositório. Serve para chegar à linha certa
> com pouco esforço: o que está **em andamento**, o que é só **backlog**, e qual norma governa qual código.

| arquivo | o que guarda |
|---|---|
| `ongoing.json` | **o primeiro relance.** O trabalho dos agentes: `ongoing` (começou, não fechou — com evidência), `review` (pronto, espera conferência humana), `blocked` (espera uma decisão nomeada), `backlog` (planejado, não começou). Aponta para o documento onde o detalhe mora; nunca copia. |
| `manifesto.json` | o elo norma ↔ código: cada fatia de norma declara o código que governa, e o porteiro avisa quando o código muda. |

## Quem atualiza `ongoing.json`, e quando

O agente, sem pedir licença: ao **começar** um item (`ongoing`, com evidência em `where`: branch,
arquivos, passe), a cada **fronteira** (a linha `next`), ao **terminar** (`review`, nunca `done` por
conta própria), ao **parar** e no **handoff** (itens `done` saem: o git é o registro). Ao **voltar** ao
repositório: relance `ongoing.json`, junte os rastros (`vp.py trace`), reconcilie — item `ongoing` sem
evidência é fantasma; evidência sem item é trabalho órfão — e pergunte ao Regente sobre o que for decisão.
Promover `backlog` para `ongoing` é ato da fila ou do Regente, nunca do acaso.

Ferramenta: `python <regency>/scripts/vp.py ongoing` e `vp.py trace` (somente leitura).
