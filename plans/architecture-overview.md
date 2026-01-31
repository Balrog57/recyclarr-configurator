# Architecture du Projet Recyclarr Config Generator

## Vue d'ensemble

Ce projet génère des fichiers de configuration YAML pour [Recyclarr](https://github.com/recyclarr/recyclarr) avec une interface graphique intuitive.

## Architecture en 3 couches

```
┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE PRÉSENTATION                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              recyclarr_gui.py (GUI Tkinter)              │    │
│  │  • Fenêtre principale avec gestion des instances         │    │
│  │  • Éditeur d'instance (templates + custom formats)       │    │
│  │  • Prévisualisation YAML en temps réel                   │    │
│  │  • Export vers fichier .yml                              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE MÉTIER                               │
│  ┌───────────────────────┐  ┌───────────────────────────────┐   │
│  │   YAMLGenerator       │  │      InstanceConfig            │   │
│  │   • Génère YAML       │  │      • Configuration instance  │   │
│  │   • Structure données │  │      • Templates + CFs         │   │
│  └───────────────────────┘  └───────────────────────────────┘   │
│  ┌───────────────────────┐  ┌───────────────────────────────┐   │
│  │     DataManager       │  │  CustomFormatSelection         │   │
│  │   • Charge JSON       │  │  • CF sélectionné avec scores  │   │
│  │   • Indexe CF par ID  │  │                                │   │
│  └───────────────────────┘  └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE DONNÉES (Sources)                      │
│  ┌───────────────────────┐  ┌───────────────────────────────┐   │
│  │  custom_formats.json  │  │      templates.json            │   │
│  │  (405 CF indexés)     │  │  • 12 templates Radarr         │   │
│  │                       │  │  • 10 templates Sonarr         │   │
│  │ Source: TRaSH Guides  │  │  • 72 includes (QF/QP/CF)      │   │
│  │ Extrait par:          │  │                                │   │
│  │ trash_cf_extractor.py │  │ Source: config-templates       │   │
│  │                       │  │ Extrait par:                   │   │
│  │                       │  │ templates_extractor.py         │   │
│  └───────────────────────┘  └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Flux de données

1. **Extraction** (scripts de mise à jour)
   - trash_cf_extractor.py → custom_formats.json (TRaSH Guides)
   - templates_extractor.py → templates.json (config-templates)

2. **Chargement** (au démarrage GUI)
   - DataManager charge les 2 fichiers JSON
   - Indexation des CF par trash_id pour accès rapide

3. **Configuration** (utilisateur)
   - Création d'instances Radarr/Sonarr
   - Sélection des templates à inclure
   - Sélection des Custom Formats individuels
   - Définition des scores par profil

4. **Génération** (export YAML)
   - YAMLGenerator structure les données
   - Export au format Recyclarr compatible

## Structure YAML générée

```yaml
# Exemple de sortie
radarr:
  instance-1:
    base_url: http://localhost:7878
    api_key: xxx
    delete_old_custom_formats: true
    include:
      - template: radarr-quality-definition-movie
      - template: radarr-quality-profile-hd-bluray-web
    custom_formats:
      - trash_ids: ["id1", "id2"]
        assign_scores_to:
          - name: "Profile HD"

sonarr:
  instance-1:
    # ...
```

## Fichiers du projet

| Fichier | Description | Lignes |
|---------|-------------|--------|
| trash_cf_extractor.py | Extrait les CF du TRaSH Guides | 450 |
| templates_extractor.py | Extrait les templates Recyclarr | 250 |
| recyclarr_gui.py | Application GUI complète | 637 |
| custom_formats.json | Cache des CF (généré) | - |
| templates.json | Cache des templates (généré) | - |
| requirements.txt | Dépendances Python | - |
| README.md | Documentation utilisateur | - |
| plans/architecture.md | Documentation technique | - |
