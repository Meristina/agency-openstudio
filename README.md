# Agency Studio

> **Statut : scaffold (docs + roadmap).** Aucun code applicatif pour l'instant — ce
> repo contient la vision, l'architecture et le plan de construction. L'implémentation
> suivra par vagues (voir [`ROADMAP.md`](./ROADMAP.md)).

**Agency Studio** est un **studio agentique local-first** : il empile
[agency-kit](https://github.com/Meristina/agency-kit) (le *cerveau* qui orchestre
9 départements — route → execute → synthesize → inspect avec veto) au-dessus d'une
couche **multimodale locale** (génération d'images, voix STT/TTS, RAG sur tes documents).

L'idée n'est pas de refaire un énième runner de modèle (LM Studio, Jan, GPT4All,
Uncensored-Local-Studio le font déjà), mais de poser **l'étage d'orchestration**
au-dessus d'eux, avec une GUI propre et une posture de sécurité saine.

## Principe directeur

- 🧠 **Cerveau = Opus via l'abonnement Claude CLI** (engine `claude-code` déjà câblé
  côté agency-kit) → raisonnement de qualité, **coût marginal nul**.
- 🦾 **Bras = modèles locaux** (Stable Diffusion, Whisper, Kokoro, embeddings RAG),
  ciblés **Apple Silicon / Metal**, chargés **mutuellement exclusifs** (contrainte 16 Go).
- 🖥️ **Écran = GUI React/Vite** servie en local, timeline de mission en direct (SSE).
- 🔒 **Sécurité d'abord** : bind `127.0.0.1`, pas de CORS `*`, garde anti path-traversal
  (l'inverse des défauts relevés dans les runners existants).
- ⚖️ **Licence MIT-compatible** : on réemploie les patterns MIT/Apache, on **écarte
  l'AGPL** (Jan, chunkr) pour ne pas contaminer le projet.

## Ce qui marchera (une fois implémenté)

```
agency studio        # lance le serveur local + ouvre la Mission Console
→ tape un goal       # "lance une campagne pour X au Maroc"
→ regarde les départements tourner en direct (route → dépts → synth → inspect)
→ récupère le dossier + le livrable, avec images générées et résumé lu en voix
```

## Documentation

- 🗺️ [`ROADMAP.md`](./ROADMAP.md) — le plan de construction complet (vagues 0-6).
- 🏛️ [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — architecture cible + flux de streaming.
- 🔐 [`docs/SECURITY.md`](./docs/SECURITY.md) — garde de sécurité non négociable.
- 📜 [`docs/LICENSES.md`](./docs/LICENSES.md) — inventaire des composants tiers et licences.
- 🤖 [`CLAUDE.md`](./CLAUDE.md) — guidance pour Claude Code dans ce repo.

## Licence

MIT — voir [`LICENSE`](./LICENSE).
