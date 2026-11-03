# Installer le chef

1. Copie tout le contenu de ce dossier à la racine de ton projet (y compris le dossier caché `.claude/`).
2. Initialise git si ce n'est pas déjà fait : `git init && git add . && git commit -m "Config du chef"`
   (les worktrees des exécutants en ont besoin).
3. Ouvre `CLAUDE.md` et règle ton abonnement et le nombre d'agents simultanés.
4. Optionnel, pour le suivi de consommation : vérifie que `npx ccusage@latest blocks --active` fonctionne.
5. Lance `claude` dans le dossier et commence par : « Nouveau projet : … ».

Le chef relit `CLAUDE.md` et `ETAT.md` à chaque session et reprend là où vous vous êtes arrêtés.

## Contenu

| Fichier | Rôle |
|---|---|
| `CLAUDE.md` | Règles du chef |
| `ETAT.md` | Tableau de bord tenu par le chef |
| `.claude/agents/*.md` | Les cinq types d'agents |
| `docs/interfaces/` | Contrats entre sous-systèmes |
| `docs/decisions/` | Journal des décisions validées |
