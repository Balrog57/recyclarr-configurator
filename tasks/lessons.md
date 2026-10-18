# Leçons Apprises (Memory)

## Concepts et Patterns
- **Architecture GUI** : Le projet utilise une approche par "Actes" pour guider l'utilisateur, ce qui est un excellent pattern pour les configurations complexes.
- **YAML & Commentaires** : L'utilisation de `ruamel.yaml` est cruciale ici pour générer un YAML lisible avec des commentaires explicatifs (noms des CFs).
- **Windows Context** : Le projet est explicitement orienté Windows (PowerShell, Inno Setup).

## Recyclarr v8 & TRaSH Guides Migration
- **Guide-Backed Quality Profiles (`trash_id`)** : Recyclarr v8 a complètement abandonné les templates d'inclusion statiques (`includes/`) dans `recyclarr/config-templates`. Les profils de qualité sont désormais gérés par un `trash_id` immuable adossé directement aux fichiers JSON de `TRaSH-Guides/Guides` (`docs/json/{app}/quality-profiles/*.json`).
- **Nouveau chemin des Profils TRaSH** : Les définitions complètes des profils (qualités autorisées, groupes, cutoff, minFormatScore, formatItems) résident dans `TRaSH-Guides/Guides` sous `docs/json/{app}/quality-profiles/`.
- **Quality Definitions v8** : Les tailles/définitions de qualité sont définies via le bloc `quality_definition: type: movie/series` au lieu d'inclusions externes.
- **Custom Formats & Scores** : La clé pour assigner les scores aux profils dans les blocs `custom_formats` est désormais `assign_scores_to:` (au lieu de l'ancien nœud dupliqué `quality_profiles:`).
- **Extraction haute performance** : Interroger l'API Git Trees de GitHub (`git/trees/master?recursive=1`) permet de lister 600+ fichiers en un seul appel (0.5s) tout en téléchargeant le contenu brut via `raw.githubusercontent.com` sans subir les limites de taux de l'API REST.

- **Options supprimées en v8** : `replace_existing_custom_formats` n'existe plus (le schéma v8 rejette la config). Les `include: - template:` officiels n'existent plus non plus : les packs CF s'écrivent `custom_format_groups: add: - trash_id: ...`.
- **Validation** : valider le YAML généré contre `https://schemas.recyclarr.dev/v8/config-schema.json` (les qualités doivent être des objets `- name: X`, jamais des chaînes).
- **Tests UI** : simuler aussi les changements d'onglets (l'Acte 3 resynchronise les profils) — un test qui ne fait que choisir un template rate ce genre de régression.
- **CF groups `add`** : sans `assign_scores_to`, un groupe n'applique ses scores qu'aux profils de sa liste `include` (silencieusement ignoré sinon). Les groupes FR (« French Anime », « Release Groups French ») n'incluent que « Base Profile » et n'ont aucun CF required/default : il faut `select_all: true` + `assign_scores_to`.
- **Comparer des profils** : `tests/recyclarr_sim.py` simule la résolution Recyclarr (profil guide + groupes + overrides) ; comparer le profil effectif, pas le YAML.
- **Portable (PyInstaller onefile)** : `Path(__file__)` pointe dans `_MEIPASS` (effacé à la fermeture). Écrire à côté de `sys.executable` (`core/paths.py`) et résoudre les chemins au chargement, pas à l'instanciation.
- **Rien en dur** : l'assistant détecte profils (score_set `french-*`, tag `[Anime]`), paliers (nom après le tag), jeux de scores, CF de langue (par nom TRaSH), groupes et critères refusés depuis les données ; un test modifie un score TRaSH et vérifie que la sortie suit.
- **Groupes ajoutés sans CF default/required** : ne pas mettre `select_all` à l'aveugle (« Language Profiles » contient « Language: Not English » -10000). Sélectionner les CF scorés pour le score_set + ceux utilisés par les profils de la même famille (`family_cfs`).
