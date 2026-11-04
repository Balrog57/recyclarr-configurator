#!/usr/bin/env python3
import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QPushButton, QLabel, QFileDialog, QMessageBox, QInputDialog,
    QHBoxLayout, QMenu, QTabBar, QFormLayout, QDialog, QLineEdit,
    QDialogButtonBox, QStyle, QProgressDialog, QRadioButton, QButtonGroup,
    QStatusBar, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, QSize, QTranslator, QLocale, QLibraryInfo

# Core Imports
from core.data_manager import DataManager
from core.yaml_generator import YAMLGenerator
from core.models import RecyclarrConfiguration, InstanceConfig
from core.worker import SyncWorker

# UI Imports
from ui.styles import CinemaTheme, GLOBAL_STYLESHEET
from ui.widgets.include_tree import IncludeTreeWidget
from ui.widgets.profile_builder import QualityProfileManager
from ui.widgets.cf_editor import CFEditor
from ui.widgets.quick_profile_dialog import QuickProfileDialog
from core.quick_profile import build_quick_profile, group_add_options, QDEF
from core.resolver import auto_groups, resolve, unreachable_min_scores
from dataclasses import replace
from core.paths import app_dir
from PySide6.QtWidgets import (QProgressDialog, QDialog, QRadioButton, QButtonGroup, 
                               QDialogButtonBox, QLineEdit, QMessageBox, QWidget,
                               QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
                               QMainWindow, QStatusBar, QPushButton, QGroupBox, 
                               QFormLayout, QComboBox, QTabBar, QMenu, QInputDialog)
from PySide6.QtGui import QIcon, QAction 
from PySide6.QtCore import Qt
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Set to True to enable automatic data update from GitHub at startup.
# Set to False for testing or offline development.
UPDATE_DATA_ON_STARTUP = True 

class InstanceSettingsDialog(QDialog):
    """Dialog to edit Base URL and API Key."""
    def __init__(self, parent=None, base_url="", api_key=""):
        super().__init__(parent)
        self.setWindowTitle("Connexion au serveur")
        self.resize(400, 150)
        layout = QFormLayout(self)
        
        self.edit_url = QLineEdit(base_url)
        self.edit_url.setPlaceholderText("http://localhost:7878")
        
        self.edit_key = QLineEdit(api_key)
        self.edit_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        
        layout.addRow("Adresse du serveur :", self.edit_url)
        layout.addRow("Clé d'API :", self.edit_key)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_values(self):
        return self.edit_url.text().strip(), self.edit_key.text().strip()

class CustomTabBar(QTabBar):
    """Tab Bar with context menu support."""
    def contextMenuEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx >= 0:
            menu = QMenu(self)
            action_edit = QAction("Modifier l'adresse et la clé d'API", self)
            action_edit.triggered.connect(lambda: self.edit_tab_settings(idx))
            menu.addAction(action_edit)
            
            action_rename = QAction("Renommer", self)
            action_rename.triggered.connect(lambda: self.rename_tab(idx))
            menu.addAction(action_rename)
            
            menu.exec(event.globalPos())
            
    def edit_tab_settings(self, index):
        # Find the widget associated with this tab
        # We need access to the QTabWidget to get the widget
        parent = self.parent() 
        if isinstance(parent, QTabWidget):
            widget = parent.widget(index)
            if hasattr(widget, "edit_connection_info"):
                widget.edit_connection_info()
                
    def rename_tab(self, index):
        parent = self.parent()
        if isinstance(parent, QTabWidget):
            old_name = parent.tabText(index)
            new_name, ok = QInputDialog.getText(self, "Renommer", "Nom du serveur :", text=old_name)
            if ok and new_name:
                parent.setTabText(index, new_name)
                # Update config name in widget
                widget = parent.widget(index)
                if hasattr(widget, "update_config_name"):
                    widget.update_config_name(new_name)

class InstanceEditor(QWidget):
    """
    Editor for a single instance (e.g. Radarr), containing the 3 Acts.
    """
    def __init__(self, data_manager, app_type="radarr"):
        super().__init__()
        self.data_manager = data_manager
        self.app_type = app_type
        
        # State
        self.config = InstanceConfig(name="default", base_url="", api_key="")
        self.loaded_group_options = {}  # custom_format_groups.add options read from a YAML
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # --- TAB 1: GÉNÉRAL (Config, Template, Logiciel) ---
        self.tab_general = QWidget()
        gen_layout = QFormLayout(self.tab_general)
        
        # Header Acte 1
        header_gen = QLabel("Étape 1 : connexion et profil de départ")
        header_gen.setProperty("class", "h2")
        gen_layout.addRow(header_gen)
        
        desc_gen = QLabel("Indiquez où se trouve votre serveur, puis choisissez comment créer votre profil.")
        desc_gen.setStyleSheet("color: #888; margin-bottom: 10px;")
        gen_layout.addRow(desc_gen)
        gen_layout.addRow(QLabel(" ")) # Spacer
        
        # 1.1 Basic Info (Name is handled via Tab Title, URL/Key via right click)
        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("http://localhost:8989" if self.app_type == "sonarr" else "http://localhost:7878")
        self.edit_url.textEdited.connect(lambda text: setattr(self.config, "base_url", text.strip()))
        gen_layout.addRow("Adresse du serveur :", self.edit_url)

        self.edit_key = QLineEdit()
        self.edit_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.edit_key.setPlaceholderText(f"Dans {self.app_type.capitalize()} : Settings > General > API Key")
        self.edit_key.textEdited.connect(lambda text: setattr(self.config, "api_key", text.strip()))
        gen_layout.addRow("Clé d'API :", self.edit_key)
        
        gen_layout.addRow(QLabel(" ")) # Spacer
        
        # 1.4 Quick wizard first: the simplest way to get a working profile
        hint_quick = QLabel("Le plus simple : l'assistant crée votre profil en quelques clics.")
        hint_quick.setStyleSheet("color: #888;")
        gen_layout.addRow(hint_quick)
        self.btn_quick = QPushButton("⚡ Assistant rapide (qualité, langue, codecs)…")
        self.btn_quick.clicked.connect(self.open_quick_wizard)
        gen_layout.addRow(self.btn_quick)

        hint_model = QLabel("Ou partez d'un modèle officiel, puis ajustez-le dans les onglets suivants :")
        hint_model.setStyleSheet("color: #888; margin-top: 10px;")
        gen_layout.addRow(hint_model)

        # 1.2 Quality Definition (types detected from TRaSH quality-size files)
        self.combo_qdef = QComboBox()
        qdef_types = {(q.get("content") or {}).get("type") or q.get("name")
                      for q in self.data_manager.get_includes_by_type(self.app_type, "quality-definitions")}
        default_type = QDEF[self.app_type]
        self.combo_qdef.addItems(sorted(qdef_types | {default_type}, key=lambda t: (t != default_type, t)))
        self.combo_qdef.setToolTip("Tailles minimum et maximum des fichiers recommandées par TRaSH pour ce type de contenu.")
        gen_layout.addRow("Tailles de fichiers :", self.combo_qdef)
        
        # 1.3 Template / Mode
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Aucun (je choisis moi-même)")
        
        # Load templates from DataManager
        templates = self.data_manager.get_templates_for_app(self.app_type)
        for t in templates:
            self.combo_mode.addItem(t.get("name", "Unnamed"), t)
            
        gen_layout.addRow("Modèle officiel :", self.combo_mode)
        self.combo_mode.currentIndexChanged.connect(self.on_template_changed)

        
        self.tabs.addTab(self.tab_general, "1. Connexion")
        
        # --- TAB 2: INCLUDES (Casting) ---
        self.act1_widget = IncludeTreeWidget(self.data_manager)
        self.act1_widget.load_for_app(self.app_type)
        self.act1_widget.selection_changed.connect(self._on_casting_changed) 
        self.tabs.addTab(self.act1_widget, "2. Profils")
        
        # --- TAB 3: QUALITY PROFILES (Mise en Scène) ---
        self.act2_widget = QualityProfileManager(self.app_type)
        self.tabs.addTab(self.act2_widget, "3. Réglages")
        
        # --- TAB 4: CUSTOM FORMATS (Effets Spéciaux) ---
        cfs_data = self.data_manager.get_custom_formats_for_app(self.app_type)
        self.act3_widget = CFEditor(cfs_data, available_profiles=[]) 
        self.tabs.addTab(self.act3_widget, "4. Scores")
        
        # Connect Tabs
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tabs)

    def on_template_changed(self, index):
        """Loads an official Recyclarr v8 template into the acts."""
        self.act3_widget.active_assignments.clear()
        self.loaded_group_options = {}

        if index == 0:
            # Custom/Manuel: Clear everything to start fresh
            self.act2_widget.sync_profiles([])
            self._select_casting([], [], [])
            self.act3_widget.sync_assignments_from_templates([])
            return

        template_data = self.combo_mode.itemData(index)
        if not template_data:
            return
        app_content = template_data.get("content", {}).get(self.app_type, {})
        instance_data = list(app_content.values())[0] if app_content else {}

        self._set_qdef(instance_data)
        self.act2_widget.sync_profiles(self._guide_profiles(instance_data))
        self._select_casting_from(instance_data)
        self._refresh_guide_scores()

    def open_quick_wizard(self):
        dialog = QuickProfileDialog(self.data_manager, self.app_type, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.apply_quick_profile(**dialog.get_values())
            except ValueError as e:
                QMessageBox.warning(self, "Assistant rapide", str(e))

    def apply_quick_profile(self, anime, tier, variant, accepted=()):
        """Replaces the instance setup with a TRaSH profile in the chosen language variant."""
        plan = build_quick_profile(self.data_manager, self.app_type, anime, tier, variant, accepted)
        # "Aucun" mode, cleared even if it was already selected
        self.combo_mode.blockSignals(True)
        self.combo_mode.setCurrentIndex(0)
        self.combo_mode.blockSignals(False)
        self.on_template_changed(0)
        self.combo_qdef.setCurrentText(plan["qdef"])

        profile = {**self.data_manager.get_quality_profile_by_id(plan["profile_trash_id"]), "active": True}
        if plan["score_set"]:
            profile["score_set"] = plan["score_set"]
        self.act2_widget.load_profiles([profile])
        self._select_casting([plan["profile_trash_id"]], plan["cf_groups"], [])
        self.act3_widget.load_assignments_from_template(plan["custom_formats"], clear_existing=True)
        self._refresh_guide_scores()

    def _set_qdef(self, data: dict):
        qdef = data.get("quality_definition", {})
        qdef_type = qdef.get("type") if isinstance(qdef, dict) else qdef
        if qdef_type:
            if self.combo_qdef.findText(str(qdef_type)) < 0:
                self.combo_qdef.addItem(str(qdef_type))
            self.combo_qdef.setCurrentText(str(qdef_type))

    def _guide_profiles(self, data: dict) -> list:
        """quality_profiles entries merged over their TRaSH guide profile (YAML keys win)."""
        profiles = []
        for qp in data.get("quality_profiles") or []:
            if not isinstance(qp, dict):
                continue
            guide_qp = self.data_manager.get_quality_profile_by_id(qp["trash_id"]) if qp.get("trash_id") else None
            # Without the key Recyclarr resets nothing: same as disabled
            profile = {"reset_unmatched_scores": {"enabled": False}, **qp, "active": True}
            profiles.append({**guide_qp, **profile} if guide_qp else profile)
        return profiles

    def _select_casting(self, profile_ids, add_ids, skip_ids):
        """Checks profiles and opt-in groups in Act 2, then marks the default groups Recyclarr auto-syncs."""
        self.act1_widget.set_selected_includes(list(profile_ids) + list(add_ids))
        self.act1_widget.set_auto_groups(auto_groups(self.data_manager, self.app_type, profile_ids), skip=skip_ids)

    def _select_casting_from(self, data: dict):
        groups = data.get("custom_format_groups") or {}
        profile_ids = [qp["trash_id"] for qp in data.get("quality_profiles") or [] if isinstance(qp, dict) and qp.get("trash_id")]
        add_ids = [g["trash_id"] for g in groups.get("add") or [] if isinstance(g, dict) and g.get("trash_id")]
        self._select_casting(profile_ids, add_ids, groups.get("skip") or [])

    def _on_casting_changed(self):
        selected = self.act1_widget.get_selected_by_type("quality-profiles")
        self.act1_widget.set_auto_groups(auto_groups(self.data_manager, self.app_type, selected))

    def edit_connection_info(self):
        """Opens dialog to edit URL and Key."""
        dialog = InstanceSettingsDialog(self, self.config.base_url, self.config.api_key)
        if dialog.exec() == QDialog.Accepted:
            url, key = dialog.get_values()
            self.config.base_url = url
            self.config.api_key = key
            self._refresh_connection_fields()
            QMessageBox.information(self, "Serveur modifié", f"Réglages de {self.config.name} enregistrés.")

    def _refresh_connection_fields(self):
        # str(): a YAML can hold !secret / !env_var values, kept in the config unless the field is edited
        self.edit_url.setText(str(self.config.base_url or ""))
        self.edit_key.setText(str(self.config.api_key or ""))

    def update_config_name(self, text):
        self.config.name = text

    def on_tab_changed(self, index):
        # Index 2 = Act 3 (Mise en Scène / Quality Profiles)
        if index == 2:
            self._sync_act3_profiles()

        # Index 3 = Act 4 (Effets Spéciaux / Custom Formats)
        elif index == 3:
            self._refresh_guide_scores()

    def _sync_act3_profiles(self):
        """Syncs Act 3 profiles from Act 2 selections, keeping existing profiles and their edits."""
        selected = self.act1_widget.get_selected_by_type("quality-profiles")
        manager = self.act2_widget
        manager.profiles = [p for p in manager.profiles if not p.trash_id or p.trash_id in selected]
        present = {p.trash_id for p in manager.profiles}

        new_profiles_data = []
        for trash_id in selected:
            guide_qp = self.data_manager.get_quality_profile_by_id(trash_id)
            if guide_qp and trash_id not in present:
                # Checked in Act 2 means wanted in the config
                new_profiles_data.append({**guide_qp, "active": True})

        manager._import_profiles(new_profiles_data, source="include")
        manager.refresh_list()

    def _refresh_guide_scores(self):
        """Act 4 base layer: every CF score per profile exactly as Recyclarr will sync it (guide + groups)."""
        self._sync_act3_profiles()
        profiles = [p for p in self.act2_widget.get_profiles() if p.active]
        self.act3_widget.set_available_profiles(sorted(p.name for p in profiles))
        config = replace(self.get_config(), active_cfs=[])
        instance = YAMLGenerator()._generate_instance_config(config, default_qdef=QDEF[self.app_type])
        entries = [{"trash_ids": [tid], "assign_scores_to": [{"name": name, "score": score}]}
                   for name, p in resolve(instance, self.app_type, self.data_manager).items()
                   for tid, score in p["cfs"].items()]
        self.act3_widget.sync_assignments_from_templates(entries)

    def load_config(self, data: dict):
        """Populates the editor from a dictionary (YAML data)."""
        self.config.base_url = data.get("base_url", "")
        self.config.api_key = data.get("api_key", "")
        self._refresh_connection_fields()
        self.config.delete_old_custom_formats = data.get("delete_old_custom_formats", False)
        self._set_qdef(data)
        qdef = data.get("quality_definition")
        if qdef:
            self.config.quality_definition_type = self.combo_qdef.currentText()
        self.config.quality_definition_extra = {k: v for k, v in qdef.items() if k != "type"} if isinstance(qdef, dict) else {}
        self.config.yaml_extra = {k: data[k] for k in ("media_naming", "media_management") if data.get(k)}
        # v7 `template:` includes no longer exist in v8 (load_yaml_config warns about them)
        includes = [i for i in data.get("include") or [] if "template" not in i]
        if includes:
            self.config.yaml_extra["include"] = includes

        self.act3_widget.active_assignments.clear()
        profiles = self._guide_profiles(data)
        self.act2_widget.load_profiles(profiles)
        self._select_casting_from(data)
        groups_add = (data.get("custom_format_groups") or {}).get("add") or []
        self.loaded_group_options = {g["trash_id"]: {k: v for k, v in g.items() if k != "trash_id"}
                                     for g in groups_add if isinstance(g, dict) and len(g) > 1}
        self.act3_widget.load_assignments_from_template(self._assign_by_name(data.get("custom_formats") or [], profiles),
                                                        clear_existing=True)

    @staticmethod
    def _assign_by_name(custom_formats: list, profiles: list) -> list:
        """custom_formats with assign_scores_to references by trash_id turned into names (Act 4 keys scores by name)."""
        names = {}
        for p in profiles:
            if p.get("trash_id") and p.get("name"):
                names.setdefault(p["trash_id"], []).append(p["name"])
        result = []
        for entry in custom_formats:
            assigns = []
            for a in entry.get("assign_scores_to") or []:
                if a.get("trash_id"):
                    if a["trash_id"] not in names:
                        logger.warning(f"assign_scores_to ignored: profile {a['trash_id']} is not in quality_profiles")
                    # A trash_id targets every variant of the profile
                    assigns += [{**{k: v for k, v in a.items() if k != "trash_id"}, "name": n} for n in names.get(a["trash_id"], [])]
                else:
                    assigns.append(a)
            result.append({**entry, "assign_scores_to": assigns})
        return result

    def get_config(self) -> InstanceConfig:
        """Collect data from all widgets."""
        self.config.quality_definition_type = self.combo_qdef.currentText()
        added, self.config.cf_group_skip = self.act1_widget.group_state()
        # An auto-synced group listed in `add` customizes its CFs (exclude, select...): keep it if still checked
        checked = self.act1_widget.get_selected_by_type("custom-formats")
        self.config.includes_cfs = added + [g for g in self.loaded_group_options if g in checked and g not in added]
        self.config.custom_profiles = self.act2_widget.get_profiles()
        # Added groups get what Recyclarr needs to apply them (assign_scores_to, select...) unless the YAML set it
        targets = [(p.name, p.trash_id, p.score_set or (self.data_manager.get_quality_profile_by_id(p.trash_id) or {}).get("score_set"))
                   for p in self.config.custom_profiles if p.active]
        self.config.cf_group_options = {
            gid: self.loaded_group_options.get(gid) or group_add_options(self.data_manager, self.app_type, gid, targets)
            for gid in self.config.includes_cfs
        }
        self.config.active_cfs = list(self.act3_widget.active_assignments.values())
        return self.config

    def is_blank(self) -> bool:
        """Tab left untouched: writing it would make `recyclarr sync` stop on a server that was never set up."""
        config = self.get_config()
        return not (config.api_key or config.active_cfs or any(p.active for p in config.custom_profiles))

    def problems(self) -> list:
        """What would make this instance fail in Recyclarr, in words a beginner can act on."""
        config = self.get_config()
        found = []
        if not config.api_key:
            found.append(f"{config.name} : la clé d'API manque (étape 1).")
        instance = YAMLGenerator()._generate_instance_config(config, default_qdef=QDEF[self.app_type])
        for name, minimum, total in unreachable_min_scores(instance, self.app_type, self.data_manager):
            found.append(f"{config.name} : Recyclarr refusera le profil « {name} » : son score minimum ({minimum}) "
                         f"dépasse le total de ses scores positifs ({total}).")
        return found

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recyclarr Configurator")
        self.resize(1200, 800)
        
        # Data Manager
        self.data_manager = DataManager()
        
        # Update Logic
        if UPDATE_DATA_ON_STARTUP:
            self.start_initial_sync()
        else:
             # Direct Load
            if not self.data_manager.load_data():
                QMessageBox.critical(self, "Erreur", "Impossible de charger les données TRaSH (fichiers json).")
            self.setup_ui()

    def start_initial_sync(self):
        """Starts the background worker to update data."""
        self.progress_dialog = QProgressDialog("Mise à jour des données TRaSH (GitHub)…", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        
        self.worker = SyncWorker()
        self.worker.progress.connect(self.update_sync_progress)
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.error.connect(self.on_sync_error)
        
        self.progress_dialog.show()
        self.worker.start()
        
    def update_sync_progress(self, msg):
        self.progress_dialog.setLabelText(msg)
        
    def on_sync_finished(self):
        self.progress_dialog.cancel()
        if not self.data_manager.load_data():
             QMessageBox.critical(self, "Erreur", "Impossible de charger les données mises à jour.")
        else:
              QMessageBox.information(self, "Terminé", "Données TRaSH à jour !")
        
        self.setup_ui()
        self.show()

    def on_sync_error(self, err):
        self.progress_dialog.cancel()
        QMessageBox.warning(self, "Attention", f"Mise à jour impossible : {err}\nLes données déjà présentes sont utilisées.")
        if not self.data_manager.load_data():
            QMessageBox.critical(self, "Erreur", "Impossible de charger les données locales.")
        self.setup_ui()
        self.show()



    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5) # Reduce margins for cleaner look
        
        # Instance Tabs
        # Instance Tabs
        self.tabs = QTabWidget()
        # Install Custom Tab Bar
        self.tab_bar = CustomTabBar(self.tabs)
        self.tabs.setTabBar(self.tab_bar)
        
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True) 
        
        # 1. Enable Scroll Buttons to prevent window from expanding infinitely
        self.tab_bar.setUsesScrollButtons(True) 
        self.tabs.setUsesScrollButtons(True)

        # 2. HIDE the native scroll buttons via CSS so only ours are visible
        #    Also verify the close button style
        self.tabs.setStyleSheet("""
            QTabBar::scroller { width: 0px; height: 0px; }
            QTabBar::close-button { subcontrol-position: right; }
        """)
        
        self.tabs.tabCloseRequested.connect(self.remove_instance_by_index)
        
        # --- Right Corner Actions (Prev, Next, Add, Del, Gen) ---
        # We group EVERYTHING in the TopRightCorner to ensure visibility and clean layout
        right_corner_widget = QWidget()
        right_corner_layout = QHBoxLayout(right_corner_widget)
        right_corner_layout.setContentsMargins(0, 0, 0, 0)
        right_corner_layout.setSpacing(2)
        
        # Style for Nav Buttons
        # Style for Nav Buttons
        nav_btn_style = """
            QPushButton { 
                border: 1px solid #555; 
                background-color: #333333; 
                border-radius: 4px;
                margin: 0px;
                padding: 0px;
            } 
            QPushButton:hover { 
                background-color: #555555;
                border-color: #00e5ff;
            }
        """

        # Previous
        self.btn_prev_tab = QPushButton()
        self.btn_prev_tab.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.btn_prev_tab.setFixedSize(30, 30)
        self.btn_prev_tab.setIconSize(QSize(16, 16))
        self.btn_prev_tab.setToolTip("Serveur précédent")
        self.btn_prev_tab.setStyleSheet(nav_btn_style)
        self.btn_prev_tab.clicked.connect(self.select_prev_tab)
        right_corner_layout.addWidget(self.btn_prev_tab)

        # Next
        self.btn_next_tab = QPushButton()
        self.btn_next_tab.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.btn_next_tab.setFixedSize(30, 30)
        self.btn_next_tab.setIconSize(QSize(16, 16))
        self.btn_next_tab.setToolTip("Serveur suivant")
        self.btn_next_tab.setStyleSheet(nav_btn_style)
        self.btn_next_tab.clicked.connect(self.select_next_tab)
        right_corner_layout.addWidget(self.btn_next_tab)

        # Spacing Separator
        lbl_h_sep = QLabel("|")
        lbl_h_sep.setStyleSheet("color: #555; font-weight: bold; margin-left: 5px; margin-right: 5px;")
        right_corner_layout.addWidget(lbl_h_sep)
        
        # Add (Existing logic)
        self.btn_add_tab = QPushButton("+ Ajouter")
        self.btn_add_tab.setFixedHeight(30)
        self.btn_add_tab.setStyleSheet("""
            QPushButton { background-color: #ff4500; color: white; border: none; font-weight: bold; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #ff6e40; }
        """)
        self.btn_add_tab.clicked.connect(self.show_add_instance_dialog) # Changed from add_new_instance_tab
        right_corner_layout.addWidget(self.btn_add_tab)
        
        # Delete (Existing logic)
        self.btn_del_tab = QPushButton("Supprimer")
        self.btn_del_tab.setFixedHeight(30)
        self.btn_del_tab.setStyleSheet("""
            QPushButton { background-color: #ff4444; color: white; border: none; font-weight: bold; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #ff6666; }
        """)
        self.btn_del_tab.clicked.connect(self.remove_current_instance) # Changed from delete_current_instance
        right_corner_layout.addWidget(self.btn_del_tab)
        
        # Separator
        lbl_sep_2 = QLabel("|")
        lbl_sep_2.setStyleSheet("color: #555; font-weight: bold;")
        right_corner_layout.addWidget(lbl_sep_2)

        # Load YAML
        self.btn_load_yaml = QPushButton("Ouvrir un YAML")
        self.btn_load_yaml.setFixedHeight(30)
        self.btn_load_yaml.setStyleSheet("""
            QPushButton { background-color: #6200ea; color: white; border: none; font-weight: bold; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #7c43bd; }
        """)
        self.btn_load_yaml.clicked.connect(self.load_yaml_config)
        right_corner_layout.addWidget(self.btn_load_yaml)
        
        # Separator
        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("color: #555; font-weight: bold;")
        right_corner_layout.addWidget(lbl_sep)

        # Gen YAML (Existing)
        self.btn_gen_yaml = QPushButton("Générer le YAML")
        self.btn_gen_yaml.setFixedHeight(30)
        self.btn_gen_yaml.setStyleSheet("""
            QPushButton { background-color: #00e5ff; color: black; border: none; font-weight: bold; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #80f2ff; }
        """)
        self.btn_gen_yaml.clicked.connect(self.generate_yaml) # Changed from generate_final_yaml
        right_corner_layout.addWidget(self.btn_gen_yaml)
        
        self.tabs.setCornerWidget(right_corner_widget, Qt.TopRightCorner)
        
        main_layout.addWidget(self.tabs)
        
        # Status Bar (keep it at bottom)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Initial Default Instances
        self.add_instance("radarr", "Radarr")
        self.add_instance("sonarr", "Sonarr")
        
    def select_prev_tab(self):
        curr = self.tabs.currentIndex()
        if curr > 0:
            self.tabs.setCurrentIndex(curr - 1)
            
    def select_next_tab(self):
        curr = self.tabs.currentIndex()
        if curr < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(curr + 1)

    def show_add_instance_dialog(self):
        """Dialog to create a new instance."""
        # Simple dialog: Type (Radio), Name (Line)
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau serveur")
        layout = QVBoxLayout(dialog)
        
        # Type Selection
        layout.addWidget(QLabel("Application :"))
        type_group = QButtonGroup(dialog)
        
        rb_radarr = QRadioButton("Radarr")
        rb_radarr.setChecked(True)
        type_group.addButton(rb_radarr, 1)
        layout.addWidget(rb_radarr)
        
        rb_sonarr = QRadioButton("Sonarr")
        type_group.addButton(rb_sonarr, 2)
        layout.addWidget(rb_sonarr)
        
        # Name
        layout.addWidget(QLabel("Nom du serveur :"))
        name_edit = QLineEdit("mon-serveur")
        layout.addWidget(name_edit)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec() == QDialog.Accepted:
            app_type = "radarr" if rb_radarr.isChecked() else "sonarr"
            name = name_edit.text().strip() or f"mon-{app_type}"
            self.add_instance(app_type, name)

    def add_instance(self, app_type, name):
        """Creates and adds a new instance tab."""
        # Check uniqueness of name? Recyclarr needs unique keys but displayed name is flexible.
        # We'll use the editor.
        editor = InstanceEditor(self.data_manager, app_type)
        # Assuming we can set the name in the editor
        # Update: InstanceEditor init sets a default name "My Radarr".
        # We should update it.
        editor.config.name = name 
        # Update UI header if we had one, but we skipped it in previous step.
        # Let's just use the tab title.
        
        icon = QIcon() # Placeholder or app specific icon
        self.tabs.addTab(editor, name)
        self.tabs.setCurrentWidget(editor)
        self.status_bar.showMessage(f"Serveur « {name} » ajouté.", 3000)

    def remove_current_instance(self):
        idx = self.tabs.currentIndex()
        if idx != -1:
            self.remove_instance_by_index(idx)
            
    def remove_instance_by_index(self, index):
        name = self.tabs.tabText(index)
        confirm = QMessageBox.question(self, "Supprimer", f"Supprimer le serveur « {name} » ?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.tabs.removeTab(index)
            self.status_bar.showMessage(f"Serveur « {name} » supprimé.", 3000)

    def generate_yaml(self):
        radarr_instances = []
        sonarr_instances = []

        editors = [self.tabs.widget(i) for i in range(self.tabs.count())]
        editors = [e for e in editors if isinstance(e, InstanceEditor) and not e.is_blank()]
        if not editors:
            QMessageBox.information(self, "Rien à générer",
                                    "Choisissez d'abord un profil : utilisez l'assistant rapide de l'étape 1.")
            return
        # Recyclarr silently syncs nothing (exit code 0) when two instances share a name, even across Radarr and Sonarr
        names = [e.config.name for e in editors]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        if duplicates:
            QMessageBox.warning(self, "Deux serveurs portent le même nom",
                                f"Nom en double : {', '.join(duplicates)}.\n\n"
                                "Recyclarr ne synchronise rien si deux serveurs ont le même nom, même un Radarr et un Sonarr. "
                                "Faites un clic droit sur l'onglet, puis « Renommer ».")
            return
        problems = [p for e in editors for p in e.problems()]
        if problems and QMessageBox.question(self, "Vérifiez votre configuration",
                                             "\n\n".join(problems) + "\n\nGénérer quand même ?",
                                             QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        for editor in editors:
            config = editor.get_config()
            if editor.app_type == "radarr":
                radarr_instances.append(config)
            elif editor.app_type == "sonarr":
                sonarr_instances.append(config)
        
        full_config = RecyclarrConfiguration(
            radarr_instances=radarr_instances,
            sonarr_instances=sonarr_instances
        )
        
        # Portable: let the user pick the file, defaulting next to the app (not the shortcut's cwd)
        target, _ = QFileDialog.getSaveFileName(self, "Enregistrer la configuration Recyclarr",
                                                str(app_dir() / "recyclarr.yml"), "Fichiers YAML (*.yml *.yaml)")
        if not target:
            return

        generator = YAMLGenerator()
        try:
            path = generator.generate_config(full_config, filename=target)
            QMessageBox.information(self, "Fichier créé", (
                f"Fichier créé :\n{path}\n\n"
                "Étapes suivantes :\n"
                "1. Installez Recyclarr : https://recyclarr.dev/guide/installation/\n"
                f'2. Vérifiez sans rien changer : recyclarr sync --preview --config "{path}"\n'
                f'3. Appliquez : recyclarr sync --config "{path}"\n\n'
                "Une ligne qui commence par [ERR] signale quelque chose qui n'a pas été appliqué."))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def load_yaml_config(self):
        """Loads a config.yml file and repopulates the tabs."""
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir une configuration", "", "Fichiers YAML (*.yml *.yaml)")
        if not path:
            return
            
        generator = YAMLGenerator()
        try:
            data = generator.load_yaml(path)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le fichier :\n{e}")
            return
            
        # Confirm overwrite
        if self.tabs.count() > 0:
            resp = QMessageBox.question(self, "Remplacer ?", 
                                        "Ouvrir un fichier ferme les onglets actuels. Continuer ?",
                                        QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes:
                return
        
        # Clear tabs
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
            
        # Process Radarr
        radarr_data = data.get("radarr", {})
        # Warning: radarr_data might be a dict (instances) or list? Recyclarr usually uses dict for named instances.
        if isinstance(radarr_data, dict):
            for name, config_data in radarr_data.items():
                self.add_instance("radarr", name)
                # Get the newly created editor
                editor = self.tabs.widget(self.tabs.count() - 1)
                if isinstance(editor, InstanceEditor):
                    editor.load_config(config_data)
                
        # Process Sonarr
        sonarr_data = data.get("sonarr", {})
        if isinstance(sonarr_data, dict):
            for name, config_data in sonarr_data.items():
                self.add_instance("sonarr", name)
                editor = self.tabs.widget(self.tabs.count() - 1)
                if isinstance(editor, InstanceEditor):
                    editor.load_config(config_data)
                
        # Recyclarr v8 removed the official include templates: say what was dropped
        v7 = [inc["template"] for app in ("radarr", "sonarr") for inst in (data.get(app) or {}).values()
              if isinstance(inst, dict) for inc in inst.get("include") or [] if isinstance(inc, dict) and "template" in inc]
        if v7:
            QMessageBox.warning(self, "Modèles Recyclarr v7",
                                "Ces modèles v7 n'existent plus dans Recyclarr v8 et ont été ignorés :\n"
                                + "\n".join(v7) + "\n\nChoisissez un modèle officiel ou l'assistant rapide (étape 1).")
        QMessageBox.information(self, "Terminé", "Configuration ouverte !")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # French standard buttons and dialogs (OK/Annuler, Oui/Non)
    translator = QTranslator(app)
    if translator.load(QLocale("fr"), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
    
    # Apply Theme
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
