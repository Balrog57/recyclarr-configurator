import os
import logging
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing import Dict, Any, List

from core.models import RecyclarrConfiguration, InstanceConfig, QualityProfile

logger = logging.getLogger(__name__)

class YAMLGenerator:
    """
    Generates the recyclarr configuration file using ruamel.yaml according to Recyclarr v8 schema.
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
        output = CommentedMap()
        
        # Header
        header = "# Configuration Recyclarr générée automatiquement\n"
        header += "# Documentation: https://recyclarr.dev\n"

        # Generate Radarr
        if config.radarr_instances:
            output["radarr"] = self._generate_app_section(config.radarr_instances, default_qdef="movie")

        # Generate Sonarr
        if config.sonarr_instances:
            output["sonarr"] = self._generate_app_section(config.sonarr_instances, default_qdef="series")
        
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

    def _generate_app_section(self, instances: List[InstanceConfig], default_qdef: str = "movie") -> Dict[str, Any]:
        """Generates the section for an app (radarr or sonarr)."""
        app_section = CommentedMap()

        for instance in instances:
            instance_config = self._generate_instance_config(instance, default_qdef=default_qdef)
            if instance_config:
                app_section[instance.name] = instance_config

        return app_section

    def _generate_instance_config(self, instance: InstanceConfig, default_qdef: str = "movie") -> Dict[str, Any]:
        """Generates the configuration for a single instance in strict v8 order."""
        config = CommentedMap()

        # 1. Base Instance Config
        default_url = "http://localhost:8989" if default_qdef == "series" else "http://localhost:7878"
        config["base_url"] = instance.base_url if instance.base_url else default_url
        config["api_key"] = instance.api_key if instance.api_key else "<YOUR_API_KEY>"
        config["delete_old_custom_formats"] = instance.delete_old_custom_formats

        # 2. Quality Definition (Recyclarr v8 guide-backed standard)
        qdef_type = getattr(instance, "quality_definition_type", None) or default_qdef
        config["quality_definition"] = CommentedMap({"type": qdef_type})

        # 3. Custom Format Groups (v8 replaces the removed official include templates)
        if instance.includes_cfs:
            config["custom_format_groups"] = CommentedMap({
                "add": [CommentedMap({"trash_id": tid}) for tid in instance.includes_cfs]
            })

        # 4. Quality Profiles (TRaSH Guides guide-backed and/or custom)
        if instance.custom_profiles:
            qp_list = []
            for qp in instance.custom_profiles:
                if not qp.active:
                    continue
                
                qp_dict = CommentedMap()
                trash_id = getattr(qp, "trash_id", "").strip()

                if trash_id:
                    # Guide-backed profile
                    qp_dict["trash_id"] = trash_id
                # Always explicit: keeps renames and matches assign_scores_to references by name
                qp_dict["name"] = qp.name

                qp_dict["reset_unmatched_scores"] = CommentedMap({
                    "enabled": qp.reset_unmatched_scores
                })

                # Upgrade settings
                if qp.upgrade_allowed or qp.upgrade_until:
                    upgrade_dict = CommentedMap({"allowed": qp.upgrade_allowed})
                    if qp.upgrade_until:
                        upgrade_dict["until_quality"] = qp.upgrade_until
                    if qp.until_score:
                        upgrade_dict["until_score"] = qp.until_score
                    qp_dict["upgrade"] = upgrade_dict

                if qp.min_format_score != 0:
                    qp_dict["min_format_score"] = qp.min_format_score

                if qp.score_set:
                    qp_dict["score_set"] = qp.score_set

                # Guide-backed profiles take their qualities from TRaSH Guides
                if not trash_id:
                    qualities_structure = []
                    for item in qp.items:
                        if item.qualities:
                            qualities_structure.append(CommentedMap({
                                "name": item.name,
                                "qualities": item.qualities
                            }))
                        else:
                            qualities_structure.append(CommentedMap({"name": item.name}))
                            
                    if qualities_structure:
                        qp_dict["qualities"] = qualities_structure

                qp_list.append(qp_dict)
            
            if qp_list:
                config["quality_profiles"] = qp_list

        # 5. Custom Formats (AFTER quality_profiles)
        if instance.active_cfs:
            custom_formats_list = []
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
                
                # Commented sequence for trash_ids with CF names
                ids_seq = CommentedSeq(trash_ids)
                for i, tid in enumerate(trash_ids):
                    name = tid_to_name.get(tid)
                    if name:
                        ids_seq.yaml_add_eol_comment(name, i)
                
                entry["trash_ids"] = ids_seq
                
                if assignments:
                    entry["assign_scores_to"] = [
                        CommentedMap({"name": p_name, "score": score}) for p_name, score in assignments
                    ]
                custom_formats_list.append(entry)
                
            config["custom_formats"] = custom_formats_list

        return config
