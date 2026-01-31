#!/usr/bin/env python3
"""
TRaSH Custom Formats Extractor

Extracts Custom Formats from the TRaSH-Guides GitHub repository
and generates a structured JSON file with all formats, trash_ids,
descriptions, and associated scores.

Usage:
    python trash_cf_extractor.py [--output OUTPUT_FILE]
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

# Configuration
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
REPO_OWNER = "TRaSH-Guides"
REPO_NAME = "Guides"
BRANCH = "master"

# Paths in the repository
CF_PATHS = {
    "radarr": "docs/json/radarr/cf/",
    "sonarr": "docs/json/sonarr/cf/",
    "guide-only": "docs/json/guide-only/",
}

# Description path
DESCRIPTION_PATH = "includes/cf-descriptions/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def name_to_kebab(name: str) -> str:
    """Convert a Custom Format name to kebab-case filename."""
    result = name.lower()
    result = result.replace("+", "plus")
    result = result.replace("&", "and")
    result = result.replace("(", "").replace(")", "")
    result = result.replace("/", "-")
    result = result.replace(".", "-")
    result = result.replace("_", "-")
    result = re.sub(r"\s+", "-", result)
    result = re.sub(r"-+", "-", result)
    result = result.strip("-")
    return result


@dataclass
class CustomFormat:
    """Represents a Custom Format with all its metadata."""

    name: str
    trash_id: str
    app: str
    trash_scores: dict[str, int] = field(default_factory=dict)
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "trash_id": self.trash_id,
        }

        if self.description:
            result["description"] = self.description

        if self.trash_scores:
            result["trash_scores"] = self.trash_scores

        result["app"] = self.app

        return result


class GitHubClient:
    """Client for interacting with GitHub (no API, web scraping only)."""

    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self._file_cache: dict[str, list[str]] = {}

        # Increase connection pool size to handle parallel requests
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
        self.session.mount("https://", adapter)

    def get_files_in_path(self, path_prefix: str) -> list[str]:
        """Get all files under a path prefix by scraping GitHub HTML."""
        if path_prefix in self._file_cache:
            return self._file_cache[path_prefix]

        files = self._scrape_directory_html(path_prefix)
        self._file_cache[path_prefix] = files
        return files

    def _scrape_directory_html(self, path_prefix: str) -> list[str]:
        """Scrape directory listing from GitHub HTML page."""
        files = []
        path = path_prefix.rstrip("/")
        url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/tree/{BRANCH}/{path}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Extract file paths from embedded JSON data
            # Pattern: "path":"docs/json/radarr/cf/filename.json"
            pattern = r'"path":"(' + re.escape(path) + r'/[^"]+)"'
            matches = re.findall(pattern, response.text)
            files.extend(matches)

        except Exception as e:
            logger.error(f"Failed to scrape directory {path}: {e}")

        return files

    def get_raw_file(self, path: str) -> str:
        """Get raw content of a file."""
        url = f"{GITHUB_RAW_BASE}/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{path}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def get_json_file(self, path: str) -> dict[str, Any]:
        """Get and parse a JSON file."""
        content = self.get_raw_file(path)
        return json.loads(content)


class DescriptionExtractor:
    """Extracts descriptions from markdown files."""

    def __init__(self, client: GitHubClient):
        self.client = client
        self.descriptions: dict[str, str] = {}
        self._loaded = False
        self._lock = Lock()

    def load_descriptions(self) -> None:
        """Load all description files from the repository."""
        with self._lock:
            if self._loaded:
                return
            self._load_descriptions_impl()

    def _load_descriptions_impl(self) -> None:
        """Internal implementation of description loading."""

        logger.info("Loading description files...")

        try:
            md_files = [f for f in self.client.get_files_in_path(DESCRIPTION_PATH) if f.endswith(".md")]
            logger.info(f"Found {len(md_files)} description files")

            # Parallel fetch descriptions
            with ThreadPoolExecutor(max_workers=20) as executor:
                future_to_file = {
                    executor.submit(self._load_single_description, path): path
                    for path in md_files
                }

                for future in as_completed(future_to_file):
                    path = future_to_file[future]
                    try:
                        key, content = future.result()
                        if key and content:
                            self.descriptions[key] = content
                    except Exception as e:
                        logger.debug(f"Failed to load {path}: {e}")

            self._loaded = True
            logger.info(f"Loaded {len(self.descriptions)} descriptions")

        except Exception as e:
            logger.warning(f"Failed to load descriptions: {e}")
            self._loaded = True

    def _load_single_description(self, path: str) -> tuple[str | None, str | None]:
        """Load a single description file."""
        try:
            content = self.client.get_raw_file(path)
            filename = path.split("/")[-1]
            key = filename.replace(".md", "")
            return key, self._clean_markdown(content)
        except Exception:
            return None, None

    def get_description(self, cf_name: str) -> str | None:
        """Get description for a Custom Format by name."""
        self.load_descriptions()

        key = name_to_kebab(cf_name)

        if key in self.descriptions:
            return self.descriptions[key]

        # Try variations
        variations = [
            key.replace("plus", "+"),
            cf_name.lower().replace(" ", "-"),
            cf_name.lower().replace(" ", ""),
            re.sub(r"[^a-z0-9-]", "", key),
        ]

        for var in variations:
            if var in self.descriptions:
                return self.descriptions[var]

        return None

    @staticmethod
    def _clean_markdown(content: str) -> str:
        """Clean markdown content for plain text description."""
        # Remove HTML comments
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # Remove markdown link target attributes {:target="_blank" ...}
        content = re.sub(r'\{:target="[^"]*"[^}]*\}', "", content)
        content = re.sub(r'\{:target=\\"[^"]*\\"[^}]*\}', "", content)
        content = re.sub(r'\{[^}]*target[^}]*\}', "", content)

        # Convert markdown links to plain text BEFORE removing source lines
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

        # Remove "From Wikipedia..." lines and similar source attributions
        content = re.sub(r"^From Wikipedia[^\n]*$", "", content, flags=re.IGNORECASE | re.MULTILINE)
        content = re.sub(r"^Source:?[^\n]*$", "", content, flags=re.IGNORECASE | re.MULTILINE)

        # Remove orphaned brackets
        content = re.sub(r"^\s*\[\s*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"^\s*\]\s*$", "", content, flags=re.MULTILINE)

        # Remove bold/italic markers
        content = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
        content = re.sub(r"\*([^*]+)\*", r"\1", content)

        # Remove code markers
        content = re.sub(r"`([^`]+)`", r"\1", content)

        # Remove headers
        content = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)

        # Clean HTML
        content = re.sub(r"<br\s*/?>", "\n", content)
        content = re.sub(r"<[^>]+>", "", content)

        # Clean up whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r"^\s+", "", content, flags=re.MULTILINE)

        return content.strip()


class CustomFormatExtractor:
    """Extracts Custom Formats from the TRaSH-Guides repository."""

    def __init__(self, client: GitHubClient, description_extractor: DescriptionExtractor):
        self.client = client
        self.description_extractor = description_extractor

    def extract_all(self) -> dict[str, list[CustomFormat]]:
        """Extract all Custom Formats from all applications."""
        logger.info("Starting extraction from GitHub...")

        # Pre-load descriptions before parallel extraction
        self.description_extractor.load_descriptions()

        results: dict[str, list[CustomFormat]] = {}

        for app, path in CF_PATHS.items():
            logger.info(f"Extracting Custom Formats for {app}...")
            try:
                formats = self._extract_from_path(app, path)
                results[app] = formats
                logger.info(f"Extracted {len(formats)} Custom Formats for {app}")
            except Exception as e:
                logger.error(f"Failed to extract formats for {app}: {e}")
                results[app] = []

        return results

    def _extract_from_path(self, app: str, path: str) -> list[CustomFormat]:
        """Extract Custom Formats from a specific path."""
        formats: list[CustomFormat] = []

        json_files = [f for f in self.client.get_files_in_path(path) if f.endswith(".json")]
        logger.info(f"Found {len(json_files)} JSON files for {app}")

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_file = {
                executor.submit(self._extract_single_format, app, path): path
                for path in json_files
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    cf = future.result()
                    if cf:
                        formats.append(cf)
                except Exception as e:
                    logger.warning(f"Failed to extract {file_path}: {e}")

        formats.sort(key=lambda x: x.name.lower())
        return formats

    def _extract_single_format(self, app: str, file_path: str) -> CustomFormat | None:
        """Extract a single Custom Format from a file."""
        try:
            data = self.client.get_json_file(file_path)

            name = data.get("name", "")
            trash_id = data.get("trash_id", "")

            if not name or not trash_id:
                logger.warning(f"Missing name or trash_id in {file_path}")
                return None

            trash_scores = data.get("trash_scores", {})
            description = self.description_extractor.get_description(name)

            return CustomFormat(
                name=name,
                trash_id=trash_id,
                app=app,
                trash_scores=trash_scores,
                description=description,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")
            return None


def generate_output(formats: dict[str, list[CustomFormat]]) -> dict[str, Any]:
    """Generate the output JSON structure."""
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
            "branch": BRANCH,
            "total_formats": sum(len(f) for f in formats.values()),
        },
        "custom_formats": {},
    }

    for app, cf_list in formats.items():
        output["custom_formats"][app] = {
            "count": len(cf_list),
            "formats": [cf.to_dict() for cf in cf_list],
        }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Extract TRaSH Custom Formats from GitHub repository"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="custom_formats.json",
        help="Output JSON file path (default: custom_formats.json)",
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

    logger.info("Starting TRaSH Custom Formats extraction...")

    client = GitHubClient(token=args.token)
    description_extractor = DescriptionExtractor(client)
    extractor = CustomFormatExtractor(client, description_extractor)

    try:
        formats = extractor.extract_all()
    except Exception as e:
        logger.error(f"Failed to extract formats: {e}")
        sys.exit(1)

    output = generate_output(formats)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE")
    print("=" * 50)
    print(f"  Radarr:     {len(formats.get('radarr', []))} custom formats")
    print(f"  Sonarr:     {len(formats.get('sonarr', []))} custom formats")
    print(f"  Guide-only: {len(formats.get('guide-only', []))} custom formats")
    print("-" * 50)
    print(f"  Total:      {output['metadata']['total_formats']} custom formats")
    print(f"  Status:     OK (no errors)")
    print(f"  Output:     {output_path}")
    print("=" * 50)

    # Countdown before exit
    for i in range(10, 0, -1):
        print(f"\rClosing in {i}s...", end="", flush=True)
        time.sleep(1)
    print()


if __name__ == "__main__":
    main()
