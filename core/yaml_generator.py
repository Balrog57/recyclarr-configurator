import os
import logging
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing import Dict, Any, List

# Ensure we import the InstanceConfig from our new models
from core.models import RecyclarrConfiguration, InstanceConfig

logger = logging.getLogger(__name__)

class YAMLGenerator:
    """
    Generates the recyclarr configuration file using ruamel.yaml.
    """
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def load_yaml(self, filepath: str) -> Dict[str, Any]:
        """Loads a YAML file and returns the dictionary."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return self.yaml.load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load YAML: {e}")
            raise e

    def generate_config(self, config: RecyclarrConfiguration, filename="config.yml") -> str:
        """
        Builds the dictionary from the RecyclarrConfiguration object and saves it to YAML.
        """
        output = {}
        
        # Add Header
        header = "# Configuration Recyclarr générée automatiquement\n"
        header += "# Documentation: https://recyclarr.dev\n"

        # Generate Radarr
        if config.radarr_instances:
            output["radarr"] = self._generate_app_section(config.radarr_instances)

        # Generate Sonarr
        if config.sonarr_instances:
            output["sonarr"] = self._generate_app_section(config.sonarr_instances)
        
        # Resolve path
        output_file = Path(os.getcwd()) / filename
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(header)
                self.yaml.dump(output, f)
            logger.info(f"Configuration saved to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Failed to generate YAML: {e}")
            raise e

    def _generate_app_section(self, instances: List[InstanceConfig]) -> Dict[str, Any]:
        """Generates the section for an app (radarr or sonarr)."""
        app_section = {}

        for instance in instances:
            instance_config = self._generate_instance_config(instance)
            if instance_config:
                app_section[instance.name] = instance_config

        return app_section

    def _generate_instance_config(self, instance: InstanceConfig) -> Dict[str, Any]:
        """Generates the configuration for a single instance in strict order."""
        # 1. Base Instance Config
        config = {
            "base_url": instance.base_url if instance.base_url else "http://localhost:7878",
            "api_key": instance.api_key if instance.api_key else "YOUR_API_KEY",
            "delete_old_custom_formats": instance.delete_old_custom_formats,
            "replace_existing_custom_formats": instance.replace_existing_custom_formats
        }

        # 2. Includes (templates)
        all_includes = []
        if instance.includes_quality_defs:
            all_includes.extend([{"template": t} for t in instance.includes_quality_defs])
        if instance.includes_profiles:
            all_includes.extend([{"template": t} for t in instance.includes_profiles])
        if instance.includes_cfs:
            all_includes.extend([{"template": t} for t in instance.includes_cfs])
            
        if all_includes:
            config["include"] = all_includes

        # Quality Profiles
        if instance.custom_profiles:
            qp_list = []
            for qp in instance.custom_profiles:
                if not qp.active:
                    continue
                    
                qp_dict = {
                    "name": qp.name,
                    "reset_unmatched_scores": {
                        "enabled": qp.reset_unmatched_scores
                    },
                    "upgrade": {
                        "allowed": qp.upgrade_allowed,
                        "until_quality": qp.upgrade_until,
                        "until_score": qp.until_score 
                    },
                    "min_format_score": qp.min_format_score,
                    "quality_sort": qp.quality_sort,
                    "score_set": qp.score_set
                }
                
                # Build the tree structure for 'qualities'
                qualities_structure = []
                for item in qp.items:
                    if item.qualities:
                        # It's a group
                        qualities_structure.append({
                            "name": item.name,
                            "qualities": item.qualities
                        })
                    else:
                        # It's a single quality
                        qualities_structure.append(item.name)
                        
                qp_dict["qualities"] = qualities_structure
                qp_list.append(qp_dict)
            
            if qp_list:
                config["quality_profiles"] = qp_list
            
        # 4. Custom Formats (AFTER quality_profiles)
        if instance.active_cfs:
            custom_formats_list = []
            
            # Map for looking up CF names by ID
            tid_to_name = {cf.trash_id: cf.name for cf in instance.active_cfs}
            
            groups = {}
            for cf in instance.active_cfs:
                if cf.profile_scores:
                    assignments = tuple(sorted((p['name'], p['score']) for p in cf.profile_scores))
                else:
                    assignments = tuple(sorted((p, cf.score) for p in cf.profiles))
                
                if assignments not in groups:
                    groups[assignments] = []
                groups[assignments].append(cf.trash_id)
            
            for assignments, trash_ids in groups.items():
                entry = CommentedMap()
                
                # Create a commented sequence for trash_ids
                ids_seq = CommentedSeq(trash_ids)
                for i, tid in enumerate(trash_ids):
                    name = tid_to_name.get(tid)
                    if name:
                        ids_seq.yaml_add_eol_comment(name, i)
                
                entry["trash_ids"] = ids_seq
                
                if assignments:
                    entry["assign_scores_to"] = [
                        {"name": p_name, "score": score} for p_name, score in assignments
                    ]
                custom_formats_list.append(entry)
            config["custom_formats"] = custom_formats_list

        return config
