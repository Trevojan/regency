# Keyboard

The source of truth for keys is `../BRIEF.md` (Views and Commands); `ux.py brief` fails a key used twice.
This file holds the rules every key follows.

- `Ctrl K` opens the command palette from any view: recent first, then the brief's groups; each row
  shows its label, the view code it lands in and its shortcut.
- `Ctrl 1…9` switch views in rail order; `Ctrl ,` opens settings.
- `Esc` closes the one open overlay and returns focus.
- `Ctrl Z` undoes the last file-changing action; the toast names it.
- `Ctrl S` saves pending fields (settings, forms); switches never wait for it.
- Buttons show their key in a `kbd` hint; a primary action has one.
- Focus order follows the visual order: rail → navigator → centre → inspector.
- ⟨product-specific rules, e.g. an insert key inside the editor⟩
