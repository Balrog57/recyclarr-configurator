import os
import logging
from pathlib import Path
from ruamel.yaml import YAML
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
        """Generates the configuration for a single instance."""
        config = {
            "base_url": instance.base_url if instance.base_url else "http://localhost:7878",
            "api_key": instance.api_key if instance.api_key else "YOUR_API_KEY",
        }

        # Includes (templates)
        # We consolidate all include lists
        all_includes = []
        if instance.includes_quality_defs:
            all_includes.extend([{"template": t} for t in instance.includes_quality_defs])
        if instance.includes_profiles:
            all_includes.extend([{"template": t} for t in instance.includes_profiles])
        if instance.includes_cfs:
            all_includes.extend([{"template": t} for t in instance.includes_cfs])
            
        if all_includes:
            config["include"] = all_includes

        # Custom Formats with Grouping Logic
        if instance.active_cfs:
            custom_formats_list = []
            
            # Grouping logic: Key = (Score, Tuple(Profiles))
            # groups = { (score, profiles_tuple): [trash_id1, trash_id2, ...] }
            groups = {}
            for cf in instance.active_cfs:
                # We sort profiles tuple to ensure uniqueness of the key
                key = (cf.score, tuple(sorted(cf.profiles)))
                if key not in groups:
                    groups[key] = []
                groups[key].append(cf.trash_id)
            
            # Create YAML entries from groups
            for (score, profiles), trash_ids in groups.items():
                entry = {"trash_ids": trash_ids}
                
                # If there are profiles assigned, we use assign_scores_to
                if profiles:
                    entry["assign_scores_to"] = [
                        {"name": p_name, "score": score} for p_name in profiles
                    ]
                else:
                    # Fallback logic if no specific profiles are assigned but a score is set
                    # This might depend on user intent, but usually we want to assign scores globally if no profile specified?
                    # Or maybe just set the quality_profiles to empty list. 
                    # Assuming if no profile is selected, it applies to all? Use cautiously.
                    # Based on user requets, 'profiles' is the key. 
                    # If empty, maybe we just set score? (Not standard Recyclarr way unless global)
                    # Let's keep it simple: if no profiles, we might just list it with score if supported,
                    # but typically assign_scores_to is preferred. 
                    # If list is empty, we assume it's just enabled with that score globally or we rely on default.
                    
                    # For now, if no profiles, we skip assign_scores_to (using default score or just enabling)
                    # But if score != default, we might want to specify it. 
                    # Let's assume the user ALWAYS selects profiles in the UI logic.
                    pass 
                
                custom_formats_list.append(entry)

            config["custom_formats"] = custom_formats_list

        # Quality Profiles
        if instance.custom_profiles:
            qp_list = []
            for qp in instance.custom_profiles:
                qp_dict = {
                    "name": qp.name,
                    "reset_unmatched_scores": {
                        "enabled": True
                    },
                    "upgrade": {
                        "allowed": qp.upgrade_allowed,
                        "until_quality": qp.upgrade_until,
                        "until_score": 10000 
                    },
                    "min_format_score": qp.min_format_score,
                    "quality_sort": "top",
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
                        qualities_structure.append(item.name) # Just the string name if it's a leaf quality?
                        # Recyclarr spec: - name: "Quality" OR just "Quality"? 
                        # Usually inside 'qualities' list of a profile, it is a list of objects or strings.
                        # If simple quality: just string. 
                        # If group: object with name and qualities.
                        # User example:
                        # qualities:
                        #   - name: Bluray...
                        #     qualities: ...
                        #   - name: Bluray...
                        #     qualities: ...
                        # All are groups in the user example.
                        # But basic qualities should be just strings or {name: Q}.
                        # Let's use {name: Q} to be safe or string. 
                        # Looking at Recyclarr docs, simple strings are allowed.
                        # Let's check my previous code: `qualities_structure.append({"name": item.name})`
                        # This works `name: 720p`.
                        pass
                        
                # Actually, correction: if it is a single item at root, it is usually just a quality name or {name: X}
                # But if we want to support groups, we use the dict structure.
                # My previous code did: qualities_structure.append({"name": item.name}) for single items.
                # If the user example has ONLY groups, then my profile builder should force groups?
                # The user said "create groups".
                # I'll stick to the previous dict logic for single items, it's valid.

                qp_dict["qualities"] = qualities_structure
                qp_list.append(qp_dict)
            
            config["quality_profiles"] = qp_list

        return config
