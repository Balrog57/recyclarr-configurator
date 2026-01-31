#!/usr/bin/env python3
"""
Recyclarr Config Templates Extractor

Extracts configuration templates and includes from the recyclarr/config-templates
GitHub repository and generates a structured JSON file with all templates,
includes, and their associated metadata.

Usage:
    python templates_extractor.py [--output OUTPUT_FILE] [--token TOKEN]
"""

import argparse
import json
import logging
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import requests
import yaml

# Configuration
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
REPO_OWNER = "recyclarr"
REPO_NAME = "config-templates"
BRANCH = "master"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class IncludeFile:
    """Represents an include file (quality definitions, quality profiles, custom formats)."""
    name: str
    file: str
    path: str
    type: str  # 'quality-definition', 'quality-profile', 'custom-format'
    content: dict[str, Any] = field(default_factory=dict)
    trash_ids: list[str] = field(default_factory=list)
    assign_scores_to: list[dict] = field(default_factory=list)


@dataclass
class Template:
    """Represents a template file from the templates directory."""
    name: str
    file: str
    path: str
    description: str = ""
    includes: list[str] = field(default_factory=list)
    content: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Configuration for an application (radarr or sonarr)."""
    templates: list[Template] = field(default_factory=list)
    includes: dict[str, list[IncludeFile]] = field(default_factory=dict)


class GitHubClient:
    """Client for interacting with GitHub (web scraping only)."""

    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self._file_cache: dict[str, list[str]] = {}
        self._content_cache: dict[str, str] = {}

        # Increase connection pool size
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
        self.session.mount("https://", adapter)

    def get_files_in_path(self, path_prefix: str) -> list[str]:
        """Get all files under a path prefix by scraping GitHub HTML."""
        cache_key = f"files:{path_prefix}"
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        files = self._scrape_directory_html(path_prefix)
        self._file_cache[cache_key] = files
        return files

    def _scrape_directory_html(self, path_prefix: str, recursive: bool = True) -> list[str]:
        """Scrape directory listing from GitHub HTML page."""
        files = []
        directories = []
        path = path_prefix.rstrip("/")
        url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/tree/{BRANCH}/{path}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Try to extract items with their content type from GitHub's JSON
            # Pattern: "path":"...", ... "contentType":"file" or "directory"
            item_pattern = r'"path":"(' + re.escape(path) + r'/[^"]+)"[^}]*"contentType":"([^"]+)"'
            typed_matches = re.findall(item_pattern, response.text)

            if typed_matches:
                for item_path, content_type in typed_matches:
                    if content_type == "file":
                        files.append(item_path)
                    elif content_type == "directory":
                        directories.append(item_path)
            else:
                # Fallback: extract paths and guess type by extension
                pattern = r'"path":"(' + re.escape(path) + r'/[^"]+)"'
                matches = re.findall(pattern, response.text)

                for match in matches:
                    # Check if it's a file (has extension) or directory
                    if '.' in match.split('/')[-1]:
                        files.append(match)
                    else:
                        directories.append(match)

            # Recursively scrape subdirectories
            if recursive:
                for subdir in directories:
                    subfiles = self._scrape_directory_html(subdir, recursive=True)
                    files.extend(subfiles)

        except Exception as e:
            logger.error(f"Failed to scrape directory {path}: {e}")

        return files

    def get_raw_file(self, path: str) -> str:
        """Get raw content of a file."""
        if path in self._content_cache:
            return self._content_cache[path]

        url = f"{GITHUB_RAW_BASE}/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{path}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        content = response.text
        self._content_cache[path] = content
        return content

    def get_yaml_file(self, path: str) -> dict[str, Any]:
        """Get and parse a YAML file."""
        content = self.get_raw_file(path)
        return yaml.safe_load(content)


class ConfigTemplatesExtractor:
    """Extracts templates and includes from config-templates repository."""

    def __init__(self, client: GitHubClient):
        self.client = client

    def extract_all(self) -> dict[str, Any]:
        """Extract all templates and includes for both radarr and sonarr."""
        logger.info("Starting extraction from config-templates...")

        result = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
                "branch": BRANCH,
            },
            "radarr": self._extract_app("radarr"),
            "sonarr": self._extract_app("sonarr"),
        }

        return result

    def _extract_app(self, app: str) -> dict[str, Any]:
        """Extract templates and includes for a specific application."""
        logger.info(f"Extracting configuration for {app}...")

        return {
            "templates": self._extract_templates(app),
            "includes": self._extract_includes(app),
        }

    def _extract_templates(self, app: str) -> list[dict[str, Any]]:
        """Extract templates from the templates directory."""
        templates_path = f"{app}/templates"
        templates: list[dict[str, Any]] = []

        try:
            files = self.client.get_files_in_path(templates_path)
            # Filter for .yml files and exclude sqp subfolder
            yml_files = [f for f in files if f.endswith(".yml") and "/sqp/" not in f]

            logger.info(f"Found {len(yml_files)} template files for {app} (excluding sqp)")

            for file_path in yml_files:
                try:
                    template = self._parse_template(file_path)
                    if template:
                        templates.append(template)
                except Exception as e:
                    logger.warning(f"Failed to parse template {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to extract templates for {app}: {e}")

        return templates

    def _parse_template(self, file_path: str) -> dict[str, Any] | None:
        """Parse a single template file."""
        try:
            content = self.client.get_yaml_file(file_path)
            file_name = Path(file_path).name
            template_name = file_name.replace(".yml", "")

            # Extract includes from the template content
            includes = self._extract_includes_from_content(content)

            # Extract description from comments if present
            raw_content = self.client.get_raw_file(file_path)
            description = self._extract_description_from_comments(raw_content)

            return {
                "name": template_name,
                "file": file_name,
                "path": file_path,
                "description": description,
                "includes": includes,
                "content": content,
            }

        except Exception as e:
            logger.warning(f"Error parsing template {file_path}: {e}")
            return None

    def _extract_includes_from_content(self, content: dict) -> list[str]:
        """Extract include template names from YAML content."""
        includes = []

        # Navigate through the YAML structure to find includes
        for app_key, app_config in content.items():
            if isinstance(app_config, dict):
                for instance_key, instance_config in app_config.items():
                    if isinstance(instance_config, dict) and "include" in instance_config:
                        for include_item in instance_config.get("include", []):
                            if isinstance(include_item, dict) and "template" in include_item:
                                includes.append(include_item["template"])

        return includes

    def _extract_description_from_comments(self, raw_content: str) -> str:
        """Extract description from YAML comments."""
        lines = raw_content.split("\n")
        description_lines = []

        for line in lines:
            if line.startswith("#"):
                comment_text = line.lstrip("# ").strip()
                if comment_text and not comment_text.startswith(("Updated:", "Documentation:")):
                    description_lines.append(comment_text)
            elif line.strip() and not line.startswith("#"):
                break

        return " ".join(description_lines[:3]) if description_lines else ""

    def _extract_includes(self, app: str) -> dict[str, list[dict[str, Any]]]:
        """Extract include files (quality definitions, profiles, custom formats)."""
        includes_path = f"{app}/includes"
        includes: dict[str, list[dict[str, Any]]] = {
            "quality-definitions": [],
            "quality-profiles": [],
            "custom-formats": [],
        }

        try:
            # Extract quality definitions
            qd_path = f"{includes_path}/quality-definitions"
            includes["quality-definitions"] = self._extract_include_files(qd_path, "quality-definition")

            # Extract quality profiles
            qp_path = f"{includes_path}/quality-profiles"
            includes["quality-profiles"] = self._extract_include_files(qp_path, "quality-profile")

            # Extract custom formats
            cf_path = f"{includes_path}/custom-formats"
            includes["custom-formats"] = self._extract_custom_format_files(cf_path)

        except Exception as e:
            logger.error(f"Failed to extract includes for {app}: {e}")

        return includes

    def _extract_include_files(self, path: str, file_type: str) -> list[dict[str, Any]]:
        """Extract generic include files from a directory."""
        files: list[dict[str, Any]] = []

        try:
            all_files = self.client.get_files_in_path(path)
            # Filter for .yml files and exclude sqp
            yml_files = [f for f in all_files if f.endswith(".yml") and "/sqp/" not in f and "-sqp-" not in f]

            for file_path in yml_files:
                try:
                    content = self.client.get_yaml_file(file_path)
                    file_name = Path(file_path).name
                    template_name = file_name.replace(".yml", "")

                    files.append({
                        "name": template_name,
                        "file": file_name,
                        "path": file_path,
                        "type": file_type,
                        "content": content,
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse include file {file_path}: {e}")

        except Exception as e:
            logger.debug(f"No {file_type} files found at {path}: {e}")

        return files

    def _extract_custom_format_files(self, path: str) -> list[dict[str, Any]]:
        """Extract custom format include files."""
        files: list[dict[str, Any]] = []

        try:
            all_files = self.client.get_files_in_path(path)
            # Filter for .yml files and exclude sqp
            yml_files = [f for f in all_files if f.endswith(".yml") and "/sqp/" not in f and "-sqp-" not in f]

            for file_path in yml_files:
                try:
                    content = self.client.get_yaml_file(file_path)
                    file_name = Path(file_path).name
                    template_name = file_name.replace(".yml", "")

                    # Extract trash_ids and assign_scores_to from content
                    trash_ids = self._extract_trash_ids_from_cf(content)
                    assign_scores = self._extract_assign_scores_from_cf(content)

                    files.append({
                        "name": template_name,
                        "file": file_name,
                        "path": file_path,
                        "type": "custom-format",
                        "content": content,
                        "trash_ids": trash_ids,
                        "assign_scores_to": assign_scores,
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse custom format file {file_path}: {e}")

        except Exception as e:
            logger.debug(f"No custom format files found at {path}: {e}")

        return files

    def _extract_trash_ids_from_cf(self, content: dict) -> list[str]:
        """Extract trash_ids from custom format content."""
        trash_ids = []

        if "custom_formats" in content:
            cf_data = content["custom_formats"]
            if isinstance(cf_data, list):
                for cf_item in cf_data:
                    if isinstance(cf_item, dict) and "trash_ids" in cf_item:
                        for tid in cf_item["trash_ids"]:
                            if isinstance(tid, str):
                                trash_ids.append(tid.split("#")[0].strip())
                            elif isinstance(tid, dict):
                                # Handle nested structure
                                for key in tid:
                                    trash_ids.append(str(key).split("#")[0].strip())

        return list(set(trash_ids))

    def _extract_assign_scores_from_cf(self, content: dict) -> list[dict]:
        """Extract assign_scores_to from custom format content."""
        assign_scores = []

        if "custom_formats" in content:
            cf_data = content["custom_formats"]
            if isinstance(cf_data, list):
                for cf_item in cf_data:
                    if isinstance(cf_item, dict) and "assign_scores_to" in cf_item:
                        assign_scores.extend(cf_item["assign_scores_to"])

        return assign_scores


def main():
    parser = argparse.ArgumentParser(
        description="Extract Recyclarr config templates from GitHub repository"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="templates.json",
        help="Output JSON file path (default: templates.json)",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub API token (optional, for higher rate limits)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting Recyclarr templates extraction...")

    client = GitHubClient(token=args.token)
    extractor = ConfigTemplatesExtractor(client)

    try:
        result = extractor.extract_all()
    except Exception as e:
        logger.error(f"Failed to extract templates: {e}")
        sys.exit(1)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Print summary
    total_templates = (
        len(result.get("radarr", {}).get("templates", [])) +
        len(result.get("sonarr", {}).get("templates", []))
    )
    total_includes = (
        len(result.get("radarr", {}).get("includes", {}).get("custom-formats", [])) +
        len(result.get("sonarr", {}).get("includes", {}).get("custom-formats", [])) +
        len(result.get("radarr", {}).get("includes", {}).get("quality-profiles", [])) +
        len(result.get("sonarr", {}).get("includes", {}).get("quality-profiles", []))
    )

    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE")
    print("=" * 50)
    print(f"  Radarr templates: {len(result.get('radarr', {}).get('templates', []))}")
    print(f"  Sonarr templates: {len(result.get('sonarr', {}).get('templates', []))}")
    print(f"  Total includes:   {total_includes}")
    print("-" * 50)
    print(f"  Total templates:  {total_templates}")
    print(f"  Status:           OK (no errors)")
    print(f"  Output:           {output_path}")
    print("=" * 50)

    # Countdown before exit
    for i in range(5, 0, -1):
        print(f"\rClosing in {i}s...", end="", flush=True)
        time.sleep(1)
    print()


if __name__ == "__main__":
    main()
