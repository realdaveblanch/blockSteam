# Contributing

Thanks for considering a contribution.

## Development setup

```powershell
py -m pip install -r requirements.txt
py steam_blocker.py
```

Run the application as Administrator when testing the actual blocking feature.

## Guidelines

- Keep the interface bilingual-friendly and plain-language.
- Do not add Windows Firewall rules or modify ESET settings.
- Do not close, terminate, or alter the monitored executable; this project blocks connection attempts only.
- Keep generated files out of commits (`build/`, `dist/`, bytecode, and local configuration).
- Explain and test changes that affect the network filter, the allow/block behaviour, or privileges.

## Pull requests

Use a concise title, describe the observable change, and include reproduction/testing notes. Keep unrelated formatting changes out of the same pull request.
