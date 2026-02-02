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
from PySide6.QtCore import Qt, QSize

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
UPDATE_DATA_ON_STARTUP = False 

class InstanceSettingsDialog(QDialog):
    """Dialog to edit Base URL and API Key."""
    def __init__(self, parent=None, base_url="", api_key=""):
        super().__init__(parent)
        self.setWindowTitle("Connection Settings")
        self.resize(400, 150)
        layout = QFormLayout(self)
        
        self.edit_url = QLineEdit(base_url)
        self.edit_url.setPlaceholderText("http://localhost:7878")
        
        self.edit_key = QLineEdit(api_key)
        self.edit_key.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        
        layout.addRow("Base URL:", self.edit_url)
        layout.addRow("API Key:", self.edit_key)
        
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
            action_edit = QAction("Edit URL & API Key", self)
            action_edit.triggered.connect(lambda: self.edit_tab_settings(idx))
            menu.addAction(action_edit)
            
            action_rename = QAction("Rename", self)
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
            new_name, ok = QInputDialog.getText(self, "Rename", "Instance Name:", text=old_name)
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
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # --- TAB 1: GÉNÉRAL (Config, Template, Logiciel) ---
        self.tab_general = QWidget()
        gen_layout = QFormLayout(self.tab_general)
        
        # Header Acte 1
        header_gen = QLabel("Act 1: The Script")
        header_gen.setProperty("class", "h2")
        gen_layout.addRow(header_gen)
        
        desc_gen = QLabel("Configure the identity of the instance and its base model.")
        desc_gen.setStyleSheet("color: #888; margin-bottom: 10px;")
        gen_layout.addRow(desc_gen)
        gen_layout.addRow(QLabel(" ")) # Spacer
        
        # 1.1 Basic Info (Name is handled via Tab Title, URL/Key via right click)
        self.lbl_info = QLabel("<i>(Right-click on the tab to edit URL & API Key)</i>")
        self.lbl_info.setStyleSheet("color: #888;")
        gen_layout.addRow(self.lbl_info)
        
        gen_layout.addRow(QLabel(" ")) # Spacer
        
        # 1.2 Quality Definition
        self.combo_qdef = QComboBox()
        if self.app_type == "radarr":
            self.combo_qdef.addItems(["movie", "anime"]) # Radarr types
        else:
            self.combo_qdef.addItems(["series", "anime"]) # Sonarr types
        gen_layout.addRow("Quality Definition Type:", self.combo_qdef)
        
        # 1.3 Template / Mode
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Custom (Manual)")
        
        # Load templates from DataManager
        templates = self.data_manager.get_templates_for_app(self.app_type)
        for t in templates:
            self.combo_mode.addItem(t.get("name", "Unnamed"), t)
            
        gen_layout.addRow("Profile Model:", self.combo_mode)
        self.combo_mode.currentIndexChanged.connect(self.on_template_changed)
        
        self.tabs.addTab(self.tab_general, "Act 1: Script")
        
        # --- TAB 2: INCLUDES (Casting) ---
        self.act1_widget = IncludeTreeWidget(self.data_manager)
        self.act1_widget.load_for_app(self.app_type) 
        self.tabs.addTab(self.act1_widget, "Act 2: Casting")
        
        # --- TAB 3: QUALITY PROFILES (Mise en Scène) ---
        self.act2_widget = QualityProfileManager()
        self.tabs.addTab(self.act2_widget, "Act 3: Staging")
        
        # --- TAB 4: CUSTOM FORMATS (Effets Spéciaux) ---
        cfs_data = self.data_manager.get_custom_formats_for_app(self.app_type)
        self.act3_widget = CFEditor(cfs_data, available_profiles=[]) 
        self.tabs.addTab(self.act3_widget, "Act 4: Special Effects")
        
        # Connect Tabs
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tabs)

    def on_template_changed(self, index):
        """Loads template data into other tabs."""
        # Always clear active overrides when changing mode/template
        self.act3_widget.active_assignments.clear()

        if index == 0:
            # Custom/Manuel: Clear everything to start fresh
            self.act1_widget.set_selected_includes([])
            self.act3_widget.sync_assignments_from_templates([])
            return
            
        template_data = self.combo_mode.itemData(index)
        if not template_data:
            return
            
        # 1. Update Tab 2 (Includes)
        includes = template_data.get("includes", [])
        self.act1_widget.set_selected_includes(includes)
        
        # 2. Update Tab 4 (CF Assignments)
        # Parse content -> app -> instance_key -> custom_formats
        try:
            # Recursively resolve ALL custom_formats from includes + template itself
            merged_cfs = self.data_manager.resolve_template_includes(self.app_type, template_data)
            
            # Also check the top-level 'content' for the main template's direct CFs (which resolve_template_includes does, but let's be sure we are looking at the right structure)
            # resolve_template_includes looks at 'custom_formats' key at root of template/include.
            # But in 'templates.json', for the main template, it is nested in 'content -> app -> [config] -> custom_formats'.
            # Wait, resolve_template_includes expects the dict having 'custom_formats'.
            
            # For the main template, we need to extract the 'custom_formats' list from the nested structure FIRST, 
            # OR pass the nested structure as a "virtual include"?
            
            # Actually, let's look at a template structure:
            # { "name": ..., "includes": [...], "content": { "sonarr": { "hd-bluray-web": { "custom_formats": [...] } } } }
            
            # My resolve_template_includes checks `root_template["custom_formats"]`.
            # So for the root template, I need to extract the CFs from the content first and pass it, OR update logic.
            # But included templates (raw includes) often have `custom_formats` at top level (for CF includes) OR inside content (for profile bundles).
            
            # Let's simple append the root template's nested CFs manually to the resolved list from includes.
            
            # 1. Get Includes CFs
            resolved_cfs = self.data_manager.resolve_template_includes(self.app_type, template_data)
            
            # 2. Get Root Template CFs (if any, nested in content)
            app_content = template_data.get("content", {}).get(self.app_type, {})
            if app_content:
                config_key = list(app_content.keys())[0]
                config_data = app_content[config_key]
                if config_data:
                    root_cfs = config_data.get("custom_formats") or []
                    if isinstance(root_cfs, list):
                        resolved_cfs.extend(root_cfs)
                    else:
                        logger.warning(f"Ignored non-list custom_formats in root template: {type(root_cfs)}")
                
            # Load as base layer (template assignments), not active overrides
            self.act3_widget.sync_assignments_from_templates(resolved_cfs)
        except Exception as e:
            import traceback
            logger.error(f"Error loading template CFs: {e}")
            logger.error(traceback.format_exc())
            
        # 3. Update Tab 3 (Profile)
        # Find which include is the quality profile
        # Heuristic: contains "quality-profile" in name
        qp_include_name = next((inc for inc in includes if "quality-profile" in inc), None)
        
        if qp_include_name:
             # Just trigger sync logic which we moved to separate method, 
             # but we can't easily call it without events. 
             # For now, rely on Tab Change to sync.
             pass

        
    def edit_connection_info(self):
        """Opens dialog to edit URL and Key."""
        dialog = InstanceSettingsDialog(self, self.config.base_url, self.config.api_key)
        if dialog.exec() == QDialog.Accepted:
            url, key = dialog.get_values()
            self.config.base_url = url
            self.config.api_key = key
            QMessageBox.information(self, "Instance Updated", f"Settings for {self.config.name} saved.")

    def update_config_name(self, text):
        self.config.name = text
        
    def on_tab_changed(self, index):
        # Index 2 = Act 3 (Mise en Scène / Quality Profiles)
        if index == 2:
            self._sync_act3_profiles()

        # Index 3 = Act 4 (Effets Spéciaux / Custom Formats)
        elif index == 3: 
            self._sync_act4_cfs()

    def _sync_act3_profiles(self):
        """Syncs Act 3 profiles from Act 2 selections."""
        selected_includes = self.act1_widget.get_selected_templates()
        new_profiles_data = []

        for inc_name in selected_includes:
            # Heuristic: Name contains "quality-profile"
            if "quality-profile" in inc_name.lower():
                # Loop up include data
                inc_data = self.data_manager.get_include_data(self.app_type, inc_name)
                if inc_data and "content" in inc_data:
                    qp_list = inc_data["content"].get("quality_profiles", [])
                    new_profiles_data.extend(qp_list)

        # Call sync on Act 2 widget (Profile Manager)
        # It handles preserving custom profiles + refreshing includes
        if new_profiles_data:
            self.act2_widget.sync_profiles(new_profiles_data)
        else:
             self.act2_widget.sync_profiles([])

    def _sync_act4_cfs(self):
        """Syncs Act 4 CFs from Act 2 selections and Act 3 profiles."""
        
        # 1. Update Columns (Available Profiles from Act 3)
        current_profiles = self.act2_widget.get_profiles()
        profile_names = [p.name for p in current_profiles]
        self.act3_widget.set_available_profiles(sorted(profile_names))
        
        # 2. Update Rows/Scores (From Act 2 CF Bundles)
        selected_includes = self.act1_widget.get_selected_templates()
        # We need to resolve all CFs from these includes
        resolved_cfs = []
        
        for inc_name in selected_includes:
            # Heuristic: Name contains "custom-formats"
            if "custom-formats" in inc_name.lower():
                inc_data = self.data_manager.get_include_data(self.app_type, inc_name)
                if inc_data:
                    content = inc_data.get("content", {})
                    # Try top level of content
                    cfs = content.get("custom_formats", [])
                    if cfs:
                        resolved_cfs.extend(cfs)
                    
                    # Try nested (standard recyclarr config structure)
                    app_c = content.get(self.app_type, {})
                    if app_c:
                         for k, v in app_c.items():
                             if isinstance(v, dict) and "custom_formats" in v:
                                 resolved_cfs.extend(v["custom_formats"])
        
        # Sync Act 4
        self.act3_widget.sync_assignments_from_templates(resolved_cfs)

    def get_config(self) -> InstanceConfig:
        """Collect data from all widgets."""
        # 1. Config (URL/Key are stored in self.config via dialog)
        # Name is synced
        
        # 2. Includes (categorized)
        self.config.includes_quality_defs = self.act1_widget.get_selected_by_type("quality-definition")
        self.config.includes_profiles = self.act1_widget.get_selected_by_type("quality-profiles")
        self.config.includes_cfs = self.act1_widget.get_selected_by_type("custom-formats")
        
        # 3. Profiles
        self.config.custom_profiles = self.act2_widget.get_profiles()
             
        # 4. CFs
        self.config.active_cfs = list(self.act3_widget.active_assignments.values())
        
        return self.config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recyclarr Configurator - Director's Cut")
        self.resize(1200, 800)
        
        # Data Manager
        self.data_manager = DataManager()
        
        # Update Logic
        if UPDATE_DATA_ON_STARTUP:
            self.start_initial_sync()
        else:
             # Direct Load
            if not self.data_manager.load_data():
                QMessageBox.critical(self, "Error", "Unable to load data files (json).")
            self.setup_ui()

    def start_initial_sync(self):
        """Starts the background worker to update data."""
        self.progress_dialog = QProgressDialog("Updating data (GitHub)...", "Cancel", 0, 0, self)
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
             QMessageBox.critical(self, "Error", "Unable to load updated data.")
        else:
              QMessageBox.information(self, "Success", "Data updated successfully!")
        
        self.setup_ui()
        self.show()

    def on_sync_error(self, err):
        self.progress_dialog.cancel()
        QMessageBox.warning(self, "Warning", f"Update failed: {err}\nLoading existing local data.")
        if not self.data_manager.load_data():
            QMessageBox.critical(self, "Error", "Unable to load local data.")
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
        self.btn_prev_tab.setToolTip("Previous tab")
        self.btn_prev_tab.setStyleSheet(nav_btn_style)
        self.btn_prev_tab.clicked.connect(self.select_prev_tab)
        right_corner_layout.addWidget(self.btn_prev_tab)

        # Next
        self.btn_next_tab = QPushButton()
        self.btn_next_tab.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.btn_next_tab.setFixedSize(30, 30)
        self.btn_next_tab.setIconSize(QSize(16, 16))
        self.btn_next_tab.setToolTip("Next tab")
        self.btn_next_tab.setStyleSheet(nav_btn_style)
        self.btn_next_tab.clicked.connect(self.select_next_tab)
        right_corner_layout.addWidget(self.btn_next_tab)

        # Spacing Separator
        lbl_h_sep = QLabel("|")
        lbl_h_sep.setStyleSheet("color: #555; font-weight: bold; margin-left: 5px; margin-right: 5px;")
        right_corner_layout.addWidget(lbl_h_sep)
        
        # Add (Existing logic)
        self.btn_add_tab = QPushButton("+ Add")
        self.btn_add_tab.setFixedHeight(30)
        self.btn_add_tab.setStyleSheet("""
            QPushButton { background-color: #ff4500; color: white; border: none; font-weight: bold; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #ff6e40; }
        """)
        self.btn_add_tab.clicked.connect(self.show_add_instance_dialog) # Changed from add_new_instance_tab
        right_corner_layout.addWidget(self.btn_add_tab)
        
        # Delete (Existing logic)
        self.btn_del_tab = QPushButton("Delete")
        self.btn_del_tab.setFixedHeight(30)
        self.btn_del_tab.setStyleSheet("""
            QPushButton { background-color: #ff4444; color: white; border: none; font-weight: bold; padding: 0 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #ff6666; }
        """)
        self.btn_del_tab.clicked.connect(self.remove_current_instance) # Changed from delete_current_instance
        right_corner_layout.addWidget(self.btn_del_tab)
        
        # Separator
        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("color: #555; font-weight: bold;")
        right_corner_layout.addWidget(lbl_sep)

        # Gen YAML (Existing)
        self.btn_gen_yaml = QPushButton("Generate YAML")
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
        dialog.setWindowTitle("New Instance")
        layout = QVBoxLayout(dialog)
        
        # Type Selection
        layout.addWidget(QLabel("Application Type:"))
        type_group = QButtonGroup(dialog)
        
        rb_radarr = QRadioButton("Radarr")
        rb_radarr.setChecked(True)
        type_group.addButton(rb_radarr, 1)
        layout.addWidget(rb_radarr)
        
        rb_sonarr = QRadioButton("Sonarr")
        type_group.addButton(rb_sonarr, 2)
        layout.addWidget(rb_sonarr)
        
        # Name
        layout.addWidget(QLabel("Instance Name:"))
        name_edit = QLineEdit("My Instance")
        layout.addWidget(name_edit)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec() == QDialog.Accepted:
            app_type = "radarr" if rb_radarr.isChecked() else "sonarr"
            name = name_edit.text().strip() or f"My {app_type.capitalize()}"
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
        self.status_bar.showMessage(f"Instance '{name}' added.", 3000)

    def remove_current_instance(self):
        idx = self.tabs.currentIndex()
        if idx != -1:
            self.remove_instance_by_index(idx)
            
    def remove_instance_by_index(self, index):
        name = self.tabs.tabText(index)
        confirm = QMessageBox.question(self, "Delete", f"Do you really want to delete instance '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.tabs.removeTab(index)
            self.status_bar.showMessage(f"Instance '{name}' deleted.", 3000)

    def generate_yaml(self):
        radarr_instances = []
        sonarr_instances = []

        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if isinstance(editor, InstanceEditor):
                config = editor.get_config()
                if editor.app_type == "radarr":
                    radarr_instances.append(config)
                elif editor.app_type == "sonarr":
                    sonarr_instances.append(config)
        
        full_config = RecyclarrConfiguration(
            radarr_instances=radarr_instances,
            sonarr_instances=sonarr_instances
        )
        
        # Generate
        generator = YAMLGenerator()
        try:
            path = generator.generate_config(full_config)
            QMessageBox.information(self, "Success", f"File generated:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Apply Theme
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
