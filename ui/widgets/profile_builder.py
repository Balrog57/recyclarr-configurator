from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTreeWidget, 
                               QTreeWidgetItem, QLabel, QPushButton, QSplitter, QInputDialog,
                               QMessageBox, QAbstractItemView, QMenu)
from PySide6.QtCore import Qt, QMimeData, QEvent, Signal
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
        # Avoid duplicates just in case
        if not self.findItems(quality_name, Qt.MatchExactly):
            self.addItem(quality_name)
            self.sortItems()

    def reset_list(self):
        """Resets the list to show all initial qualities."""
        self.clear()
        self.addItems(self.qualities)

    def dropEvent(self, event):
        source = event.source()
        # Handle drop from Tree (Removing qualities from profile -> Making available)
        if source and isinstance(source, QTreeWidget):
            # We assume the source is our QualityProfileTree
            items = source.selectedItems()
            for item in items:
                # Add back to available list
                self.show_quality(item.text(0))
            
            # Accept move to let Tree remove them
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

class QualityProfileTree(QTreeWidget):
    """Tree where we build the profile."""
    quality_added = Signal(str)
    quality_removed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()
            
    def is_quality_present(self, text):
        """Check if quality is already in the tree (recursively)."""
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

        # Define heuristic for what counts as a "Group"
        def is_group(item):
            if not item: return False
            # heuristic: has children, is a pipe-separated list, or starts with "Groupe"
            return (item.childCount() > 0 or 
                    "|" in item.text(0) or 
                    item.text(0).startswith("Groupe"))

        # --- CASE 1: Dropping from Source List (Adding new qualities) ---
        if source and isinstance(source, QListWidget):
            items = source.selectedItems()
            for item in items:
                text = item.text()
                
                # Uniqueness Check
                if self.is_quality_present(text):
                    continue
                
                new_item = QTreeWidgetItem([text])
                
                if target_item:
                    # If dropping ON an item that is a Group -> Add as child
                    if drop_indicator == QAbstractItemView.OnItem and is_group(target_item):
                        target_item.addChild(new_item)
                        target_item.setExpanded(True)
                    
                    # If dropping ON a leaf -> Insert Above/Below (Do NOT nest)
                    elif drop_indicator == QAbstractItemView.OnItem and not is_group(target_item):
                         # Force drop to be "Below" for better UX if user hovered "on" center
                         parent = target_item.parent()
                         if parent:
                             index = parent.indexOfChild(target_item)
                             parent.insertChild(index + 1, new_item)
                         else:
                             index = self.indexOfTopLevelItem(target_item)
                             self.insertTopLevelItem(index + 1, new_item)
                             
                    # Explicit Above/Below drops
                    elif drop_indicator == QAbstractItemView.AboveItem:
                        parent = target_item.parent()
                        if parent:
                            index = parent.indexOfChild(target_item)
                            parent.insertChild(index, new_item)
                        else:
                            index = self.indexOfTopLevelItem(target_item)
                            self.insertTopLevelItem(index, new_item)
                            
                    elif drop_indicator == QAbstractItemView.BelowItem:
                        parent = target_item.parent()
                        if parent:
                            index = parent.indexOfChild(target_item)
                            parent.insertChild(index + 1, new_item)
                        else:
                            index = self.indexOfTopLevelItem(target_item)
                            self.insertTopLevelItem(index + 1, new_item)
                        
                    # Fallback
                    else:
                        self.addTopLevelItem(new_item)
                else:
                    # Whitespace
                    self.addTopLevelItem(new_item)
                
                self.quality_added.emit(text)
            
            event.accept()

        # --- CASE 2: Internal Move (Reordering) ---
        elif source == self:
            if target_item and drop_indicator == QAbstractItemView.OnItem and not is_group(target_item):
                # Manual Move overrides "OnItem" -> "Insert Below"
                items = self.selectedItems()
                
                # We use a Clone & Delete approach to avoid C++ pointer issues with moving items manually
                for item in items:
                    if item == target_item: continue
                    
                    # 1. Clone
                    new_item = self._clone_item(item)
                    
                    # 2. Insert Below Target
                    parent = target_item.parent()
                    if parent:
                        # Index of target
                        idx = parent.indexOfChild(target_item)
                        parent.insertChild(idx + 1, new_item)
                    else:
                        idx = self.indexOfTopLevelItem(target_item)
                        self.insertTopLevelItem(idx + 1, new_item)
                    
                    # 3. Delete Original
                    # Note: We must be careful if deleting original invalidates references or shifts indices?
                    # Since we usually move one by one, deleting 'item' object is safe content-wise.
                    self.delete_item(item)
                    
                    # 4. Select New
                    self.clearSelection() # Optional, maybe keep accumulating selection?
                    new_item.setSelected(True) # Just select the last moved for now or logic to keep all?
                
                event.accept()
                return

            super().dropEvent(event)
            
    def _clone_item(self, item: QTreeWidgetItem) -> QTreeWidgetItem:
        """Deep clone of a QTreeWidgetItem."""
        new_item = QTreeWidgetItem([item.text(0)])
        # Copy flags, data, checkstate if needed?
        # For this app, Text is the main data.
        new_item.setFlags(item.flags())
        
        # Clone children recursively
        for i in range(item.childCount()):
            child = item.child(i)
            new_child = self._clone_item(child)
            new_item.addChild(new_child)
            
        new_item.setExpanded(item.isExpanded())
        return new_item
        
    def show_context_menu(self, position):
        item = self.itemAt(position)
        menu = QMenu()
        
        # Helper to check if selection contains only one group
        selected = self.selectedItems()
        # Updated heuristic usage in context menu if needed, but logic remains same
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
        
        # Get index of group to insert children there
        index = target_parent.indexOfChild(group_item)
        if index == -1: index = 0 
        
        children = [group_item.child(i) for i in range(group_item.childCount())]
        
        for child in children:
            group_item.removeChild(child)
            target_parent.insertChild(index, child)
            index += 1 
            
        # Remove the empty group
        target_parent.removeChild(group_item)

    def delete_selection(self):
        for item in self.selectedItems():
            # If item is a group, we might need to recover its children to list?
            # Or assume deleting group deletes children? 
            # User expectation: "si on la supprime elle retourne dans disponible".
            # If I delete a group "Bluray|WEB", the contained qualities should go back.
            self.recover_items_recursive(item)
            self.delete_item(item)
            
    def recover_items_recursive(self, item):
        """Recursively emit removed signal for all leaf items."""
        count = item.childCount()
        if count > 0:
            for i in range(count):
                self.recover_items_recursive(item.child(i))
        else:
            # It's a leaf (quality)
            self.quality_removed.emit(item.text(0))

    def add_group(self):
        # Get currently selected items in the tree
        selected_items = self.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner au moins une qualité pour créer un groupe.")
            return

        names = [item.text(0) for item in selected_items]
        default_name = "|".join(names)
        
        name, ok = QInputDialog.getText(self, "Nouveau Groupe", "Nom du groupe:", text=default_name)
        if ok and name:
            group_item = QTreeWidgetItem([name])
            group_item.setExpanded(True)
            self.addTopLevelItem(group_item)
            
            # Move selected items into the new group
            for item in selected_items:
                parent = item.parent()
                root = self.invisibleRootItem()
                source_parent = parent if parent else root
                
                source_parent.removeChild(item)
                group_item.addChild(item)
            
    def delete_item(self, item):
        # Remove item
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            
    def rename_group(self, item):
        name, ok = QInputDialog.getText(self, "Renommer Groupe", "Nouveau nom:", text=item.text(0))
        if ok and name:
            item.setText(0, name)
            
    def get_profile_structure(self) -> list[QualityProfileItem]:
        """Convert tree content to QualityProfileItem list."""
        items = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            # If it has children, it's a group
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
    
    def load_structure(self, items: list):
        """
        Loads the tree from a list of dicts (Recyclarr format).
        items: [{"name": "Group", "qualities": [...]}, {"name": "Quality"}]
        """
        self.clear()
        for entry in items:
            name = entry.get("name")
            sub_qualities = entry.get("qualities", [])
            
            if sub_qualities:
                # It is a group
                group_item = QTreeWidgetItem([name])
                group_item.setExpanded(True)
                self.addTopLevelItem(group_item)
                
                for q in sub_qualities:
                    # In Recyclarr json, sub-qualities might be strings or objects?
                    # Looking at json: "qualities": ["Bluray-1080p Remux", "Bluray-1080p"] -> Strings
                    # BUT sometimes it might be object? "name": "Bluray-1080p"
                    # Let's check the json snippet again.
                    # "qualities": [ "Bluray-1080p Remux", "Bluray-1080p" ]
                    
                    if isinstance(q, str):
                        q_name = q
                    else:
                        q_name = q.get("name")
                        
                    child = QTreeWidgetItem([q_name])
                    group_item.addChild(child)
                    # Emit signal to hide from source list?
                    self.quality_added.emit(q_name)
            else:
                # It is a single quality
                item = QTreeWidgetItem([name])
                self.addTopLevelItem(item)
                self.quality_added.emit(name)

class ProfileBuilder(QWidget):
    """Act 2: Builder."""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_profile_name = "Custom Profile"
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_lbl = QLabel("Acte 3 : La Mise en Scène")
        header_lbl.setProperty("class", "h2")
        layout.addWidget(header_lbl)
        
        desc = QLabel("Créez vos profils de qualité. Glissez-déposez les qualités, créez des groupes.")
        desc.setStyleSheet("color: #888;")
        layout.addWidget(desc)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Qualités Disponibles"))
        self.source_list = QualitySourceList()
        left_layout.addWidget(self.source_list)
        
        # Right Panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Votre Profil"))
        
        # Toolbar removed as per user request (Context menu only)
        # toolbar = QHBoxLayout()
        # btn_add_group = QPushButton("Créer un Groupe")
        # btn_add_group.clicked.connect(self.add_group)
        # toolbar.addWidget(btn_add_group)
        # toolbar.addStretch()
        # right_layout.addLayout(toolbar)
        
        self.tree = QualityProfileTree()
        # Connect signals for Exclusive Move Logic
        self.tree.quality_added.connect(self.source_list.hide_quality)
        self.tree.quality_removed.connect(self.source_list.show_quality)
        
        right_layout.addWidget(self.tree)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
    def add_group(self):
        self.tree.add_group()

    def get_profile(self) -> QualityProfile:
        items = self.tree.get_profile_structure()
        return QualityProfile(name=self.current_profile_name, items=items) 

    def load_profile_from_data(self, profile_data: dict):
        """
        Loads a profile from data dict (from includes).
        Expects profile_data['content']['quality_profiles'][0]['qualities'] list.
        """
        # 1. Reset everything
        self.source_list.reset_list()
        self.tree.clear_tree() # This is crucial
        
        # 2. Extract qualities list
        # Profile data should be the dictionary of the specific profile include content
        # Structure: {"quality_profiles": [ { "name": "...", "qualities": [...] } ] }
        
        q_profiles = profile_data.get("quality_profiles", [])
        if not q_profiles:
            return
            
        # We assume the first profile in the include is the main one
        main_profile = q_profiles[0]
        qualities = main_profile.get("qualities", [])
        self.current_profile_name = main_profile.get("name", "Custom Profile")
        
        # 3. Load into tree
        # This will emit 'quality_added' signals, which will trigger source_list.hide_quality
        self.tree.load_structure(qualities)
