# 📖 Documentation Recyclarr Configurator - Director's Cut

Application moderne en Python et PySide6 pour créer et gérer facilement vos fichiers de configuration `recyclarr.yml` pour Radarr et Sonarr. Suivez ce guide pour installer et utiliser l'application.

---

## 🚀 Installation & Lancement

### Prérequis
*   **Python 3.8+** installé sur votre machine.
*   **pip** (gestionnaire de paquets Python).

### 1. Cloner ou Télécharger
Récupérez les fichiers sources du projet dans un dossier sur votre ordinateur.

### 2. Installer les dépendances
Ouvrez un terminal (PowerShell sous Windows) dans le dossier du projet et lancez :
```powershell
pip install -r requirements.txt
```

### 3. Lancer l'application
Toujours depuis le dossier du projet :
```powershell
python main_gui_app.py
```
*(L'ancien fichier `recyclarr_gui.py` est obsolète, utilisez `main_gui_app.py`)*

> **Note :** Au premier lancement, l'application peut prendre quelques instants pour télécharger les dernières données de TRaSH Guides et Recyclarr.

---

## 🎬 Guide d'Utilisation - Les 4 Actes

L'interface est découpée en **Onglets (Instances)**. Vous pouvez avoir plusieurs onglets pour gérer par exemple `Radarr 4K`, `Radarr 1080p`, `Sonarr Anime`, etc.

Chaque instance est configurée en **4 Actes** :

### 🎭 Acte 1 : Le Scénario (Templates & Base)
C'est ici que vous définissez les bases de votre instance.
*   **Nom de l'instance** : Donnez un nom unique (ex: `radarr-uhd`).
*   **Connexion** : Cliquez sur ✏️ (ou faites clic-droit sur l'onglet) pour entrer l'URL et l'API Key de votre serveur.
*   **Templates** : Sélectionnez un modèle de base (ex: `radarr-quality-definition-movie`).

### 👯 Acte 2 : Le Casting (Includes)
Sélectionnez les ingrédients de votre configuration.
*   **Arbre des Includes** : Cochez les *Quality Definitions* et *Custom Formats* (Trash IDs) que vous souhaitez inclure.
*   **Visualisation** : L'arbre affiche hiérarchiquement tous les fichiers disponibles depuis les templates.

### 🎬 Acte 3 : Mise en Scène (Profils de Qualité)
Créez et personnalisez vos profils de qualité (Quality Profiles).
*   **Nouveau Profil** : Donnez un nom et cliquez sur "Ajouter Profil".
*   **Glisser-Déposer** : Construisez votre profil en glissant les qualités de la liste de droite vers la gauche.
*   **Groupement** : Sélectionnez plusieurs qualités (Ctrl+Clic) et faites Clic-Droit > "Grouper" pour créer un groupe personnalisé (ex: `HD-1080p`).
*   **Paramètres** : Activez *Upgrade Allowed* et définissez le score minimum.

### 🎇 Acte 4 : Effets Spéciaux (Custom Formats)
L'éditeur avancé pour les formats personnalisés (Custom Formats).
*   **Visualisation Claire** : Liste filtrable de tous les formats chargés pour l'instance.
*   **Configuration Détaillée** : 
    *   **Description** : Zone de texte défilante pour lire les détails complets du format.
    *   **Tableau des Scores** : Assignez des scores spécifiques pour chaque profil de qualité.
    *   **Smart Inference** : L'application détecte automatiquement les scores pertinents (ex: `VOSTFR` -> `1000`) même s'ils ne sont pas explicitement liés dans le template, et coche automatiquement la case correspondante.
    *   **Indicateurs Visuels** : Les cases à cocher "Actif" sont clairement visibles (Carré blanc = inactif, Orange = actif).

---

## 🛠️ Barre d'Outils (Haut à Droite)
*   **Navigation** : Utilisez les flèches `◀` et `▶` pour passer d'une instance à l'autre.
*   **+ Ajouter** : Crée une nouvelle instance (Radarr ou Sonarr).
*   **Supprimer** : Supprime l'instance (onglet) actuelle.
*   **Générer YAML** : C'est le but final ! Cliquez pour générer le fichier `recyclarr.yml` complet basé sur tous vos onglets.

---

## ✨ Fonctionnalités Clés
*   **Synchronisation Auto** : Les données (CFs, Templates) sont automatiquement mises à jour depuis GitHub au démarrage.
*   **Mode Sombre** : Interface *Dark Mode* native "Director's Cut".
*   **Icônes Vectorielles** : Utilisation des icônes standards Qt pour une compatibilité maximale.
*   **Score Intelligent** : Calcul automatique des scores basé sur les noms de profils (alias `french` -> `fr`).

---

## 🆘 Dépannage
*   **Crash au démarrage ?** Vérifiez votre connexion internet pour la mise à jour des données.
*   **Score Tronqué ?** L'interface a été corrigée pour afficher les colonnes de score avec une largeur fixe.
