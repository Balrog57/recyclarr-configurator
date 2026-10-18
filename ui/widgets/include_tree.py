from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                               QLabel, QHeaderView, QSplitter, QTreeWidgetItemIterator)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from ui.styles import CinemaTheme

class IncludeTreeWidget(QWidget):
    """
    Act 2: Template & Profile Selection.
    Displays available components in a tree structure:
    - Quality Definitions (movie, series, anime)
    - Quality Profiles from TRaSH Guides
    - Custom Format Groups / Packs
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
        
        desc_lbl = QLabel("Select models and profiles to include (TRaSH Guides).")
        desc_lbl.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(desc_lbl)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree)

    def load_for_app(self, app_name: str, current_config=None):
        self.tree.clear()
        
        # Root categories
        self.root_defs = QTreeWidgetItem(self.tree, ["Quality Definitions"])
        self.root_defs.setExpanded(True)
        self.root_defs.setFlags(self.root_defs.flags() & ~Qt.ItemIsUserCheckable)
        
        self.root_profiles = QTreeWidgetItem(self.tree, ["Quality Profiles (TRaSH Guides)"])
        self.root_profiles.setExpanded(True)
        self.root_profiles.setFlags(self.root_profiles.flags() & ~Qt.ItemIsUserCheckable)
        
        self.root_cfs = QTreeWidgetItem(self.tree, ["Format Packs (CF Groups)"])
        self.root_cfs.setExpanded(False)
        self.root_cfs.setFlags(self.root_cfs.flags() & ~Qt.ItemIsUserCheckable)

        # 1. Quality Definitions
        qdefs = self.data_manager.get_includes_by_type(app_name, "quality-definitions")
        for qd in qdefs:
            name = qd.get("name", "")
            item = QTreeWidgetItem([name])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setToolTip(0, f"Quality Definition: {name}")
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole, qd.get("trash_id") or name)
            item.setData(0, Qt.UserRole + 1, "quality-definition")
            item.setData(0, Qt.UserRole + 2, name)
            self.root_defs.addChild(item)

        # 2. Quality Profiles (TRaSH Guides)
        qprofiles = self.data_manager.get_includes_by_type(app_name, "quality-profiles")
        for qp in qprofiles:
            name = qp.get("name", "")
            trash_id = qp.get("trash_id", "")
            desc = qp.get("description", "")
            
            item = QTreeWidgetItem([name])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            clean_desc = desc.replace("<br>", "\n").replace("<b>", "").replace("</b>", "")
            item.setToolTip(0, f"{name}\n\n{clean_desc}" if clean_desc else name)
            item.setCheckState(0, Qt.Unchecked)
            # Store trash_id in UserRole, fallback to name
            item.setData(0, Qt.UserRole, trash_id if trash_id else name)
            item.setData(0, Qt.UserRole + 1, "quality-profile")
            item.setData(0, Qt.UserRole + 2, name)
            self.root_profiles.addChild(item)

        # 3. Custom Format Groups
        cf_groups = self.data_manager.get_includes_by_type(app_name, "custom-formats")
        for grp in cf_groups:
            name = grp.get("name", "")
            trash_id = grp.get("trash_id", "")
            default_txt = " (Default)" if grp.get("default") else ""
            
            item = QTreeWidgetItem([f"{name}{default_txt}"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setToolTip(0, f"CF Group: {name}\nFormats: {len(grp.get('trash_ids', []))}")
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole, trash_id if trash_id else name)
            item.setData(0, Qt.UserRole + 1, "custom-format")
            item.setData(0, Qt.UserRole + 2, name)
            self.root_cfs.addChild(item)

    def get_selected_templates(self) -> list[str]:
        """Returns list of all selected IDs/names."""
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
        """
        Returns list of selected IDs/names for a specific type:
        'quality-definition', 'quality-profiles'/'quality-profile', 'custom-formats'/'custom-format'.
        """
        type_prefix = include_type.rstrip("s").lower()
        selected = []
        iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            item_type = str(item.data(0, Qt.UserRole + 1) or "").lower()
            if item_type.startswith(type_prefix):
                val = item.data(0, Qt.UserRole)
                if val:
                    selected.append(val)
            iterator += 1
        return selected

    def set_selected_includes(self, includes_list: list[str]):
        """Programmatically select items based on a list of IDs or names."""
        self.tree.blockSignals(True)
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.flags() & Qt.ItemIsUserCheckable:
                item_id = item.data(0, Qt.UserRole)
                item_name = item.data(0, Qt.UserRole + 2)
                item_text = item.text(0)
                
                # Check match against ID, name, or text
                matched = (
                    item_id in includes_list or
                    item_name in includes_list or
                    item_text in includes_list
                )
                item.setCheckState(0, Qt.Checked if matched else Qt.Unchecked)
            iterator += 1
        self.tree.blockSignals(False)
        self.selection_changed.emit()

    def _on_item_changed(self, item, column):
        self.selection_changed.emit()
