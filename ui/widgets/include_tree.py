from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                               QLabel, QHeaderView, QSplitter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from ui.styles import CinemaTheme

class IncludeTreeWidget(QWidget):
    """
    Act 1: Template Selection.
    Displays available templates in a tree structure:
    - Quality Definitions
    - Quality Profiles (Prefab)
    - Custom Formats (Packs)
    """
    selection_changed = Signal()

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_lbl = QLabel("Acte 2 : Le Casting")
        header_lbl.setProperty("class", "h2") 
        layout.addWidget(header_lbl)
        
        desc_lbl = QLabel("Sélectionnez les modèles à inclure (templates).")
        desc_lbl.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(desc_lbl)


        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree)

        self.populate_tree()

    def populate_tree(self):
        """Populates the tree with categories from templates.json."""
        self.tree.clear()
        
        # We need to know which app we are currently configuring. 
        # For now, let's assume this widget is reused or updated when app changes.
        # But commonly, we might pass the app name to populate.
        # I'll add a method `load_for_app(app_name)`
        pass

    def load_for_app(self, app_name: str, current_config=None):
        self.tree.clear()
        
        templates = self.data_manager.get_templates_for_app(app_name)
        
        root_defs = QTreeWidgetItem(self.tree, ["Définitions de Qualité"])
        root_defs.setExpanded(True)
        
        root_profiles = QTreeWidgetItem(self.tree, ["Profils Préfabriqués"])
        root_profiles.setExpanded(True)
        
        root_cfs = QTreeWidgetItem(self.tree, ["Packs de Formats (Custom Formats)"])
        root_cfs.setExpanded(True)
        
        root_templates = QTreeWidgetItem(self.tree, ["Templates Complets (Bundles)"])
        root_templates.setExpanded(True)
        
        others = QTreeWidgetItem(self.tree, ["Autres"])

        # Set of already added IDs to avoid duplicates
        added_ids = set()

        # 1. First, add the Top-Level Templates (Bundles)
        for template in templates:
            name = template.get("name", template.get("id", "Unknown"))
            description = template.get("description", "")
            
            if name in added_ids: continue
            
            item = QTreeWidgetItem([name])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setToolTip(0, description)
            
            if current_config and name in current_config.includes:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)
            
            item.setData(0, Qt.UserRole, name)
            root_templates.addChild(item)
            added_ids.add(name)

        # 2. Now extract all granual includes from these templates
        # We want to list ALL possibilities Recyclarr knows about.
        # However, templates.json ONLY lists the composite templates.
        # It DOES NOT list the available "raw" includes like 'radarr-quality-definition-sqp-1' as separate searchable objects with descriptions.
        # But we can find them listed inside the 'includes' list of the templates.
        
        unique_includes = set()
        for t in templates:
            for inc in t.get("includes", []):
                unique_includes.add(inc)
                
        # Now add these unique includes to the tree
        for inc_name in sorted(list(unique_includes)):
            if inc_name in added_ids: continue
            
            item = QTreeWidgetItem([inc_name])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # We don't have a description for these raw includes from templates.json sadly, 
            # unless we fetch it from somewhere else. For now, use name.
            item.setToolTip(0, inc_name) 
            
            if current_config and inc_name in current_config.includes:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)
            
            item.setData(0, Qt.UserRole, inc_name)
            
            # Categorization logic
            lower = inc_name.lower()
            if "quality-definition" in lower:
                root_defs.addChild(item)
            elif "quality-profile" in lower:
                root_profiles.addChild(item)
            elif "custom-formats" in lower:
                root_cfs.addChild(item)
            else:
                others.addChild(item)
            
            added_ids.add(inc_name)

    def get_selected_templates(self):
        """Returns list of selected template IDs."""
        selected = []
        iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            template_id = item.data(0, Qt.UserRole)
            if template_id:
                selected.append(template_id)
            iterator += 1
        return selected

    def _on_item_changed(self, item, column):
        self.selection_changed.emit()

from PySide6.QtWidgets import QTreeWidgetItemIterator
