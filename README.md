# Recyclarr Config Generator - Home Cinema Edition 🎬

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.4+-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Application Python avec interface graphique moderne (PySide6) pour générer des fichiers de configuration YAML pour [Recyclarr](https://github.com/recyclarr/recyclarr).

![Interface Preview](https://img.shields.io/badge/interface-dark%20theme-1a1a1f)

## Fonctionnalités ✨

- **🎨 Interface moderne PySide6** avec thème sombre adapté aux passionnés de home cinema
- **📱 Design responsive** avec cartes visuelles pour les instances
- **🔒 Séparation complète Radarr/Sonarr** - Les formats et templates sont filtrés par application
- **⚡ Extraction automatique** des Custom Formats depuis le [TRaSH Guide](https://github.com/TRaSH-Guides/Guides)
- **⚡ Extraction automatique** des templates depuis [recyclarr/config-templates](https://github.com/recyclarr/config-templates)
- **🎯 Gestion intuitive** pour :
  - Gérer plusieurs instances Radarr et Sonarr
  - Sélectionner les templates à inclure (filtrés par app)
  - Créer des profils de qualité avec groupement/dégroupement
  - Choisir les Custom Formats individuellement (radarr ≠ sonarr)
  - Prévisualiser et générer le fichier YAML

## Structure du projet

```
recyclarr-config/
├── trash_cf_extractor.py       # Extraction des Custom Formats TRaSH
├── templates_extractor.py      # Extraction des templates Recyclarr
├── recyclarr_gui.py            # Application GUI complète (PySide6)
├── requirements.txt            # Dépendances Python
├── .gitignore                  # Fichiers à ignorer par Git
├── plans/                      # Documentation d'architecture
│   ├── architecture.md
│   └── architecture-overview.md
└── README.md                   # Documentation
```

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Cloner le dépôt

```bash
git clone https://github.com/VOTRE_USERNAME/recyclarr-config.git
cd recyclarr-config
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Étape 1 : Extraire les données

Avant de lancer l'application GUI, vous devez extraire les données des dépôts GitHub :

```bash
# Extraction des Custom Formats TRaSH
python trash_cf_extractor.py

# Extraction des templates Recyclarr
python templates_extractor.py
```

Ces commandes vont créer les fichiers `custom_formats.json` et `templates.json`.

### Étape 2 : Lancer l'application GUI

```bash
python recyclarr_gui.py
```

### Étape 3 : Configurer vos instances

1. **🎬 Ajouter une instance Radarr** ou **📺 Ajouter une instance Sonarr** :
   - Cliquez sur le bouton "➕ Ajouter" dans la section correspondante
   - **Panneau gauche** : Configurez les informations de base (nom, URL, API key) et sélectionnez un template prédéfini ou personnalisé
   - **Panneau droit** : Gérez les includes, créez des profils de qualité avec groupement de qualités, et ajoutez des Custom Formats

2. **👁️ Générer la prévisualisation** :
   - Cliquez sur "👁️ Prévisualiser YAML" pour voir la configuration générée

3. **💾 Sauvegarder** :
   - Cliquez sur "💾 Sauvegarder YAML" pour exporter le fichier `recyclarr-config.yml`

## 🎨 Caractéristiques de l'interface

- **Thème sombre Home Cinema** : Optimisé pour les environnements de home cinema
- **Code couleur** : 🟠 Orange pour Radarr (Films), 🔵 Bleu pour Sonarr (Séries)
- **Cartes visuelles** : Chaque instance est représentée par une carte avec ses statistiques
- **Groupement de qualités** : Créez des groupes de qualités (ex: "Bluray|WEB 2160p") par simple clic
- **Séparation des données** : Les formats Radarr et Sonarr sont complètement isolés

## Structure du fichier YAML généré

Le fichier généré suit la structure officielle de Recyclarr :

```yaml
# Configuration Recyclarr générée automatiquement

radarr:
  fr-films:
    base_url: http://localhost:7878
    api_key: <API_KEY>
    delete_old_custom_formats: true
    replace_existing_custom_formats: true

    include:
      - template: radarr-quality-definition-movie
      - template: radarr-custom-formats-hd-bluray-web-french-multi-vf

    quality_profiles:
      - name: FR-MULTi-VF-UHD
        reset_unmatched_scores:
          enabled: true
        upgrade:
          allowed: true
          until_quality: Bluray|WEB 2160p
          until_score: 10000
        qualities:
          - name: Bluray|WEB 2160p
            qualities:
              - Bluray-2160p
              - WEBDL-2160p
              - WEBRip-2160p

    custom_formats:
      - trash_ids:
          - 570bc9ebecd92723d2d21500f4be314c  # Remaster
          - eca37840c13c6ef2dd0262b141a5482f  # 4K Remaster
        assign_scores_to:
          - name: FR-MULTi-VF-UHD
          - name: FR-MULTi-VF-HD

sonarr:
  fr-series:
    base_url: http://localhost:8989
    api_key: <API_KEY>
    ...
```

## Dépendances

- Python 3.8+
- PySide6 >= 6.4.0 (interface graphique moderne)
- requests
- pyyaml

## Licence

MIT

## Liens utiles

- [Documentation Recyclarr](https://recyclarr.dev/)
- [TRaSH Guides](https://trash-guides.info/)
- [Recyclarr Config Templates](https://github.com/recyclarr/config-templates)

---

⭐ Si ce projet vous est utile, n'hésitez pas à mettre une étoile sur GitHub !
