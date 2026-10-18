import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.paths import data_file

logger = logging.getLogger(__name__)

class DataManager:
    """Manages JSON data (custom formats and templates/profiles)."""

    def __init__(self, custom_formats_file: str = "custom_formats.json",
                 templates_file: str = "templates.json"):
        self.custom_formats_file = custom_formats_file
        self.templates_file = templates_file
        
        self.custom_formats: Dict[str, Any] = {}
        self.templates: Dict[str, Any] = {}
        
        self.cf_by_id: Dict[str, Dict] = {}               # trash_id -> CF dict
        self.profiles_by_id: Dict[str, Dict] = {}         # trash_id -> Quality Profile dict
        self.profiles_by_name: Dict[tuple, Dict] = {}     # (app, name.lower()) -> QP dict
        self.groups_by_id: Dict[str, Dict] = {}           # trash_id -> CF Group dict
        self.definitions_by_name: Dict[tuple, Dict] = {}  # (app, name.lower()) -> QD dict
        self.templates_by_name: Dict[tuple, Dict] = {}    # (app, name) -> Template dict

    def load_data(self) -> bool:
        """Loads JSON data from disk and indexes all entities."""
        # Resolved at load time: the startup sync may just have written fresh files next to the app
        self.custom_formats_path = data_file(self.custom_formats_file)
        self.templates_path = data_file(self.templates_file)
        self._family_cfs = {}  # cache for quick_profile.family_cfs, rebuilt with the data
        try:
            # 1. Load custom_formats.json
            if self.custom_formats_path.exists():
                with open(self.custom_formats_path, "r", encoding="utf-8") as f:
                    self.custom_formats = json.load(f)
                self._index_custom_formats()
                total = self.custom_formats.get('metadata', {}).get('total_formats', len(self.cf_by_id))
                logger.info(f"Loaded {total} custom formats")
            else:
                logger.warning(f"File not found: {self.custom_formats_path}")
                return False

            # 2. Load templates.json
            if self.templates_path.exists():
                with open(self.templates_path, "r", encoding="utf-8") as f:
                    self.templates = json.load(f)
                self._index_templates_and_includes()
                logger.info("Templates and TRaSH quality profiles loaded successfully")
            else:
                logger.warning(f"File not found: {self.templates_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def _index_custom_formats(self):
        """Indexes custom formats by trash_id."""
        self.cf_by_id.clear()
        for app, app_data in self.custom_formats.get("custom_formats", {}).items():
            if app == "guide-only":
                continue
            for cf in app_data.get("formats", []):
                trash_id = cf.get("trash_id")
                if trash_id:
                    self.cf_by_id[trash_id] = {**cf, "app": app}

    def _index_templates_and_includes(self):
        """Indexes templates, quality profiles, quality definitions, and cf groups."""
        self.profiles_by_id.clear()
        self.profiles_by_name.clear()
        self.groups_by_id.clear()
        self.definitions_by_name.clear()
        self.templates_by_name.clear()

        for app in ["radarr", "sonarr"]:
            app_data = self.templates.get(app, {})
            
            # Index top-level templates
            for tmpl in app_data.get("templates", []):
                name = tmpl.get("name")
                if name:
                    self.templates_by_name[(app, name)] = tmpl

            # Index includes
            includes = app_data.get("includes", {})
            
            # Quality Profiles
            for qp in includes.get("quality-profiles", []):
                trash_id = qp.get("trash_id")
                name = qp.get("name")
                if trash_id:
                    self.profiles_by_id[trash_id] = qp
                if name:
                    self.profiles_by_name[(app, name.lower())] = qp

            # Quality Definitions (Sizes)
            for qd in includes.get("quality-definitions", []):
                name = qd.get("name")
                if name:
                    self.definitions_by_name[(app, name.lower())] = qd

            # Custom Format Groups
            for grp in includes.get("custom-formats", []):
                trash_id = grp.get("trash_id")
                if trash_id:
                    self.groups_by_id[trash_id] = grp

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

    def get_app_includes(self, app: str) -> Dict[str, List[Dict]]:
        """Retrieves the 'includes' section (quality-profiles, etc.) for an app."""
        return self.templates.get(app, {}).get("includes", {})

    def get_template_by_name(self, app: str, name: str) -> Optional[Dict]:
        """Retrieves a specific template by its name."""
        return self.templates_by_name.get((app, name))

    def get_includes_by_type(self, app: str, include_type: str) -> List[Dict]:
        """Retrieves includes of a specific type (e.g. quality-profiles, quality-definitions, custom-formats)."""
        includes = self.templates.get(app, {}).get("includes", {})
        return includes.get(include_type, [])

    def get_quality_profiles_for_app(self, app: str) -> List[Dict]:
        """Retrieves all guide-backed quality profiles for an app."""
        return self.get_includes_by_type(app, "quality-profiles")

    def get_quality_profile_by_id(self, trash_id: str) -> Optional[Dict]:
        """Retrieves a quality profile by its trash_id."""
        return self.profiles_by_id.get(trash_id)

    def get_quality_profile_by_name(self, app: str, name: str) -> Optional[Dict]:
        """Retrieves a quality profile by app and name."""
        return self.profiles_by_name.get((app, name.lower()))

    def get_include_data(self, app: str, identifier: str) -> Optional[Dict]:
        """Retrieves the full data of an include by name or trash_id."""
        # 1. Search by trash_id in quality profiles
        if identifier in self.profiles_by_id:
            return self.profiles_by_id[identifier]

        # 2. Search by trash_id in groups
        if identifier in self.groups_by_id:
            return self.groups_by_id[identifier]

        # 3. Search all include categories for app
        includes_map = self.get_app_includes(app)
        if not includes_map:
            return None
        
        id_lower = identifier.lower()
        for inc_type, inc_list in includes_map.items():
            for item in inc_list:
                if item.get("name") == identifier or item.get("trash_id") == identifier:
                    return item
                if item.get("name", "").lower() == id_lower:
                    return item
        return None
