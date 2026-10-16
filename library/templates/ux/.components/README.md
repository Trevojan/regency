# Components

The catalogue of contracts: what each component shows, what the consumer provides, the rules it keeps.
Styles: `components.css` (class prefix `ws-`, every value a token). Rendered anatomy:
`../.samples/workspace.html`.

The components ⟨product name⟩ uses get a folder each, `<Name>/README.md`, created from
`_component.template.md` by `python <regency>/scripts/ux.py expand ..` for every row of `../BRIEF.md`
(Components). A component not in this catalogue is added here first, with its contract, then built.

<!-- ux:components:begin -->
| In use | Used by | Folder |
|---|---|---|
<!-- ux:components:end -->

## Shared types

```ts
type Severity  = 'fix' | 'ask' | 'note' | 'ok';      // engine output; fix blocks, ask never does
type Lifecycle = 'draft' | 'issued' | 'reissued' | 'stale' | 'blocked';
type ActorKind = 'agent' | 'human' | 'machine';       // ink on line-strong · human · system
```

| Severity | Mark | Text / fill |
|---|---|---|
| `fix` | ■ | `fix` / `fix-soft` |
| `ask` | ◆ | `ask` / `ask-soft` |
| `note` | ● | `system` / `system-soft` |
| `ok` | ✓ | `ok` / `ok-soft` |

| Lifecycle | Mark | Text / fill |
|---|---|---|
| `draft` | ○ | `ink-muted` / `surface-raised` |
| `issued` | ● | `ok` / `ok-soft` |
| `reissued` | ↻ | `accent` / `accent-soft` |
| `stale` | ◆ | `ask` / `ask-soft` |
| `blocked` | ■ | `fix` / `fix-soft` |

The models: `../.patterns/states.md`. The product's mapping: `../BRIEF.md`.

## Shell

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **AppFrame** | title bar · rail · view · status bar; overlay and toast slots | `crumbs`, `active` rail code, `mark` url, `badges` (code → worst severity + count), `status` `{left, right}`, the view, `overlay?`, `toast?` | status-bar left side identical in every view; one overlay at a time, Esc closes |
| **TitleBar** | product mark, crumbs, engine and version, palette entry | `title`, `crumbs`, `engine`, `mark`, `kbd` | the engine version is always visible |
| **Rail** | view mnemonics, badges | `items` (`code` 3 letters, `label`, `kbd`, `bottom?`), `active`, `badges` | a badge shows the worst severity only, with its count; `aria-current` on the active item |
| **StatusBar** | workspace state left, view state right | `left[]`, `right[]` | left: engine · severity totals · open run |
| **ViewHead** | view title, meta line, view actions | `title`, `meta`, children | one primary button per view |
| **TabBar** | open files | `tabs` (`id`, `label`, `kind?`, `dirty?`), `active` | active tab is `ground` with an `accent` top edge; dirty is a dot, not a word |

## Navigation

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **TreeNav** | the artefact tree with marks | `nodes` (`name`, `kind` dir·file, `role?` entry·attic, `open?`, `check?` Severity, `count?`, `status?` Lifecycle, `children?`), `selected` path | mono; selection is an `accent-soft` row; the attic is `ink-faint`; `aria-expanded`, `aria-selected` |
| **NavList** | sectioned list with counts and marks | `sections` or `items` (`id`, `label`, `count?`, `mark?`, `mono?`, `dim?`), `active` | counts in mono, marks before counts |
| **SearchField** | search with result count and key | `value`, `placeholder`, `count`, `kbd` | `:focus-within` ring |
| **FilterChips** | toggle filters with counts | `items` (`id`, `label`, `count?`, `on?`, `level?`) | `aria-pressed`; on = `accent-soft` with `accent` border |
| **Segmented** | 2–4 exclusive options | `items`, `value` | more than 4: Select |
| **CommandPalette** | every command, grouped | `query`, `groups` (`label`, `items` `{view, label, hint?, kbd?}`), `active`, `footer?` | recent first; view code column; Esc returns focus |
| **InsertPalette** | vocabulary quick-insert | `query`, `groups` (`label`, `items` [term, gloss]), `active` | Enter inserts into the last focused editor |

## Source and output

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **SourceEditor** | the editable source with gutter marks, inline hints, pins | `source`, `startLine?`, `activeLine?`, `marks` (line → `{level, text?}`), `pins` (line → actor code) | the only editable code pane; marks come from the engine |
| **OutputPane** | engine output in one of the brief's formats | `text`, `format`, `formats`, `path?`, `wrap?`, `from?`, `actions?` | read-only; missing values highlighted `ask-soft`; never hand-edited |
| **SourceSpan** | a few source lines with one span underlined | `lines` (`n`, `text`), `span` (`line`, `s`, `e`), `level` | the span is the engine's, exact |
| **TermChip** | one vocabulary term | `code`, `kind?` (the brief's term kinds), `depth?`, `alias?` | the only way to show a term outside the editor; kind → hue per the brief; unknown term = `fix` with a wavy underline |
| **EntryDetail** | one vocabulary entry in full | `code`, `kind`, `def`, `formula?`, `example?`, `rules?`, `actions` | every field is engine output |

## Marks

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **SeverityBadge** | the health of a source | `level`, `count?`, `label?`, `bare?` | mark + word (+ count), never colour alone |
| **StatusPill** | the lifecycle of an artefact | `status`, `compact?`, `bare?` | a file can be issued and still carry an `ask`: badge and pill are separate |
| **Kbd** | a shortcut | text | mono, `currentColor` border |

## Checks and change

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **FieldCheck** | required fields of an artefact with their check | `fields` (`key`, `value?`, `check?`, `hint?`), `title` | empty required = `ask`, malformed = `fix` |
| **ProblemList** | problems with code, message, line, source | `items` (`id`, `level`, `code`, `message`, `line?`, `source?`), `selected` | messages verbatim; sorted fix → ask → note |
| **Preflight** | the checks that gate the commit action | `title`, `checks` (`level`, `label`, `detail?`, `action?`), `actions` | any `fix` disables the primary action; the failing row carries the button to the fix; offer the partial path |
| **ProposalDiff** | a proposed change before Apply | `lines` (`op` − + space, `n`, `text`), `source` ("re-check: 0 fix"), `actions` | head: "Proposal — N change(s)"; removed `fix-soft` with `−`, added `ok-soft` with `+`; Apply is undoable |

## Flow

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **RunList** | runs with unit, date, counts by lifecycle | `items` (`id`, `unit?`, `decision?`, `date`, `closed?`, `counts`, `agents?`), `active` | the bar of counts uses the lifecycle fills |
| **StepCycle** | the stages of one run: who plays each and its status | `stages` (`stage`, `who`, `kind` ActorKind, `status` active·reused·skipped·human·pending·blocked, `packet?`, `detail?`), `current`, `compact?` | read from the orchestration's declaration, never composed by hand; `skipped` carries its reason, `reused` its artefact |
| **TrafficGraph** | what each stage reads and writes, by path | `nodes` (`id`, `kind` packet·path·empty, `col`, `row`, `actor?`, `status?`), `edges` (`from`, `to`, `kind` reads·writes, `conflict?`) | writes solid `accent`, reads dashed `ink-muted`; a write/write collision or a cycle is `fix` and blocks; withheld items get no edge; the legend is always shown |
| **PacketCard** | one stage's packet | `id`, `actor`, `status`, `summary?`, `path?`, `reads?`, `writes?`, `asks?` | paths as links |
| **RunTimeline** | the run's events in order | `events` (`id`, `actor`, `status`, `after?`, `note?`), `current` | newest last; each event names its actor |

## Inputs and settings

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **Button** | an action | `variant` primary·quiet·ghost, `kbd?`, `disabled?` | one `primary` per pane; label a verb; disabled only beside its reason |
| **TextInput** | a value | `value`, `placeholder`, `prefix?`, `suffix?`, `mono?`, `invalid?`, `level?` ask | invalid = `fix` border; empty required = `ask` border |
| **Select** | one of many | `options`, `value`, `mono?` | — |
| **Switch** | on/off, applies at once | `on`, `label`, `disabled?` | `role=switch`, `aria-checked` |
| **SettingRow** | one setting | `label`, `hint?` (a fact), `control`, `modified?` | modified = `accent` dot + Reset |
| **SettingsSection** | a group of rows | `title`, `meta?` (the file key), rows | — |
| **TemplateForm** | a template's holes | `name`, `gloss`, `params` (`name`, `ask`, `value?`, `repeat?`), `constraints?`, `actions` | an empty hole is an `ask`, never an error |

## Data and feedback

| Component | Shows | Consumer provides | Rules |
|---|---|---|---|
| **DataTable** | rows of entries | `columns` (`key`, `label`, `width?`, `align?`, `mono?`), `rows`, `selected` | heads in `label` style; numbers right-aligned, tabular |
| **KV** | label / value pairs | `rows` [key, value] | keys `ink-muted` 12px; values wrap anywhere |
| **Toast** | the result of a file-changing action | `message`, `detail?` (the path), `action?` Undo, `kbd?`, `level?` | every file-changing action ends in one, with Undo; it sits over the centre, never over the inspector's actions |
| **EmptyState** | nothing here yet | `title`, `detail?`, `action?` | names the first action; dashed `line-strong` border |
