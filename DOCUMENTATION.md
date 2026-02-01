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
*   **Connexion** : Cliquez sur ✏️ pour entrer l'URL et l'API Key de votre serveur Radarr/Sonarr.
*   **Templates** : Sélectionnez un ou plusieurs modèles de configuration pré-existants (basés sur les *Recyclarr Config Templates*).
    *   *Exemple : `radarr-quality-definition-movie` est essentiel pour définir les qualités.*

### 👯 Acte 2 : Le Casting (Profils de Qualité)
Créez vos propres profils de qualité.
*   **Nouveau Profil** : Donnez un nom et cliquez sur "Ajouter Profil".
*   **Paramètres** : Activez *Upgrade Allowed* et définissez le score minimum/limite.
*   **Groupes de Qualités** : Glissez-déposez les qualités disponibles vers votre profil.
    *   **Astuce** : Sélectionnez plusieurs qualités avec `Ctrl+Clic` ou `Shift+Clic`, puis clic-droit > "Grouper" pour créer un groupe (ex: `Bluray-1080p` + `WEBDL-1080p` -> `HD-1080p`).

### 🎬 Acte 3 : Mise en Scène (Custom Formats)
Sélectionnez les formats personnalisés (Custom Formats) issus des **TRaSH Guides**.
*   **Arbre de gauche** : Naviguez dans les catégories (Audio, Video, Langues...). Cochez les formats que vous voulez utiliser.
*   **Liste de droite** : Ajustez le score de chaque format sélectionné.
    *   *Important* : Si vous ne donnez pas de score, Recyclarr utilisera le score par défaut du guide TRaSH.

### 🎇 Acte 4 : Effets Spéciaux (Settings Avancés)
Options supplémentaires pour l'instance.
*   **Manual Configuration** : Ajoutez ici des lignes YAML spécifiques si l'interface ne couvre pas un besoin précis.

---

## 🛠️ Barre d'Outils (Haut à Droite)
*   **Navigation** : Utilisez les flèches `◀` et `▶` pour passer d'une instance à l'autre.
*   **+ Ajouter** : Crée une nouvelle instance (Radarr ou Sonarr).
*   **Supprimer** : Supprime l'instance (onglet) actuelle.
*   **Générer YAML** : C'est le but final ! Cliquez pour générer le fichier `recyclarr.yml` complet basé sur tous vos onglets.

---

## ✨ Fonctionnalités Clés
*   **Synchronisation Auto** : Les données (CFs, Templates) sont automatiquement mises à jour depuis GitHub au démarrage (désactivable dans le code).
*   **Mode Sombre** : Interface *Dark Mode* native.
*   **Icônes Vectorielles** : Utilisation des icônes standards Qt pour une compatibilité maximale.
*   **Navigation Fluide** : Système d'onglets avancé avec navigation par boutons lorsque vous avez beaucoup d'instances.

---

## 🆘 Dépannage
*   **Crash au démarrage ?** Vérifiez votre connexion internet pour la mise à jour des données.
*   **Boutons invisibles ?** Vérifiez que vous avez bien la dernière version du code (les correctifs d'icônes ont été appliqués).
