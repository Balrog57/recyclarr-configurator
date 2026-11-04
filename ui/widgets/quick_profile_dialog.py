from PySide6.QtWidgets import (QDialog, QFormLayout, QComboBox, QListWidget, QListWidgetItem,
                               QLabel, QDialogButtonBox)
from PySide6.QtCore import Qt

from core.quick_profile import VARIANT_LABELS, profile_tiers, rejected_criteria, describe, variants


class QuickProfileDialog(QDialog):
    """Quick setup: content, quality, TRaSH language variant and accepted criteria; everything else is TRaSH Guides."""
    def __init__(self, data_manager, app_type: str, parent=None):
        super().__init__(parent)
        self.dm = data_manager
        self.app_type = app_type
        self.setWindowTitle("Assistant rapide")
        self.resize(560, 560)
        layout = QFormLayout(self)

        self.combo_content = QComboBox()
        self.combo_content.addItem("Films" if app_type == "radarr" else "Séries", False)
        self.combo_content.addItem("Animés", True)
        layout.addRow("Contenu :", self.combo_content)

        self.combo_tier = QComboBox()
        layout.addRow("Qualité :", self.combo_tier)

        self.combo_variant = QComboBox()
        layout.addRow("Langue (variante TRaSH) :", self.combo_variant)

        self.lbl_summary = QLabel()
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setStyleSheet("color: #888;")
        layout.addRow(self.lbl_summary)

        # Criteria the guide rejects in this profile (read from TRaSH data): check to accept them
        lbl_crit = QLabel("Critères refusés par TRaSH dans ce profil : cochez ceux que vous acceptez (ex. x265, AV1)")
        lbl_crit.setWordWrap(True)
        layout.addRow(lbl_crit)
        self.list_criteria = QListWidget()
        self.list_criteria.setMinimumHeight(150)
        layout.addRow(self.list_criteria)

        hint = QLabel("Prérequis TRaSH : dans les indexeurs, réglez « Multi Languages » sur Original + French. "
                      "Tous les scores viennent de TRaSH ; vous pourrez changer chacun d'eux à l'étape 4.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888;")
        layout.addRow(hint)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

        self.combo_content.currentIndexChanged.connect(self._on_content_changed)
        self.combo_tier.currentIndexChanged.connect(self._on_tier_changed)
        self.combo_variant.currentIndexChanged.connect(self._refresh)
        self._on_content_changed()

    def _on_content_changed(self):
        self.combo_tier.blockSignals(True)
        self.combo_tier.clear()
        for label in profile_tiers(self.dm, self.app_type, self.combo_content.currentData()):
            self.combo_tier.addItem(label, label)
        self.combo_tier.blockSignals(False)
        self._on_tier_changed()

    def _on_tier_changed(self):
        self.combo_variant.blockSignals(True)
        self.combo_variant.clear()
        for variant in variants(self.dm, self.app_type, self.combo_content.currentData(), self.combo_tier.currentData()):
            self.combo_variant.addItem(VARIANT_LABELS.get(variant, variant), variant)
        self.combo_variant.blockSignals(False)
        self._refresh()

    def _refresh(self, *args):
        """Summary and rejected criteria depend on content, tier and variant."""
        ready = self.combo_variant.count() > 0
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(ready)
        kept = set(self.accepted())
        self.list_criteria.clear()
        self.lbl_summary.clear()
        if not ready:
            return
        choice = (self.dm, self.app_type, self.combo_content.currentData(), self.combo_tier.currentData(), self.combo_variant.currentData())
        self.lbl_summary.setText(describe(*choice))
        for tid, name, score in rejected_criteria(*choice):
            item = QListWidgetItem(f"{name}  ({score})")
            item.setData(Qt.UserRole, tid)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if tid in kept else Qt.Unchecked)
            self.list_criteria.addItem(item)

    def accepted(self) -> list:
        items = [self.list_criteria.item(i) for i in range(self.list_criteria.count())]
        return [it.data(Qt.UserRole) for it in items if it.checkState() == Qt.Checked]

    def get_values(self) -> dict:
        return {
            "anime": self.combo_content.currentData(),
            "tier": self.combo_tier.currentData(),
            "variant": self.combo_variant.currentData(),
            "accepted": self.accepted(),
        }
