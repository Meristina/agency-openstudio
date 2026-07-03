# PLAN.md — Agence 360 : la feuille de route brick par brick

Chaque brick est un cycle **spec-kit** complet — `/speckit.specify` → `/speckit.clarify`
→ `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` — mergeable indépendamment,
dans cet ordre. La gouvernance vit dans la constitution
(`.specify/memory/constitution.md`) ; le contexte agents dans `AGENTS.md`.

**Vision** : une agence multimédia / B2B 360 / événementielle pilotée par des agents CLI
sur abonnement (zéro coût marginal), recherche internet obligatoire et vérifiable,
production jusqu'à la vidéo, interface « boîte magique » pour non-techniciens,
cross-platform, choix des modèles gratuit/payant.

---

## Brick 0 — Fondations *(en cours)*

Spec-kit initialisé (`specify init` + intégration claude), constitution ratifiée par
l'utilisateur, `AGENTS.md` canonique + `CLAUDE.md` symlink, `agencykit/` (le fork
agency-kit-studio, épinglé) et `openmontage/` (épinglé) vendorés, ce PLAN.md commité.
**Fait quand** : `specify check` passe, la suite studio (484 tests) et la suite
agencykit (70 tests) sont vertes, le dépôt s'installe seul (`pip install -e ./agencykit
&& pip install -e .`).

## Brick 1 — Le contrat Engine (abstraction multi-CLI, claude validé)

Formaliser le dict `ENGINES` d'`agencykit/agency_cli/engines/cli_engine.py` en un
contrat `Engine` explicite : `run(prompt)` / `route(prompt)` / capacités déclarées
(`web_search_headless: bool` — précondition constitutionnelle) / kill-tree sur cancel.
Le moteur **claude-code est le seul validé v1** ; codex/gemini restent enregistrés mais
marqués non-validés. Suite de contrat offline (un faux binaire par moteur).
Références : opencode `serve`, rivet-dev/sandbox-agent.
**Fait quand** : une mission tourne inchangée sur claude ; ajouter un moteur = une
implémentation du contrat + sa suite, zéro modification de la boucle de mission.

## Brick 2 — L'armée métier joue (agence marketing / B2B / événementiel réelle)

Aujourd'hui la boucle de mission ne charge que la doctrine condensée
(`_shared-{dept}.md`) — les commandants/officiers/soldats des 9 kits
(`agencykit/agency_cli/payload/` : 177 agents, 110 skills) ne participent jamais.
Câbler une **escalade à budget maîtrisé** : doctrine condensée → officier de la phase
concernée → soldat méthode (JTBD, STP, Pareto, PERT…), sélectionnés par le routeur du
département. L'événementiel (comms-kit) et le B2B 360 deviennent opérationnels.
**Fait quand** : une mission marketing invoque réellement ≥1 officier + ≥1 soldat
tracés dans le dossier ; le coût token par département reste borné et mesuré.

## Brick 3 — Internet vérifiable (de la garantie molle à la post-condition)

Le mandat « no invented information » est aujourd'hui prompt-only. Le durcir :
extraction des citations du livrable, résolution des URLs (HEAD, offline-stubbé en
test), seuil minimal de sources par département, verdict inspecteur enrichi d'un
rapport de vérification. Pattern de référence : gpt-researcher (Apache-2.0).
**Fait quand** : un livrable sans sources résolvables est bloqué par l'inspecteur avec
un rapport actionnable ; le taux de sources vérifiées apparaît dans le dossier et le GUI.

## Brick 4 — Capabilities & choix des modèles (fin de l'env-only)

`GET /api/capabilities` agrège tous les registres (IMAGE_MODELS, VIDEO_MODELS,
VISUAL_MODELS, EMBED_MODELS, extracteurs KG, STT/TTS à promouvoir en registres) **+ le
ToolRegistry OpenMontage** (son axe LOCAL / LOCAL_GPU / API = gratuit/payant natif).
Sélection persistée côté serveur (settings), exposée à l'utilisateur — les env vars
restent le override. **Fait quand** : l'utilisateur choisit ses modèles/outils
(gratuit/payant, dispo/indispo) depuis l'interface sans toucher un terminal.

## Brick 5 — Cross-platform (« n'importe quelle machine »)

Des backends non-Mac derrière les registres existants, même pattern
qu'`openmontage-remotion` : image (stable-diffusion.cpp MIT, ou passerelle LocalAI
MIT), STT (whisper.cpp / faster-whisper), TTS (Piper / Kokoro-onnx CPU), embeddings
(llama.cpp `/v1/embedding`). Chaque backend : probe → 501 propre si absent.
**Fait quand** : la même mission avec assets tourne sur un Linux/Windows sans MLX,
suite offline verte partout.

## Brick 6 — Clients & projets

Taxonomie client / projet / campagne au-dessus du store (le stamp `project_root`
existant est le hook) : champs dans le dossier, endpoints de groupement, migration
douce des missions existantes. **Fait quand** : l'historique se navigue par client et
par campagne, et un livrable appartient à un projet.

## Brick 7 — La boîte magique (refonte UI sur mesure)

Nouvelle application front : **un seul point d'entrée** (« que voulez-vous
produire ? »), brief guidé par secteur/domaine/type de livrable, timeline de mission
vivante, **bibliothèque de livrables** par client, **import** de matériel existant
(docs, images, briefs, vidéos), **export bundle** (PDF / zip média / dossier complet),
i18n FR/EN, panneau modèles (Brick 4). Chaque écran = sa propre spec.
Références UX : AnythingLLM (workspace = projet), Jan (local-first).
**Fait quand** : un utilisateur non technicien produit un livrable complet
(recherche → stratégie → vidéo → export) sans aide.

## Brick 8 — Recettes livrables (mission → production en 1 clic)

Exposer les 13 pipelines OpenMontage + des recettes agence composées (campagne
complète, pitch client, événement clé-en-main, pack contenu social) : une recette
enchaîne mission (départements) → assets (image/voix) → composition (vidéo) → export.
**Fait quand** : « lance-moi une campagne pour X » produit le dossier stratégique ET
les créas associées en une exécution.

## Brick 9 — Multi-CLI réel

codex et gemini validés bout-en-bout sur le contrat Brick 1 (recherche web headless
vérifiée par moteur), opencode ajouté ; matrice de compatibilité moteurs × capacités
publiée dans le README. **Fait quand** : la même mission passe sur deux moteurs avec
dossiers comparables et sources vérifiées (Brick 3) sur chacun.

---

## Invariants (toutes bricks)

Suite offline verte à chaque merge · zéro dépendance runtime du core · frontières
subprocess respectées · opt-in réseau par mission · sécurité (127.0.0.1, pas de CORS
`*`, path guards, clés env-only) · Conventional Commits + PR squash vers `main` ·
veto-loop d'agency-kit jamais modifié en comportement.
