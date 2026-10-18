import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from core.data_manager import DataManager
from core.models import RecyclarrConfiguration
from core.yaml_generator import YAMLGenerator
from core import quick_profile as qp

import sys
sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture(scope="module")
def dm():
    manager = DataManager()
    assert manager.load_data()
    return manager


def bucket_scores(ranking):
    """Net language score per release type, from how Radarr/Sonarr match the language CFs."""
    s = qp.language_cf_scores(ranking)
    return {
        "multi": s["orig_french"],               # Original + French audio
        "vf": s["not_original"],                 # French audio only
        "vostfr": s["not_french"] + s["vostfr"],  # original audio, VOSTFR in title
        "vo": s["not_french"],                   # original audio only
    }


def test_language_order_films():
    net = bucket_scores(["multi", "vf", "vostfr"])
    assert net["multi"] > net["vf"] > net["vostfr"] >= 0
    assert net["vo"] <= qp.REJECT


def test_language_order_anime_no_vf():
    net = bucket_scores(["multi", "vostfr"])
    assert net["multi"] > net["vostfr"] >= 0
    assert net["vf"] <= qp.REJECT and net["vo"] <= qp.REJECT


def test_no_language_rejected():
    with pytest.raises(ValueError):
        qp.language_cf_scores([])


def test_hardcoded_trash_ids_exist(dm):
    for app in ("radarr", "sonarr"):
        profile_ids = [i for tier in qp.FRENCH_PROFILES[app].values() for i in tier.values()] + [qp.ANIME_PROFILE[app]]
        for tid in profile_ids:
            assert dm.get_quality_profile_by_id(tid), f"{app} profile {tid} missing"
        cf_ids = list(qp.LANGUAGE_CFS[app].values()) + qp.ANIME_EXTRA_CFS[app] + sum(qp.CODEC_CFS[app].values(), [])
        for tid in cf_ids:
            assert dm.get_cf_by_id(tid), f"{app} CF {tid} missing"
        for gid in qp.ANIME_GROUPS[app]:
            assert dm.get_include_data(app, gid), f"{app} group {gid} missing"


def test_three_instances_end_to_end(dm, tmp_path):
    """Films (Radarr), Séries (Sonarr), Animés (Sonarr): MULTi > VF > VOSTFR, anime without VF, x265 + AV1 OK."""
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor
    app = QApplication.instance() or QApplication([])

    setups = [
        ("radarr", "films", False, "hd-bluray-web", ["multi", "vf", "vostfr"]),
        ("sonarr", "series", False, "hd-bluray-web", ["multi", "vf", "vostfr"]),
        ("sonarr", "animes", True, "anime", ["multi", "vostfr"]),
    ]
    cfg = RecyclarrConfiguration()
    for app_type, name, anime, tier, ranking in setups:
        ed = InstanceEditor(dm, app_type)
        ed.config.name = name
        ed.apply_quick_profile(anime, tier, ranking, accept_x265=True, accept_av1=True)
        for tab in (1, 2, 3, 0):  # visiting acts must not lose anything
            ed.tabs.setCurrentIndex(tab)
        getattr(cfg, f"{app_type}_instances").append(ed.get_config())

    gen = YAMLGenerator()
    out = gen.load_yaml(gen.generate_config(cfg, filename=str(tmp_path / "quick.yml")))

    films = out["radarr"]["films"]
    assert films["quality_definition"]["type"] == "movie"
    assert films["quality_profiles"][0]["trash_id"] == qp.FRENCH_PROFILES["radarr"]["hd-bluray-web"]["multi-vf"]

    animes = out["sonarr"]["animes"]
    assert animes["quality_definition"]["type"] == "anime"
    assert animes["quality_profiles"][0]["trash_id"] == qp.ANIME_PROFILE["sonarr"]
    assert animes["quality_profiles"][0]["score_set"] == "french-anime-multi"
    assert {g["trash_id"] for g in animes["custom_format_groups"]["add"]} == set(qp.ANIME_GROUPS["sonarr"])

    def score(instance, app_type, tid):
        entry = next(e for e in instance["custom_formats"] if tid in e["trash_ids"])
        return entry["assign_scores_to"][0]["score"]

    for instance, app_type in ((films, "radarr"), (out["sonarr"]["series"], "sonarr"), (animes, "sonarr")):
        profile_name = instance["quality_profiles"][0]["name"]
        for entry in instance["custom_formats"]:
            assert [a["name"] for a in entry["assign_scores_to"]] == [profile_name]
        for tid in sum(qp.CODEC_CFS[app_type].values(), []):
            assert score(instance, app_type, tid) == 0

    # Anime: VF only is rejected
    assert score(animes, "sonarr", qp.LANGUAGE_CFS["sonarr"]["not_original"]) <= qp.REJECT


def _wizard_instance(dm, tmp_path, app_type, anime, tier, ranking):
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor
    app = QApplication.instance() or QApplication([])
    ed = InstanceEditor(dm, app_type)
    ed.config.name = "x"
    ed.apply_quick_profile(anime, tier, ranking, accept_x265=True, accept_av1=True)
    gen = YAMLGenerator()
    cfg = RecyclarrConfiguration(**{f"{app_type}_instances": [ed.get_config()]})
    return gen.load_yaml(gen.generate_config(cfg, filename=str(tmp_path / f"{app_type}{anime}.yml")))[app_type]["x"]


@pytest.mark.parametrize("app_type,template", [("radarr", "french-multi-vf-hd-bluray-web"), ("sonarr", "french-multi-vf-bluray-web-1080p")])
def test_wizard_matches_official_template_except_overrides(dm, tmp_path, app_type, template):
    """Effective profile (simulated Recyclarr sync) = official v8 template + only the language/codec overrides."""
    from recyclarr_sim import resolve
    official = list(dm.get_template_by_name(app_type, template)["content"][app_type].values())[0]
    (_, ref), = resolve(official, app_type, dm).items()
    (_, got), = resolve(_wizard_instance(dm, tmp_path, app_type, False, "hd-bluray-web", ["multi", "vf", "vostfr"]), app_type, dm).items()

    overridden = set(qp.LANGUAGE_CFS[app_type].values()) | set(sum(qp.CODEC_CFS[app_type].values(), []))
    for key in ("leaves", "cutoff", "until_score", "min_score", "score_set", "upgrade"):
        assert got[key] == ref[key], key
    assert {t: s for t, s in got["cfs"].items() if t not in overridden} == {t: s for t, s in ref["cfs"].items() if t not in overridden}


def test_wizard_anime_keeps_french_release_groups(dm, tmp_path):
    """Former v7 French anime recipe: FR anime/FR release group tiers scored, BR-DISK and FastSUB rejected."""
    from recyclarr_sim import resolve
    (_, got), = resolve(_wizard_instance(dm, tmp_path, "sonarr", True, "anime", ["multi", "vostfr"]), "sonarr", dm).items()
    names = {c["trash_id"]: c["name"] for c in dm.get_custom_formats_for_app("sonarr")}
    by_name = {names[t]: s for t, s in got["cfs"].items()}
    for tier in ("FR Anime Tier 01", "FR Anime Tier 02", "FR Anime Tier 03", "FR Anime FanSub", "FR Scene Groups", "FR WEB Tier 01"):
        assert by_name.get(tier, 0) > 0, tier
    for unwanted in ("BR-DISK", "FastSUB", "FR LQ"):
        assert by_name.get(unwanted, 0) <= qp.REJECT, unwanted
