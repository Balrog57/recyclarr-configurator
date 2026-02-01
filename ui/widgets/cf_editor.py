from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QSpinBox, QCheckBox, QGroupBox, QLineEdit)
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
        
        self.lbl_name = QLabel("Sélectionnez un format")
        self.lbl_name.setProperty("class", "h3")
        
        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #888; font-style: italic; margin-bottom: 10px;")
        
        # Score Section
        score_layout = QHBoxLayout()
        self.spin_score = QSpinBox()
        self.spin_score.setRange(-10000, 10000)
        self.spin_score.valueChanged.connect(self.update_model)
        
        self.lbl_default_score = QLabel("(Défaut: 0)")
        self.lbl_default_score.setStyleSheet("color: #666; margin-left: 5px;")
        
        score_layout.addWidget(QLabel("Score:"))
        score_layout.addWidget(self.spin_score)
        score_layout.addWidget(self.lbl_default_score)
        score_layout.addStretch()
        
        # Assignment (assign_scores_to)
        # Using QListWidget for checkboxes as it's cleaner than dynamic checkboxes in a layout
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.NoSelection) # Checkboxes only
        # We handle itemChanged for updates
        self.profiles_list.itemChanged.connect(self.on_profile_check_changed)
        
        details_layout.addWidget(self.lbl_name)
        details_layout.addWidget(self.lbl_desc)
        details_layout.addLayout(score_layout)
        details_layout.addWidget(QLabel("Appliquer au profil :"))
        details_layout.addWidget(self.profiles_list)
        
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
        self.profiles_list.blockSignals(True)
        self.spin_score.blockSignals(True)

        self.lbl_name.setText(cf_data.get('name'))
        self.lbl_desc.setText(cf_data.get('description', ''))
        
        # Default score logic
        trash_scores = cf_data.get('trash_scores', {})
        # Note: trash_scores structure can be diverse, usually 'default' key exists
        default_score = trash_scores.get('default', 0) if isinstance(trash_scores, dict) else 0
        self.lbl_default_score.setText(f"(Défaut: {default_score})")
        
        current_assignment = self.active_assignments.get(trash_id)
        
        if current_assignment:
            self.spin_score.setValue(current_assignment.score)
        else:
            self.spin_score.setValue(default_score)
        
        # Update Profiles List
        self.profiles_list.clear() # Clear entries
        if not self.profiles:
             # Just show a disabled item saying no profiles
             item = QListWidgetItem("Aucun profil défini")
             item.setFlags(Qt.NoItemFlags)
             self.profiles_list.addItem(item)
        else:
            for p_name in self.profiles:
                p_item = QListWidgetItem(p_name)
                p_item.setFlags(p_item.flags() | Qt.ItemIsUserCheckable)
                
                if current_assignment and p_name in current_assignment.profiles:
                    p_item.setCheckState(Qt.Checked)
                else:
                    p_item.setCheckState(Qt.Unchecked)
                    
                self.profiles_list.addItem(p_item)
        
        self.profiles_list.blockSignals(False)
        self.spin_score.blockSignals(False)
        
    def on_profile_check_changed(self, item):
        self.update_model()
        
    def update_model(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return
        trash_id = current_item.data(99)
        
        selected_profiles = []
        for i in range(self.profiles_list.count()):
            p_item = self.profiles_list.item(i)
            if p_item.checkState() == Qt.Checked:
                selected_profiles.append(p_item.text())
        
        if not selected_profiles:
            if trash_id in self.active_assignments:
                del self.active_assignments[trash_id]
        else:
            default_text = self.lbl_default_score.text().replace("(Défaut: ", "").replace(")", "")
            try:
                def_score = int(default_text)
            except:
                def_score = 0
                
            self.active_assignments[trash_id] = CustomFormatAssignment(
                trash_id=trash_id,
                name=current_item.text(),
                description=self.lbl_desc.text(),
                score=self.spin_score.value(),
                default_score=def_score,
                profiles=selected_profiles
            )
            
    def set_available_profiles(self, profiles: list[str]):
        """Update the list of profiles available for assignment."""
        self.profiles = profiles
        # Refresh current view if item selected
        current_item = self.list_widget.currentItem()
        if current_item:
            self.load_details(current_item)
