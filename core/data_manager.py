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

    def get_app_includes(self, app: str) -> Dict[str, List[Dict]]:
        """Retrieves the raw 'includes' section (quality-profiles, etc.) for an app."""
        return self.templates.get(app, {}).get("includes", {})

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

    def get_include_data(self, app: str, include_name: str) -> Optional[Dict]:
        """Retrieves the full data/content of a specific include by name."""
        # We don't know the type, so we search all include categories
    def get_any_template_or_include(self, app: str, name: str) -> Optional[Dict]:
        """Finds a template or include by name from any source."""
        # 1. Check top-level templates
        for t in self.get_templates_for_app(app):
            if t.get("name") == name: return t
            
        # 2. Check 'includes' section
        includes_map = self.get_app_includes(app)
        for _, items in includes_map.items():
            for item in items:
                if item.get("name") == name: return item
        return None

    def resolve_template_includes(self, app: str, root_template: Dict) -> List[Dict]:
        """
        Recursively finds all 'custom_formats' from the template and its includes.
        Returns a merged list of custom_format definitions (the ones inside the template).
        """
        collected_cfs = []
        
        # 1. Add CFs from the root template itself
        if "custom_formats" in root_template:
            collected_cfs.extend(root_template["custom_formats"])
            
        # 2. Process includes
        # We need to loop carefully to avoid infinite recursion if there are cycles (unlikely but safe)
        processed_names = {root_template.get("name")}
        queue = [inc.get("template") for inc in root_template.get("include", []) if inc.get("template")]
        
        while queue:
            next_name = queue.pop(0)
            if next_name in processed_names: continue
            processed_names.add(next_name)
            
            item = self.get_any_template_or_include(app, next_name)
            if not item: continue
            
            # Add CFs from this included item
            if "custom_formats" in item:
                collected_cfs.extend(item["custom_formats"])
            
            # If this item has its own includes, add them to queue (BFS)
            # Some includes might be wrapped in 'content' if coming from 'includes' section
            # But usually 'includes' section items are raw YAML content wrappers. 
            # We need to check if 'content' exists or if keys are direct.
            
            # The 'includes' section items usually look like: 
            # { "name": "...", "content": { ... } } or just properties.
            # If it has "content", the useful stuff is inside.
            data_node = item.get("content", item)
            
            # Now allow recursion
            # Note: Recyclarr templates usually don't nest 'include' inside 'includes' section deeply, 
            # but top-level templates do include other templates.
            if "include" in data_node:
                for inc in data_node["include"]:
                    t_name = inc.get("template")
                    if t_name: queue.append(t_name)
                    
        return collected_cfs
