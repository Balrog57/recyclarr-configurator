from PySide6.QtWidgets import (QDialog, QFormLayout, QComboBox, QListWidget, QListWidgetItem,
                               QAbstractItemView, QCheckBox, QLabel, QDialogButtonBox, QHBoxLayout, QPushButton,
                               QVBoxLayout, QWidget)
from PySide6.QtCore import Qt

from core.quick_profile import LANGUAGES, tiers_for, describe

# Default language order and accepted set per content type
DEFAULTS = {
    False: (["multi", "vf", "vostfr", "vo"], {"multi", "vf", "vostfr"}),   # Films / Séries
    True: (["multi", "vostfr", "vf", "vo"], {"multi", "vostfr"}),          # Animés: pas de VF
}


class QuickProfileDialog(QDialog):
    """Quick setup: pick content, quality, language order and codecs; the rest is TRaSH Guides."""
    def __init__(self, app_type: str, parent=None):
        super().__init__(parent)
        self.app_type = app_type
        self.setWindowTitle("Assistant rapide")
        self.resize(520, 480)
        layout = QFormLayout(self)

        self.combo_content = QComboBox()
        self.combo_content.addItem("Films" if app_type == "radarr" else "Séries", False)
        self.combo_content.addItem("Animés", True)
        layout.addRow("Contenu :", self.combo_content)

        self.combo_tier = QComboBox()
        layout.addRow("Qualité :", self.combo_tier)

        # Language order: check to accept, drag (or buttons) to reorder
        self.list_lang = QListWidget()
        self.list_lang.setDragDropMode(QAbstractItemView.InternalMove)
        btn_up, btn_down = QPushButton("▲"), QPushButton("▼")
        btn_up.setAccessibleName("Monter la langue")
        btn_down.setAccessibleName("Descendre la langue")
        btn_up.clicked.connect(lambda: self._move(-1))
        btn_down.clicked.connect(lambda: self._move(1))
        moves = QVBoxLayout()
        moves.addWidget(btn_up)
        moves.addWidget(btn_down)
        moves.addStretch()
        lang_row = QHBoxLayout()
        lang_row.addWidget(self.list_lang)
        lang_row.addLayout(moves)
        lang_box = QWidget()
        lang_box.setLayout(lang_row)
        lbl_lang = QLabel("Langues : cochez pour accepter, l'ordre fixe la préférence (glisser ou ▲▼)")
        lbl_lang.setWordWrap(True)
        layout.addRow(lbl_lang)
        layout.addRow(lang_box)

        self.lbl_summary = QLabel()
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setStyleSheet("color: #888;")
        layout.addRow(self.lbl_summary)

        self.chk_x265 = QCheckBox("Accepter x265 / HEVC")
        self.chk_av1 = QCheckBox("Accepter AV1")
        self.chk_x265.setChecked(True)
        self.chk_av1.setChecked(True)
        layout.addRow("Codecs :", self.chk_x265)
        layout.addRow("", self.chk_av1)

        hint = QLabel("Prérequis TRaSH : dans les indexeurs, réglez « Multi Languages » sur Original + French.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888;")
        layout.addRow(hint)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

        self.combo_content.currentIndexChanged.connect(self._on_content_changed)
        self.list_lang.itemChanged.connect(self._update_summary)
        self.list_lang.model().rowsMoved.connect(self._update_summary)
        self._on_content_changed()

    def _on_content_changed(self):
        anime = self.combo_content.currentData()
        self.combo_tier.clear()
        for key, label in tiers_for(self.app_type, anime).items():
            self.combo_tier.addItem(label, key)
        order, accepted = DEFAULTS[anime]
        self.list_lang.blockSignals(True)
        self.list_lang.clear()
        for lang in order:
            item = QListWidgetItem(LANGUAGES[lang])
            item.setData(Qt.UserRole, lang)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if lang in accepted else Qt.Unchecked)
            self.list_lang.addItem(item)
        self.list_lang.blockSignals(False)
        # Show every language without a scrollbar
        rows = sum(self.list_lang.sizeHintForRow(i) for i in range(self.list_lang.count()))
        self.list_lang.setFixedHeight(rows + 2 * self.list_lang.frameWidth() + 8)
        self._update_summary()

    def _move(self, delta):
        row = self.list_lang.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < self.list_lang.count():
            return
        item = self.list_lang.takeItem(row)
        self.list_lang.insertItem(target, item)
        self.list_lang.setCurrentRow(target)
        self._update_summary()

    def _update_summary(self, *args):
        ranking = self.ranking()
        self.lbl_summary.setText(describe(ranking))
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(bool(ranking))

    def ranking(self) -> list:
        items = [self.list_lang.item(i) for i in range(self.list_lang.count())]
        return [it.data(Qt.UserRole) for it in items if it.checkState() == Qt.Checked]

    def get_values(self) -> dict:
        return {
            "anime": self.combo_content.currentData(),
            "tier": self.combo_tier.currentData(),
            "ranking": self.ranking(),
            "accept_x265": self.chk_x265.isChecked(),
            "accept_av1": self.chk_av1.isChecked(),
        }
