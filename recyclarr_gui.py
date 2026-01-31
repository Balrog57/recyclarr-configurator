#!/usr/bin/env python3
"""
Recyclarr Config Generator - GUI Application avec PySide6

Application graphique moderne pour générer des fichiers de configuration YAML
pour Recyclarr en utilisant les templates officiels et les Custom Formats
du TRaSH Guide.

Thème: Home Cinema Dark - Interface sombre et élégante pour les passionnés
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QLinearGradient, QBrush
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QFrame, QSplitter,
    QDialog, QDialogButtonBox, QScrollArea, QTextEdit, QFileDialog,
    QMessageBox, QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox,
    QGridLayout, QStackedWidget, QProgressBar, QStatusBar, QMenuBar, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGraphicsDropShadowEffect, QToolButton, QStyle, QRadioButton, QButtonGroup,
    QSizePolicy
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES DE STYLE - Thème Home Cinema
# ============================================================================

class CinemaTheme:
    """Thème sombre élégant pour passionnés de home cinema."""
    
    # Couleurs principales
    BACKGROUND = "#1a1a1f"
    SURFACE = "#25252d"
    SURFACE_LIGHT = "#2d2d38"
    PRIMARY = "#ff6b35"  # Orange chaud comme un projecteur
    PRIMARY_DARK = "#e55a2b"
    SECONDARY = "#4a9eff"  # Bleu électrique
    ACCENT = "#ffd700"  # Or pour les highlights
    
    # Texte
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0b0"
    TEXT_DISABLED = "#606070"
    
    # État
    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    INFO = "#2196f3"
    
    # Bordures
    BORDER = "#3a3a48"
    BORDER_FOCUS = "#ff6b35"
    
    # Radarr vs Sonarr colors
    RADARR_COLOR = "#ff6b35"  # Orange
    SONARR_COLOR = "#4a9eff"  # Bleu


# Stylesheet global
GLOBAL_STYLESHEET = f"""
QMainWindow {{
    background-color: {CinemaTheme.BACKGROUND};
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: {CinemaTheme.BACKGROUND};
    color: {CinemaTheme.TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 13px;
}}

QGroupBox {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {CinemaTheme.PRIMARY};
}}

QPushButton {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {CinemaTheme.PRIMARY_DARK};
}}

QPushButton:pressed {{
    background-color: {CinemaTheme.PRIMARY};
}}

QPushButton:disabled {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_DISABLED};
}}

QPushButton#secondary {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
}}

QPushButton#secondary:hover {{
    background-color: {CinemaTheme.BORDER};
}}

QPushButton#success {{
    background-color: {CinemaTheme.SUCCESS};
    color: white;
}}

QPushButton#success:hover {{
    background-color: #45a049;
}}

QPushButton#danger {{
    background-color: {CinemaTheme.ERROR};
    color: white;
}}

QPushButton#danger:hover {{
    background-color: #d32f2f;
}}

QLineEdit {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {CinemaTheme.PRIMARY};
}}

QLineEdit:focus {{
    border: 2px solid {CinemaTheme.PRIMARY};
}}

QCheckBox {{
    color: {CinemaTheme.TEXT_PRIMARY};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid {CinemaTheme.BORDER};
    background-color: {CinemaTheme.SURFACE};
}}

QCheckBox::indicator:checked {{
    background-color: {CinemaTheme.PRIMARY};
    border-color: {CinemaTheme.PRIMARY};
}}

QRadioButton {{
    color: {CinemaTheme.TEXT_PRIMARY};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid {CinemaTheme.BORDER};
    background-color: {CinemaTheme.SURFACE};
}}

QRadioButton::indicator:checked {{
    background-color: {CinemaTheme.PRIMARY};
    border-color: {CinemaTheme.PRIMARY};
}}

QListWidget {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 0;
}}

QListWidget::item:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}

QListWidget::item:hover {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
}}

QListWidget::item:selected:hover {{
    background-color: {CinemaTheme.PRIMARY_DARK};
}}

QTreeWidget {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}

QTreeWidget::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}

QTreeWidget::item:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}

QTreeWidget::item:hover {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
}}

QHeaderView::section {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_PRIMARY};
    padding: 8px;
    border: none;
    font-weight: bold;
}}

QScrollBar:vertical {{
    background-color: {CinemaTheme.SURFACE};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {CinemaTheme.BORDER};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {CinemaTheme.PRIMARY};
}}

QScrollBar:horizontal {{
    background-color: {CinemaTheme.SURFACE};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {CinemaTheme.BORDER};
    border-radius: 6px;
    min-width: 30px;
}}

QTextEdit {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
}}

QLabel {{
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QLabel#title {{
    font-size: 24px;
    font-weight: bold;
    color: {CinemaTheme.PRIMARY};
}}

QLabel#subtitle {{
    font-size: 16px;
    color: {CinemaTheme.TEXT_SECONDARY};
}}

QLabel#radarr-label {{
    color: {CinemaTheme.RADARR_COLOR};
    font-weight: bold;
    font-size: 14px;
}}

QLabel#sonarr-label {{
    color: {CinemaTheme.SONARR_COLOR};
    font-weight: bold;
    font-size: 14px;
}}

QTabWidget::pane {{
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    background-color: {CinemaTheme.SURFACE};
}}

QTabBar::tab {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_SECONDARY};
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: {CinemaTheme.BORDER};
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QComboBox {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 150px;
}}

QComboBox:hover {{
    border-color: {CinemaTheme.PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox QAbstractItemView {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
    selection-background-color: {CinemaTheme.PRIMARY};
}}

QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {CinemaTheme.SURFACE};
    text-align: center;
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QProgressBar::chunk {{
    background-color: {CinemaTheme.PRIMARY};
    border-radius: 4px;
}}

QStatusBar {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_SECONDARY};
}}

QMenuBar {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
}}

QMenuBar::item:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}

QMenu {{
    background-color: {CinemaTheme.SURFACE};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
}}

QMenu::item:selected {{
    background-color: {CinemaTheme.PRIMARY};
    color: white;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    padding: 8px;
    border-radius: 4px;
}}

QToolButton:hover {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
}}

QSplitter::handle {{
    background-color: {CinemaTheme.BORDER};
}}

QSplitter::handle:horizontal {{
    width: 4px;
}}

QSplitter::handle:vertical {{
    height: 4px;
}}

QFrame#card {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 8px;
}}

QFrame#radarr-card {{
    background-color: {CinemaTheme.SURFACE};
    border: 2px solid {CinemaTheme.RADARR_COLOR};
    border-radius: 8px;
}}

QFrame#sonarr-card {{
    background-color: {CinemaTheme.SURFACE};
    border: 2px solid {CinemaTheme.SONARR_COLOR};
    border-radius: 8px;
}}

QFrame#section-frame {{
    background-color: {CinemaTheme.SURFACE};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 8px;
    padding: 12px;
}}

QSpinBox {{
    background-color: {CinemaTheme.SURFACE_LIGHT};
    color: {CinemaTheme.TEXT_PRIMARY};
    border: 1px solid {CinemaTheme.BORDER};
    border-radius: 4px;
    padding: 4px;
}}
"""


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CustomFormatSelection:
    """Représente la sélection d'un Custom Format."""
    trash_id: str
    name: str
    enabled: bool = True
    scores: dict[str, int] = field(default_factory=dict)


@dataclass
class InstanceConfig:
    """Configuration d'une instance Radarr ou Sonarr."""
    name: str
    base_url: str = ""
    api_key: str = ""
    delete_old_custom_formats: bool = True
    replace_existing_custom_formats: bool = True
    # Structure pour le YAML
    includes: list[str] = field(default_factory=list)  # Templates inclus
    quality_profiles: list[dict] = field(default_factory=list)  # Profils de qualité
    custom_formats: list[dict] = field(default_factory=list)  # CFs avec scores


@dataclass
class RecyclarrConfiguration:
    """Configuration complète Recyclarr."""
    radarr_instances: list[InstanceConfig] = field(default_factory=list)
    sonarr_instances: list[InstanceConfig] = field(default_factory=list)


# ============================================================================
# GESTIONNAIRE DE DONNÉES
# ============================================================================

class DataManager:
    """Gestionnaire des données JSON (custom formats et templates)."""

    def __init__(self, custom_formats_path: str = "custom_formats.json",
                 templates_path: str = "templates.json"):
        self.custom_formats_path = Path(custom_formats_path)
        self.templates_path = Path(templates_path)
        self.custom_formats: dict[str, Any] = {}
        self.templates: dict[str, Any] = {}
        self.cf_by_id: dict[str, dict] = {}  # Index par trash_id

    def load_data(self) -> bool:
        """Charge les données JSON."""
        try:
            # Charger custom_formats.json
            if self.custom_formats_path.exists():
                with open(self.custom_formats_path, "r", encoding="utf-8") as f:
                    self.custom_formats = json.load(f)
                self._index_custom_formats()
                total = self.custom_formats.get('metadata', {}).get('total_formats', 0)
                logger.info(f"Chargé {total} custom formats")
            else:
                logger.warning(f"Fichier non trouvé: {self.custom_formats_path}")
                return False

            # Charger templates.json
            if self.templates_path.exists():
                with open(self.templates_path, "r", encoding="utf-8") as f:
                    self.templates = json.load(f)
                logger.info("Templates chargés avec succès")
            else:
                logger.warning(f"Fichier non trouvé: {self.templates_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            return False

    def _index_custom_formats(self):
        """Crée un index des custom formats par trash_id."""
        for app, app_data in self.custom_formats.get("custom_formats", {}).items():
            if app == "guide-only":
                continue
            for cf in app_data.get("formats", []):
                trash_id = cf.get("trash_id")
                if trash_id:
                    self.cf_by_id[trash_id] = {**cf, "app": app}

    def get_cf_by_id(self, trash_id: str) -> dict | None:
        """Récupère un custom format par son trash_id."""
        return self.cf_by_id.get(trash_id)

    def get_cf_name(self, trash_id: str) -> str:
        """Récupère le nom d'un custom format par son trash_id."""
        cf = self.cf_by_id.get(trash_id)
        return cf.get("name", trash_id) if cf else trash_id

    def get_custom_formats_for_app(self, app: str) -> list[dict]:
        """Récupère les custom formats pour une application spécifique."""
        return self.custom_formats.get("custom_formats", {}).get(app, {}).get("formats", [])

    def get_templates_for_app(self, app: str) -> list[dict]:
        """Récupère les templates pour une application spécifique."""
        return self.templates.get(app, {}).get("templates", [])

    def get_template_by_name(self, app: str, name: str) -> dict | None:
        """Récupère un template spécifique par son nom."""
        templates = self.get_templates_for_app(app)
        for template in templates:
            if template.get("name") == name:
                return template
        return None

    def get_includes_by_type(self, app: str, include_type: str) -> list[dict]:
        """Récupère les includes d'un type spécifique."""
        includes = self.templates.get(app, {}).get("includes", {})
        return includes.get(include_type, [])


# ============================================================================
# GÉNÉRATEUR YAML
# ============================================================================

class YAMLGenerator:
    """Générateur de configuration YAML Recyclarr."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def generate(self, config: RecyclarrConfiguration) -> str:
        """Génère le contenu YAML complet."""
        output = {}

        # Générer Radarr
        if config.radarr_instances:
            output["radarr"] = self._generate_app_section(config.radarr_instances)

        # Générer Sonarr
        if config.sonarr_instances:
            output["sonarr"] = self._generate_app_section(config.sonarr_instances)

        # Convertir en YAML
        yaml_content = yaml.dump(
            output,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
            indent=2,
        )

        # Ajouter un header
        header = "# Configuration Recyclarr générée automatiquement\n"
        header += "# Documentation: https://recyclarr.dev\n\n"

        return header + yaml_content

    def _generate_app_section(self, instances: list[InstanceConfig]) -> dict[str, Any]:
        """Génère la section pour une application (radarr ou sonarr)."""
        app_section = {}

        for instance in instances:
            instance_config = self._generate_instance_config(instance)
            if instance_config:
                app_section[instance.name] = instance_config

        return app_section

    def _generate_instance_config(self, instance: InstanceConfig) -> dict[str, Any]:
        """Génère la configuration d'une instance."""
        config = {
            "base_url": instance.base_url if instance.base_url else "http://localhost:7878",
            "api_key": instance.api_key if instance.api_key else "VOTRE_API_KEY",
        }

        # Options de mise à jour
        if instance.delete_old_custom_formats:
            config["delete_old_custom_formats"] = True
        if instance.replace_existing_custom_formats:
            config["replace_existing_custom_formats"] = True

        # Includes (templates)
        if instance.includes:
            config["include"] = [{"template": tmpl} for tmpl in instance.includes]

        # Quality profiles
        if instance.quality_profiles:
            config["quality_profiles"] = instance.quality_profiles

        # Custom formats
        if instance.custom_formats:
            config["custom_formats"] = instance.custom_formats

        return config


# ============================================================================
# WIDGETS POUR CONFIGURATION VISUELLE
# ============================================================================

class TemplateSelectorWidget(QWidget):
    """Widget pour sélectionner UN template (prédéfini ou custom) avec affichage du contenu."""
    
    template_changed = Signal(str, list)  # Nom du template, liste des includes
    
    def __init__(self, data_manager: DataManager, app: str, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.app = app
        self.selected_template = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Groupe Template
        template_group = QGroupBox("Template de base")
        template_layout = QVBoxLayout(template_group)
        
        # Radio buttons pour choisir le type
        radio_layout = QHBoxLayout()
        self.radio_predefined = QRadioButton("Template prédéfini")
        self.radio_custom = QRadioButton("Template personnalisé")
        self.radio_predefined.setChecked(True)
        
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.radio_predefined)
        self.radio_group.addButton(self.radio_custom)
        
        radio_layout.addWidget(self.radio_predefined)
        radio_layout.addWidget(self.radio_custom)
        radio_layout.addStretch()
        template_layout.addLayout(radio_layout)
        
        # Sélecteur de template prédéfini
        self.predefined_widget = QWidget()
        predefined_layout = QVBoxLayout(self.predefined_widget)
        predefined_layout.setContentsMargins(0, 0, 0, 0)
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(300)
        self._populate_templates()
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        predefined_layout.addWidget(self.template_combo)
        
        # Description du template sélectionné
        self.template_desc = QLabel("Sélectionnez un template pour voir sa description")
        self.template_desc.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        self.template_desc.setWordWrap(True)
        predefined_layout.addWidget(self.template_desc)
        
        # Affichage des includes du template
        self.includes_preview = QLabel("")
        self.includes_preview.setStyleSheet(f"color: {CinemaTheme.SECONDARY}; font-size: 10px; padding: 4px; background-color: {CinemaTheme.SURFACE_LIGHT}; border-radius: 4px;")
        self.includes_preview.setWordWrap(True)
        predefined_layout.addWidget(self.includes_preview)
        
        template_layout.addWidget(self.predefined_widget)
        
        # Widget pour template personnalisé
        self.custom_widget = QWidget()
        custom_layout = QVBoxLayout(self.custom_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        
        custom_info = QLabel("Vous pourrez sélectionner manuellement les includes dans la section de droite")
        custom_info.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        custom_info.setWordWrap(True)
        custom_layout.addWidget(custom_info)
        
        self.custom_widget.setVisible(False)
        template_layout.addWidget(self.custom_widget)
        
        # Connecter les radio buttons
        self.radio_predefined.toggled.connect(self._on_mode_changed)
        
        layout.addWidget(template_group)
        
        # Émettre le template par défaut
        self._on_template_changed(0)
    
    def _populate_templates(self):
        """Remplit le combo avec les templates disponibles."""
        self.template_combo.clear()
        self.template_combo.addItem("-- Choisir un template --", None)
        
        templates = self.data_manager.get_templates_for_app(self.app)
        for template in templates:
            name = template.get("name", "")
            desc = template.get("description", "")[:50]
            display = f"{name}"
            self.template_combo.addItem(display, name)
    
    def _on_mode_changed(self, checked):
        """Change entre template prédéfini et custom."""
        is_predefined = self.radio_predefined.isChecked()
        self.predefined_widget.setVisible(is_predefined)
        self.custom_widget.setVisible(not is_predefined)
        
        if is_predefined:
            self._on_template_changed(self.template_combo.currentIndex())
        else:
            self.template_changed.emit("__custom__", [])
    
    def _on_template_changed(self, index):
        """Quand un template est sélectionné."""
        if index <= 0:
            return
        
        template_name = self.template_combo.itemData(index)
        if not template_name:
            return
        
        template = self.data_manager.get_template_by_name(self.app, template_name)
        if template:
            self.selected_template = template_name
            desc = template.get("description", "Pas de description")
            self.template_desc.setText(desc)
            
            includes = template.get("includes", [])
            includes_text = " | ".join(includes[:5]) if includes else "Aucun include"
            if len(includes) > 5:
                includes_text += f" (+{len(includes) - 5} autres)"
            self.includes_preview.setText(f"📦 Includes: {includes_text}")
            
            self.template_changed.emit(template_name, includes)


class IncludeItemWidget(QWidget):
    """Widget pour un item d'include avec bouton supprimer."""
    
    delete_requested = Signal(str)  # Émet le nom de l'include
    
    def __init__(self, include_name: str, include_type: str = "template", parent=None):
        super().__init__(parent)
        self.include_name = include_name
        self.include_type = include_type
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Icône selon le type
        icons = {
            "quality-definitions": "📊",
            "quality-profiles": "⚙️",
            "custom-formats": "🎯",
            "template": "📋"
        }
        icon_label = QLabel(icons.get(self.include_type, "📋"))
        layout.addWidget(icon_label)
        
        # Nom
        name_label = QLabel(self.include_name)
        name_label.setStyleSheet(f"color: {CinemaTheme.TEXT_PRIMARY}; font-size: 12px;")
        layout.addWidget(name_label, stretch=1)
        
        # Bouton supprimer
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {CinemaTheme.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {CinemaTheme.ERROR};
                color: white;
                border-radius: 4px;
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.include_name))
        layout.addWidget(delete_btn)
        
        self.setStyleSheet(f"""
            IncludeItemWidget {{
                background-color: {CinemaTheme.SURFACE_LIGHT};
                border-radius: 4px;
            }}
        """)


class IncludesSectionWidget(QWidget):
    """Section pour gérer les includes."""
    
    includes_changed = Signal(list)  # Liste des includes
    
    def __init__(self, data_manager: DataManager, app: str, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.app = app
        self.include_items: list[IncludeItemWidget] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("📦 Include")
        header.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {CinemaTheme.PRIMARY};")
        header_layout.addWidget(header)
        
        # Info
        info = QLabel("Templates inclus dans la configuration")
        info.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        header_layout.addWidget(info)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Liste des includes
        self.includes_container = QWidget()
        self.includes_layout = QVBoxLayout(self.includes_container)
        self.includes_layout.setSpacing(4)
        self.includes_layout.setContentsMargins(0, 0, 0, 0)
        self.includes_layout.addStretch()
        layout.addWidget(self.includes_container)
        
        # Sélecteur pour ajouter
        add_layout = QHBoxLayout()
        self.include_selector = QComboBox()
        self.include_selector.setPlaceholderText("Ajouter un template...")
        self._populate_selector()
        add_layout.addWidget(self.include_selector, stretch=1)
        
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setObjectName("success")
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self._add_selected)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
    
    def _populate_selector(self):
        """Remplit le sélecteur avec les includes disponibles."""
        # Types d'includes disponibles
        include_types = ["quality-definitions", "quality-profiles", "custom-formats"]
        
        for include_type in include_types:
            includes = self.data_manager.get_includes_by_type(self.app, include_type)
            for include in includes:
                name = include.get("name", "")
                display = f"[{include_type}] {name}"
                # Stocker le nom et le type
                self.include_selector.addItem(display, {"name": name, "type": include_type})
    
    def _add_selected(self):
        """Ajoute l'include sélectionné."""
        index = self.include_selector.currentIndex()
        if index < 0:
            return
        
        data = self.include_selector.itemData(index)
        if not data:
            return
        
        name = data.get("name", "")
        include_type = data.get("type", "template")
        
        if name and not self._is_already_added(name):
            self.add_include(name, include_type)
            self._emit_change()
        
        self.include_selector.setCurrentIndex(-1)
    
    def _is_already_added(self, name: str) -> bool:
        """Vérifie si un include est déjà ajouté."""
        for item in self.include_items:
            if item.include_name == name:
                return True
        return False
    
    def add_include(self, name: str, include_type: str = "template"):
        """Ajoute un include."""
        item = IncludeItemWidget(name, include_type)
        item.delete_requested.connect(self._remove_include)
        self.include_items.append(item)
        
        # Insérer avant le stretch
        count = self.includes_layout.count()
        self.includes_layout.insertWidget(count - 1, item)
    
    def _remove_include(self, name: str):
        """Supprime un include."""
        for item in self.include_items[:]:
            if item.include_name == name:
                self.include_items.remove(item)
                self.includes_layout.removeWidget(item)
                item.deleteLater()
                break
        self._emit_change()
    
    def _emit_change(self):
        """Émet le signal de changement."""
        includes = [item.include_name for item in self.include_items]
        self.includes_changed.emit(includes)
    
    def set_includes(self, includes: list[str]):
        """Définit la liste des includes."""
        # Supprimer tous
        for item in self.include_items[:]:
            self._remove_include(item.include_name)
        
        # Ajouter les nouveaux
        for name in includes:
            self.add_include(name)
    
    def get_includes(self) -> list[str]:
        """Retourne la liste des includes."""
        return [item.include_name for item in self.include_items]


class QualityProfileItemWidget(QWidget):
    """Widget pour un item de Quality Profile."""
    
    delete_requested = Signal(str)  # Émet le nom du profil
    edit_requested = Signal(str, dict)  # Émet le nom et les données
    
    def __init__(self, profile_name: str, profile_data: dict, parent=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self.profile_data = profile_data
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Icône
        icon_label = QLabel("⚙️")
        layout.addWidget(icon_label)
        
        # Nom
        name_label = QLabel(self.profile_name)
        name_label.setStyleSheet(f"color: {CinemaTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        layout.addWidget(name_label, stretch=1)
        
        # Info
        upgrade = self.profile_data.get("upgrade", {})
        if upgrade.get("allowed"):
            until = upgrade.get("until_quality", "")
            info_text = f"↑ Jusqu'à: {until}"
            info_label = QLabel(info_text)
            info_label.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 10px;")
            layout.addWidget(info_label)
        
        # Boutons
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {CinemaTheme.SURFACE_LIGHT};
                border-radius: 4px;
            }}
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.profile_name, self.profile_data))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {CinemaTheme.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {CinemaTheme.ERROR};
                color: white;
                border-radius: 4px;
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.profile_name))
        layout.addWidget(delete_btn)
        
        self.setStyleSheet(f"""
            QualityProfileItemWidget {{
                background-color: {CinemaTheme.SURFACE_LIGHT};
                border-radius: 4px;
                border-left: 3px solid {CinemaTheme.SECONDARY};
            }}
        """)


class QualityProfilesSectionWidget(QWidget):
    """Section pour gérer les Quality Profiles."""
    
    profiles_changed = Signal(list)  # Liste des profils
    
    def __init__(self, data_manager: DataManager, app: str, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.app = app
        self.profile_items: list[QualityProfileItemWidget] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("⚙️ Quality Profile")
        header.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {CinemaTheme.PRIMARY};")
        header_layout.addWidget(header)
        
        info = QLabel("Profils de qualité pour la gestion des médias")
        info.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        header_layout.addWidget(info)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Liste des profils
        self.profiles_container = QWidget()
        self.profiles_layout = QVBoxLayout(self.profiles_container)
        self.profiles_layout.setSpacing(4)
        self.profiles_layout.setContentsMargins(0, 0, 0, 0)
        self.profiles_layout.addStretch()
        layout.addWidget(self.profiles_container)
        
        # Bouton ajouter
        add_btn = QPushButton("➕ Ajouter un profil")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self._add_new_profile)
        layout.addWidget(add_btn)
    
    def _add_new_profile(self):
        """Ouvre un dialog pour ajouter un nouveau profil."""
        dialog = QualityProfileDialog(self, app=self.app)
        if dialog.exec() == QDialog.Accepted and dialog.profile_data:
            self.add_profile(dialog.profile_name, dialog.profile_data)
            self._emit_change()
    
    def add_profile(self, name: str, data: dict):
        """Ajoute un profil."""
        # Vérifier si existe déjà
        for item in self.profile_items:
            if item.profile_name == name:
                return
        
        item = QualityProfileItemWidget(name, data)
        item.delete_requested.connect(self._remove_profile)
        item.edit_requested.connect(self._edit_profile)
        self.profile_items.append(item)
        
        count = self.profiles_layout.count()
        self.profiles_layout.insertWidget(count - 1, item)
    
    def _remove_profile(self, name: str):
        """Supprime un profil."""
        for item in self.profile_items[:]:
            if item.profile_name == name:
                self.profile_items.remove(item)
                self.profiles_layout.removeWidget(item)
                item.deleteLater()
                break
        self._emit_change()
    
    def _edit_profile(self, name: str, data: dict):
        """Édite un profil."""
        dialog = QualityProfileDialog(self, name, data, app=self.app)
        if dialog.exec() == QDialog.Accepted and dialog.profile_data:
            # Mettre à jour
            for item in self.profile_items:
                if item.profile_name == name:
                    item.profile_data = dialog.profile_data
                    break
            self._emit_change()
    
    def _emit_change(self):
        """Émet le signal de changement."""
        profiles = [{"name": item.profile_name, **item.profile_data} for item in self.profile_items]
        self.profiles_changed.emit(profiles)
    
    def set_profiles(self, profiles: list[dict]):
        """Définit la liste des profils."""
        for item in self.profile_items[:]:
            self._remove_profile(item.profile_name)
        
        for profile in profiles:
            name = profile.get("name", "")
            data = {k: v for k, v in profile.items() if k != "name"}
            self.add_profile(name, data)
    
    def get_profiles(self) -> list[dict]:
        """Retourne la liste des profils."""
        return [{"name": item.profile_name, **item.profile_data} for item in self.profile_items]


# Qualités disponibles par application
RADARR_QUALITIES = [
    ("Bluray-2160p", "4K Bluray"),
    ("WEBDL-2160p", "4K WEB-DL"),
    ("WEBRip-2160p", "4K WEB-Rip"),
    ("Bluray-1080p", "1080p Bluray"),
    ("WEBDL-1080p", "1080p WEB-DL"),
    ("WEBRip-1080p", "1080p WEB-Rip"),
    ("Remux-1080p", "1080p Remux"),
    ("HDTV-2160p", "4K HDTV"),
    ("HDTV-1080p", "1080p HDTV"),
    ("Raw-HD", "Raw HD"),
    ("BR-DISK", "Bluray Disk"),
    ("Bluray-720p", "720p Bluray"),
    ("WEBDL-720p", "720p WEB-DL"),
    ("WEBRip-720p", "720p WEB-Rip"),
    ("HDTV-720p", "720p HDTV"),
    ("Bluray-576p", "576p Bluray"),
    ("Bluray-480p", "480p Bluray"),
    ("WEBDL-480p", "480p WEB-DL"),
    ("WEBRip-480p", "480p WEB-Rip"),
    ("WEB 720p", "720p WEB"),
    ("WEB 480p", "480p WEB"),
    ("DVD-R", "DVD-R"),
    ("DVD", "DVD"),
    ("SDTV", "SDTV"),
    ("DVDSCR", "DVD Screener"),
    ("REGIONAL", "Regional"),
    ("TELECINE", "Telecine"),
    ("TELESYNC", "Telesync"),
    ("CAM", "Cam"),
    ("WORKPRINT", "Workprint"),
    ("Unknown", "Unknown"),
]

SONARR_QUALITIES = [
    ("WEBDL-2160p", "4K WEB-DL"),
    ("WEBRip-2160p", "4K WEB-Rip"),
    ("Bluray-2160p", "4K Bluray"),
    ("Bluray-2160p Remux", "4K Remux"),
    ("HDTV-2160p", "4K HDTV"),
    ("WEBDL-1080p", "1080p WEB-DL"),
    ("WEBRip-1080p", "1080p WEB-Rip"),
    ("Bluray-1080p", "1080p Bluray"),
    ("Bluray-1080p Remux", "1080p Remux"),
    ("HDTV-1080p", "1080p HDTV"),
    ("Raw-HD", "Raw HD"),
    ("Bluray-720p", "720p Bluray"),
    ("WEBDL-720p", "720p WEB-DL"),
    ("WEBRip-720p", "720p WEB-Rip"),
    ("HDTV-720p", "720p HDTV"),
    ("Bluray-576p", "576p Bluray"),
    ("Bluray-480p", "480p Bluray"),
    ("WEBDL-480p", "480p WEB-DL"),
    ("WEBRip-480p", "480p WEB-Rip"),
    ("DVD", "DVD"),
    ("SDTV", "SDTV"),
    ("Unknown", "Unknown"),
]


class QualitySelectionWidget(QWidget):
    """Widget pour sélectionner et ordonner les qualités."""
    
    qualities_updated = Signal(list)  # Émet la liste des qualités/groupes pour le dropdown
    
    def __init__(self, app: str, parent=None):
        super().__init__(parent)
        self.app = app
        self.qualities = RADARR_QUALITIES if app == "radarr" else SONARR_QUALITIES
        self.selected_qualities: list[tuple[str, list[str]]] = []  # [(group_name, [qualities])]
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header avec bouton "Tout sélectionner"
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("🎬 Qualités disponibles"))
        header_layout.addStretch()
        
        select_all_btn = QPushButton("✓ Tout")
        select_all_btn.setFixedWidth(80)
        select_all_btn.clicked.connect(self.select_all)
        header_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗ Aucun")
        deselect_all_btn.setFixedWidth(80)
        deselect_all_btn.clicked.connect(self.deselect_all)
        header_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(header_layout)
        
        # Liste des qualités avec cases à cocher
        self.qualities_list = QListWidget()
        self.qualities_list.setSelectionMode(QListWidget.MultiSelection)
        
        for quality_id, quality_name in self.qualities:
            item = QListWidgetItem(f"☐ {quality_name}")
            item.setData(Qt.UserRole, quality_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.qualities_list.addItem(item)
        
        layout.addWidget(self.qualities_list)
        
        # Boutons de groupe
        group_layout = QHBoxLayout()
        group_btn = QPushButton("📁 Grouper la sélection")
        group_btn.clicked.connect(self.create_group)
        group_layout.addWidget(group_btn)
        
        ungroup_btn = QPushButton("📂 Dégrouper")
        ungroup_btn.clicked.connect(self.ungroup_selection)
        group_layout.addWidget(ungroup_btn)
        
        group_layout.addStretch()
        layout.addLayout(group_layout)
        
        # Liste des qualités/groupes sélectionnés avec ordre
        layout.addWidget(QLabel("📋 Qualités/groupes dans l'ordre de préférence (haut = meilleur):"))
        
        self.selected_list = QListWidget()
        self.selected_list.setDragDropMode(QListWidget.InternalMove)
        layout.addWidget(self.selected_list)
        
        # Connecter les changements de case à cocher
        self.qualities_list.itemChanged.connect(self.on_quality_checked)
        
        # Connecter changements dans selected_list pour mettre à jour le dropdown
        self.selected_list.model().rowsMoved.connect(self._emit_qualities_update)
    
    def _emit_qualities_update(self):
        """Émet le signal de mise à jour des qualités."""
        qualities = self.get_qualities_for_dropdown()
        self.qualities_updated.emit(qualities)
    
    def get_qualities_for_dropdown(self) -> list[str]:
        """Retourne la liste des noms pour le dropdown."""
        names = []
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            if item:
                text = item.text().replace("📄 ", "").replace("📁 ", "")
                names.append(text)
        return names
    
    def on_quality_checked(self, item: QListWidgetItem):
        """Quand une qualité est cochée/décochée."""
        quality_id = item.data(Qt.UserRole)
        quality_name = item.text().replace("☐ ", "").replace("☑ ", "")
        
        if item.checkState() == Qt.Checked:
            item.setText(f"☑ {quality_name}")
            # Ajouter à la liste si pas déjà présent
            if not self._is_in_selected(quality_id):
                list_item = QListWidgetItem(f"📄 {quality_name}")
                list_item.setData(Qt.UserRole, {"type": "single", "qualities": [quality_id]})
                self.selected_list.addItem(list_item)
        else:
            item.setText(f"☐ {quality_name}")
            # Retirer de la liste
            self._remove_from_selected(quality_id)
        
        # Émettre le signal de mise à jour
        self._emit_qualities_update()
    
    def _is_in_selected(self, quality_id: str) -> bool:
        """Vérifie si une qualité est déjà dans la liste sélectionnée."""
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            data = item.data(Qt.UserRole)
            if data and quality_id in data.get("qualities", []):
                return True
        return False
    
    def _remove_from_selected(self, quality_id: str):
        """Retire une qualité de la liste sélectionnée."""
        for i in range(self.selected_list.count() - 1, -1, -1):
            item = self.selected_list.item(i)
            data = item.data(Qt.UserRole)
            if data and quality_id in data.get("qualities", []):
                if data.get("type") == "single":
                    self.selected_list.takeItem(i)
                else:
                    # Groupe - retirer juste cette qualité
                    qualities = data.get("qualities", [])
                    if quality_id in qualities:
                        qualities.remove(quality_id)
                        if len(qualities) == 1:
                            # Plus qu'une qualité, transformer en single
                            item.setData(Qt.UserRole, {"type": "single", "qualities": qualities})
                            item.setText(f"📄 {self._get_quality_name(qualities[0])}")
                        elif len(qualities) == 0:
                            self.selected_list.takeItem(i)
                        else:
                            item.setData(Qt.UserRole, {"type": "group", "qualities": qualities})
                            item.setText(f"📁 {' | '.join(self._get_quality_name(q) for q in qualities)}")
                break
    
    def _get_quality_name(self, quality_id: str) -> str:
        """Récupère le nom affiché d'une qualité."""
        for qid, qname in self.qualities:
            if qid == quality_id:
                return qname
        return quality_id
    
    def create_group(self):
        """Crée un groupe à partir des qualités cochées dans la liste de gauche."""
        # Récupérer les qualités cochées dans qualities_list
        checked_quality_ids = []
        for i in range(self.qualities_list.count()):
            item = self.qualities_list.item(i)
            if item.checkState() == Qt.Checked:
                quality_id = item.data(Qt.UserRole)
                checked_quality_ids.append(quality_id)
        
        if len(checked_quality_ids) < 2:
            QMessageBox.information(self, "Info", "Cochez au moins 2 qualités dans la liste de gauche pour les grouper")
            return
        
        # Trouver ces qualités dans selected_list et récupérer leurs positions
        rows_to_remove = []
        first_row = None
        
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            data = item.data(Qt.UserRole)
            if data:
                item_qualities = data.get("qualities", [])
                # Si cette item contient une des qualités cochées
                for qid in checked_quality_ids:
                    if qid in item_qualities:
                        rows_to_remove.append(i)
                        if first_row is None:
                            first_row = i
                        break
        
        if len(rows_to_remove) < 2:
            QMessageBox.information(self, "Info", "Les qualités cochées doivent d'abord être ajoutées à la liste de droite")
            return
        
        # Créer le groupe avec toutes les qualités cochées
        group_name = " | ".join(self._get_quality_name(q) for q in checked_quality_ids[:3])
        if len(checked_quality_ids) > 3:
            group_name += f" (+{len(checked_quality_ids) - 3})"
        
        group_item = QListWidgetItem(f"📁 {group_name}")
        group_item.setData(Qt.UserRole, {"type": "group", "qualities": checked_quality_ids.copy()})
        
        # Supprimer les anciens items individuels (en ordre inverse pour garder les indices valides)
        for row in sorted(rows_to_remove, reverse=True):
            self.selected_list.takeItem(row)
        
        # Insérer le groupe à la position du premier item supprimé
        self.selected_list.insertItem(first_row, group_item)
        self.selected_list.setCurrentItem(group_item)
        
        # Émettre le signal de mise à jour
        self._emit_qualities_update()
    
    def ungroup_selection(self):
        """Dégroupe l'item sélectionné."""
        current_item = self.selected_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Sélectionnez un groupe à dégrouper dans la liste de droite")
            return
        
        data = current_item.data(Qt.UserRole)
        if not data or data.get("type") != "group":
            QMessageBox.information(self, "Info", "L'élément sélectionné n'est pas un groupe")
            return
        
        row = self.selected_list.row(current_item)
        qualities = data.get("qualities", [])
        
        self.selected_list.takeItem(row)
        
        # Ajouter chaque qualité individuellement
        for quality_id in qualities:
            item = QListWidgetItem(f"📄 {self._get_quality_name(quality_id)}")
            item.setData(Qt.UserRole, {"type": "single", "qualities": [quality_id]})
            self.selected_list.insertItem(row, item)
            row += 1
        
        # Émettre le signal de mise à jour
        self._emit_qualities_update()
    
    def select_all(self):
        """Sélectionne toutes les qualités."""
        for i in range(self.qualities_list.count()):
            item = self.qualities_list.item(i)
            item.setCheckState(Qt.Checked)
        # Le signal est déjà émis par on_quality_checked
    
    def deselect_all(self):
        """Désélectionne toutes les qualités."""
        self.selected_list.clear()
        for i in range(self.qualities_list.count()):
            item = self.qualities_list.item(i)
            item.setCheckState(Qt.Unchecked)
        # Émettre le signal de mise à jour
        self._emit_qualities_update()
    
    def get_qualities_config(self) -> list[dict]:
        """Retourne la configuration des qualités pour le YAML."""
        config = []
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            data = item.data(Qt.UserRole)
            if data:
                qualities = data.get("qualities", [])
                if len(qualities) == 1:
                    config.append(qualities[0])
                elif len(qualities) > 1:
                    # Créer un groupe
                    group_name = " | ".join(qualities[:2])
                    if len(qualities) > 2:
                        group_name += f" (+{len(qualities) - 2})"
                    config.append({
                        "name": group_name,
                        "qualities": qualities
                    })
        return config
    
    def set_qualities_config(self, qualities: list):
        """Définit la configuration des qualités."""
        self.deselect_all()
        
        for item in qualities:
            if isinstance(item, str):
                # Qualité simple
                for i in range(self.qualities_list.count()):
                    list_item = self.qualities_list.item(i)
                    if list_item.data(Qt.UserRole) == item:
                        list_item.setCheckState(Qt.Checked)
                        break
            elif isinstance(item, dict):
                # Groupe
                group_qualities = item.get("qualities", [])
                for quality_id in group_qualities:
                    for i in range(self.qualities_list.count()):
                        list_item = self.qualities_list.item(i)
                        if list_item.data(Qt.UserRole) == quality_id:
                            list_item.setCheckState(Qt.Checked)
                            break
                
                # Créer l'item de groupe
                if group_qualities:
                    group_name = item.get("name", " | ".join(group_qualities[:2]))
                    group_item = QListWidgetItem(f"📁 {group_name}")
                    group_item.setData(Qt.UserRole, {"type": "group", "qualities": group_qualities})
                    self.selected_list.addItem(group_item)


class QualityProfileDialog(QDialog):
    """Dialog complet pour créer/éditer un Quality Profile."""
    
    def __init__(self, parent=None, profile_name: str = "", profile_data: dict = None, app: str = "radarr"):
        super().__init__(parent)
        self.setWindowTitle(f"Modifier le profil de qualité - {profile_name or 'Nouveau'}")
        self.setMinimumSize(700, 800)
        
        self.profile_name = profile_name or ""
        self.profile_data = profile_data or {}
        self.app = app
        
        self.setup_ui()
        
        if profile_name:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Scroll area pour tout le contenu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        
        # === SECTION NOM ===
        name_group = QGroupBox("Nom du profil")
        name_layout = QVBoxLayout(name_group)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("ex: FR-MULTi-VF-UHD")
        name_layout.addWidget(self.name_edit)
        content_layout.addWidget(name_group)
        
        # === SECTION UPGRADE ===
        upgrade_group = QGroupBox("Mise à niveau (Upgrade)")
        upgrade_layout = QGridLayout(upgrade_group)
        
        self.upgrade_cb = QCheckBox("Mises à niveau autorisées")
        self.upgrade_cb.setChecked(True)
        upgrade_layout.addWidget(self.upgrade_cb, 0, 0, 1, 2)
        
        upgrade_layout.addWidget(QLabel("Mise à niveau jusqu'à la qualité:"), 1, 0)
        self.until_quality = QComboBox()
        self.until_quality.setPlaceholderText("Sélectionnez une qualité...")
        upgrade_layout.addWidget(self.until_quality, 1, 1)
        
        upgrade_layout.addWidget(QLabel("Score minimum de format personnalisé:"), 2, 0)
        self.min_score = QSpinBox()
        self.min_score.setRange(0, 100000)
        self.min_score.setValue(0)
        upgrade_layout.addWidget(self.min_score, 2, 1)
        
        upgrade_layout.addWidget(QLabel("Mise à niveau jusqu'au score:"), 3, 0)
        self.until_score = QSpinBox()
        self.until_score.setRange(0, 100000)
        self.until_score.setValue(10000)
        self.until_score.setSingleStep(1000)
        upgrade_layout.addWidget(self.until_score, 3, 1)
        
        upgrade_layout.addWidget(QLabel("Incrément minimal du score:"), 4, 0)
        self.score_increment = QSpinBox()
        self.score_increment.setRange(1, 10000)
        self.score_increment.setValue(1)
        upgrade_layout.addWidget(self.score_increment, 4, 1)
        
        content_layout.addWidget(upgrade_group)
        
        # === SECTION QUALITÉS ===
        qualities_group = QGroupBox("Qualités")
        qualities_layout = QVBoxLayout(qualities_group)
        
        info_label = QLabel("Les qualités plus élevées dans la liste sont plus préférées. Les qualités au sein d'un même groupe sont égales.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        qualities_layout.addWidget(info_label)
        
        self.qualities_widget = QualitySelectionWidget(self.app)
        qualities_layout.addWidget(self.qualities_widget)
        
        # Connecter le signal maintenant que le widget existe
        self.qualities_widget.qualities_updated.connect(self._update_quality_dropdown)
        
        content_layout.addWidget(qualities_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # === BOUTONS ===
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        
        save_btn = buttons.button(QDialogButtonBox.Save)
        save_btn.setText("💾 Sauvegarder")
        
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("❌ Annuler")
        
        layout.addWidget(buttons)
    
    def _update_quality_dropdown(self, qualities: list[str]):
        """Met à jour le dropdown des qualités avec les qualités/groupes sélectionnés."""
        current_text = self.until_quality.currentText()
        self.until_quality.clear()
        for quality in qualities:
            self.until_quality.addItem(quality)
        # Restaurer la sélection si possible
        index = self.until_quality.findText(current_text)
        if index >= 0:
            self.until_quality.setCurrentIndex(index)
    
    def load_data(self):
        """Charge les données existantes."""
        self.name_edit.setText(self.profile_name)
        
        # Upgrade settings
        upgrade = self.profile_data.get("upgrade", {})
        self.upgrade_cb.setChecked(upgrade.get("allowed", True))
        
        until_quality = upgrade.get("until_quality", "")
        if until_quality:
            self.until_quality.setCurrentText(until_quality)
        
        self.until_score.setValue(upgrade.get("until_score", 10000))
        self.min_score.setValue(self.profile_data.get("min_format_score", 0))
        self.score_increment.setValue(upgrade.get("min_custom_format_score", 1))
        
        # Qualities
        qualities = self.profile_data.get("qualities", [])
        if qualities:
            self.qualities_widget.set_qualities_config(qualities)
    
    def save(self):
        """Sauvegarde le profil."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom du profil est requis")
            return
        
        self.profile_name = name
        
        # Construire les données
        qualities = self.qualities_widget.get_qualities_config()
        
        self.profile_data = {
            "reset_unmatched_scores": {"enabled": True},
            "upgrade": {
                "allowed": self.upgrade_cb.isChecked(),
                "until_quality": self.until_quality.currentText(),
                "until_score": self.until_score.value(),
                "min_custom_format_score": self.score_increment.value()
            },
            "min_format_score": self.min_score.value(),
            "score_set": "default",
            "quality_sort": "top",
            "qualities": qualities if qualities else None
        }
        
        # Retirer les valeurs None
        self.profile_data = {k: v for k, v in self.profile_data.items() if v is not None}
        
        self.accept()


class CustomFormatItemWidget(QWidget):
    """Widget pour un item de Custom Format avec score."""
    
    delete_requested = Signal(str)  # Émet le trash_id
    score_changed = Signal(str, int)  # Émet trash_id et nouveau score
    
    def __init__(self, cf_name: str, trash_id: str, score: int, description: str = "", parent=None):
        super().__init__(parent)
        self.cf_name = cf_name
        self.trash_id = trash_id
        self.description = description
        self.setup_ui(score)
    
    def setup_ui(self, score: int):
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Nom
        name_label = QLabel(self.cf_name)
        name_label.setStyleSheet(f"color: {CinemaTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")
        if self.description:
            name_label.setToolTip(self.description[:200])
        layout.addWidget(name_label, stretch=1)
        
        # Score
        layout.addWidget(QLabel("Score:"))
        self.score_spin = QSpinBox()
        self.score_spin.setRange(-100000, 100000)
        self.score_spin.setValue(score)
        self.score_spin.setSingleStep(100)
        self.score_spin.setFixedWidth(80)
        self.score_spin.valueChanged.connect(lambda v: self.score_changed.emit(self.trash_id, v))
        layout.addWidget(self.score_spin)
        
        # Bouton supprimer
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {CinemaTheme.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {CinemaTheme.ERROR};
                color: white;
                border-radius: 4px;
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.trash_id))
        layout.addWidget(delete_btn)
        
        self.setStyleSheet(f"""
            CustomFormatItemWidget {{
                background-color: {CinemaTheme.SURFACE_LIGHT};
                border-radius: 4px;
                border-left: 3px solid {CinemaTheme.ACCENT};
            }}
        """)


class CustomFormatsSectionWidget(QWidget):
    """Section pour gérer les Custom Formats."""
    
    custom_formats_changed = Signal(list)  # Liste des CFs
    
    def __init__(self, data_manager: DataManager, app: str, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.app = app
        self.cf_items: list[CustomFormatItemWidget] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🎯 Custom Format")
        header.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {CinemaTheme.PRIMARY};")
        header_layout.addWidget(header)
        
        info = QLabel("Formats personnalisés avec scores")
        info.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        header_layout.addWidget(info)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Liste des CFs
        self.cf_container = QWidget()
        self.cf_layout = QVBoxLayout(self.cf_container)
        self.cf_layout.setSpacing(4)
        self.cf_layout.setContentsMargins(0, 0, 0, 0)
        self.cf_layout.addStretch()
        layout.addWidget(self.cf_container)
        
        # Sélecteur pour ajouter
        add_layout = QHBoxLayout()
        self.cf_selector = QComboBox()
        self.cf_selector.setPlaceholderText("Ajouter un Custom Format...")
        self._populate_selector()
        add_layout.addWidget(self.cf_selector, stretch=1)
        
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setObjectName("success")
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self._add_selected)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
    
    def _populate_selector(self):
        """Remplit le sélecteur avec les CFs disponibles."""
        cfs = self.data_manager.get_custom_formats_for_app(self.app)
        for cf in cfs:
            name = cf.get("name", "")
            trash_id = cf.get("trash_id", "")
            self.cf_selector.addItem(name, trash_id)
    
    def _add_selected(self):
        """Ajoute le CF sélectionné."""
        index = self.cf_selector.currentIndex()
        if index < 0:
            return
        
        trash_id = self.cf_selector.itemData(index)
        cf_data = self.data_manager.get_cf_by_id(trash_id)
        
        if cf_data and not self._is_already_added(trash_id):
            name = cf_data.get("name", "")
            # Score par défaut depuis Trash Guide
            trash_scores = cf_data.get("trash_scores", {})
            default_score = trash_scores.get("default", 0)
            description = cf_data.get("description", "")
            
            self.add_custom_format(name, trash_id, default_score, description)
            self._emit_change()
        
        self.cf_selector.setCurrentIndex(-1)
    
    def _is_already_added(self, trash_id: str) -> bool:
        """Vérifie si un CF est déjà ajouté."""
        for item in self.cf_items:
            if item.trash_id == trash_id:
                return True
        return False
    
    def add_custom_format(self, name: str, trash_id: str, score: int, description: str = ""):
        """Ajoute un CF."""
        item = CustomFormatItemWidget(name, trash_id, score, description)
        item.delete_requested.connect(self._remove_cf)
        item.score_changed.connect(self._on_score_changed)
        self.cf_items.append(item)
        
        count = self.cf_layout.count()
        self.cf_layout.insertWidget(count - 1, item)
    
    def _remove_cf(self, trash_id: str):
        """Supprime un CF."""
        for item in self.cf_items[:]:
            if item.trash_id == trash_id:
                self.cf_items.remove(item)
                self.cf_layout.removeWidget(item)
                item.deleteLater()
                break
        self._emit_change()
    
    def _on_score_changed(self, trash_id: str, score: int):
        """Quand le score change."""
        self._emit_change()
    
    def _emit_change(self):
        """Émet le signal de changement."""
        cfs = []
        for item in self.cf_items:
            cfs.append({
                "name": item.cf_name,
                "trash_id": item.trash_id,
                "score": item.score_spin.value()
            })
        self.custom_formats_changed.emit(cfs)
    
    def set_custom_formats(self, cfs: list[dict]):
        """Définit la liste des CFs."""
        for item in self.cf_items[:]:
            self._remove_cf(item.trash_id)
        
        for cf in cfs:
            name = cf.get("name", "")
            trash_id = cf.get("trash_id", "")
            score = cf.get("score", 0)
            
            cf_data = self.data_manager.get_cf_by_id(trash_id)
            description = cf_data.get("description", "") if cf_data else ""
            
            self.add_custom_format(name, trash_id, score, description)
    
    def get_custom_formats(self) -> list[dict]:
        """Retourne la liste des CFs."""
        return [
            {
                "name": item.cf_name,
                "trash_id": item.trash_id,
                "score": item.score_spin.value()
            }
            for item in self.cf_items
        ]


class InstanceEditorDialog(QDialog):
    """Dialog d'édition d'une instance - Interface refondue."""
    
    def __init__(self, data_manager: DataManager, app: str, 
                 instance: InstanceConfig | None = None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.app = app
        self.instance = instance or InstanceConfig(name="")
        self.result_instance: InstanceConfig | None = None
        
        self.setWindowTitle(f"Configuration {'Radarr' if app == 'radarr' else 'Sonarr'}")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("🎬" if self.app == "radarr" else "📺")
        icon.setStyleSheet(f"font-size: 32px; color: {CinemaTheme.RADARR_COLOR if self.app == 'radarr' else CinemaTheme.SONARR_COLOR};")
        header.addWidget(icon)
        
        title = QLabel(f"Configuration {'Radarr' if self.app == 'radarr' else 'Sonarr'}")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {CinemaTheme.RADARR_COLOR if self.app == 'radarr' else CinemaTheme.SONARR_COLOR};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # === PANNEAU GAUCHE ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)
        
        # Informations de base
        info_group = QGroupBox("Informations de base")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("Nom:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("ex: mon-radarr")
        info_layout.addWidget(self.name_edit, 0, 1)
        
        info_layout.addWidget(QLabel("URL:"), 1, 0)
        self.url_edit = QLineEdit()
        default_url = "http://localhost:7878" if self.app == "radarr" else "http://localhost:8989"
        self.url_edit.setPlaceholderText(default_url)
        info_layout.addWidget(self.url_edit, 1, 1)
        
        info_layout.addWidget(QLabel("API Key:"), 2, 0)
        self.api_edit = QLineEdit()
        self.api_edit.setEchoMode(QLineEdit.Password)
        info_layout.addWidget(self.api_edit, 2, 1)
        
        left_layout.addWidget(info_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.delete_old_cb = QCheckBox("Supprimer les anciens Custom Formats")
        self.delete_old_cb.setChecked(True)
        options_layout.addWidget(self.delete_old_cb)
        
        self.replace_cb = QCheckBox("Remplacer les Custom Formats existants")
        self.replace_cb.setChecked(True)
        options_layout.addWidget(self.replace_cb)
        
        left_layout.addWidget(options_group)
        
        # Sélecteur de template
        self.template_selector = TemplateSelectorWidget(self.data_manager, self.app)
        self.template_selector.template_changed.connect(self._on_template_changed)
        left_layout.addWidget(self.template_selector)
        
        left_layout.addStretch()
        splitter.addWidget(left_panel)
        
        # === PANNEAU DROIT ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        
        # Titre
        yaml_preview_title = QLabel("📄 Configuration YAML")
        yaml_preview_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {CinemaTheme.TEXT_PRIMARY};")
        right_layout.addWidget(yaml_preview_title)
        
        # Section Include
        self.includes_section = IncludesSectionWidget(self.data_manager, self.app)
        self.includes_section.includes_changed.connect(self._update_yaml_preview)
        right_layout.addWidget(self.includes_section)
        
        # Section Quality Profiles
        self.profiles_section = QualityProfilesSectionWidget(self.data_manager, self.app)
        self.profiles_section.profiles_changed.connect(self._update_yaml_preview)
        right_layout.addWidget(self.profiles_section)
        
        # Section Custom Formats
        self.cf_section = CustomFormatsSectionWidget(self.data_manager, self.app)
        self.cf_section.custom_formats_changed.connect(self._update_yaml_preview)
        right_layout.addWidget(self.cf_section)
        
        # Aperçu YAML
        self.yaml_preview = QTextEdit()
        self.yaml_preview.setReadOnly(True)
        self.yaml_preview.setMaximumHeight(150)
        self.yaml_preview.setPlaceholderText("L'aperçu du YAML apparaîtra ici...")
        right_layout.addWidget(self.yaml_preview)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter, stretch=1)
        
        # Boutons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        save_btn = button_box.button(QDialogButtonBox.Save)
        save_btn.setText("💾 Sauvegarder")
        
        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("❌ Annuler")
        
        layout.addWidget(button_box)
    
    def _on_template_changed(self, template_name: str, includes: list):
        """Quand un template est sélectionné."""
        if template_name != "__custom__":
            # Mettre à jour les includes
            self.includes_section.set_includes(includes)
        self._update_yaml_preview()
    
    def _update_yaml_preview(self):
        """Met à jour l'aperçu YAML."""
        # Construire un aperçu temporaire
        preview = f"""{self.name_edit.text() or 'instance-name'}:
  base_url: {self.url_edit.text() or 'http://localhost:7878'}
  api_key: {'***' if self.api_edit.text() else 'VOTRE_API_KEY'}
  
  include:"""
        
        includes = self.includes_section.get_includes()
        if includes:
            for inc in includes:
                preview += f"\n    - template: {inc}"
        else:
            preview += "\n    # Aucun template sélectionné"
        
        profiles = self.profiles_section.get_profiles()
        if profiles:
            preview += "\n  \n  quality_profiles:"
            for p in profiles:
                preview += f"\n    - name: {p.get('name', '')}"
        
        cfs = self.cf_section.get_custom_formats()
        if cfs:
            preview += "\n  \n  custom_formats:"
            for cf in cfs[:3]:  # Limiter l'aperçu
                preview += f"\n    - {cf.get('name', '')}: {cf.get('score', 0)}"
            if len(cfs) > 3:
                preview += f"\n    # ... et {len(cfs) - 3} autres"
        
        self.yaml_preview.setText(preview)
    
    def load_data(self):
        """Charge les données de l'instance."""
        if self.instance.name:
            self.name_edit.setText(self.instance.name)
            self.url_edit.setText(self.instance.base_url)
            self.api_edit.setText(self.instance.api_key)
            self.delete_old_cb.setChecked(self.instance.delete_old_custom_formats)
            self.replace_cb.setChecked(self.instance.replace_existing_custom_formats)
            
            self.includes_section.set_includes(self.instance.includes)
            self.profiles_section.set_profiles(self.instance.quality_profiles)
            
            # Convertir les CFs
            cf_list = []
            for cf in self.instance.custom_formats:
                cf_list.append({
                    "name": cf.get("name", ""),
                    "trash_id": cf.get("trash_id", ""),
                    "score": cf.get("score", 0)
                })
            self.cf_section.set_custom_formats(cf_list)
            
            self._update_yaml_preview()
    
    def save(self):
        """Sauvegarde l'instance."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom de l'instance est requis")
            return
        
        # Récupérer les CFs avec la bonne structure
        cf_list = []
        for cf in self.cf_section.get_custom_formats():
            cf_list.append({
                "trash_ids": [cf["trash_id"]],
                "assign_scores_to": [{"name": "default", "score": cf["score"]}]
            })
        
        self.result_instance = InstanceConfig(
            name=name,
            base_url=self.url_edit.text(),
            api_key=self.api_edit.text(),
            delete_old_custom_formats=self.delete_old_cb.isChecked(),
            replace_existing_custom_formats=self.replace_cb.isChecked(),
            includes=self.includes_section.get_includes(),
            quality_profiles=self.profiles_section.get_profiles(),
            custom_formats=cf_list
        )
        
        self.accept()


class InstanceCard(QFrame):
    """Carte visuelle pour afficher une instance."""
    
    edit_requested = Signal(str, object)
    delete_requested = Signal(str, object)
    
    def __init__(self, app: str, instance: InstanceConfig, parent=None):
        super().__init__(parent)
        self.app = app
        self.instance = instance
        self.setObjectName(f"{app}-card")
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QHBoxLayout()
        
        icon_label = QLabel("🎬" if self.app == "radarr" else "📺")
        icon_label.setStyleSheet(f"font-size: 24px; color: {CinemaTheme.RADARR_COLOR if self.app == 'radarr' else CinemaTheme.SONARR_COLOR};")
        header.addWidget(icon_label)
        
        name_label = QLabel(self.instance.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        header.addWidget(name_label, stretch=1)
        
        layout.addLayout(header)
        
        # URL
        url_text = self.instance.base_url or "Non configuré"
        url_label = QLabel(f"🔗 {url_text}")
        url_label.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 12px;")
        url_label.setWordWrap(True)
        layout.addWidget(url_label)
        
        # Stats
        stats_layout = QHBoxLayout()
        
        includes_count = len(self.instance.includes)
        cf_count = len(self.instance.custom_formats)
        
        includes_label = QLabel(f"📋 {includes_count} includes")
        includes_label.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        stats_layout.addWidget(includes_label)
        
        cf_label = QLabel(f"🎯 {cf_count} CFs")
        cf_label.setStyleSheet(f"color: {CinemaTheme.TEXT_SECONDARY}; font-size: 11px;")
        stats_layout.addWidget(cf_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ Modifier")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.on_edit)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.on_delete)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def on_edit(self):
        self.edit_requested.emit(self.app, self.instance)
    
    def on_delete(self):
        self.delete_requested.emit(self.app, self.instance)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recyclarr Config Generator - Home Cinema Edition")
        self.setMinimumSize(1400, 900)
        
        self.data_manager = DataManager()
        self.yaml_generator = YAMLGenerator(self.data_manager)
        self.config = RecyclarrConfiguration()
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🎬 Recyclarr Config Generator")
        title.setObjectName("title")
        header.addWidget(title)
        
        header.addStretch()
        
        preview_btn = QPushButton("👁️ Prévisualiser YAML")
        preview_btn.clicked.connect(self.generate_preview)
        header.addWidget(preview_btn)
        
        save_btn = QPushButton("💾 Sauvegarder YAML")
        save_btn.clicked.connect(self.save_yaml)
        header.addWidget(save_btn)
        
        layout.addLayout(header)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panneau gauche: Instances
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)
        
        # Section Radarr
        radarr_header = QHBoxLayout()
        radarr_title = QLabel("🎬 RADARR - Films")
        radarr_title.setObjectName("radarr-label")
        radarr_header.addWidget(radarr_title)
        radarr_header.addStretch()
        
        add_radarr_btn = QPushButton("➕ Ajouter")
        add_radarr_btn.setObjectName("secondary")
        add_radarr_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CinemaTheme.RADARR_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }}
        """)
        add_radarr_btn.clicked.connect(lambda: self.add_instance("radarr"))
        radarr_header.addWidget(add_radarr_btn)
        
        left_layout.addLayout(radarr_header)
        
        # Scroll area pour les cartes Radarr
        radarr_scroll = QScrollArea()
        radarr_scroll.setWidgetResizable(True)
        radarr_scroll.setFrameShape(QFrame.NoFrame)
        radarr_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.radarr_container = QWidget()
        self.radarr_layout = QVBoxLayout(self.radarr_container)
        self.radarr_layout.setSpacing(12)
        self.radarr_layout.addStretch()
        
        radarr_scroll.setWidget(self.radarr_container)
        left_layout.addWidget(radarr_scroll)
        
        # Section Sonarr
        sonarr_header = QHBoxLayout()
        sonarr_title = QLabel("📺 SONARR - Séries")
        sonarr_title.setObjectName("sonarr-label")
        sonarr_header.addWidget(sonarr_title)
        sonarr_header.addStretch()
        
        add_sonarr_btn = QPushButton("➕ Ajouter")
        add_sonarr_btn.setObjectName("secondary")
        add_sonarr_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CinemaTheme.SONARR_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }}
        """)
        add_sonarr_btn.clicked.connect(lambda: self.add_instance("sonarr"))
        sonarr_header.addWidget(add_sonarr_btn)
        
        left_layout.addLayout(sonarr_header)
        
        # Scroll area pour les cartes Sonarr
        sonarr_scroll = QScrollArea()
        sonarr_scroll.setWidgetResizable(True)
        sonarr_scroll.setFrameShape(QFrame.NoFrame)
        sonarr_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.sonarr_container = QWidget()
        self.sonarr_layout = QVBoxLayout(self.sonarr_container)
        self.sonarr_layout.setSpacing(12)
        self.sonarr_layout.addStretch()
        
        sonarr_scroll.setWidget(self.sonarr_container)
        left_layout.addWidget(sonarr_scroll)
        
        main_splitter.addWidget(left_panel)
        
        # Panneau droit: Prévisualisation YAML
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        
        preview_header = QLabel("📄 Prévisualisation YAML")
        preview_header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        right_layout.addWidget(preview_header)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Cliquez sur 'Prévisualiser YAML' pour voir la configuration générée...")
        right_layout.addWidget(self.preview_text)
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([500, 900])
        
        layout.addWidget(main_splitter, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt - Chargez les données JSON pour commencer")
    
    def load_data(self):
        """Charge les données au démarrage."""
        if not self.data_manager.load_data():
            QMessageBox.warning(
                self,
                "Données manquantes",
                "Les fichiers de données sont manquants.\n\n"
                "Veuillez exécuter:\n"
                "1. python trash_cf_extractor.py\n"
                "2. python templates_extractor.py"
            )
        else:
            total_cf = self.data_manager.custom_formats.get('metadata', {}).get('total_formats', 0)
            radarr_count = len(self.data_manager.get_custom_formats_for_app("radarr"))
            sonarr_count = len(self.data_manager.get_custom_formats_for_app("sonarr"))
            self.status_bar.showMessage(
                f"✅ Données chargées - {radarr_count} CFs Radarr, {sonarr_count} CFs Sonarr disponibles"
            )
    
    def add_instance(self, app: str):
        """Ajoute une nouvelle instance."""
        dialog = InstanceEditorDialog(self.data_manager, app, parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.result_instance:
            instance = dialog.result_instance
            if app == "radarr":
                self.config.radarr_instances.append(instance)
                self.refresh_radarr_cards()
            else:
                self.config.sonarr_instances.append(instance)
                self.refresh_sonarr_cards()
            
            self.status_bar.showMessage(f"✅ Instance '{instance.name}' ajoutée avec succès")
    
    def edit_instance(self, app: str, instance: InstanceConfig):
        """Édite une instance existante."""
        dialog = InstanceEditorDialog(self.data_manager, app, instance, parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.result_instance:
            instances = self.config.radarr_instances if app == "radarr" else self.config.sonarr_instances
            for i, inst in enumerate(instances):
                if inst is instance:
                    instances[i] = dialog.result_instance
                    break
            
            if app == "radarr":
                self.refresh_radarr_cards()
            else:
                self.refresh_sonarr_cards()
            
            self.status_bar.showMessage(f"✅ Instance '{dialog.result_instance.name}' modifiée")
    
    def delete_instance(self, app: str, instance: InstanceConfig):
        """Supprime une instance."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'instance '{instance.name}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if app == "radarr":
                self.config.radarr_instances.remove(instance)
                self.refresh_radarr_cards()
            else:
                self.config.sonarr_instances.remove(instance)
                self.refresh_sonarr_cards()
            
            self.status_bar.showMessage(f"🗑️ Instance '{instance.name}' supprimée")
    
    def refresh_radarr_cards(self):
        """Rafraîchit l'affichage des cartes Radarr."""
        while self.radarr_layout.count() > 1:
            item = self.radarr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for instance in self.config.radarr_instances:
            card = InstanceCard("radarr", instance)
            card.edit_requested.connect(self.edit_instance)
            card.delete_requested.connect(self.delete_instance)
            self.radarr_layout.insertWidget(self.radarr_layout.count() - 1, card)
    
    def refresh_sonarr_cards(self):
        """Rafraîchit l'affichage des cartes Sonarr."""
        while self.sonarr_layout.count() > 1:
            item = self.sonarr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for instance in self.config.sonarr_instances:
            card = InstanceCard("sonarr", instance)
            card.edit_requested.connect(self.edit_instance)
            card.delete_requested.connect(self.delete_instance)
            self.sonarr_layout.insertWidget(self.sonarr_layout.count() - 1, card)
    
    def generate_preview(self):
        """Génère la prévisualisation YAML."""
        if not self.config.radarr_instances and not self.config.sonarr_instances:
            QMessageBox.information(self, "Information", "Aucune instance configurée")
            return
        
        yaml_content = self.yaml_generator.generate(self.config)
        self.preview_text.setText(yaml_content)
        
        radarr_count = len(self.config.radarr_instances)
        sonarr_count = len(self.config.sonarr_instances)
        self.status_bar.showMessage(f"📄 Prévisualisation générée - {radarr_count} Radarr, {sonarr_count} Sonarr")
    
    def save_yaml(self):
        """Sauvegarde le fichier YAML."""
        if not self.config.radarr_instances and not self.config.sonarr_instances:
            QMessageBox.information(self, "Information", "Aucune instance configurée")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder la configuration",
            "recyclarr-config.yml",
            "YAML files (*.yml *.yaml);;All files (*.*)"
        )
        
        if file_path:
            yaml_content = self.yaml_generator.generate(self.config)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(yaml_content)
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Configuration sauvegardée dans:\n{file_path}"
                )
                self.status_bar.showMessage(f"💾 Fichier sauvegardé: {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de sauvegarder:\n{e}"
                )


def main():
    """Point d'entrée principal."""
    app = QApplication(sys.argv)
    
    # Appliquer le stylesheet
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
