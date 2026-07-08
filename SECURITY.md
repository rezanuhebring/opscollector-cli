# Security Policy

This repository is **public**. Treat everything committed here as visible to the
world.

## Reporting a Vulnerability
Open a public issue or contact the maintainer directly. Do **not** post
credentials or sensitive data in issues.

## Rules for Contributors
- Never commit secrets: passwords, API keys, tokens, private keys, `.env` files,
  or connection strings. The repo `.gitignore` already excludes common secret
  patterns (`.env`, `*.pem`, `*.key`, `id_rsa`, `secrets.json`, etc.).
- The application stores operational data in a local SQLite database
  (`database/opscollector.db`). That file and all runtime data dirs
  (`backup/`, `export/`, `evidence/`, `logs/`) are git-ignored — do not force-add
  them.
- Rotate any credential immediately if it was ever committed, even after
  deleting it (git history retains it). Use `git filter-repo` / BFG to purge and
  assume the secret is compromised.

## Data Privacy
OpsCollector-CLI is offline-first and portable. It does not transmit data over
the network. Evidence files and reports stay on your machine.
