# Plano — reescrever `Docs/.guidelines/PLAN/` como escada de execução

## Contexto

O cliente pediu um plano de desenvolvimento **do mínimo ao máximo**, organizado como
checklist do mais simples até o sistema entregável, com uma hierarquia literal:

```
degrau = módulo → fases → afazeres → arquivos → código → norma → teste → missão cumprida
```

Cada passo é um commit; o esforço mora na escada, não no GRAND nem no MINIMUM. A
primeira tentativa de planos (escrita antes desta explicação) ficou leve demais na
execução e a folha de gate reprovou a abertura. Além disso, o `PLAN.md` da raiz — que é o
backlog real, com 141 itens e as dependências declaradas — estava fora da pasta e não
tinha sido incorporado.

**A planta antes das paredes.** Os **sete** degraus são escritos agora, com o mesmo rigor
e o mesmo detalhamento: fases, afazeres, arquivos, funções, norma e teste de cada um.
O que fica para o momento certo é o **conteúdo** — o código. Isso não conflita com a
regra 3 do `PLANOS.md` ("`LADDER` nunca é sobrescrito"), porque um degrau só **congela**
quando o gate dele é assinado `SOLUTION: sim`; antes disso é planta, e planta se corrige
com o que a realidade responder nos degraus anteriores.

**Resultado esperado:** `PLAN/` com um plano executável de 7 degraus e ~129 afazeres
nomeados um a um, dois marcos (MVP-0 em 22 commits, MVP-1 em 78), rastreio item-a-item
contra o backlog e uma checklist marcável.

**Decisões já tomadas pelo cliente:** emendar a fórmula do gate para somatório; renomear
o backlog para `BACKLOG.md`; nomear dois MVPs; **não** fazer agora o POC de conferência
com cards reais.

---

## 1. Movimentação de arquivos

| Ação | De | Para |
|---|---|---|
| `git mv` | `PLAN.md` (raiz) | `Docs/.guidelines/PLAN/BACKLOG.md` |
| Reescrever | `PLAN/GRAND_PLAN.md` | idem — enxuga, teto de 120 linhas |
| Reescrever | `PLAN/MINIMUM_PLAN.md` | idem — teto de 90 linhas, ganha §Alcance do MVP e §POC nuclear |
| Reescrever | `PLAN/LADDER_PLAN_PART_1.md` | o módulo Cadastro completo, detalhado |
| Criar | — | `PLAN/LADDER_PLAN_PART_2.md` … `PART_7.md` — **mesmo detalhamento do PART_1** |
| Criar | — | `PLAN/CHECKLIST.md`, `PLAN/RASTREIO.md`, `PLAN/README.md` |
| Excluir | `PLAN/GATE_2026-08-14_PARTE_1.md` | substituído por `GATE_PARTE_1_<data>.md` |
| Emendar | `PLAN/PLANOS.md` | bloco `## Emendas` datado no fim — **sem tocar no texto do cliente** |

`git mv` e não cópia: preserva o histórico das 880 linhas do backlog.

---

## 2. A hierarquia, com definição operacional

**As 7 fases são fixas em todos os degraus** — ditadas pelo `DECISIONS/ARCHITECTURE.md`,
para que duas pessoas decomponham igual. Fase vazia se declara vazia, não se omite.

| Fase | Nome | Onde mexe | Contrato que publica |
|---|---|---|---|
| F0 | Norma | `DECISIONS/`, `SOURCES/` | a regra citável que as próximas obedecem |
| F1 | Contrato | `Models/`, `Services/I*.cs`, `Data/Migrations/` | tipos, assinaturas, schema |
| F2 | Regra | `Services/*.cs` + `REMUNERACAO_PROBE` | comportamento provado |
| F3 | Exposição | `API_PANEL/Controllers/`, `Auth/Perfis.cs` | rota HTTP + autorização |
| F4 | Consumo | `UPLINK_DRIVE/` | cliente tipado |
| F5 | Tela | `VIEW_CORE/` + `Telas.Prontas` + `VIEW_PROBE` | tela navegável e marcada pronta |
| F6 | Fechamento | `CHANGELOG.md`, `API_ENDPOINTS.md`, `BACKLOG.md`, gate | o degrau seguinte abre |

**Afazer = um commit.** Critério fechado: build sem avisos novos; os dois `*_PROBE` verdes
rodados projeto a projeto; cabe numa frase imperativa sem "e"; e é revertível sozinho.
Calibragem: um afazer é sempre dificuldade 1 na escala do backlog.

**Fase é fronteira de dependência; afazer é fronteira de reversibilidade.** Trocar duas
fases de ordem quebra o sistema (F3 antes de F2 é regra no Controller, que o
`ARCHITECTURE.md` proíbe com `[MAND]`); trocar dois afazeres da mesma fase não quebra nada.

**Norma** = a regra citável que aquele código obedece: um `[MAND]` do `ARCHITECTURE.md`,
uma linha do `BUSINESS_RULES.md`, ou um ADR. Todo afazer cita a sua — afazer sem norma é
código sem critério de aceite.

---

## 3. A escada — 7 degraus, ~129 afazeres

| # | Degrau | Módulo | Commits | Acum. | Marco |
|---|---|---|---:|---:|---|
| 1 | Cadastro e Administração | 8º módulo (DHO) | 22 | 22 | **MVP-0 — Piloto de cadastro** |
| 2 | Aprovação & Nota Fiscal | 3 | 22 | 44 | — |
| 3 | Conferência Mensal | 4 | 19 | 63 | — |
| 4 | Extrato individual (leitura) | 6a | 15 | 78 | **MVP-1 — Um mês fechado** |
| 5 | Folha | 5 | 19 | 97 | — |
| 6 | Fechamento & envio | 6b | 18 | 115 | — |
| 7 | DRE Gerencial | 7 | 14 | 129 | **Entregável topo de linha** |

**Ordem por dependência real, não por preferência:** o degrau 1 é o único sem dependência
de entrada, preenche `gestor_id`/`centro_receita_id` que o Módulo 3 precisa para rotear a
aprovação, e cria as contas de gestor e financeiro sem as quais o Módulo 3 **não pode ser
homologado** — não se aceita um handoff entre três papéis com uma conta só. Do degrau 2 em
diante vale a ordem do backlog: sem card em `Recebido` não há conferência, sem apuração
não há extrato, sem mês fechado não há DRE.

**Requisito não funcional não vira degrau.** Ancora na F0 ou F5 do primeiro degrau que
sofreria sem ele; se nenhum sofre, fica `[late]` no backlog e nunca entra na escada.

---

## 4. Conteúdo de cada arquivo

### `GRAND_PLAN.md` — teto 120 linhas
Seções do template + **`## Definição de entregável topo de linha`**: os 7 módulos mais as
convenções não-funcionais que aceleram o core (motor como fonte única, restrição de
visibilidade no Service, blindagem por build configuration, prova por `*_PROBE`). É ela
que dá critério ao último degrau.
**Não entra:** nome de arquivo, assinatura, estimativa, id de backlog.

### `MINIMUM_PLAN.md` — teto 90 linhas
Tabela de fatores **encolhe para 4 colunas** (`# | Fator | Depende de | Degrau alvo`) — as
colunas de atestado saem, porque atestado é da escada. Ganha:
- **`## Alcance do MVP`** — declara `N_mvp = 4`, que a fórmula emendada do gate consome.
- **`## POC nuclear`** — o provedor de e-mail, com cinco campos: risco não provado,
  pergunta fechada, como se responde, critério de descarte, o que muda se der não. Roda
  em paralelo ao degrau 1 porque não é trabalho de código, e três coisas dependem dele
  (recuperação de senha do ADR-012, credencial inicial do degrau 1, envio do extrato do
  degrau 6).
- **`## Emendas`** — bloco append-only, vazio na abertura.
- **`## Riscos aceitos sem prova`** — registra que o motor nunca encontrou um card real e
  que a conferência contra a planilha do escritório foi adiada para o degrau 4, por
  decisão do PO nesta data.

### `LADDER_PLAN_PART_1.md` … `PART_7.md` — onde o esforço mora
**Os sete têm a mesma estrutura, o mesmo rigor e o mesmo nível de detalhe.** Seções do
`PLANOS.md` (`Por que este degrau agora`, `Funções afetadas`, `Escopo`, `Atestados`,
`POC necessário`, `Critério de conclusão`) mais a seção central `## Fases e afazeres`,
com uma tabela por fase:

| Afazer | Cobre | Arquivos | Função / assinatura | Norma | Teste | Commit |
|---|---|---|---|---|---|---|
| `P1.F2.A03` | `B-CAD-01` | `REMUNERACAO_CORE/Services/CadastroService.cs` | `Task<PessoaViewModel> CriarPessoaAsync(PessoaRequest, EscopoUsuario)` | ADR-005 · BR §Validações | `CadastroServiceTests.CriarPessoaAsync_NascePendenteDeTroca` | `feat(CADASTRO): criar pessoa com senha provisória gerada` |

O que **é** escrito agora, para os sete: o caminho de cada arquivo, o nome e a assinatura
de cada função, a norma que a governa, o nome do teste que a prova e a mensagem de commit.
O que **não** é escrito: o corpo das funções. Planta, não parede.

**Onde a planta é necessariamente menos firme, ela diz isso** em vez de fingir precisão —
por exemplo, o download do `.xlsx` numa janela Photino (degrau 7, F5) é um desconhecido
real: janela nativa não tem pasta de downloads de navegador. Fica registrado como `POC
necessário` daquele degrau, com a pergunta que ele responde.

### `CHECKLIST.md` — a rampa pedida
Arquivo próprio, único, global, **derivado** da escada (linha sem afazer de origem é bug
de processo). Marcável com `- [ ]`. Ordem declarada e reproduzível: topológica primeiro,
dificuldade crescente dentro do que está livre, `[late]` só quando nada mais está livre.
Marcos `⟦ MARCO ⟧` para MVP-0, MVP-1 e topo de linha. Fica fora dos `LADDER` porque marcar
caixinha é escrever no arquivo, e a regra 3 diz que `LADDER` não se sobrescreve: **o
LADDER é o que foi decidido, o CHECKLIST é o que foi feito.**

### `RASTREIO.md` — nada se perde, nada nasce do nada
Uma linha por item do backlog, id estável `B-<AREA>-<nn>` e **exatamente quatro estados**:
`coberto` (com o afazer), `adiado` (com degrau alvo), `fora da escada` (com motivo),
`descartado` (com motivo). Sem célula vazia.
- **Sentido 1:** nº de linhas do RASTREIO == nº de itens da Parte II do BACKLOG.
- **Sentido 2:** todo afazer cita um `B-id`, ou `origem: GRAND`, ou `origem: norma`.

O sentido 2 já pega dois buracos reais: `Shell.razor` §roteamento e §guarda de saída, e o
ADR de política de resíduo — trabalho prometido na Parte III sem cartão na Parte II.

### `BACKLOG.md` (o antigo `PLAN.md`)
Estrutura preservada. Quatro mudanças: id `B-<AREA>-<nn>` em cada linha das Partes I e II;
corrigir "18 categorias" para 19; o bloco "Funções a implementar" da Parte III passa a ser
matéria-prima com ponteiro `→ LADDER_PART_X §Fase N`; e a nota de precedência reescrita:

> **BACKLOG manda sobre fato** (o que existe, o que falta, quanto custa).
> **GRAND/MINIMUM/LADDER mandam sobre decisão** (o que se faz, em que ordem, sob qual critério).
> **Regra de negócio não mora em nenhum dos dois** — mora em `DECISIONS/BUSINESS_RULES.md`.

### `README.md` da pasta
Tabela arquivo → pergunta que responde → dono → quando muda; ordem de leitura; índice
datado dos gates emitidos.

---

## 5. Emendas ao `PLANOS.md` (bloco datado, texto do cliente intacto)

**5. O esforço mora na escada** — GRAND ≤ 120 linhas, MINIMUM ≤ 90. Excedente migra.

**6. Fórmula do gate** *(autorizada pelo cliente)*:
```
((MINIMUM < GRAND) & (MINIMUM <= (Σ LADDER_PART_1..N_mvp + POC))) = SOLUTION
```
com `N_mvp` declarado em `MINIMUM_PLAN §Alcance do MVP`. Não afrouxa: continua exigindo
cobertura integral por degraus escritos mais POC delimitado. Replicar em `TEAM/TEAM.md §4`
e `TEAM/PO.md §8`, senão os papéis contradizem a lei.

**7. A planta inteira é escrita antes da primeira parede.** Os sete `LADDER` existem, com
o mesmo detalhamento, antes de a execução abrir. O que a regra 4 do cliente governa é a
**abertura** de um degrau, não a existência da sua planta.

**8. Um `LADDER` só congela quando o gate dele é assinado `SOLUTION: sim`.** Antes disso é
planta e pode ser corrigida pelo que os degraus anteriores ensinarem — e é isso que
autoriza descartar a primeira tentativa sem quebrar a regra 3.

**9. Dois tipos de folha de gate** — `tipo: triangulacao` (uma vez, na abertura do P1) e
`tipo: degrau` (nas seguintes: critério da parte anterior + veredicto do QA + nenhum item
do RASTREIO regredido).

**10. Dois tipos de POC** — *nuclear* (no MINIMUM, sobre a viabilidade do MVP) e *de
degrau* (no LADDER, sobre a viabilidade daquele degrau). POC vive em branch que não chega
à `main`; o único artefato que sobrevive é documento.

**11. Ciclo de fechamento de degrau** (tudo no mesmo commit): verificar o critério →
marcar `DEGRAU X CUMPRIDO` no CHECKLIST → mover os itens cobertos da Parte II para a I no
BACKLOG preservando o `B-id` → atualizar RASTREIO → emitir o gate da parte seguinte →
revisar a planta do degrau seguinte com o que se aprendeu → congelar o degrau que fechou.

**12. Degrau em execução não muda de escopo** — pedido novo vai para o BACKLOG.

---

## 6. Referências a corrigir no mesmo commit da migração

- `SOURCES/AGENTS.md` — a tabela de `PLAN/` cita `PLAN.md` da raiz; passa a citar
  `PLAN/BACKLOG.md`. Corrigir também "18 áreas" → 19.
- `SOURCES/README.md` — descreve `PLAN/` só como "templates".
- `SOURCES/GLYPH_LEGEND.md` — lista o `PLAN.md` da raiz entre os não-Glyph; o caminho muda.
- `TEAM/TEAM.md` e `TEAM/PO.md` — a fórmula do gate, em três lugares.

---

## 7. Verificação

Não há código nesta entrega; a verificação é de coerência e de contagem.

1. **Rastreio fecha nos dois sentidos:** `nº de linhas do RASTREIO.md == nº de itens da
   Parte II do BACKLOG.md`, zero linhas sem estado, e zero afazeres sem origem declarada.
2. **Paridade de detalhamento:** os sete `LADDER` têm as mesmas seções e todos os afazeres
   com as sete colunas preenchidas — nenhuma célula "a definir" fora de `POC necessário`.
3. **Soma dos commits:** a contagem por degrau no `CHECKLIST.md` bate com a soma das
   tabelas de cada `LADDER_PART_X`, e o total fecha 129.
4. **Tetos:** `wc -l GRAND_PLAN.md` ≤ 120 e `MINIMUM_PLAN.md` ≤ 90.
5. **Gate:** a folha nova fecha `SOLUTION: sim` com a fórmula emendada e `N_mvp = 4`.
6. **Sem referência quebrada:** `grep -rn "PLAN.md" --include=*.md .` não aponta para a raiz.
7. **Git:** `git log --follow Docs/.guidelines/PLAN/BACKLOG.md` mostra o histórico anterior
   do arquivo — prova de que o `git mv` preservou a linha do tempo.

## Fora do escopo desta entrega

Nenhum código de produção. O degrau 1 só abre depois do gate aprovado, e o primeiro
afazer dele (`P1.F0.A01`) é escrever o ADR do cadastro.