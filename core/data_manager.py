import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DataManager:
    """Manages JSON data (custom formats and templates)."""

    def __init__(self, custom_formats_path: str = "data/custom_formats.json",
                 templates_path: str = "data/templates.json"):
        # Resolve paths relative to the project root (where main.py is)
        root_path = Path(__file__).resolve().parent.parent
        self.custom_formats_path = root_path / custom_formats_path
        self.templates_path = root_path / templates_path
        
        self.custom_formats: Dict[str, Any] = {}
        self.templates: Dict[str, Any] = {}
        self.cf_by_id: Dict[str, Dict] = {}  # Index by trash_id

    def load_data(self) -> bool:
        """Loads JSON data from disk."""
        try:
            # Load custom_formats.json
            if self.custom_formats_path.exists():
                with open(self.custom_formats_path, "r", encoding="utf-8") as f:
                    self.custom_formats = json.load(f)
                self._index_custom_formats()
                total = self.custom_formats.get('metadata', {}).get('total_formats', 0)
                logger.info(f"Loaded {total} custom formats")
            else:
                logger.warning(f"File not found: {self.custom_formats_path}")
                return False

            # Load templates.json
            if self.templates_path.exists():
                with open(self.templates_path, "r", encoding="utf-8") as f:
                    self.templates = json.load(f)
                logger.info("Templates loaded successfully")
            else:
                logger.warning(f"File not found: {self.templates_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def _index_custom_formats(self):
        """Indexes custom formats by trash_id."""
        for app, app_data in self.custom_formats.get("custom_formats", {}).items():
            if app == "guide-only":
                continue
            for cf in app_data.get("formats", []):
                trash_id = cf.get("trash_id")
                if trash_id:
                    self.cf_by_id[trash_id] = {**cf, "app": app}

    def get_cf_by_id(self, trash_id: str) -> Optional[Dict]:
        """Retrieves a custom format by its trash_id."""
        return self.cf_by_id.get(trash_id)

    def get_cf_name(self, trash_id: str) -> str:
        """Retrieves the name of a custom format by its trash_id."""
        cf = self.cf_by_id.get(trash_id)
        return cf.get("name", trash_id) if cf else trash_id

    def get_custom_formats_for_app(self, app: str) -> List[Dict]:
        """Retrieves custom formats for a specific application."""
        return self.custom_formats.get("custom_formats", {}).get(app, {}).get("formats", [])

    def get_templates_for_app(self, app: str) -> List[Dict]:
        """Retrieves templates for a specific application."""
        return self.templates.get(app, {}).get("templates", [])

    def get_template_by_name(self, app: str, name: str) -> Optional[Dict]:
        """Retrieves a specific template by its name."""
        templates = self.get_templates_for_app(app)
        for template in templates:
            if template.get("name") == name:
                return template
        return None

    def get_includes_by_type(self, app: str, include_type: str) -> List[Dict]:
        """Retrieves includes of a specific type."""
        includes = self.templates.get(app, {}).get("includes", {})
        return includes.get(include_type, [])
