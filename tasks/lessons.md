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
