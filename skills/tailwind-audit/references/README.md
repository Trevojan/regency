# References

Two layers, kept apart on purpose so the skill survives a redesign.

| Layer | Path | Changes when |
|---|---|---|
| **Layout knowledge** (where boxes go) | [layout/](layout/README.md): [flex/](layout/flex/SPEC.md), [grid/](layout/grid/SPEC.md), [absolute/](layout/absolute/SPEC.md), [utilities.css](layout/utilities.css), [debug.js](layout/debug.js) | never by a redesign; only when a new trap or pattern is learned |
| **Design layer** (what boxes look like) | [norm.md](norm.md), [theme.css](theme.css), [components/](components/README.md) | the design system changes |
| Render shell | [render-shell.html](render-shell.html) | the Regent's template; kept verbatim |

Start points:
- "Where should this go / why is it there?" → [layout/README.md](layout/README.md): choosing a primitive and the triage procedure.
- "What should this component look like?" → [components/README.md](components/README.md): catalogue and norm gaps.
- "Which rule applies?" → [norm.md](norm.md).
