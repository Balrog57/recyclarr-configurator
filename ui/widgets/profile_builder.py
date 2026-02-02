from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTreeWidget, 
                               QTreeWidgetItem, QLabel, QPushButton, QSplitter, QInputDialog,
                               QMessageBox, QAbstractItemView, QMenu, QDialog, QFormLayout,
                               QLineEdit, QCheckBox, QComboBox, QSpinBox, QDialogButtonBox, QGroupBox)
from PySide6.QtCore import Qt, QMimeData, QEvent, Signal, QSize
from PySide6.QtGui import QDrag, QIcon, QAction

from core.models import QualityProfile, QualityProfileItem

class QualitySourceList(QListWidget):
    """List of available qualities to drag from."""
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # Standard qualities
        self.qualities = [
            "Bluray-2160p", "Remux-2160p", "WEB-2160p", "WEBDL-2160p",
            "Bluray-1080p", "Remux-1080p", "WEB-1080p", "WEBDL-1080p",
            "HDTV-1080p", "Bluray-720p", "WEB-720p", "HDTV-720p",
            "DVD", "SDTV", "CAM", "TS"
        ]
        self.addItems(self.qualities)

    def hide_quality(self, quality_name: str):
        """Hides/Removes quality from list."""
        items = self.findItems(quality_name, Qt.MatchExactly)
        for item in items:
            self.takeItem(self.row(item))

    def show_quality(self, quality_name: str):
        """Shows/Adds quality back to list."""
        if not self.findItems(quality_name, Qt.MatchExactly):
            self.addItem(quality_name)
            self.sortItems()

    def reset_list(self):
        """Resets the list to show all initial qualities."""
        self.clear()
        self.addItems(self.qualities)

    def dropEvent(self, event):
        source = event.source()
        if source and isinstance(source, QTreeWidget):
            items = source.selectedItems()
            for item in items:
                self.show_quality(item.text(0))
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

class QualityProfileTree(QTreeWidget):
    """Tree where we build the profile."""
    quality_added = Signal(str)
    quality_removed = Signal(str)
    structure_changed = Signal() # To update combo boxes

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.model().rowsInserted.connect(self.structure_changed)
        self.model().rowsRemoved.connect(self.structure_changed)
        # Note: model changes might not catch text changes perfectly without more signals, but structural adds/removes are key.
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()
            
    def is_quality_present(self, text):
        root = self.invisibleRootItem()
        stack = [root.child(i) for i in range(root.childCount())]
        while stack:
            item = stack.pop()
            if item.text(0) == text:
                return True
            for i in range(item.childCount()):
                stack.append(item.child(i))
        return False

    def dropEvent(self, event):
        source = event.source()
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        drop_indicator = self.dropIndicatorPosition()

        def is_group(item):
            if not item: return False
            return (item.childCount() > 0 or "|" in item.text(0) or item.text(0).startswith("Groupe"))

        if source and isinstance(source, QListWidget):
            items = source.selectedItems()
            for item in items:
                text = item.text()
                if self.is_quality_present(text): continue
                
                new_item = QTreeWidgetItem([text])
                new_item.setFlags(new_item.flags() & ~Qt.ItemIsDropEnabled) # Individual qualities can't have children
                
                if target_item:
                    is_target_group = is_group(target_item)
                    if drop_indicator == QAbstractItemView.OnItem and is_target_group:
                        target_item.addChild(new_item)
                        target_item.setExpanded(True)
                    else:
                        # For OnItem (non-group) or Above/Below, always insert as sibling
                        parent = target_item.parent()
                        root = self.invisibleRootItem()
                        target_parent = parent if parent else root
                        
                        idx = target_parent.indexOfChild(target_item)
                        if drop_indicator == QAbstractItemView.BelowItem:
                            idx += 1
                        elif drop_indicator == QAbstractItemView.OnItem:
                            # If they drop "on" a non-group quality, we assume they want it after (like a list)
                            idx += 1
                        
                        target_parent.insertChild(idx, new_item)
                else:
                    self.addTopLevelItem(new_item)
                
                self.quality_added.emit(text)
            event.accept()
            self.structure_changed.emit()

        elif source == self:
            # Internal move
            if target_item and drop_indicator == QAbstractItemView.OnItem and not is_group(target_item):
                # Prevent dropping ON a quality (no nesting allowed if target is not a group)
                # Instead, treat it as dropping below
                event.setDropAction(Qt.MoveAction)
                # We let the default handle Above/Below, but we must block "On" for non-groups
                # A safer way is to manually handle it or signal that OnItem is only valid for groups
                pass 
            
            super().dropEvent(event)
            # Post-drop cleanup: if something ended up nested in a non-group, fix it?
            # Or better, prevent it via dragMoveEvent
            self.structure_changed.emit()

    def dragMoveEvent(self, event):
        """Prevent drop indicator 'OnItem' for non-group items."""
        target_item = self.itemAt(event.position().toPoint())
        
        def is_group(item):
            if not item: return False
            return (item.childCount() > 0 or "|" in item.text(0) or item.text(0).startswith("Groupe"))

        if target_item and not is_group(target_item):
            # If the cursor is right on the item, don't allow 'On' action
            # Standard QTreeWidget will switch to Above/Below if we are at edge
            if self.dropIndicatorPosition() == QAbstractItemView.OnItem:
                # We can't easily force it to Above/Below from here without changing position,
                # but we can ignore the OnItem action.
                # However, the user wants to be able to move above/below.
                pass
        super().dragMoveEvent(event)
            
    def show_context_menu(self, position):
        item = self.itemAt(position)
        menu = QMenu()
        selected = self.selectedItems()
        is_single_group = len(selected) == 1 and (selected[0].childCount() > 0 or "|" in selected[0].text(0))
        
        action_add_group = QAction("Créer un groupe (avec sélection)", self)
        action_add_group.triggered.connect(self.add_group)
        menu.addAction(action_add_group)
        
        if item:
            if is_single_group:
                action_ungroup = QAction("Dégrouper", self)
                action_ungroup.triggered.connect(lambda: self.ungroup_item(selected[0]))
                menu.addAction(action_ungroup)
                
                action_rename = QAction("Renommer", self)
                action_rename.triggered.connect(lambda: self.rename_group(selected[0]))
                menu.addAction(action_rename)
            
            action_delete = QAction("Supprimer", self)
            action_delete.triggered.connect(lambda: self.delete_selection())
            menu.addAction(action_delete)

        menu.exec(self.viewport().mapToGlobal(position))
        
    def ungroup_item(self, group_item):
        """Moves children of the group to the group's parent (flattening)."""
        parent = group_item.parent()
        root = self.invisibleRootItem()
        target_parent = parent if parent else root
        index = target_parent.indexOfChild(group_item)
        if index == -1: index = 0 
        
        children = [group_item.child(i) for i in range(group_item.childCount())]
        for child in children:
            group_item.removeChild(child)
            target_parent.insertChild(index, child)
            index += 1 
        target_parent.removeChild(group_item)
        self.structure_changed.emit()

    def delete_selection(self):
        for item in self.selectedItems():
            self.recover_items_recursive(item)
            parent = item.parent()
            if parent: parent.removeChild(item)
            else: self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        self.structure_changed.emit()
            
    def recover_items_recursive(self, item):
        count = item.childCount()
        if count > 0:
            for i in range(count):
                self.recover_items_recursive(item.child(i))
        else:
            self.quality_removed.emit(item.text(0))

    def add_group(self):
        selected_items = self.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select at least one quality to create a group.")
            return

        names = [item.text(0) for item in selected_items]
        default_name = "|".join(names)
        
        name, ok = QInputDialog.getText(self, "New Group", "Group Name:", text=default_name)
        if ok and name:
            group_item = QTreeWidgetItem([name])
            group_item.setFlags(group_item.flags() | Qt.ItemIsDropEnabled) # Groups CAN have children
            group_item.setExpanded(True)
            self.addTopLevelItem(group_item)
            
            for item in selected_items:
                parent = item.parent()
                root = self.invisibleRootItem()
                source_parent = parent if parent else root
                source_parent.removeChild(item)
                group_item.addChild(item)
            self.structure_changed.emit()
            
    def rename_group(self, item):
        name, ok = QInputDialog.getText(self, "Rename Group", "New Name:", text=item.text(0))
        if ok and name:
            item.setText(0, name)
            self.structure_changed.emit()
            
    def get_profile_structure(self) -> list[QualityProfileItem]:
        items = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            if child.childCount() > 0:
                qualities = []
                for j in range(child.childCount()):
                    qualities.append(child.child(j).text(0))
                items.append(QualityProfileItem(name=child.text(0), qualities=qualities))
            else:
                items.append(QualityProfileItem(name=child.text(0), qualities=[]))
        return items
    
    def clear_tree(self):
        self.clear()
        self.structure_changed.emit()
    
    def load_structure(self, items: list):
        self.clear()
        for entry in items:
            name = entry.get("name")
            sub_qualities = entry.get("qualities", [])
            
            if sub_qualities:
                group_item = QTreeWidgetItem([name])
                group_item.setFlags(group_item.flags() | Qt.ItemIsDropEnabled) # Allow children
                group_item.setExpanded(True)
                self.addTopLevelItem(group_item)
                for q in sub_qualities:
                    q_name = q if isinstance(q, str) else q.get("name")
                    child = QTreeWidgetItem([q_name])
                    child.setFlags(child.flags() & ~Qt.ItemIsDropEnabled) # No children allowed
                    group_item.addChild(child)
                    self.quality_added.emit(q_name)
            else:
                item = QTreeWidgetItem([name])
                item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled) # No children allowed
                self.addTopLevelItem(item)
                self.quality_added.emit(name)
        self.structure_changed.emit()
        
    def get_top_level_names(self):
        """Returns names of all top level items (groups or single qualities)."""
        names = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            names.append(root.child(i).text(0))
        return names

class ProfileEditorDialog(QDialog):
    """Dialog to edit a single Quality Profile."""
    def __init__(self, parent=None, profile: QualityProfile = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Quality Profile")
        self.resize(1000, 700)
        self.profile = profile or QualityProfile(name="New Profile")
        
        self.setup_ui()
        self.load_profile()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Section: Form Data ---
        form_group = QGroupBox("Configuration")
        form_layout = QFormLayout(form_group)
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Reset Unmatched Scores
        self.reset_scores_chk = QCheckBox("Enable (Reset Unmatched Scores)")
        self.reset_scores_chk.setToolTip("If enabled, score is reset to 0 for unmatched releases.")
        form_layout.addRow("Reset Unmatched Scores:", self.reset_scores_chk)
        
        # Upgrade Allowed
        self.upgrade_chk = QCheckBox("If disabled, qualities will not be upgraded")
        form_layout.addRow("Upgrades Allowed:", self.upgrade_chk)
        
        # Upgrade Until Quality (ComboBox)
        self.upgrade_until_combo = QComboBox()
        self.upgrade_until_combo.setEditable(True) # Allow custom text if needed, but usually strictly from list
        form_layout.addRow("Upgrade until quality:", self.upgrade_until_combo)
        
        # Min Format Score
        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(-10000, 100000)
        form_layout.addRow("Minimum custom format score:", self.min_score_spin)
        
        # Until Score
        self.until_score_spin = QSpinBox()
        self.until_score_spin.setRange(0, 1000000)
        form_layout.addRow("Upgrade until score:", self.until_score_spin)
        
        # Score Set
        self.score_set_edit = QLineEdit()
        self.score_set_edit.setPlaceholderText("e.g., french-multi-vf")
        form_layout.addRow("Score Set:", self.score_set_edit)
        
        # Quality Sort
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["top", "bottom"])
        form_layout.addRow("Quality Sort:", self.sort_combo)
        
        main_layout.addWidget(form_group)
        
        # --- Middle Section: Builder ---
        builder_group = QGroupBox("Profile Structure")
        builder_layout = QVBoxLayout(builder_group)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Source
        left_widget = QWidget()
        l_layout = QVBoxLayout(left_widget)
        l_layout.addWidget(QLabel("Available Qualities"))
        self.source_list = QualitySourceList()
        l_layout.addWidget(self.source_list)
        
        # Right: Tree
        right_widget = QWidget()
        r_layout = QVBoxLayout(right_widget)
        r_layout.addWidget(QLabel("Your Profile (Drag & Drop, Right-click to Group)"))
        self.tree = QualityProfileTree()
        r_layout.addWidget(self.tree)
        
        # Signals
        self.tree.quality_added.connect(self.source_list.hide_quality)
        self.tree.quality_removed.connect(self.source_list.show_quality)
        self.tree.structure_changed.connect(self.refresh_upgrade_combo)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)
        
        builder_layout.addWidget(splitter)
        main_layout.addWidget(builder_group)
        
        # --- Bottom: Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
    def load_profile(self):
        self.name_edit.setText(self.profile.name)
        self.reset_scores_chk.setChecked(self.profile.reset_unmatched_scores)
        self.upgrade_chk.setChecked(self.profile.upgrade_allowed)
        self.min_score_spin.setValue(self.profile.min_format_score)
        self.until_score_spin.setValue(self.profile.until_score)
        self.score_set_edit.setText(self.profile.score_set)
        
        idx = self.sort_combo.findText(self.profile.quality_sort)
        if idx != -1: self.sort_combo.setCurrentIndex(idx)
        
        # Load Tree
        self.source_list.reset_list()
        self.tree.clear_tree()
        
        # Create structure list for tree loader
        # Profile Items are objects, we convert them to dicts for the loader (legacy reused logic)
        # or adapt the loader. Let's adapt the loader to accept objects?
        # Loader expects list of dicts. Let's convert current items.
        structure_data = []
        for item in self.profile.items:
            structure_data.append({
                "name": item.name,
                "qualities": item.qualities
            })
        self.tree.load_structure(structure_data)
        
        # Deferred Combo Set (after tree loaded)
        self.refresh_upgrade_combo()
        self.upgrade_until_combo.setCurrentText(self.profile.upgrade_until)

    def refresh_upgrade_combo(self):
        current_text = self.upgrade_until_combo.currentText()
        self.upgrade_until_combo.clear()
        items = self.tree.get_top_level_names()
        self.upgrade_until_combo.addItems(items)
        # Try to restore select
        if current_text in items:
            self.upgrade_until_combo.setCurrentText(current_text)

    def save_and_accept(self):
        # Validation
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "Profile name is required.")
            return

        self.profile.name = self.name_edit.text().strip()
        self.profile.reset_unmatched_scores = self.reset_scores_chk.isChecked()
        self.profile.upgrade_allowed = self.upgrade_chk.isChecked()
        self.profile.upgrade_until = self.upgrade_until_combo.currentText()
        self.profile.min_format_score = self.min_score_spin.value()
        self.profile.until_score = self.until_score_spin.value()
        self.profile.score_set = self.score_set_edit.text().strip()
        self.profile.quality_sort = self.sort_combo.currentText()
        
        self.profile.items = self.tree.get_profile_structure()
        
        self.accept()
        
    def get_profile(self) -> QualityProfile:
        return self.profile

class QualityProfileManager(QWidget):
    """Act 3: Management of Multiple Quality Profiles."""
    def __init__(self):
        super().__init__()
        self.profiles: list[QualityProfile] = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_lbl = QLabel("Act 3: Staging")
        header_lbl.setProperty("class", "h2")
        layout.addWidget(header_lbl)
        
        desc = QLabel("Create and manage your quality profiles.")
        desc.setStyleSheet("color: #888;")
        layout.addWidget(desc)
        
        # Toolbar
        toolbar = QHBoxLayout()
        btn_add = QPushButton("New Profile")
        btn_add.setIcon(QIcon.fromTheme("list-add"))
        btn_add.clicked.connect(self.add_profile)
        btn_add.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        
        btn_edit = QPushButton("Modify")
        btn_edit.clicked.connect(self.edit_profile)
        
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self.delete_profile)
        
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # List of Profiles
        self.list_widget = QListWidget()
        self.list_widget.doubleClicked.connect(self.edit_profile)
        layout.addWidget(self.list_widget)
        
    def refresh_list(self):
        self.list_widget.clear()
        for p in self.profiles:
            self.list_widget.addItem(f"{p.name} (Items: {len(p.items)})")
            
    def add_profile(self):
        dialog = ProfileEditorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_profile = dialog.get_profile()
            self.profiles.append(new_profile)
            self.refresh_list()
            
    def edit_profile(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        
        profile_to_edit = self.profiles[row]
        dialog = ProfileEditorDialog(self, profile=profile_to_edit)
        if dialog.exec() == QDialog.Accepted:
            # Update was done in place on the object, but we refresh list text
            self.refresh_list()
            
    def delete_profile(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        
        name = self.profiles[row].name
        if QMessageBox.question(self, "Delete", f"Delete profile '{name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.profiles.pop(row)
            self.refresh_list()
            
    def get_profiles(self) -> list[QualityProfile]:
        return self.profiles

    def load_profiles(self, profiles_data: list):
        """Legacy: Loads profiles and clears everything."""
        self.profiles.clear()
        self._import_profiles(profiles_data)
        self.refresh_list()

    def sync_profiles(self, profiles_data: list):
        """Syncs profiles: Keeps 'custom' ones, replaces 'include' ones."""
        # 1. Keep custom profiles
        self.profiles = [p for p in self.profiles if p.source == "custom"]
        
        # 2. Add new included profiles
        self._import_profiles(profiles_data, source="include")
        
        # 3. Refresh
        self.refresh_list()

    def _import_profiles(self, profiles_data: list, source: str = "custom"):
        """Helper to parse list of dicts into QualityProfile objects."""
        for p_data in profiles_data:
            name = p_data.get("name", "Imported Profile")
            profile = QualityProfile(name=name, source=source)
            
            # Load metadata if present (extended config)
            # YAML format: usage of 'upgrade', 'reset_unmatched_scores', etc.
            # Check for nested keys
            
            # Reset Unmatched Scores
            rus = p_data.get("reset_unmatched_scores")
            if isinstance(rus, dict):
                profile.reset_unmatched_scores = rus.get("enabled", True)
            elif isinstance(rus, bool):
                profile.reset_unmatched_scores = rus
                
            # Upgrade
            upg = p_data.get("upgrade", {})
            if isinstance(upg, dict):
                profile.upgrade_allowed = upg.get("allowed", False)
                profile.upgrade_until = upg.get("until_quality", "")
                profile.until_score = upg.get("until_score", 10000)
                
            profile.min_format_score = p_data.get("min_format_score", 0)
            profile.score_set = p_data.get("score_set", "")
            profile.quality_sort = p_data.get("quality_sort", "top")
            
            # Load Qualities Structure
            qualities = p_data.get("qualities", [])
            items = []
            for q_entry in qualities:
                 # Entry can be dict (group/quality) or string (quality)
                 if isinstance(q_entry, str):
                     items.append(QualityProfileItem(name=q_entry))
                 elif isinstance(q_entry, dict):
                     q_name = q_entry.get("name", "Unknown")
                     q_sub = q_entry.get("qualities", [])
                     items.append(QualityProfileItem(name=q_name, qualities=q_sub))
            
            profile.items = items
            self.profiles.append(profile)

