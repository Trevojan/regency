# packs/ — regency's public layer

Packs shipped with regency: what regency becomes in one domain (`library/packs.md`). Each pack is a folder
`packs/<id>/` holding `pack.json` and its files; an adopted one keeps its source verbatim under `upstream/`.

- A pack here is published with regency, so it needs an open-source license regency may redistribute.
  `python scripts/packs.py adopt <folder | git url> --id <id> --layer public` refuses a source without one.
- A pack the Regent keeps private, or one another project owns, lives in that project instead:
  `<guidelines>/.packs/<id>/` (`--layer project`).
- A pack does nothing until a project switches it on (`/regency:pack activate <id>`), and its hooks run only after
  the Regent ratifies them there (`/regency:pack ratify <id> hooks`).

None shipped yet. `python scripts/packs.py check` validates whatever lands here; doctor runs it.
