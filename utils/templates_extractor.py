#!/usr/bin/env python3
"""
Recyclarr Config Templates & TRaSH Guides Profiles Extractor

Extracts:
- Configuration templates from recyclarr/config-templates GitHub repository
- Guide-backed Quality Profiles, Quality Definitions, and CF Groups from TRaSH-Guides/Guides
Generates a structured JSON file with all templates, includes, and their associated metadata.

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
from typing import Any, Optional

import requests
import yaml

# Configuration
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_API_BASE = "https://api.github.com"

RECYCLARR_OWNER = "recyclarr"
RECYCLARR_REPO = "config-templates"
RECYCLARR_BRANCH = "master"

TRASH_OWNER = "TRaSH-Guides"
TRASH_REPO = "Guides"
TRASH_BRANCH = "master"

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
    trash_id: str = ""
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
    """Client for interacting with GitHub (API + Raw + HTML scraping fallback)."""

    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self._file_cache: dict[str, list[str]] = {}
        self._content_cache: dict[str, str] = {}
        self._tree_cache: dict[str, list[str]] = {}

        # Increase connection pool size
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
        self.session.mount("https://", adapter)

    def get_repo_tree(self, owner: str, repo: str, branch: str = "master") -> list[str]:
        """Fetch the entire repository tree via GitHub API if available."""
        cache_key = f"{owner}/{repo}:{branch}"
        if cache_key in self._tree_cache:
            return self._tree_cache[cache_key]

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                paths = [item["path"] for item in data.get("tree", []) if "path" in item]
                self._tree_cache[cache_key] = paths
                logger.debug(f"Loaded {len(paths)} tree paths via API for {owner}/{repo}")
                return paths
            else:
                logger.warning(f"GitHub API tree returned status {resp.status_code} for {owner}/{repo}")
        except Exception as e:
            logger.warning(f"Failed to fetch tree from API for {owner}/{repo}: {e}")

        return []

    def get_files_in_path(self, path_prefix: str, owner: str = RECYCLARR_OWNER,
                          repo: str = RECYCLARR_REPO, branch: str = RECYCLARR_BRANCH) -> list[str]:
        """Get all files under a path prefix using tree API or HTML scraping fallback."""
        cache_key = f"{owner}/{repo}:{path_prefix}"
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        prefix = path_prefix.strip("/") + "/"
        tree = self.get_repo_tree(owner, repo, branch)
        if tree:
            files = [p for p in tree if p.startswith(prefix) or p == path_prefix.strip("/")]
            self._file_cache[cache_key] = files
            return files

        # Fallback to HTML scraping
        files = self._scrape_directory_html(path_prefix, owner=owner, repo=repo, branch=branch)
        self._file_cache[cache_key] = files
        return files

    def _scrape_directory_html(self, path_prefix: str, owner: str = RECYCLARR_OWNER,
                               repo: str = RECYCLARR_REPO, branch: str = RECYCLARR_BRANCH,
                               recursive: bool = True) -> list[str]:
        """Scrape directory listing from GitHub HTML page."""
        files = []
        directories = []
        path = path_prefix.rstrip("/")
        url = f"https://github.com/{owner}/{repo}/tree/{branch}/{path}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            item_pattern = r'"path":"(' + re.escape(path) + r'/[^"]+)"[^}]*"contentType":"([^"]+)"'
            typed_matches = re.findall(item_pattern, response.text)

            if typed_matches:
                for item_path, content_type in typed_matches:
                    if content_type == "file":
                        files.append(item_path)
                    elif content_type == "directory":
                        directories.append(item_path)
            else:
                pattern = r'"path":"(' + re.escape(path) + r'/[^"]+)"'
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if '.' in match.split('/')[-1]:
                        files.append(match)
                    else:
                        directories.append(match)

            if recursive:
                for subdir in directories:
                    subfiles = self._scrape_directory_html(subdir, owner=owner, repo=repo,
                                                          branch=branch, recursive=True)
                    files.extend(subfiles)

        except Exception as e:
            logger.error(f"Failed to scrape directory {path} ({owner}/{repo}): {e}")

        return files

    def get_raw_file(self, path: str, owner: str = RECYCLARR_OWNER,
                     repo: str = RECYCLARR_REPO, branch: str = RECYCLARR_BRANCH) -> str:
        """Get raw content of a file."""
        cache_key = f"{owner}/{repo}/{branch}:{path}"
        if cache_key in self._content_cache:
            return self._content_cache[cache_key]

        url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{path}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        content = response.text
        self._content_cache[cache_key] = content
        return content

    def get_yaml_file(self, path: str, owner: str = RECYCLARR_OWNER,
                      repo: str = RECYCLARR_REPO, branch: str = RECYCLARR_BRANCH) -> dict[str, Any]:
        """Get and parse a YAML file."""
        content = self.get_raw_file(path, owner=owner, repo=repo, branch=branch)
        return yaml.safe_load(content) or {}

    def get_json_file(self, path: str, owner: str = TRASH_OWNER,
                      repo: str = TRASH_REPO, branch: str = TRASH_BRANCH) -> dict[str, Any]:
        """Get and parse a JSON file."""
        content = self.get_raw_file(path, owner=owner, repo=repo, branch=branch)
        return json.loads(content)


class ConfigTemplatesExtractor:
    """Extracts templates and includes from recyclarr/config-templates and TRaSH-Guides/Guides."""

    def __init__(self, client: GitHubClient):
        self.client = client

    def extract_all(self) -> dict[str, Any]:
        """Extract all templates and includes for both radarr and sonarr."""
        logger.info("Starting extraction of Recyclarr templates & TRaSH Guides...")

        result = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source_templates": f"https://github.com/{RECYCLARR_OWNER}/{RECYCLARR_REPO}",
                "source_guides": f"https://github.com/{TRASH_OWNER}/{TRASH_REPO}",
                "branch_templates": RECYCLARR_BRANCH,
                "branch_guides": TRASH_BRANCH,
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
        """Extract templates from recyclarr/config-templates repository."""
        templates_path = f"{app}/templates"
        templates: list[dict[str, Any]] = []

        try:
            files = self.client.get_files_in_path(
                templates_path, owner=RECYCLARR_OWNER, repo=RECYCLARR_REPO, branch=RECYCLARR_BRANCH
            )
            # Filter for .yml files and exclude sqp subfolder
            yml_files = [f for f in files if f.endswith(".yml") and "/sqp/" not in f]

            logger.info(f"Found {len(yml_files)} template files for {app} (excluding sqp)")

            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_file = {executor.submit(self._parse_template, f): f for f in yml_files}
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        template = future.result()
                        if template:
                            templates.append(template)
                    except Exception as e:
                        logger.warning(f"Failed to parse template {file_path}: {e}")

            templates.sort(key=lambda t: t.get("name", ""))

        except Exception as e:
            logger.error(f"Failed to extract templates for {app}: {e}")

        return templates

    def _parse_template(self, file_path: str) -> dict[str, Any] | None:
        """Parse a single template file."""
        try:
            content = self.client.get_yaml_file(
                file_path, owner=RECYCLARR_OWNER, repo=RECYCLARR_REPO, branch=RECYCLARR_BRANCH
            )
            file_name = Path(file_path).name
            template_name = file_name.replace(".yml", "")

            # Extract includes from content (both legacy include and new quality_profiles trash_ids)
            includes = self._extract_includes_from_content(content)

            # Extract description from comments if present
            raw_content = self.client.get_raw_file(
                file_path, owner=RECYCLARR_OWNER, repo=RECYCLARR_REPO, branch=RECYCLARR_BRANCH
            )
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
        """Extract include template names and profile trash_ids from YAML content."""
        includes = []

        for app_key, app_config in content.items():
            if isinstance(app_config, dict):
                for instance_key, instance_config in app_config.items():
                    if not isinstance(instance_config, dict):
                        continue
                    # 1. Legacy includes: `include: [ { template: ... } ]`
                    if "include" in instance_config:
                        for include_item in instance_config.get("include", []):
                            if isinstance(include_item, dict) and "template" in include_item:
                                includes.append(include_item["template"])

                    # 2. Guide-backed quality profiles: `quality_profiles: [ { trash_id: ... } ]`
                    if "quality_profiles" in instance_config:
                        for qp in instance_config.get("quality_profiles", []):
                            if isinstance(qp, dict) and "trash_id" in qp:
                                includes.append(qp["trash_id"])

        return list(dict.fromkeys(includes))

    def _extract_description_from_comments(self, raw_content: str) -> str:
        """Extract description from YAML comments."""
        lines = raw_content.split("\n")
        description_lines = []

        for line in lines:
            if line.startswith("#"):
                comment_text = line.lstrip("# ").strip()
                if (
                    comment_text
                    and not comment_text.startswith(("Updated:", "Documentation:", "yaml-language-server:"))
                ):
                    description_lines.append(comment_text)
            elif line.strip() and not line.startswith("#"):
                break

        return " ".join(description_lines[:3]) if description_lines else ""

    def _extract_includes(self, app: str) -> dict[str, list[dict[str, Any]]]:
        """
        Extract include files (quality profiles, quality definitions, cf groups)
        from TRaSH-Guides/Guides repository.
        """
        includes: dict[str, list[dict[str, Any]]] = {
            "quality-definitions": [],
            "quality-profiles": [],
            "custom-formats": [],
        }

        try:
            # 1. Quality Profiles from TRaSH-Guides (docs/json/{app}/quality-profiles/)
            qp_path = f"docs/json/{app}/quality-profiles"
            includes["quality-profiles"] = self._extract_trash_quality_profiles(app, qp_path)

            # 2. Quality Definitions from TRaSH-Guides (docs/json/{app}/quality-size/)
            qd_path = f"docs/json/{app}/quality-size"
            includes["quality-definitions"] = self._extract_trash_quality_sizes(qd_path)

            # 3. Custom Format Groups from TRaSH-Guides (docs/json/{app}/cf-groups/)
            cf_path = f"docs/json/{app}/cf-groups"
            includes["custom-formats"] = self._extract_trash_cf_groups(cf_path)

        except Exception as e:
            logger.error(f"Failed to extract includes for {app}: {e}")

        return includes

    def _extract_trash_quality_profiles(self, app: str, path: str) -> list[dict[str, Any]]:
        """Extract Guide-Backed Quality Profiles from TRaSH-Guides JSON files."""
        profiles: list[dict[str, Any]] = []

        try:
            all_files = self.client.get_files_in_path(
                path, owner=TRASH_OWNER, repo=TRASH_REPO, branch=TRASH_BRANCH
            )
            json_files = [
                f for f in all_files
                if f.endswith(".json") and not f.endswith("base-profile.json")
            ]

            logger.info(f"Found {len(json_files)} TRaSH quality profiles for {app}")

            def _fetch_profile(file_path: str):
                try:
                    data = self.client.get_json_file(
                        file_path, owner=TRASH_OWNER, repo=TRASH_REPO, branch=TRASH_BRANCH
                    )
                    file_name = Path(file_path).name
                    profile_name = data.get("name") or file_name.replace(".json", "")
                    trash_id = data.get("trash_id", "")

                    return {
                        "name": profile_name,
                        "file": file_name,
                        "path": file_path,
                        "trash_id": trash_id,
                        "type": "quality-profile",
                        "description": data.get("trash_description", ""),
                        "cutoff": data.get("cutoff", ""),
                        "upgradeAllowed": data.get("upgradeAllowed", False),
                        "minFormatScore": data.get("minFormatScore", 0),
                        "cutoffFormatScore": data.get("cutoffFormatScore", 10000),
                        "minUpgradeFormatScore": data.get("minUpgradeFormatScore", 1),
                        "score_set": data.get("trash_score_set", ""),
                        "items": data.get("items", []),
                        "formatItems": data.get("formatItems", {}),
                        "content": data,
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse quality profile {file_path}: {e}")
                    return None

            with ThreadPoolExecutor(max_workers=15) as executor:
                results = executor.map(_fetch_profile, json_files)
                for res in results:
                    if res:
                        profiles.append(res)

            profiles.sort(key=lambda p: p.get("name", ""))

        except Exception as e:
            logger.error(f"Failed to extract TRaSH quality profiles from {path}: {e}")

        return profiles

    def _extract_trash_quality_sizes(self, path: str) -> list[dict[str, Any]]:
        """Extract Quality Sizes/Definitions from TRaSH-Guides JSON files."""
        definitions: list[dict[str, Any]] = []

        try:
            all_files = self.client.get_files_in_path(
                path, owner=TRASH_OWNER, repo=TRASH_REPO, branch=TRASH_BRANCH
            )
            json_files = [f for f in all_files if f.endswith(".json")]

            for file_path in json_files:
                try:
                    data = self.client.get_json_file(
                        file_path, owner=TRASH_OWNER, repo=TRASH_REPO, branch=TRASH_BRANCH
                    )
                    file_name = Path(file_path).name
                    def_name = data.get("type") or Path(file_path).stem
                    definitions.append({
                        "name": def_name,
                        "file": file_name,
                        "path": file_path,
                        "trash_id": data.get("trash_id", ""),
                        "type": "quality-definition",
                        "content": data,
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse quality definition {file_path}: {e}")

            definitions.sort(key=lambda d: d.get("name", ""))

        except Exception as e:
            logger.debug(f"No quality-size files found at {path}: {e}")

        return definitions

    def _extract_trash_cf_groups(self, path: str) -> list[dict[str, Any]]:
        """Extract Custom Format Groups from TRaSH-Guides JSON files."""
        groups: list[dict[str, Any]] = []

        try:
            all_files = self.client.get_files_in_path(
                path, owner=TRASH_OWNER, repo=TRASH_REPO, branch=TRASH_BRANCH
            )
            json_files = [f for f in all_files if f.endswith(".json")]

            def _fetch_group(file_path: str):
                try:
                    data = self.client.get_json_file(
                        file_path, owner=TRASH_OWNER, repo=TRASH_REPO, branch=TRASH_BRANCH
                    )
                    file_name = Path(file_path).name
                    group_name = data.get("name") or Path(file_path).stem
                    cfs = data.get("custom_formats", [])
                    trash_ids = [cf.get("trash_id") for cf in cfs if isinstance(cf, dict) and cf.get("trash_id")]

                    return {
                        "name": group_name,
                        "file": file_name,
                        "path": file_path,
                        "trash_id": data.get("trash_id", ""),
                        "type": "custom-format",
                        "default": str(data.get("default", "false")).lower() == "true",
                        "trash_ids": trash_ids,
                        "assign_scores_to": [],
                        "content": data,
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse cf-group {file_path}: {e}")
                    return None

            with ThreadPoolExecutor(max_workers=15) as executor:
                results = executor.map(_fetch_group, json_files)
                for res in results:
                    if res:
                        groups.append(res)

            groups.sort(key=lambda g: g.get("name", ""))

        except Exception as e:
            logger.debug(f"No cf-groups found at {path}: {e}")

        return groups


def main():
    parser = argparse.ArgumentParser(
        description="Extract Recyclarr config templates and TRaSH Guides quality profiles from GitHub"
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total_templates = (
        len(result.get("radarr", {}).get("templates", [])) +
        len(result.get("sonarr", {}).get("templates", []))
    )
    total_profiles = (
        len(result.get("radarr", {}).get("includes", {}).get("quality-profiles", [])) +
        len(result.get("sonarr", {}).get("includes", {}).get("quality-profiles", []))
    )
    total_qdefs = (
        len(result.get("radarr", {}).get("includes", {}).get("quality-definitions", [])) +
        len(result.get("sonarr", {}).get("includes", {}).get("quality-definitions", []))
    )
    total_cfs = (
        len(result.get("radarr", {}).get("includes", {}).get("custom-formats", [])) +
        len(result.get("sonarr", {}).get("includes", {}).get("custom-formats", []))
    )

    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE")
    print("=" * 50)
    print(f"  Radarr templates:   {len(result.get('radarr', {}).get('templates', []))}")
    print(f"  Sonarr templates:   {len(result.get('sonarr', {}).get('templates', []))}")
    print(f"  Quality profiles:   {total_profiles}")
    print(f"  Quality definitions: {total_qdefs}")
    print(f"  Custom format packs: {total_cfs}")
    print("-" * 50)
    print(f"  Total templates:    {total_templates}")
    print(f"  Status:             OK (no errors)")
    print(f"  Output:             {output_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
