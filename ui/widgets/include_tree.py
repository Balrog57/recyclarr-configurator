from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                               QLabel, QTreeWidgetItemIterator)
from PySide6.QtCore import Qt, Signal

AUTO_ROLE = Qt.UserRole + 3  # CF group auto-synced by Recyclarr for the checked profiles


class IncludeTreeWidget(QWidget):
    """
    Act 2: TRaSH Guides selection (Recyclarr v8).
    - Quality Profiles from TRaSH Guides (guide-backed, by trash_id)
    - Custom Format Groups: "(auto)" ones are synced by Recyclarr for the checked profiles
      (uncheck = skip), the others are opt-in (check = add)
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

        desc_lbl = QLabel("Check TRaSH profiles. CF groups marked (auto) sync with them: uncheck to skip, check others to add.")
        desc_lbl.setWordWrap(True)
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
        self.root_profiles = QTreeWidgetItem(self.tree, ["Quality Profiles (TRaSH Guides)"])
        self.root_profiles.setExpanded(True)
        self.root_profiles.setFlags(self.root_profiles.flags() & ~Qt.ItemIsUserCheckable)

        self.root_cfs = QTreeWidgetItem(self.tree, ["Format Packs (CF Groups)"])
        self.root_cfs.setExpanded(True)
        self.root_cfs.setFlags(self.root_cfs.flags() & ~Qt.ItemIsUserCheckable)

        # 1. Quality Profiles (TRaSH Guides)
        for qp in self.data_manager.get_includes_by_type(app_name, "quality-profiles"):
            name = qp.get("name", "")
            trash_id = qp.get("trash_id", "")
            desc = qp.get("description", "")

            item = QTreeWidgetItem([name])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            clean_desc = desc.replace("<br>", "\n").replace("<b>", "").replace("</b>", "")
            item.setToolTip(0, f"{name}\n\n{clean_desc}" if clean_desc else name)
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole, trash_id if trash_id else name)
            item.setData(0, Qt.UserRole + 1, "quality-profile")
            item.setData(0, Qt.UserRole + 2, name)
            self.root_profiles.addChild(item)

        # 2. Custom Format Groups
        for grp in self.data_manager.get_includes_by_type(app_name, "custom-formats"):
            name = grp.get("name", "")
            trash_id = grp.get("trash_id", "")
            content = grp.get("content") or {}
            cf_names = ", ".join(cf.get("name", "") for cf in content.get("custom_formats", []))

            item = QTreeWidgetItem([name])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setToolTip(0, f"CF Group: {name}\n{content.get('trash_description', '')}\n\n{cf_names}")
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
        Returns list of selected IDs for a specific type:
        'quality-profiles'/'quality-profile', 'custom-formats'/'custom-format'.
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
                matched = (item.data(0, Qt.UserRole) in includes_list
                           or item.data(0, Qt.UserRole + 2) in includes_list)
                item.setCheckState(0, Qt.Checked if matched else Qt.Unchecked)
            iterator += 1
        self.tree.blockSignals(False)
        self.selection_changed.emit()

    def _on_item_changed(self, item, column):
        self.selection_changed.emit()

    def _group_items(self) -> list:
        return [self.root_cfs.child(i) for i in range(self.root_cfs.childCount())]

    def set_auto_groups(self, auto_ids, skip=None):
        """
        Marks the CF groups Recyclarr auto-syncs for the checked profiles.
        skip: auto groups to leave unchecked (from a config); None keeps the user's current choices.
        """
        self.tree.blockSignals(True)
        for item in self._group_items():
            tid, name = item.data(0, Qt.UserRole), item.data(0, Qt.UserRole + 2)
            was_auto, is_auto = bool(item.data(0, AUTO_ROLE)), tid in auto_ids
            item.setData(0, AUTO_ROLE, is_auto)
            item.setText(0, f"{name}  (auto)" if is_auto else name)
            if is_auto and (skip is not None or not was_auto):
                item.setCheckState(0, Qt.Unchecked if skip and tid in skip else Qt.Checked)
            elif was_auto and not is_auto:
                item.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)

    def group_state(self):
        """(added, skipped): opt-in groups checked, auto groups unchecked."""
        added, skipped = [], []
        for item in self._group_items():
            checked, auto = item.checkState(0) == Qt.Checked, bool(item.data(0, AUTO_ROLE))
            if checked and not auto:
                added.append(item.data(0, Qt.UserRole))
            elif auto and not checked:
                skipped.append(item.data(0, Qt.UserRole))
        return added, skipped
