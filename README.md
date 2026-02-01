# Recyclarr Configurator - Director's Cut 🎬

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.4+-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**L'outil ultime pour configurer Recyclarr.**
Application graphique moderne (PySide6) pour générer des fichiers de configuration YAML pour [Recyclarr](https://github.com/recyclarr/recyclarr), optimisée pour les cinéphiles exigeants.

![Interface Screenshot](assets/screenshot.png)

---

## 🌟 Nouveautés "Director's Cut"

Cette version révisée apporte une refonte complète de l'expérience utilisateur, structurée en **4 Actes** pour une configuration intuitive :
*   **Acte 1 - Le Scénario** : Paramètres de base et Templates.
*   **Acte 2 - Le Casting** : Bibliothèques d'Includes (Custom Formats, Quality Defs).
*   **Acte 3 - Mise en Scène** : Création de profils de qualité avancés (Glisser-Déposer, Groupes).
*   **Acte 4 - Effets Spéciaux** : Éditeur de Custom Formats avec inférence intelligente des scores.

## ✨ Fonctionnalités

*   **🎨 Interface "Dark Cinema"** : Thème sombre immersif et responsive.
*   **📱 Gestion Multi-Instances** : Onglets dynamiques pour gérer Radarr 4K, Radarr 1080p, Sonarr, etc.
*   **🔄 Sync Auto** : Téléchargement automatique des dernières données TRaSH Guides au démarrage.
*   **🧠 Smart Score Inference** : Assignation automatique intelligente des scores pour les formats personnalisés (détecte les alias comme "french" -> "fr" et coche automatiquement les cases pertinentes).
*   **👁️ Visualisation Améliorée** : Checkbox à contraste élevé et colonnes ajustées pour une lisibilité parfaite.
*   **📂 Template Deep Scan** : Chargement récursif complet de tous les templates et includes.
*   **🖱️ Drag & Drop** : Groupement facile des qualités (ex: Bluray + WebDL).
*   **⚡ Performance** : Navigation fluide et icônes vectorielles standardisées.

## 🚀 Démarrage Rapide

1.  **Installation**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Lancement**
    ```bash
    python main_gui_app.py
    ```

👉 **Pour plus de détails, consultez la [DOCUMENTATION COMPLÈTE](DOCUMENTATION.md).**

## 📂 Structure du Projet

```
recyclarr-config/
├── core/                   # Cœur logique (DataManager, Models)
├── ui/                     # (Optionnel) Composants UI
├── main_gui_app.py         # Point d'entrée principal
├── DOCUMENTATION.md        # Guide utilisateur détaillé
├── requirements.txt        # Dépendances
└── ...
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une Issue ou une Pull Request.

## 📄 Licence

MIT

---
*Fait avec ❤️ pour la communauté Home Server.*
