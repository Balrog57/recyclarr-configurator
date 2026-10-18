import os
import json
import pytest
from pathlib import Path

# Use offscreen platform for Qt tests in headless environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from core.models import (
    QualityProfile,
    QualityProfileItem,
    CustomFormatAssignment,
    InstanceConfig,
    RecyclarrConfiguration
)
from core.data_manager import DataManager
from core.yaml_generator import YAMLGenerator


@pytest.fixture(scope="session")
def data_manager():
    dm = DataManager()
    assert dm.load_data(), "Failed to load DataManager JSON data"
    return dm


def test_data_manager_loads_quality_profiles(data_manager):
    """Verify that DataManager loads and indexes TRaSH Guides quality profiles."""
    radarr_profiles = data_manager.get_quality_profiles_for_app("radarr")
    sonarr_profiles = data_manager.get_quality_profiles_for_app("sonarr")

    assert len(radarr_profiles) > 0, "No Radarr quality profiles found"
    assert len(sonarr_profiles) > 0, "No Sonarr quality profiles found"

    # Check that HD Bluray + WEB is loaded for Radarr
    hd_bluray = data_manager.get_quality_profile_by_id("d1d67249d3890e49bc12e275d989a7e9")
    assert hd_bluray is not None, "HD Bluray + WEB profile missing by trash_id"
    assert "HD Bluray + WEB" in hd_bluray["name"]
    assert len(hd_bluray.get("items", [])) > 0
    assert len(hd_bluray.get("formatItems", {})) > 0

    # Check French MULTi.VF profile
    fr_profile = data_manager.get_quality_profile_by_id("500ecc23572575511fd81893777d1e06")
    assert fr_profile is not None
    assert "French MULTi.VF" in fr_profile["name"]


def test_data_manager_resolves_v8_template(data_manager):
    """Verify that DataManager resolves v8 templates with guide-backed profiles & CFs."""
    template = data_manager.get_template_by_name("radarr", "french-multi-vf-hd-bluray-web")
    assert template is not None, "Template french-multi-vf-hd-bluray-web not found"

    from core.resolver import resolve
    instance = list(template["content"]["radarr"].values())[0]
    (name, profile), = resolve(instance, "radarr", data_manager).items()
    assert name == "[French MULTi.VF] HD Bluray + WEB"
    assert profile["score_set"] == "french-multi-vf"
    names = {(data_manager.get_cf_by_id(t) or {}).get("name"): s for t, s in profile["cfs"].items()}
    # Guide scores of the French language CFs, straight from TRaSH data
    assert names["Language: Original + French"] > 0 and names["Language: Not French"] < 0


def test_yaml_generator_v8_syntax(tmp_path):
    """Test generating a Recyclarr v8 compliant YAML configuration."""
    generator = YAMLGenerator()

    # Create a guide-backed profile
    qp_guide = QualityProfile(
        name="[French MULTi.VF] HD Bluray + WEB",
        trash_id="500ecc23572575511fd81893777d1e06",
        reset_unmatched_scores=True,
        upgrade_allowed=True,
        upgrade_until="Bluray|WEB 1080p",
        until_score=10000,
        active=True
    )

    # Create a custom profile
    qp_custom = QualityProfile(
        name="Custom 1080p",
        trash_id="", # Custom manual
        reset_unmatched_scores=True,
        upgrade_allowed=False,
        items=[
            QualityProfileItem(name="Bluray-1080p"),
            QualityProfileItem(name="WEB 1080p", qualities=["WEBRip-1080p", "WEBDL-1080p"])
        ],
        source="custom",
        active=True
    )

    # Custom format assignment
    cf1 = CustomFormatAssignment(
        trash_id="404c08fd0bd67f39b4d8e5709319094e",
        name="VFF",
        description="French VFF",
        score=1000,
        default_score=0,
        profiles=[],
        profile_scores=[{"name": "[French MULTi.VF] HD Bluray + WEB", "score": 1000}]
    )

    instance_radarr = InstanceConfig(
        name="radarr_main",
        base_url="http://192.168.1.50:7878",
        api_key="test_api_key_radarr",
        quality_definition_type="movie",
        custom_profiles=[qp_guide, qp_custom],
        active_cfs=[cf1]
    )

    instance_sonarr = InstanceConfig(
        name="sonarr_main",
        base_url="http://192.168.1.50:8989",
        api_key="test_api_key_sonarr",
        quality_definition_type="series",
        custom_profiles=[
            QualityProfile(
                name="Remux + WEB 1080p",
                trash_id="fe9470e577c300a5ad9a3274f6d1cdf2",
                reset_unmatched_scores=True,
                active=True
            )
        ]
    )

    config = RecyclarrConfiguration(
        radarr_instances=[instance_radarr],
        sonarr_instances=[instance_sonarr]
    )

    output_file = tmp_path / "recyclarr_test.yml"
    out_path = generator.generate_config(config, filename=str(output_file))
    assert Path(out_path).exists()

    # Read back and verify structure
    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure v8 requirements
    assert "quality_definition:" in content
    assert "type: movie" in content
    assert "type: series" in content

    # Ensure guide-backed quality profile has trash_id
    assert "trash_id: 500ecc23572575511fd81893777d1e06" in content
    assert "trash_id: fe9470e577c300a5ad9a3274f6d1cdf2" in content

    # Ensure custom profile has qualities structure
    assert "Custom 1080p" in content
    assert "WEBDL-1080p" in content

    # Ensure CFs have assign_scores_to (v8 requirement)
    assert "assign_scores_to:" in content
    assert "score: 1000" in content

    # Ensure no obsolete include templates like 'radarr-quality-definition-movie'
    assert "radarr-quality-definition" not in content
    assert "radarr-quality-profile" not in content

    # Verify YAML is valid by reloading it
    loaded_data = generator.load_yaml(out_path)
    assert "radarr" in loaded_data
    assert "sonarr" in loaded_data
    assert loaded_data["radarr"]["radarr_main"]["quality_definition"]["type"] == "movie"
    assert loaded_data["sonarr"]["sonarr_main"]["quality_definition"]["type"] == "series"

    # Removed in v8: Recyclarr rejects the config if present
    assert "replace_existing_custom_formats" not in content
    # v8 schema requires every quality entry to be an object with a name
    custom_qp = [q for q in loaded_data["radarr"]["radarr_main"]["quality_profiles"] if q["name"] == "Custom 1080p"][0]
    assert all(isinstance(q, dict) and "name" in q for q in custom_qp["qualities"])
    # Guide-backed profiles take their qualities from the guide
    guide_qp = [q for q in loaded_data["radarr"]["radarr_main"]["quality_profiles"] if q.get("trash_id")][0]
    assert "qualities" not in guide_qp


def test_ui_widgets_instantiation(data_manager):
    """Verify that PySide6 UI widgets can be instantiated and interact cleanly."""
    from PySide6.QtWidgets import QApplication
    from ui.widgets.include_tree import IncludeTreeWidget
    from ui.widgets.profile_builder import QualityProfileManager
    from ui.widgets.cf_editor import CFEditor

    app = QApplication.instance() or QApplication([])

    # 1. IncludeTreeWidget
    tree_widget = IncludeTreeWidget(data_manager)
    tree_widget.load_for_app("radarr")
    assert tree_widget.root_profiles.childCount() > 0
    assert tree_widget.root_cfs.childCount() > 0

    # 2. QualityProfileManager
    qp_manager = QualityProfileManager()
    qp_data = data_manager.get_quality_profiles_for_app("radarr")[:2]
    qp_manager.sync_profiles(qp_data)
    profiles = qp_manager.get_profiles()
    assert len(profiles) == 2
    assert profiles[0].trash_id != ""

    # 3. CFEditor
    cfs_data = data_manager.get_custom_formats_for_app("radarr")
    cf_editor = CFEditor(cfs_data, available_profiles=["HD Bluray + WEB"])
    assert cf_editor.list_widget.count() > 0


def test_instance_editor_selection_and_generation(data_manager, tmp_path):
    """Verify that InstanceEditor selects a v8 template, syncs across all acts, and exports valid config."""
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor

    app = QApplication.instance() or QApplication([])

    editor = InstanceEditor(data_manager, app_type="radarr")
    editor.config.name = "radarr_test"
    editor.config.base_url = "http://localhost:7878"
    editor.config.api_key = "abc123key"

    # Select a French template (e.g. index 1 or find french-multi-vf-hd-bluray-web)
    combo_idx = -1
    for i in range(editor.combo_mode.count()):
        if "french-multi-vf-hd-bluray-web" in editor.combo_mode.itemText(i):
            combo_idx = i
            break
    assert combo_idx >= 0, "french-multi-vf-hd-bluray-web template not in combo_mode"

    editor.combo_mode.setCurrentIndex(combo_idx)

    # 1. Check Act 1 Quality definition
    assert editor.combo_qdef.currentText() == "movie"

    # 2. Check Act 3 Profile loaded and active
    profiles = editor.act2_widget.get_profiles()
    assert len(profiles) > 0, "Quality profile was not loaded into Act 3"
    active_profile = profiles[0]
    assert active_profile.active, "Loaded template profile should be active"
    assert active_profile.trash_id == "500ecc23572575511fd81893777d1e06"

    # 3. Check Act 4 CFs loaded
    assert len(editor.act3_widget.template_assignments) > 0

    # Visiting Act 3/4 re-syncs profiles: the template profile must stay active
    for tab in (1, 2, 3, 0):
        editor.tabs.setCurrentIndex(tab)
    assert [p.active for p in editor.act2_widget.get_profiles()] == [True]

    # 4. Generate Config
    config = editor.get_config()
    assert config.quality_definition_type == "movie"
    assert len(config.custom_profiles) > 0

    generator = YAMLGenerator()
    full_config = RecyclarrConfiguration(radarr_instances=[config])
    out_file = tmp_path / "instance_test.yml"
    out_path = generator.generate_config(full_config, filename=str(out_file))

    # Read and verify YAML output
    with open(out_path, "r", encoding="utf-8") as f:
        yaml_text = f.read()

    assert "radarr_test:" in yaml_text
    assert "type: movie" in yaml_text
    assert "trash_id: 500ecc23572575511fd81893777d1e06" in yaml_text

    # Reload into a fresh InstanceEditor
    loaded_data = generator.load_yaml(out_path)

    # Same effective profile as the official template (its groups are auto-synced defaults)
    from core.resolver import resolve
    template = data_manager.get_template_by_name("radarr", "french-multi-vf-hd-bluray-web")
    (_, ref), = resolve(list(template["content"]["radarr"].values())[0], "radarr", data_manager).items()
    (_, got), = resolve(loaded_data["radarr"]["radarr_test"], "radarr", data_manager).items()
    assert got["cfs"] == ref["cfs"] and got["leaves"] == ref["leaves"]
    editor2 = InstanceEditor(data_manager, app_type="radarr")
    editor2.load_config(loaded_data["radarr"]["radarr_test"])

    assert editor2.combo_qdef.currentText() == "movie"
    profiles_reloaded = editor2.act2_widget.get_profiles()
    assert len(profiles_reloaded) > 0
    assert profiles_reloaded[0].trash_id == "500ecc23572575511fd81893777d1e06"


def test_sonarr_instance_editor_selection_and_generation(data_manager, tmp_path):
    """Verify that InstanceEditor for Sonarr selects a template and produces valid v8 config."""
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor

    app = QApplication.instance() or QApplication([])

    editor = InstanceEditor(data_manager, app_type="sonarr")
    editor.config.name = "sonarr_anime"
    editor.config.base_url = "http://localhost:8989"
    editor.config.api_key = "sonarr_secret_key"

    # Select Sonarr template (e.g. web-1080p or anime-remux-1080p)
    combo_idx = -1
    for i in range(editor.combo_mode.count()):
        if "web-1080p" in editor.combo_mode.itemText(i):
            combo_idx = i
            break
    assert combo_idx >= 0, "web-1080p template not in combo_mode"

    editor.combo_mode.setCurrentIndex(combo_idx)

    # 1. Check Act 1 Quality definition (series for sonarr)
    assert editor.combo_qdef.currentText() == "series"

    # 2. Check Act 3 Profiles
    profiles = editor.act2_widget.get_profiles()
    assert len(profiles) > 0
    assert profiles[0].trash_id != ""

    # 3. Generate Config
    config = editor.get_config()
    generator = YAMLGenerator()
    full_config = RecyclarrConfiguration(sonarr_instances=[config])
    out_file = tmp_path / "sonarr_test.yml"
    out_path = generator.generate_config(full_config, filename=str(out_file))

    with open(out_path, "r", encoding="utf-8") as f:
        yaml_text = f.read()

    assert "sonarr_anime:" in yaml_text
    assert "type: series" in yaml_text
    assert "trash_id:" in yaml_text


