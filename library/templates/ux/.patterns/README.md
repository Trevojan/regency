# Patterns

How ⟨product name⟩ behaves, whatever the screen. A view may add rules in its own README; it never
contradicts these without a `UX-UI-##` in `../.rules/`.

| File | Subject |
|---|---|
| `states.md` | the three state models: severity, lifecycle, actors |
| `keyboard.md` | the palette, shortcuts, focus order |

## Interaction rules

- **One state everywhere.** The rail badge, the navigator marks, the status bar, the problems view and
  the preflight count the same problems, from one store.
- **Master → detail.** Lists on the left, the selected item's detail on the right; the detail follows
  the selection.
- **Disabled with a reason.** A disabled commit button always sits under the check that blocks it, and
  that check carries the button that leads to the fix. Offer the partial path when one exists.
- **Preview before change.** An automatic fix is shown as a diff and re-checked by the engine before
  Apply. The commit action (⟨from BRIEF⟩) runs a preflight.
- **Everything is undoable.** A change keeps the previous version in ⟨the attic, from BRIEF⟩; the toast
  offers Undo with its shortcut and names the path.
- **Keyboard first.** Every function has a palette command; most have a shortcut; buttons show their
  `kbd` (`keyboard.md`).
- **Visible system status.** The title bar names the engine and its version; the status bar's left
  side is the same in every view.
- **Empty is a state.** A unit with nothing yet shows its first action; a skipped stage shows its
  reason, never a gap.
- **Settings are a file.** Switches apply at once; fields wait for Save; Open source shows the file.
- **Actors are read, not chosen.** Who plays each stage is read from the documents `../BRIEF.md` names;
  the interface shows it and never decides it.
- **One overlay at a time.** Esc closes it and returns focus to where it was.
