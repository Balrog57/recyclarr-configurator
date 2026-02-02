# 📖 Recyclarr Configurator Documentation - Director's Cut

A modern Python and PySide6 application to easily create and manage your `recyclarr.yml` configuration files for Radarr and Sonarr. Follow this guide to install and use the application.

---

## 🚀 Installation & Launch

### Prerequisites
*   **Python 3.8+** installed on your machine.
*   **pip** (Python package manager).

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
*   **Templates**: Select a base model (e.g., `radarr-quality-definition-movie`).

### 👯 Act 2: The Casting (Includes)
Select the ingredients for your configuration.
*   **Include Tree**: Check the *Quality Definitions* and *Custom Formats* (Trash IDs) you want to include.
*   **Visualization**: The tree hierarchically displays all files available from the templates.

### 🎬 Act 3: Staging (Quality Profiles)
Create and customize your Quality Profiles.
*   **New Profile**: Give it a name and build your list.
*   **Drag & Drop**: Build your profile by dragging qualities from the right list to the left tree.
*   **Grouping**: Select multiple qualities and Right-Click > "Group" to create a custom group (e.g., `HD-1080p`).
*   **Safety**: Individual qualities cannot be nested inside each other; only folders (groups) allow children.

### 🎇 Act 4: Special Effects (Custom Formats)
The advanced editor for Custom Formats.
*   **Clear Visualization**: Filterable list of all formats loaded for the instance.
*   **Detailed Configuration**: 
    *   **Description**: Scrollable text area to read full format details.
    *   **Score Table**: Assign specific scores for each quality profile.
    *   **Smart Inference**: The app automatically detects relevant scores (e.g., `VOSTFR` -> `1000`) based on profile names.
    *   **YAML Comments**: Names of chosen formats will be added as comments in your final file!

---

## 🛠️ Toolbar (Top Right)
*   **Navigation**: Use the `◀` and `▶` arrows to switch between instances.
*   **+ Add**: Create a new instance (Radarr or Sonarr).
*   **Delete**: Remove the current instance (tab).
*   **Generate YAML**: The final goal! Click to generate the complete `recyclarr.yml` file.

---

## ✨ Key Features
*   **Auto-Sync**: Data (CFs, Templates) is automatically updated from GitHub at startup.
*   **Dark Mode**: Immersive modern "Director's Cut" interface.
*   **Smart Scoring**: Automatic detection of profile-specific scores.
*   **Clean Export**: Intelligent grouping in the YAML file for a minimalist and readable configuration.

---

## 🆘 Troubleshooting
*   **Crash at startup?** Check your internet connection for the initial data update.
*   **Profiles overlapping?** Use groups to bundle qualities, otherwise they will remain as individual items.
