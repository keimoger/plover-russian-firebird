# plover-russian-firebird

Firebird — a Russian steno theory for [Plover](https://www.openstenoproject.org/plover/),
targeting a standard 22-key Stenograph/Stentura layout

Status: bare plugin scaffold. The theory itself (key layout, orthography
rules, dictionary) hasn't been designed yet — see `plover_russian_firebird/system.py`
for the open question on the steno order before that can happen.

## Development install

```bash
pip install -e .
```

Then in Plover: Preferences > Plugins, confirm `plover-russian-firebird`
is loaded, and select "Russian Firebird" under Preferences > System.

(Note: the system isn't functional yet — `KEYS` is empty until the
theory's key layout is designed.)
