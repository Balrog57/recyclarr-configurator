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

    def get_any_template_or_include(self, app: str, identifier: str) -> Optional[Dict]:
        """Finds a template or include by name or trash_id from any source."""
        # Check top-level templates
        tmpl = self.get_template_by_name(app, identifier)
        if tmpl:
            return tmpl
            
        # Check includes
        return self.get_include_data(app, identifier)

    def resolve_template_includes(self, app: str, root_template: Dict) -> List[Dict]:
        """
        Resolves custom formats and their recommended scores from:
        1. Recyclarr v8 templates (quality_profiles trash_ids, custom_format_groups, custom_formats)
        2. Guide-backed Quality Profile formatItems
        3. Legacy includes (include: - template: ...)
        """
        collected_cfs = []
        processed_tids = set()

        # Extract content node for this app
        app_content = root_template.get("content", {}).get(app, {})
        instance_data = {}
        if app_content:
            config_key = list(app_content.keys())[0]
            instance_data = app_content.get(config_key, {}) or {}

        # 1. Direct custom_formats in template (if any)
        if "custom_formats" in instance_data and isinstance(instance_data["custom_formats"], list):
            collected_cfs.extend(instance_data["custom_formats"])

        # 2. Resolve CFs from Guide-Backed Quality Profiles (v8)
        qp_entries = instance_data.get("quality_profiles", [])
        for qp_entry in qp_entries:
            if not isinstance(qp_entry, dict):
                continue
            qp_trash_id = qp_entry.get("trash_id")
            if not qp_trash_id:
                continue

            profile = self.get_quality_profile_by_id(qp_trash_id)
            if not profile:
                continue

            p_name = profile.get("name", "Guide Profile")
            score_set = profile.get("score_set") or profile.get("trash_score_set", "")

            # formatItems in profile: { "CF Name": "trash_id", ... }
            format_items = profile.get("formatItems", {})
            for cf_name, cf_tid in format_items.items():
                if cf_tid in processed_tids:
                    continue
                processed_tids.add(cf_tid)

                cf_data = self.get_cf_by_id(cf_tid)
                trash_scores = cf_data.get("trash_scores", {}) if cf_data else {}
                
                # Determine score: check score_set first, then default
                cf_score = 0
                if score_set and score_set in trash_scores:
                    cf_score = trash_scores[score_set]
                elif "default" in trash_scores:
                    cf_score = trash_scores["default"]

                collected_cfs.append({
                    "trash_ids": [cf_tid],
                    "assign_scores_to": [{"name": p_name, "score": cf_score}]
                })

        # 3. Resolve CFs from custom_format_groups (v8)
        cf_groups = instance_data.get("custom_format_groups", {})
        if isinstance(cf_groups, dict):
            add_groups = cf_groups.get("add") or []
            for grp_entry in add_groups:
                if not isinstance(grp_entry, dict):
                    continue
                grp_id = grp_entry.get("trash_id")
                grp = self.groups_by_id.get(grp_id)
                if not grp:
                    continue
                for cf_tid in grp.get("trash_ids", []):
                    if cf_tid in processed_tids:
                        continue
                    processed_tids.add(cf_tid)
                    cf_data = self.get_cf_by_id(cf_tid)
                    default_score = cf_data.get("trash_scores", {}).get("default", 0) if cf_data else 0
                    collected_cfs.append({
                        "trash_ids": [cf_tid],
                        "assign_scores_to": [] # Will infer or match active profiles
                    })

        # 4. Legacy include recursion fallback
        root_includes = root_template.get("include") or instance_data.get("include") or []
        queue = [inc.get("template") for inc in root_includes if isinstance(inc, dict) and inc.get("template")]
        processed_names = {root_template.get("name")}

        while queue:
            next_name = queue.pop(0)
            if not next_name or next_name in processed_names:
                continue
            processed_names.add(next_name)

            item = self.get_any_template_or_include(app, next_name)
            if not item:
                continue

            if "custom_formats" in item and item["custom_formats"]:
                collected_cfs.extend(item["custom_formats"])

            data_node = item.get("content", item)
            if isinstance(data_node, dict) and "include" in data_node and data_node["include"]:
                for inc in data_node["include"]:
                    if isinstance(inc, dict):
                        t_name = inc.get("template")
                        if t_name:
                            queue.append(t_name)

        return collected_cfs
