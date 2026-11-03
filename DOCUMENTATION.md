# 📖 Recyclarr Configurator Documentation - Director's Cut

A modern Python and PySide6 application to easily create and manage your `recyclarr.yml` configuration files for Radarr and Sonarr. Follow this guide to install and use the application.

---

## 🚀 Installation & Launch

### Prerequisites
*   **Python 3.8+** installed on your machine.
*   **pip** (Python package manager).

### Portable version (Windows, no Python needed)
Download `RecyclarrConfigurator.exe` from the [Releases](https://github.com/Balrog57/recyclarr-configurator/releases) page and put it in any folder you can write to (USB key included). Nothing is installed:
*   TRaSH data is refreshed at startup into a `data/` folder **next to the .exe**.
*   Offline first launch: the data bundled in the .exe at release time is used.
*   **Generate YAML** asks where to save, defaulting to `recyclarr.yml` next to the .exe.

### 1. Clone or Download
Download the project source files into a folder on your computer.

### 2. Install Dependencies
Open a terminal (PowerShell on Windows) in the project folder and run:
```powershell
pip install -r requirements.txt
```

### 3. Launch the Application
From the project folder:
```powershell
python main_gui_app.py
```

> **Note:** On the first launch, the application may take a moment to download the latest data from TRaSH Guides and Recyclarr.

---

## 🎬 User Guide - The 4 Acts

The interface is divided into **Tabs (Instances)**. You can have multiple tabs to manage, for example, `Radarr 4K`, `Radarr 1080p`, `Sonarr Anime`, etc.

Each instance is configured in **4 Acts**:

### 🎭 Act 1: The Script (Templates & Base)
This is where you define the foundation of your instance.
*   **Instance Name**: Give it a unique name (e.g., `radarr-uhd`).
*   **Connection**: Right-click on the tab to enter your server's URL and API Key.
*   **Quality Definition Type**: The types found in TRaSH Guides (e.g. `movie`, `anime`, `sqp-*` for Radarr; `series`, `anime` for Sonarr), written as `quality_definition: type:`.
*   **Templates**: Official Recyclarr v8 templates (e.g., `french-multi-vf-hd-bluray-web`, `hd-bluray-web`) or manual Custom mode.
*   **⚡ Assistant rapide**: Pick content (films/séries or animés), a quality tier, the language order (e.g. MULTi > VF > VOSTFR, or MULTi > VOSTFR for anime) and which criteria rejected by TRaSH you accept (e.g. x265, AV1). It loads the matching TRaSH French profile (or the TRaSH French anime recipe) and sets the scores in Act 4. Unchecked languages are rejected.
    *   Everything is detected from the TRaSH data downloaded at startup: quality tiers, score sets, language custom formats, CF groups, rejected criteria and their scores. When TRaSH adds or re-scores something, the wizard follows.
    *   How it works: Radarr/Sonarr do not parse `VOSTFR` as French, so a VOSTFR release counts as original audio; the `VOSTFR` custom format lifts it back above plain VO.
    *   Prerequisite (TRaSH): set the indexers' *Multi Languages* option to `Original` + `French`.

### 👯 Act 2: The Casting (TRaSH Guides)
Select the ingredients for your configuration directly from TRaSH Guides (Recyclarr v8):
*   **Quality Profiles**: Guide-backed profiles from TRaSH Guides (e.g., `[French MULTi.VF] HD Bluray + WEB`), exported as `trash_id`.
*   **Format Packs (CF groups)**: groups marked **(auto)** are synced by Recyclarr for the checked profiles; uncheck one to opt out (`skip`). Check any other group to add it (`add`): the app adds `assign_scores_to` / `select` when Recyclarr needs them to apply the group to your profiles.

### 🎬 Act 3: Staging (Quality Profiles)
Create and customize your Quality Profiles.
*   **Guide-Backed Profiles**: Retain their TRaSH ID (`trash_id`) so Recyclarr automatically syncs upstream recommendations. Only what you change is written to the YAML (upgrade, scores, score set); editing the qualities of such a profile writes them as an explicit override, which then stops following TRaSH.
*   **New Profile**: Create custom profiles from scratch with custom qualities.
*   **Drag & Drop**: Build your profile by dragging qualities from the right list to the left tree.
*   **Grouping**: Select multiple qualities and Right-Click > "Group" to create a custom group (e.g., `HD-1080p`).
*   **Safety**: Individual qualities cannot be nested inside each other; only folders (groups) allow children.

### 🎇 Act 4: Special Effects (Custom Formats)
The advanced editor for Custom Formats.
*   **Clear Visualization**: Filterable list of all formats loaded for the instance.
*   **Detailed Configuration**: 
    *   **Description**: Scrollable text area to read full format details.
    *   **Score Table**: Assign specific scores for each quality profile via `assign_scores_to`.
    *   **Guide Scores**: Formats in **bold** are synced by TRaSH Guides in your profiles; their score is the one Recyclarr will apply (profile + CF groups + score set). Check a profile to override it.
    *   **YAML Comments**: Names of chosen formats will be added as comments in your final file!

---

## 🛠️ Toolbar (Top Right)
*   **Navigation**: Use the `◀` and `▶` arrows to switch between instances.
*   **+ Add**: Create a new instance (Radarr or Sonarr).
*   **Delete**: Remove the current instance (tab).
*   **Load YAML**: Import an existing `config.yml` (or `.yaml`) to edit your current instances.
*   **Generate YAML**: The final goal! Choose where to save the complete `recyclarr.yml` file (Recyclarr v8 format).

---

## ✨ Key Features
*   **Auto-Sync**: Data (CFs, Templates) is automatically updated from GitHub at startup.
*   **Dark Mode**: Immersive modern "Director's Cut" interface.
*   **Smart Scoring**: Automatic detection of profile-specific scores.
*   **Clean Export**: Intelligent grouping in the YAML file for a minimalist and readable configuration.

---

## 🆘 Troubleshooting
*   **Crash at startup?** Check your internet connection for the initial data update (the portable .exe falls back to its bundled data).
*   **Profiles overlapping?** Use groups to bundle qualities, otherwise they will remain as individual items.
