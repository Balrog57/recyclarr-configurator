from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QSpinBox, QCheckBox, QGroupBox, QLineEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit)
from PySide6.QtCore import Qt
from core.models import CustomFormatAssignment

class CFEditor(QWidget):
    """
    Act 3: Custom Format Editor.
    Links Custom Formats (trash_ids) to Scores and Quality Profiles.
    """
    def __init__(self, all_formats_data, available_profiles):
        super().__init__()
        self.data = all_formats_data  # Json loaded data (list of dicts)
        self.profiles = available_profiles # List of profile names (strings)
        self.active_assignments = {} # {trash_id: CustomFormatAssignment}
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_lbl = QLabel("Acte 4 : Les Effets Spéciaux")
        header_lbl.setProperty("class", "h2")
        layout.addWidget(header_lbl)
        
        desc_lbl = QLabel("Assignez des scores aux formats personnalisés.")
        desc_lbl.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(desc_lbl)
        
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)
        
        # 1. Left Layout (Search + List)
        left_layout = QVBoxLayout()
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un format...")
        self.search_input.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.search_input)
        
        # List
        self.list_widget = QListWidget()
        self.populate_list()
        self.list_widget.itemClicked.connect(self.load_details)
        left_layout.addWidget(self.list_widget)
        
        content_layout.addLayout(left_layout, 1)
        
        # 2. Right Panel (Inspector)
        self.details_panel = QGroupBox("Configuration du Format")
        details_layout = QVBoxLayout()
        # Details Panel
        self.lbl_name = QLabel("Nom du Format")
        self.lbl_name.setProperty("class", "h4")
        details_layout.addWidget(self.lbl_name)
        
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setStyleSheet("color: #aaa; font-style: italic; background: transparent; border: none;")
        details_layout.addWidget(self.desc_text, 1) # Stretch 1/3

        # Default Score Display
        self.lbl_default_score = QLabel("(Score par défaut: 0)")
        self.lbl_default_score.setStyleSheet("color: #666; font-weight: bold; margin-top: 5px;")
        details_layout.addWidget(self.lbl_default_score)

        details_layout.addSpacing(10)
        details_layout.addWidget(QLabel("Score par Profil:"))

        # Table for Profile Assignments
        # Columns: [Profile Name, Enabled (Checkbox), Score (Spinbox)]
        self.profile_table = QTableWidget()
        self.profile_table.setColumnCount(3)
        self.profile_table.setHorizontalHeaderLabels(["Profil", "Actif", "Score"])
        self.profile_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.profile_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.profile_table.setColumnWidth(1, 60) # Fixed width for Checkbox
        self.profile_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.profile_table.setColumnWidth(2, 130) # Wider for -10000
        
        self.profile_table.verticalHeader().setVisible(False)
        self.profile_table.verticalHeader().setDefaultSectionSize(40) # Ensure height for SpinBox
        self.profile_table.setSelectionMode(QTableWidget.NoSelection)
        self.profile_table.setFocusPolicy(Qt.NoFocus) # Remove cell focus/blue box
        # self.profile_table.itemChanged.connect(self.on_table_item_changed) # Removed to avoid conflict with cell widgets
        
        details_layout.addWidget(self.profile_table, 2) # Stretch 2/3
        
        self.details_panel.setLayout(details_layout)
        
        content_layout.addWidget(self.details_panel, 1)

    def populate_list(self):
        self.list_widget.clear()
        # Sort by name
        sorted_cfs = sorted(self.data, key=lambda x: x.get('name', ''))
        for cf in sorted_cfs:
            item = QListWidgetItem(cf.get('name', 'Unknown'))
            item.setData(99, cf.get('trash_id')) 
            item.setToolTip(cf.get('description', 'Pas de description'))
            self.list_widget.addItem(item)
            
    def filter_list(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_details(self, item):
        trash_id = item.data(99)
        cf_data = next((x for x in self.data if x.get('trash_id') == trash_id), None)
        
        if not cf_data:
            return
            
        # Block signals to avoid triggering updates during load
        self.profile_table.blockSignals(True)

        self.lbl_name.setText(cf_data.get('name'))
        self.desc_text.setText(cf_data.get('description', ''))
        
        # Default score logic
        trash_scores = cf_data.get('trash_scores', {})
        default_score = trash_scores.get('default', 0) if isinstance(trash_scores, dict) else 0
        self.lbl_default_score.setText(f"(Score par défaut: {default_score})")
        
        current_assignment = self.active_assignments.get(trash_id)
        
        # Prepare Rows
        self.profile_table.setRowCount(len(self.profiles))
        
        for i, p_name in enumerate(self.profiles):
            # 1. Profile Name
            name_item = QTableWidgetItem(p_name)
            name_item.setFlags(Qt.ItemIsEnabled) # Read only
            self.profile_table.setItem(i, 0, name_item)
            
            # 2. Checkbox (Active) - Using Cell Widget for centering and styling
            container = QWidget()
            c_layout = QHBoxLayout(container)
            c_layout.setContentsMargins(0,0,0,0)
            c_layout.setAlignment(Qt.AlignCenter)
            
            chk = QCheckBox()
            # Style: White box when unchecked (visible), Standard accent when checked
            chk.setStyleSheet("""
                QCheckBox::indicator { 
                    width: 20px; 
                    height: 20px; 
                    background-color: white; 
                    border: 1px solid #666; 
                    border-radius: 4px;
                }
                QCheckBox::indicator:checked { 
                    background-color: #d35400; 
                    border: 1px solid #d35400;
                    image: none;
                }
            """)
            # Note: Checking the box will turn it Orange (accent).
            
            c_layout.addWidget(chk)
            self.profile_table.setCellWidget(i, 1, container)
            
            # 3. Score Spinbox
            spin = QSpinBox()
            spin.setRange(-10000, 10000)
            spin.setEnabled(False) # Disabled by default until checked
            
            # Determine state from active assignment
            
            inferred_score = self._infer_score(cf_data, p_name, default_score)
            final_val = inferred_score
            is_active = False
            
            if current_assignment:
                # Check explicit assignment first
                p_score_entry = next((x for x in current_assignment.profile_scores if x.get('name') == p_name), None)
                if p_score_entry:
                    final_val = p_score_entry.get('score', default_score)
                    is_active = True
                # Fallback to legacy
                elif not current_assignment.profile_scores and p_name in current_assignment.profiles:
                    final_val = current_assignment.score
                    is_active = True
            
            # If not explicitly active but inferred score is different from default
            if not is_active and inferred_score != default_score:
                 final_val = inferred_score
                 is_active = True

            spin.setValue(final_val)
            chk.setChecked(is_active)
            spin.setEnabled(is_active)
            
            self.profile_table.setCellWidget(i, 2, spin)
            
            # Connect signals
            # Use lambdas to capture current row content effectively or just trigger update
            chk.stateChanged.connect(lambda state, r=i: self.on_checkbox_toggled(r, state))
            spin.valueChanged.connect(self.update_model)

        self.profile_table.blockSignals(False)
        
        
    def on_checkbox_toggled(self, row, state):
        is_checked = (state == Qt.Checked) or (state == 2) # Qt.Checked is 2
        spin_widget = self.profile_table.cellWidget(row, 2)
        if spin_widget:
            spin_widget.setEnabled(is_checked)
        self.update_model()
        
    def update_model(self):
        # Save current table state to active_assignments
        item = self.list_widget.currentItem()
        if not item: return
        
        trash_id = item.data(99)
        cf_data = next((x for x in self.data if x.get('trash_id') == trash_id), None)
        if not cf_data: return
        
        trash_scores = cf_data.get('trash_scores', {})
        default_score = trash_scores.get('default', 0) if isinstance(trash_scores, dict) else 0

        # Build profile_scores list
        profile_scores = []
        
        for i in range(self.profile_table.rowCount()):
            # Checkbox is in CellWidget at col 1
            container = self.profile_table.cellWidget(i, 1)
            if not container or not container.layout() or container.layout().count() == 0:
                continue
                
            chk = container.layout().itemAt(0).widget()
            
            if chk and chk.isChecked():
                p_name = self.profile_table.item(i, 0).text()
                spin = self.profile_table.cellWidget(i, 2)
                val = spin.value()
                profile_scores.append({"name": p_name, "score": val})
        
        if not profile_scores:
            # If no profiles assigned, remove from active?
            if trash_id in self.active_assignments:
                del self.active_assignments[trash_id]
        else:
            # Create/Update Assignment
            # Legacy fields (score/profiles) can be dummy or derived
            start_score = profile_scores[0]["score"] if profile_scores else default_score
            p_names = [x["name"] for x in profile_scores]
            
            self.active_assignments[trash_id] = CustomFormatAssignment(
                trash_id=trash_id,
                name=cf_data.get('name'),
                description=cf_data.get('description', ''),
                score=start_score, # Deprecated but keep valid
                default_score=default_score,
                profiles=p_names, # Deprecated but keep valid
                profile_scores=profile_scores
            )
            
    def set_available_profiles(self, profiles: list[str]):
        """Update the list of profiles available for assignment."""
        self.profiles = profiles
        # Refresh current view if item selected
        current_item = self.list_widget.currentItem()
        if current_item:
            self.load_details(current_item)

    def load_assignments_from_template(self, cf_list: list[dict]):
        """
        Loads assignments from a template config list.
        cf_list structure: [{"trash_ids": ["id1"], "assign_scores_to": [{"name": "P1", "score": 100}]}]
        """
        self.active_assignments.clear()
        
        for entry in cf_list:
            trash_ids = entry.get("trash_ids")
            if trash_ids is None:
                trash_ids = []
            
            names = entry.get("names")
            if names:
                if isinstance(names, str):
                    names = [names]
                for name in names:
                    found = next((x for x in self.data if x.get('name') == name), None)
                    if found:
                        trash_ids.append(found.get('trash_id'))

            if not trash_ids: 
                continue
            
            # For each trash_id in this group (template entry can list multiple IDs)
            for tid in trash_ids:
                cf_data = next((x for x in self.data if x.get('trash_id') == tid), None)
                if not cf_data: continue
                
                # Get default score from CF data
                trash_scores = cf_data.get('trash_scores', {})
                default_score = trash_scores.get('default', 0) if isinstance(trash_scores, dict) else 0

                # Build profile_scores for THIS specific CF based on template assignments
                profile_scores = []
                assignments = entry.get("assign_scores_to") or []
                
                for assign in assignments:
                    a_name = assign.get("name")
                    a_score = assign.get("score")
                    
                    if a_score is None:
                        # Infer score from trash_scores using profile name
                        a_score = self._infer_score(cf_data, a_name, default_score)
                        
                    profile_scores.append({"name": a_name, "score": a_score})
                
                # If no explicit assignments, but we have inferred scores based on available profiles?
                # The template might specify assignments to specific names (e.g. FR-VOSTFR...).
                # Even if those profiles are NOT in our list of 'available_profiles' (from Tab 3), we should probably store them.
                # But typically we only care about assigning to the profile we are building.
                
                # However, if 'assign_scores_to' lists profiles, we should use them.
                
                # Derive legacy score (use first one or default)
                start_score = profile_scores[0]["score"] if profile_scores else default_score
                p_names = [x["name"] for x in profile_scores]

                self.active_assignments[tid] = CustomFormatAssignment(
                    trash_id=tid,
                    name=cf_data.get('name'),
                    description=cf_data.get('description', ''),
                    score=start_score, 
                    default_score=default_score,
                    profiles=p_names, 
                    profile_scores=profile_scores
                )

    def _infer_score(self, cf_data: dict, profile_name: str, default_score: int) -> int:
        """Attempts to infer the correct score for a profile based on trash_scores keys."""
        trash_scores = cf_data.get('trash_scores', {})
        if not trash_scores: return default_score
        
        # Normalize profile name
        p_norm = profile_name.lower().replace(" ", "-").replace("_", "-")
        
        best_match_score = default_score
        
        # Heuristic: Check if specific trash_score keys are contained in the profile name
        # e.g. "french-vostfr" (key) vs "fr-vostfr-web-2160p" (profile)
        # We look for significant overlap.
        for key, sc in trash_scores.items():
            if key == 'default': continue
            
            # Simple containment check: if the key (or its significant parts) is in the profile name
            # Remove 'french' from key as it's common prefix for FR profiles?
            k_norm = key.lower()
            
            # 0. Alias substitution (french -> fr)
            k_alias = k_norm.replace("french", "fr")
            
            # 1. Exact containment (with or without alias)
            if k_norm in p_norm or k_alias in p_norm:
                return sc
                
            # 2. Token overlap
            # Split key by '-' and check if ALL tokens map to the profile
            # We use the alias version to match "fr" tokens if needed
            tokens = [t for t in k_alias.split('-') if t not in ['hq', 'hd']] 
            if tokens and all(t in p_norm for t in tokens):
                return sc
                
            # 3. Special case fallback 
            if k_alias in ["vostfr", "vf", "vo"] and k_alias in p_norm.split("-"):
                 return sc

        return best_match_score

        # Refresh UI
        current_item = self.list_widget.currentItem()
        if current_item:
            self.load_details(current_item)
