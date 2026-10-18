# Planification et Suivi - Migration Recyclarr v8 & TRaSH Guides

## Objectifs de la Session
- [x] Étape 1 : Mise à jour de l'extracteur de données (`utils/templates_extractor.py`) pour extraire les profils de qualité et définitions depuis le nouveau chemin `TRaSH-Guides/Guides` (`docs/json/{app}/quality-profiles/`) au lieu des includes obsolètes de `config-templates`.
- [x] Étape 2 : Adaptation des modèles (`core/models.py`) pour intégrer `trash_id` dans `QualityProfile` et `quality_definition_type` dans `InstanceConfig`.
- [x] Étape 3 : Mise à niveau de `core/data_manager.py` pour indexer les profils TRaSH par `trash_id`/nom et résoudre les templates v8 avec leurs profils et CFs.
- [x] Étape 4 : Mise à jour de l'UI (`ui/widgets/include_tree.py`, `ui/widgets/profile_builder.py`, `main_gui_app.py`) pour afficher les profils TRaSH Guide, synchroniser les actes et gérer les profils adossés au guide (`trash_id`).
- [x] Étape 5 : Refonte du générateur YAML (`core/yaml_generator.py`) pour produire une configuration Recyclarr v8 valide (`quality_definition`, `quality_profiles` avec `trash_id`, `assign_scores_to`, suppression des `include` obsolètes).
- [x] Étape 6 : Création d'une suite de tests automatisés (`tests/`) et validation complète de bout en bout (extraction, génération Radarr/Sonarr, import/export).
- [x] Étape 7 : Documentation des apprentissages dans `tasks/lessons.md`.

## Implémentation Détaillée
1. **Extraction de données** :
   - Pointer vers `TRaSH-Guides/Guides` pour `docs/json/radarr/quality-profiles` et `docs/json/sonarr/quality-profiles`.
   - Extraire les templates de `recyclarr/config-templates` (`radarr/templates`, `sonarr/templates`).
   - Mettre à jour `data/templates.json` avec les profils complets (trash_id, items de qualité, cutoff, scores, description).
2. **Gestionnaire de données & Modèles** :
   - Stocker `trash_id` sur chaque `QualityProfile`.
   - Méthodes d'accès rapide par `trash_id` et par nom dans `DataManager`.
   - Résolution automatique des `trash_id` lorsqu'un template est choisi en Acte 1.
3. **Interface Utilisateur (4 Actes)** :
   - Acte 1 : Sélection de template ou mode manuel -> pré-remplit le type de qualité et charge le profil TRaSH correspondant.
   - Acte 2 : Arbre des includes affichant les profils TRaSH Guides et groupes de formats disponibles.
   - Acte 3 : Arborescence des qualités issues du JSON de TRaSH Guides avec support de `trash_id`.
   - Acte 4 : Association dynamique des scores aux profils actifs.
4. **Génération YAML (v8)** :
   - Bloc `quality_definition: type: movie/series`.
   - Bloc `quality_profiles:` avec `trash_id: <id>` (ou profil personnalisé si manuel).
   - Bloc `custom_formats:` avec `assign_scores_to:`.
5. **Tests & Validation** :
   - Tests pytest pour l'extraction, la résolution des profils, la génération YAML et le rechargement.

