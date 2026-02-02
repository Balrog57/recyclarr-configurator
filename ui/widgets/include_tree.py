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
        header_lbl = QLabel("Act 2: The Casting")
        header_lbl.setProperty("class", "h2") 
        layout.addWidget(header_lbl)
        
        desc_lbl = QLabel("Select models to include (templates).")
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
        
        root_defs = QTreeWidgetItem(self.tree, ["Quality Definitions"])
        root_defs.setExpanded(True)
        root_defs.setFlags(root_defs.flags() & ~Qt.ItemIsUserCheckable)
        
        root_profiles = QTreeWidgetItem(self.tree, ["Prefab Profiles"])
        root_profiles.setExpanded(True)
        root_profiles.setFlags(root_profiles.flags() & ~Qt.ItemIsUserCheckable)
        
        root_cfs = QTreeWidgetItem(self.tree, ["Format Packs (Custom Formats)"])
        root_cfs.setExpanded(True)
        root_cfs.setFlags(root_cfs.flags() & ~Qt.ItemIsUserCheckable)
        
        # Set of already added IDs to avoid duplicates
        added_ids = set()

        # 2. Extract ALL possible templates/includes.
        unique_includes = set()
        
        # 1. Bundled Templates & their includes
        for t in templates:
            name = t.get("name")
            if name: unique_includes.add(name)
            for inc in t.get("includes", []):
                unique_includes.add(inc)

        # 2. Raw/Orphan Includes (quality-defs, quality-profiles, etc.)
        raw_includes_data = self.data_manager.get_app_includes(app_name)
        # Defines mappings: key in JSON -> loop over items -> add 'name'
        # keys: "quality-definitions", "quality-profiles", "custom-formats"
        for category_key, items in raw_includes_data.items():
            for item in items:
                name = item.get("name")
                if name:
                    unique_includes.add(name)

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
            elif "custom-format" in lower:
                root_cfs.addChild(item)
            else:
                continue
            
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

    def get_selected_by_type(self, include_type: str) -> list[str]:
        """Returns list of selected template IDs for a specific type."""
        # Mapping: quality-definition, quality-profiles, custom-formats
        category_map = {
            "quality-definition": "quality-definition",
            "quality-profiles": "quality-profile",
            "custom-formats": "custom-format"
        }
        target_marker = category_map.get(include_type, include_type)
        
        selected = []
        iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            template_id = item.data(0, Qt.UserRole)
            if template_id and target_marker in template_id.lower():
                selected.append(template_id)
            iterator += 1
        return selected

    def set_selected_includes(self, includes_list: list[str]):
        """Programmatically select items based on a list of IDs."""
        self.tree.blockSignals(True)
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            # If item is a leaf/selectable
            if item.flags() & Qt.ItemIsUserCheckable:
                template_id = item.data(0, Qt.UserRole)
                if template_id in includes_list:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
            iterator += 1
        self.tree.blockSignals(False)
        self.selection_changed.emit()

    def _on_item_changed(self, item, column):
        self.selection_changed.emit()

from PySide6.QtWidgets import QTreeWidgetItemIterator
